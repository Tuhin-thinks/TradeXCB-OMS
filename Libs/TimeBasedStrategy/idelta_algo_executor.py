import datetime
import sys
from copy import deepcopy

import openpyxl
import pandas as pd
from PyQt5 import QtCore
from colorama import Fore, Back, Style
from kiteconnect import KiteConnect, KiteTicker

from Libs.globals import *
from . import config, GetUserSession
from .Utils import ATM_parser

nine_fifteen = datetime.datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
three_thirty = datetime.datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)

logger = exception_handler.getIDeltaLogger("algo_executor")
future_logger = exception_handler.getFutureLogger("algo_executor")


def fix_values(value, tick_size_stock):
    return round(int(value / tick_size_stock) * tick_size_stock, len(str(tick_size_stock)))


class AlgoExecutor(QtCore.QObject):
    status = QtCore.pyqtSignal(object)
    error_stop = QtCore.pyqtSignal(object)  # signal to emit, when code stops due to error
    signal_stop_strategy_timer = QtCore.pyqtSignal()

    def __init__(self, paper_trade: int):
        super(AlgoExecutor, self).__init__()
        self.atm_pe_list = None
        self.atm_ce_list = None
        self.instruments_to_subscribe = None
        self.latest_ltp = None
        self.stop_flag = False
        self.algo_running = False
        self.df_dict_ = None
        self.paper_trade = paper_trade
        self.nfo_nse_map = None
        self.algo_timer = None
        self.order_history_timer = None
        self.orders_history = None
        self.instrumentFile = None
        self.symbol_mapping_df = None
        self.ztoken = None
        self.kite = None
        self.kws = None
        self.web_socket = None

        # error stop signal
        self.signal_stop_strategy_timer.connect(self.stop_strategy_timer)

    def start_strategy_timer(self):
        tasks_ = [
            self.init_instruments_file,
            self.init_token,
            self.read_excel_file,
            self.start_order_history_timer,
            self.start_algo_timer
        ]
        for fn in tasks_:
            if not self.stop_flag:
                try:
                    fn()
                except Exception as e:
                    future_logger.critical(f"Failed to run algorithm, error reason: {e.__str__()}", exc_info=True)
                    self.stop_strategy_timer()
                    error_string = e.__str__()
                    if "list index out of range" in error_string:
                        error_string = "Invalid configuration in Trading Symbol Mapping"
                    self._do_error_stop(error_string)
            else:
                self.stop_strategy_timer()
                break

    def stop_strategy_timer(self):
        try:
            self.stop_flag = True
            self.algo_timer.stop()
            self.order_history_timer.stop()
        except Exception as e:
            # logger.warning(f"Error in stopping : {e.__str__()}")
            pass

    def _do_error_stop(self, error_msg: str):
        try:
            self.error_stop.emit("Algorithm stopped with error: " + error_msg)
        except Exception:
            pass

    def init_instruments_file(self):
        config.download_instruments_file()  # download file based on conditions
        self.symbol_mapping_df = config.load_symbols_mapping_file()
        self.instrumentFile = pd.read_csv(settings.DATA_FILES['INSTRUMENTS_CSV'])

    def init_token(self):
        future_logger.debug("connecting to kite...")
        self.ztoken = GetUserSession.ZerodhaAccessToken()
        self.kite = KiteConnect(api_key=self.ztoken.apiKey)
        self.kite.set_access_token(self.ztoken.access_token)
        future_logger.debug("Token initialized....")
        self.kws = KiteTicker(self.ztoken.apiKey, self.ztoken.access_token, self.ztoken.accountUserName)
        self.kws.debug = False
        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.connect(threaded=True)
        future_logger.debug("waiting 10secs...")
        time.sleep(10)
        future_logger.debug("wait completed...")
        future_logger.debug("successfully connected")

    def read_excel_file(self):
        future_logger.debug("reading excel file...")
        df = pd.read_excel(settings.DATA_FILES.get('Delta_plus_Algo_File'))
        future_logger.debug("data loaded successfully...")
        ce_instruments_list = []
        pe_instruments_list = []

        # ============== create ce/pe instruments from symbol name input ===============
        self.instrumentFile['days2expire'] = self.instrumentFile['expiry'].apply(
            lambda _row: (pd.to_datetime(_row) - datetime.datetime.now()).days + 1)
        instrumentFile = self.instrumentFile[
            (self.instrumentFile.days2expire <= settings.INSTRUMENTS_EXPIRY_THRESHOLD) &
            (self.instrumentFile.days2expire >= 0)]
        nfo_symbols_array, self.nfo_nse_map = ATM_parser.create_symbols_mapping(
            settings.DATA_FILES.get("Delta_plus_Algo_File")
        )
        self.atm_ce_list = []
        self.atm_pe_list = []
        atm_ce_cache = dict()
        atm_pe_cache = dict()
        future_logger.info("Please wait, Calculating ATM CE/PE instruments...")
        for exchange, symbol_name_, atm_ce, atm_pe, expiry_date in zip(df['Exchange'], df['Symbol Name'],
                                                                       df["CE_Instrument"], df["PE_Instrument"],
                                                                       df["Expiry Date"]):
            mapped_symbol_name = self.nfo_nse_map[symbol_name_]
            expiry_string = str(expiry_date).split()[0]
            self.atm_ce_list.append(atm_ce)
            self.atm_pe_list.append(atm_pe)
            if f"CE_{exchange}_{mapped_symbol_name}" not in atm_ce_cache:
                ce_instrument = ATM_parser.get_strikes(self.kite, instrumentFile, symbol_name_, mapped_symbol_name,
                                                       atm_ce, "CE", expiry_string, exchange)
                atm_ce_cache[f"CE_{exchange}_{mapped_symbol_name}_{expiry_string}"] = ce_instrument
            else:
                ce_instrument = atm_ce_cache[f"CE_{exchange}_{mapped_symbol_name}_{expiry_string}"]

            if f"PE_{exchange}_{mapped_symbol_name}" not in atm_pe_cache:
                pe_instrument = ATM_parser.get_strikes(self.kite, instrumentFile, symbol_name_, mapped_symbol_name,
                                                       atm_pe, "PE", expiry_string, exchange)
                atm_pe_cache[f"PE_{exchange}_{mapped_symbol_name}_{expiry_string}"] = pe_instrument
            else:
                pe_instrument = atm_pe_cache[f"PE_{exchange}_{mapped_symbol_name}_{expiry_string}"]

            ce_instruments_list.append(ce_instrument)
            pe_instruments_list.append(pe_instrument)

        # ---------------- build the dataframe with instruments/instrument token --------------------
        df['CE_Instrument'] = ce_instruments_list
        df['PE_Instrument'] = pe_instruments_list
        df['CE_Instrument_Order_Id'] = None
        df['PE_Instrument_Order_Id'] = None
        df['CE_Instrument_Entry_Price'] = None
        df['PE_Instrument_Entry_Price'] = None
        df['CE_Instrument_Exit_Price'] = None
        df['PE_Instrument_Exit_Price'] = None
        df['CE_Profit'] = None
        df['PE_Profit'] = None
        df['SL_CE'] = None
        df['SL_PE'] = None
        df['SL_CE_SET'] = 0
        df['SL_PE_SET'] = 0
        df['CE_Target_Set'] = 0
        df['PE_Target_Set'] = 0
        # ------------- Target ------------------
        df['CE_Target'] = None
        df['PE_Target'] = None

        df['Order_Placed'] = 0
        df['Completed'] = 0
        df['Executed'] = 0
        df['Order_Placement_Time'] = None
        df['SL_CE_Value'] = None
        df['SL_PE_Value'] = None
        df['Order_Entry_Time'] = None
        df['Order_Exit_Time'] = None
        df['Index'] = range(len(df))  # generate indices automatically
        df = df.dropna(axis=0, subset=['Transaction_Type'])
        df.index = df['Index']
        logger.debug(df)
        logger.debug(len(df))
        main_df_dict = df.to_dict('index')
        logger.debug("Excel file read done.")
        self.latest_ltp = dict()
        self.instruments_to_subscribe = []
        for x in list(main_df_dict):
            exchange = main_df_dict[x]['Exchange']
            entry_time = str(main_df_dict[x]['Entry_Time']).split('.')
            exit_time = str(main_df_dict[x]['Exit_Time']).split('.')
            main_df_dict[x]['Entry_Time'] = datetime.time(int(entry_time[0]), int(entry_time[1]), int(entry_time[2]))
            main_df_dict[x]['Exit_Time'] = datetime.time(int(exit_time[0]), int(exit_time[1]), int(exit_time[2]))

            main_df_dict[x]['CE_Instrument_Token'] = self.get_instrument_token(main_df_dict[x]['CE_Instrument'],
                                                                               exchange)
            main_df_dict[x]['PE_Instrument_Token'] = self.get_instrument_token(main_df_dict[x]['PE_Instrument'],
                                                                               exchange)

            lot_size = instrumentFile[instrumentFile['instrument_token'] == main_df_dict[x]['CE_Instrument_Token']][
                'lot_size'].values.tolist()[0]
            main_df_dict[x]['quantity'] = int(main_df_dict[x]['No. of lots']) * lot_size  # added quantity calculation

            self.latest_ltp[main_df_dict[x]['CE_Instrument_Token']] = None
            self.latest_ltp[main_df_dict[x]['PE_Instrument_Token']] = None

            self.instruments_to_subscribe.append(int(main_df_dict[x]['CE_Instrument_Token']))
            self.instruments_to_subscribe.append(int(main_df_dict[x]['PE_Instrument_Token']))

            if main_df_dict[x]['Entry_Time'] >= main_df_dict[x]['Exit_Time']:
                logger.warning(f"'Entry_time' is greater than 'Exit_time', for index: {x}")
                self.stop_flag = True
                self.error_stop.emit("Entry time cannot be greater or equals to Exit time")
                return
            if main_df_dict[x]['CE_Instrument'] is None:
                logger.warning("Error Instrument is Empty.")
            if main_df_dict[x]['PE_Instrument'] is None:
                logger.warning("Error Instrument is Empty.")

        logger.debug(self.instruments_to_subscribe)
        self.subs(self.instruments_to_subscribe)
        time.sleep(5)
        logger.info("Starting the Algorithm Now.")
        # ----------- save paper trade value to excel -----------------
        wb = openpyxl.load_workbook(settings.DATA_FILES.get('Delta_plus_Algo_File'))
        settings_sheet = wb['Settings']
        settings_sheet.cell(row=2, column=1).value = self.paper_trade
        wb.save(settings.DATA_FILES.get('Delta_plus_Algo_File'))
        self.df_dict_ = main_df_dict

    # =========================== MAIN ALGORITHM =====================
    def main_algorithm(self):
        if self.algo_running:
            return
        pnl_df = pd.DataFrame()
        for _key in list(self.df_dict_):
            if self.stop_flag:
                self.stop_strategy_timer()
                return

            this_row = self.df_dict_[_key]
            _entry_time = this_row['Entry_Time']
            if datetime.datetime.now().time() < _entry_time:  # if entry time in future
                print(f"Skipping {this_row['Symbol Name']} entry time hasn't reached yet.")
                continue
            instruments_ltp_1 = self.latest_ltp[this_row['CE_Instrument_Token']]
            instruments_ltp_2 = self.latest_ltp[this_row['PE_Instrument_Token']]
            if instruments_ltp_1 is None:
                logger.warning(f"Ltp for {this_row['CE_Instrument_Token']} is None. Continuing")
                continue
            elif instruments_ltp_2 is None:
                logger.warning(f"Ltp for {this_row['PE_Instrument_Token']} is None. Continuing")
                continue
            # print(instruments_ltp_2,instruments_ltp_1)
            try:
                if this_row['Order_Placed'] == 0 and this_row['Completed'] == 0:
                    if this_row['Entry_Time'] <= datetime.datetime.now().time() <= this_row['Exit_Time']:
                        # Place and Order
                        if this_row['Transaction_Type'].upper() == 'BUY':
                            this_row['Order_Placement_Time'] = datetime.datetime.now()
                            this_row['Order_Placed'] = 1
                            this_row['CE_Instrument_Entry_Price'] = fix_values(
                                instruments_ltp_1 * (1 + this_row['Buy_Ltp_Percent'] / 100), 0.05)
                            this_row['PE_Instrument_Entry_Price'] = fix_values(
                                instruments_ltp_2 * (1 + this_row['Buy_Ltp_Percent'] / 100), 0.05)

                            if self.paper_trade == 0:
                                this_row['CE_Instrument_Order_Id'] = \
                                    self.kite.place_order(
                                        variety='regular',
                                        exchange=this_row['Exchange'],
                                        tradingsymbol=this_row['CE_Instrument'],
                                        transaction_type=this_row['Transaction_Type'].upper(),
                                        quantity=this_row['quantity'],
                                        product='MIS', order_type='LIMIT',
                                        price=fix_values(
                                            instruments_ltp_1 * (1 - this_row['Buy_Ltp_Percent'] / 100),
                                            0.05), validity='DAY'
                                    )
                                this_row['PE_Instrument_Order_Id'] = self.kite.place_order(
                                    variety='regular',
                                    exchange=this_row['Exchange'],
                                    tradingsymbol=this_row['PE_Instrument'],
                                    transaction_type=this_row['Transaction_Type'].upper(),
                                    quantity=this_row['quantity'],
                                    product='MIS', order_type='LIMIT',
                                    price=fix_values(instruments_ltp_2 * (1 - this_row['Buy_Ltp_Percent'] / 100),
                                                     0.05),
                                    validity='DAY')
                            logger.info(f"Order Placed {this_row} ")

                        elif this_row['Transaction_Type'].upper() == 'SELL':
                            this_row['Order_Placement_Time'] = datetime.datetime.now()
                            this_row['Order_Placed'] = 1
                            this_row['CE_Instrument_Entry_Price'] = fix_values(
                                instruments_ltp_1 * (1 + this_row['Sell_Ltp_Percent'] / 100), 0.05)
                            this_row['PE_Instrument_Entry_Price'] = fix_values(
                                instruments_ltp_2 * (1 + this_row['Sell_Ltp_Percent'] / 100), 0.05)

                            if self.paper_trade == 0:
                                this_row['CE_Instrument_Order_Id'] = self.kite.place_order(
                                    variety='regular',
                                    exchange=this_row['Exchange'],
                                    tradingsymbol=this_row['CE_Instrument'],
                                    transaction_type=this_row['Transaction_Type'].upper(),
                                    quantity=this_row['quantity'],
                                    product='MIS', order_type='LIMIT',
                                    price=fix_values(instruments_ltp_1 * (1 + this_row['Sell_Ltp_Percent'] / 100),
                                                     0.05), validity='DAY')
                                this_row['PE_Instrument_Order_Id'] = self.kite.place_order(
                                    variety='regular',
                                    exchange=this_row['Exchange'],
                                    tradingsymbol=this_row['PE_Instrument'],
                                    transaction_type=this_row['Transaction_Type'].upper(),
                                    quantity=this_row['quantity'],
                                    product='MIS', order_type='LIMIT',
                                    price=fix_values(instruments_ltp_2 * (1 + this_row['Sell_Ltp_Percent'] / 100),
                                                     0.05), validity='DAY')

                            logger.info(f"Order Placed {this_row} ")

                elif this_row['Order_Placed'] == 1 and this_row['Completed'] == 0 and this_row['Executed'] == 0:
                    # logger.info(f"Order Placed {this_row} ")

                    if self.paper_trade == 1:
                        if this_row['Transaction_Type'].upper() == 'BUY':

                            if instruments_ltp_1 <= this_row['CE_Instrument_Entry_Price']:
                                this_row['PE_Instrument_Entry_Price'] = instruments_ltp_2
                                this_row['Executed'] = 1
                                this_row['Order_Entry_Time'] = datetime.datetime.now()
                                logger.info(
                                    f"Instrument 1 Executed. Executing 2nd Instrument {instruments_ltp_1} {this_row['CE_Instrument_Entry_Price']}")
                                logger.info(f"{this_row}")

                            elif instruments_ltp_2 <= this_row['PE_Instrument_Entry_Price']:
                                this_row['CE_Instrument_Entry_Price'] = instruments_ltp_1
                                this_row['Executed'] = 1
                                this_row['Order_Entry_Time'] = datetime.datetime.now()
                                logger.info(
                                    f"Instrument 2 Executed. Executing 1st Instrument {instruments_ltp_2} {this_row['PE_Instrument_Entry_Price']}")
                                logger.info(f"{this_row}")

                            if ((datetime.datetime.now() - this_row['Order_Placement_Time']).seconds >=
                                    this_row['Wait_Time']):
                                this_row['CE_Instrument_Entry_Price'] = instruments_ltp_1
                                this_row['PE_Instrument_Entry_Price'] = instruments_ltp_2
                                this_row['Executed'] = 1
                                this_row['Order_Entry_Time'] = datetime.datetime.now()
                                logger.info("Shifting Orders to Market as wait time has passed.")
                                logger.info(f"{this_row}")

                        if this_row['Transaction_Type'].upper() == 'SELL':

                            if instruments_ltp_1 >= this_row['CE_Instrument_Entry_Price']:
                                this_row['PE_Instrument_Entry_Price'] = instruments_ltp_2
                                this_row['Executed'] = 1
                                this_row['Order_Entry_Time'] = datetime.datetime.now()
                                logger.info(
                                    f"Instrument 1 Executed. Executing 2nd Instrument {instruments_ltp_1} {this_row['CE_Instrument_Entry_Price']}")
                                logger.info(f"{this_row}")

                            elif instruments_ltp_2 >= this_row['PE_Instrument_Entry_Price']:
                                this_row['CE_Instrument_Entry_Price'] = instruments_ltp_1
                                this_row['Executed'] = 1
                                this_row['Order_Entry_Time'] = datetime.datetime.now()
                                logger.info(
                                    f"Instrument 2 Executed. Executing 1st Instrument {instruments_ltp_2} {this_row['PE_Instrument_Entry_Price']}")
                                logger.info(f"{this_row}")

                            if (datetime.datetime.now() - this_row['Order_Placement_Time']).seconds >= \
                                    this_row['Wait_Time']:
                                logger.info("Shifting Orders to Market")
                                this_row['CE_Instrument_Entry_Price'] = instruments_ltp_1
                                this_row['PE_Instrument_Entry_Price'] = instruments_ltp_2
                                this_row['Executed'] = 1
                                this_row['Order_Entry_Time'] = datetime.datetime.now()
                                logger.info("Shifting Orders to Market as wait time has passed.")
                                logger.info(f"{this_row}")

                    if self.paper_trade == 0:

                        order_status_CE_Instrument = self.order_status(this_row['CE_Instrument_Order_Id'])
                        order_status_PE_Instrument = self.order_status(this_row['PE_Instrument_Order_Id'])

                        logger.info(f"{order_status_CE_Instrument},{order_status_PE_Instrument}")
                        logger.info(
                            f"{(datetime.datetime.now() - this_row['Order_Placement_Time']).seconds}," + f" {this_row['Wait_Time']}")

                        if order_status_CE_Instrument == 'COMPLETE' and order_status_PE_Instrument != 'COMPLETE':
                            self.kite.modify_order(variety='regular', order_id=this_row['PE_Instrument_Order_Id'],
                                                   order_type='MARKET')
                            this_row['Executed'] = 1
                            this_row['Order_Entry_Time'] = datetime.datetime.now()
                            logger.info(f"Instrument 1 Executed. Executing 2nd Instrument")
                            this_row['PE_Instrument_Entry_Price'] = instruments_ltp_2
                            logger.info(f"{this_row}")

                        elif order_status_CE_Instrument != 'COMPLETE' and order_status_PE_Instrument == 'COMPLETE':
                            self.kite.modify_order(variety='regular', order_id=this_row['CE_Instrument_Order_Id'],
                                                   order_type='MARKET')
                            logger.info(f"Instrument 2 Executed. Executing 1st Instrument")
                            this_row['CE_Instrument_Entry_Price'] = instruments_ltp_1
                            logger.info(f"{this_row}")
                            this_row['Order_Entry_Time'] = datetime.datetime.now()
                            this_row['Executed'] = 1

                        if ((datetime.datetime.now() - this_row['Order_Placement_Time']).seconds >=
                                this_row['Wait_Time']):
                            this_row['CE_Instrument_Entry_Price'] = instruments_ltp_1
                            this_row['PE_Instrument_Entry_Price'] = instruments_ltp_2
                            this_row['Order_Entry_Time'] = datetime.datetime.now()
                            logger.info("Shifting Orders to Market as wait time has passed.")
                            logger.info(f"{this_row}")
                            try:
                                if order_status_PE_Instrument != 'COMPLETE':
                                    this_row['Executed'] = 1
                                    self.kite.modify_order(variety='regular',
                                                           order_id=this_row['PE_Instrument_Order_Id'],
                                                           order_type='MARKET')
                            except:
                                pass
                            try:
                                if order_status_CE_Instrument != 'COMPLETE':
                                    this_row['Executed'] = 1
                                    self.kite.modify_order(variety='regular',
                                                           order_id=this_row['CE_Instrument_Order_Id'],
                                                           order_type='MARKET')
                            except:
                                pass

                if this_row['Executed'] == 1 and this_row['Completed'] == 0:

                    if this_row['Transaction_Type'].upper() == 'BUY':

                        this_row['CE_Profit'] = (instruments_ltp_1 - this_row['CE_Instrument_Entry_Price']) * \
                                                this_row[
                                                    'quantity']

                        this_row['PE_Profit'] = (instruments_ltp_2 - this_row['PE_Instrument_Entry_Price']) * \
                                                this_row[
                                                    'quantity']
                        # --------------------------------- -----------------------------------------
                        if this_row['SL_CE_SET'] == 0:
                            this_row['SL_CE_SET'] = 1
                            if this_row['stoploss_type'] == 'Percentage':
                                this_row['SL_CE'] = (this_row['CE_Instrument_Entry_Price']) * (
                                        1 - this_row['CE_Stoploss'] / 100)
                                this_row['SL_CE_Value'] = (this_row['CE_Instrument_Entry_Price']) * this_row[
                                    'CE_Stoploss'] / 100

                            if this_row['stoploss_type'] == 'Value':
                                this_row['SL_CE'] = (this_row['CE_Instrument_Entry_Price']) - this_row[
                                    'CE_Stoploss']
                                this_row['SL_CE_Value'] = this_row['CE_Stoploss']

                        if this_row['SL_PE_SET'] == 0:
                            this_row['SL_PE_SET'] = 1
                            if this_row['stoploss_type'] == 'Percentage':
                                this_row['SL_PE'] = (this_row['PE_Instrument_Entry_Price']) * (
                                        1 - this_row['PE_Stoploss'] / 100)
                                this_row['SL_PE_Value'] = (this_row['PE_Instrument_Entry_Price']) * this_row[
                                    'PE_Stoploss'] / 100

                            if this_row['stoploss_type'] == 'Value':
                                this_row['SL_PE'] = (this_row['PE_Instrument_Entry_Price']) - this_row[
                                    'PE_Stoploss']
                                this_row['SL_PE_Value'] = this_row['PE_Stoploss']
                        # --------------------------------- -----------------------------------------

                        if this_row['CE_Target_Set'] == 0 or this_row['PE_Target_Set'] == 0:

                            if this_row['CE_Target_Set'] == 0:
                                this_row['CE_Target_Set'] = 1
                            elif this_row['PE_Target_Set'] == 0:
                                this_row['PE_Target_Set'] = 1

                            if this_row['target_type'] == 'Percentage':
                                this_row['CE_Target'] = ((this_row['CE_Instrument_Entry_Price']) *
                                                         (1 + this_row['CE_target'] / 100))
                                this_row['PE_Target'] = ((this_row['PE_Instrument_Entry_Price']) *
                                                         (1 + this_row['PE_target'] / 100))
                            if this_row['target_type'] == 'Value':
                                this_row['CE_Target'] = this_row['CE_Instrument_Entry_Price'] + this_row[
                                    'CE_target']
                                this_row['PE_Target'] = this_row['PE_Instrument_Entry_Price'] + this_row[
                                    'PE_target']

                        if (this_row['SL_CE_SET'] == 1) or (this_row['SL_PE_SET'] == 1):
                            old_SL_CE = this_row['SL_CE']
                            old_SL_PE = this_row['SL_PE']
                            if this_row['tsl_type'] == 'Percentage':
                                # ---------------------------------- ----------------------------------
                                # ------------------>>> for sl_1
                                if self.latest_ltp[this_row['CE_Instrument_Token']] > (
                                        (this_row['CE_Instrument_Entry_Price']) *
                                        (1 + this_row['CE_TSL'] / 100)):
                                    temp_ = instruments_ltp_1 - this_row['SL_CE_Value']
                                else:
                                    temp_ = this_row['SL_CE']
                                this_row['SL_CE'] = temp_
                                # ------------------>>> for sl_2
                                if self.latest_ltp[this_row['PE_Instrument_Token']] > (
                                        this_row['PE_Instrument_Entry_Price'] *
                                        (1 + this_row['PE_TSL'] / 100)):
                                    temp_ = instruments_ltp_2 - this_row['SL_PE_Value']
                                else:
                                    temp_ = this_row['SL_PE']
                                this_row['SL_PE'] = temp_
                                # --------------------------------- ----------------------------------

                            if this_row['tsl_type'] == 'Value':
                                # -------------------------- --------------------------------------------
                                if instruments_ltp_1 > (this_row['CE_Instrument_Entry_Price']) + this_row['CE_TSL']:
                                    temp_ = instruments_ltp_1 - this_row['SL_CE_Value']
                                else:
                                    temp_ = this_row['SL_CE']
                                logger.info(f"Trailing SL_CE from {old_SL_CE} to {this_row['SL_CE']}")
                                this_row['SL_CE'] = temp_

                                if instruments_ltp_2 > (this_row['PE_Instrument_Entry_Price']) + this_row['PE_TSL']:
                                    temp_ = instruments_ltp_2 - this_row['SL_PE_Value']
                                else:
                                    temp_ = this_row['SL_PE']
                                logger.info(f"Trailing SL_PE from {old_SL_PE} to {this_row['SL_PE']}")
                                this_row['SL_PE'] = temp_
                                # ---------------------------------- ------------------------------------

                        # ---------------------------condition and assignment modified here--------------------------
                        if instruments_ltp_1 < this_row['SL_CE'] and this_row['SL_CE_SET'] == 1:

                            logger.info(f"SL_CE has been Hit")
                            this_row['CE_Instrument_Exit_Price'] = instruments_ltp_1
                            logger.info(this_row)
                            this_row['Order_Placed'] = 0
                            this_row['Order_Placement_Time'] = None
                            order_placement_time = None
                            this_row['Completed'] = 1
                            if self.paper_trade == 0:
                                self.close_position(symbol_name=this_row['CE_Instrument'])

                        if instruments_ltp_2 < this_row['SL_PE'] and this_row['SL_PE_SET'] == 1:

                            logger.info(f"SL_PE has been Hit")
                            this_row['PE_Instrument_Exit_Price'] = instruments_ltp_2
                            logger.info(this_row)
                            this_row['Order_Placed'] = 0
                            this_row['Order_Placement_Time'] = None
                            order_placement_time = None
                            this_row['Completed'] = 1
                            if self.paper_trade == 0:
                                self.close_position(symbol_name=this_row['PE_Instrument'])

                        # --------------------------------------- ---------------------------------------

                        if instruments_ltp_1 >= this_row['CE_Target'] and this_row['CE_Target_Set'] == 1:
                            logger.info(f"CE_Target has been Hit")
                            this_row['CE_Instrument_Exit_Price'] = instruments_ltp_1
                            logger.info(this_row)
                            this_row['Order_Placed'] = 0
                            this_row['Order_Placement_Time'] = None
                            order_placement_time = None
                            this_row['Completed'] = 1
                            if self.paper_trade == 0:
                                self.close_position(symbol_name=this_row['CE_Instrument'])

                        if instruments_ltp_2 >= this_row['PE_Target'] and this_row['PE_Target_Set'] == 1:
                            logger.info(f"PE_Target has been Hit")
                            this_row['PE_Instrument_Exit_Price'] = instruments_ltp_2
                            logger.info(this_row)
                            this_row['Order_Placed'] = 0
                            this_row['Order_Placement_Time'] = None
                            order_placement_time = None
                            this_row['Completed'] = 1
                            if self.paper_trade == 0:
                                self.close_position(symbol_name=this_row['PE_Instrument'])

                    if this_row['Transaction_Type'].upper() == 'SELL':

                        this_row['CE_Profit'] = ((this_row['CE_Instrument_Entry_Price'] - instruments_ltp_1) *
                                                 this_row['quantity'])
                        this_row['PE_Profit'] = ((this_row['PE_Instrument_Entry_Price'] - instruments_ltp_2) *
                                                 this_row['quantity'])

                        if this_row['SL_CE_SET'] == 0 or this_row['SL_PE_SET'] == 0:
                            if this_row['SL_CE_SET'] == 0:
                                this_row['SL_CE_SET'] = 1
                            else:
                                this_row['SL_PE_SET'] = 1

                            if this_row['stoploss_type'] == 'Percentage':
                                this_row['SL_CE'] = ((this_row['CE_Instrument_Entry_Price']) *
                                                     (1 + this_row['CE_Stoploss'] / 100))
                                this_row['SL_PE'] = ((this_row['PE_Instrument_Entry_Price']) *
                                                     (1 + this_row['PE_Stoploss'] / 100))
                                this_row['SL_CE_Value'] = (
                                        this_row['CE_Instrument_Entry_Price'] * this_row['CE_Stoploss'] / 100)
                                this_row['SL_PE_Value'] = (
                                        this_row['PE_Instrument_Entry_Price'] * this_row['PE_Stoploss'] / 100)

                            if this_row['stoploss_type'] == 'Value':
                                this_row['SL_CE'] = ((this_row['CE_Instrument_Entry_Price']) +
                                                     this_row['CE_Stoploss'])
                                this_row['SL_CE_Value'] = this_row['CE_Stoploss']

                                this_row['SL_PE'] = ((this_row['PE_Instrument_Entry_Price']) +
                                                     this_row['PE_Stoploss'])
                                this_row['SL_PE_Value'] = this_row['PE_Stoploss']

                        if this_row['CE_Target_Set'] == 0 or this_row['PE_Target_Set'] == 0:
                            if this_row['CE_Target_Set'] == 0:
                                this_row['CE_Target_Set'] = 1
                            else:
                                this_row['PE_Target_Set'] = 1

                            if this_row['target_type'] == 'Percentage':
                                this_row['CE_Target'] = (this_row['CE_Instrument_Entry_Price']) * (
                                        1 - this_row['CE_target'] / 100)
                                this_row['PE_Target'] = (this_row['PE_Instrument_Entry_Price']) * (
                                        1 - this_row['PE_target'] / 100)
                            if this_row['target_type'] == 'Value':
                                this_row['CE_Target'] = (this_row['CE_Instrument_Entry_Price']) - this_row[
                                    'CE_target']
                                this_row['PE_Target'] = (this_row['PE_Instrument_Entry_Price']) - this_row[
                                    'PE_target']

                        if this_row['SL_CE_SET'] == 1 or this_row['SL_PE_SET'] == 1:
                            old_SL_CE = this_row['SL_CE']
                            old_SL_PE = this_row['SL_PE']

                            if this_row['tsl_type'] == 'Percentage':
                                if instruments_ltp_1 < ((this_row['CE_Instrument_Entry_Price']) *
                                                        (1 - this_row['CE_TSL'] / 100)):
                                    temp_ = instruments_ltp_1 + this_row['SL_CE_Value']
                                else:
                                    temp_ = this_row['SL_CE']
                                this_row['SL_CE'] = temp_
                                logger.info(f"Trailing SL_CE from {old_SL_CE} to {this_row['SL_CE']}")

                            if this_row['tsl_type'] == 'Percentage':
                                if instruments_ltp_2 < ((this_row['PE_Instrument_Entry_Price']) *
                                                        (1 - this_row['PE_TSL'] / 100)):
                                    temp_ = instruments_ltp_2 + this_row['SL_PE_Value']
                                else:
                                    temp_ = this_row['SL_PE']
                                this_row['SL_PE'] = temp_
                                logger.info(f"Trailing SL_PE from {old_SL_PE} to {this_row['SL_PE']}")

                            if this_row['tsl_type'] == 'Value':
                                if instruments_ltp_1 < ((this_row['CE_Instrument_Entry_Price']) -
                                                        this_row['CE_TSL']):
                                    temp_ = instruments_ltp_1 + this_row['SL_CE_Value']
                                else:
                                    temp_ = this_row['SL_CE']

                                this_row['SL_CE'] = temp_

                                logger.info(f"Trailing SL_CE from {old_SL_CE} to {this_row['SL_CE']}")

                                if instruments_ltp_2 < ((this_row['PE_Instrument_Entry_Price']) -
                                                        this_row['PE_TSL']):
                                    temp_ = instruments_ltp_2 + this_row['SL_PE_Value']
                                else:
                                    temp_ = this_row['SL_PE']

                                this_row['SL_PE'] = temp_

                                logger.info(f"Trailing SL_PE from {old_SL_PE} to {this_row['SL_PE']}")

                        # -------------------------------- (sl) ----------------------------------------
                        if instruments_ltp_1 > this_row['SL_CE'] and this_row['SL_CE_SET'] == 1:

                            logger.info(f"SL_CE has been Hit")
                            this_row['CE_Instrument_Exit_Price'] = instruments_ltp_1
                            logger.info(this_row)
                            this_row['Order_Placed'] = 0
                            this_row['Order_Placement_Time'] = None
                            order_placement_time = None
                            this_row['Completed'] = 1
                            if self.paper_trade == 0:
                                self.close_position(symbol_name=this_row['CE_Instrument'])

                        if instruments_ltp_2 > this_row['SL_PE'] and this_row['SL_PE_SET'] == 1:

                            logger.info(f"SL_PE has been Hit")
                            this_row['PE_Instrument_Exit_Price'] = instruments_ltp_2
                            logger.info(this_row)
                            this_row['Order_Placed'] = 0
                            this_row['Order_Placement_Time'] = None
                            order_placement_time = None
                            this_row['Completed'] = 1
                            if self.paper_trade == 0:
                                self.close_position(symbol_name=this_row['PE_Instrument'])
                        # -------------------------------- ----------------------------------------

                        # ------------------------- (target) ----------------------------------------
                        if instruments_ltp_1 < this_row['CE_Target'] and this_row['CE_Target_Set'] == 1:

                            logger.info(f"CE_Target has been Hit")
                            this_row['CE_Instrument_Exit_Price'] = instruments_ltp_1
                            logger.info(this_row)
                            this_row['Order_Placed'] = 0
                            this_row['Order_Placement_Time'] = None
                            order_placement_time = None
                            this_row['Completed'] = 1
                            if self.paper_trade == 0:
                                self.close_position(symbol_name=this_row['CE_Instrument'])

                        if instruments_ltp_2 < this_row['PE_Target'] and this_row['PE_Target_Set'] == 1:

                            logger.info(f"PE_Target has been Hit")
                            this_row['PE_Instrument_Exit_Price'] = instruments_ltp_2
                            logger.info(this_row)
                            this_row['Order_Placed'] = 0
                            this_row['Order_Placement_Time'] = None
                            order_placement_time = None
                            this_row['Completed'] = 1
                            if self.paper_trade == 0:
                                self.close_position(symbol_name=this_row['PE_Instrument'])
                        # ------------------------------------- ---------------------------------------------

                    if datetime.datetime.now().time() >= this_row['Exit_Time']:
                        logger.info(f"Closing Positions as Exit time has passed.")
                        if self.paper_trade == 0:
                            self.close_position(symbol_name=this_row['CE_Instrument'])
                            self.close_position(symbol_name=this_row['PE_Instrument'])
                        this_row['PE_Instrument_Exit_Price'] = instruments_ltp_2
                        this_row['CE_Instrument_Exit_Price'] = instruments_ltp_1
                        logger.info(f"{this_row}")
                        this_row['Order_Placed'] = 0
                        this_row['Order_Placement_Time'] = None
                        order_placement_time = None
                        this_row['Completed'] = 1

                pnl_df = pnl_df.append(this_row, ignore_index=True)

                # -------------------- calculate VWAP --------------------
                ce_tokens = pnl_df.apply(lambda _row: f"{_row['Exchange']}:{_row['CE_Instrument']}",
                                         axis=1).values.tolist()
                pe_tokens = pnl_df.apply(lambda _row: f"{_row['Exchange']}:{_row['PE_Instrument']}",
                                         axis=1).values.tolist()
                quotes_ce = ATM_parser.get_quote(self.kite, ce_tokens)
                quotes_pe = ATM_parser.get_quote(self.kite, pe_tokens)

                temp_df = pd.DataFrame()
                avg_price_ce = [quotes_ce[token]['average_price'] for token in ce_tokens]
                avg_price_pe = [quotes_pe[token]['average_price'] for token in pe_tokens]
                last_price_ce = [quotes_ce[token]['last_price'] for token in ce_tokens]
                last_price_pe = [quotes_pe[token]['last_price'] for token in pe_tokens]
                temp_df["avg_price_ce"] = avg_price_ce
                temp_df["last_price_ce"] = last_price_ce
                temp_df["avg_price_pe"] = avg_price_pe
                temp_df["last_price_pe"] = last_price_pe
                temp_df['vwap_ce'] = temp_df.apply(
                    lambda _row: "CE above VWAP" if _row.last_price_ce > _row.avg_price_ce else "CE below VWAP",
                    axis=1)
                temp_df['vwap_pe'] = temp_df.apply(
                    lambda _row: "PE above VWAP" if _row.last_price_pe > _row.avg_price_pe else "PE below VWAP",
                    axis=1)

                pnl_df["VWAP_CE"] = temp_df['vwap_ce']
                pnl_df["VWAP_PE"] = temp_df['vwap_pe']
            except KeyboardInterrupt:
                return
            except:
                logger.info(str(sys.exc_info()))
                logger.warning(sys.exc_info())
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logger.info(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")

        # ---------- fetch current ltp based on entry time -------------
        new_df_dict_ = deepcopy(self.df_dict_)
        for _key in list(self.df_dict_):  # iterate on df_dict.keys()
            if self.stop_flag:
                self.stop_strategy_timer()
                return
            row = self.df_dict_[_key]
            _expiry_date = str(row['Expiry Date'])
            _symbol_name = row['Symbol Name']
            _mapped_symbol_name = self.nfo_nse_map[_symbol_name]
            _exchange = row['Exchange']
            _atm_ce = self.atm_ce_list[int(_key)]
            _atm_pe = self.atm_pe_list[int(_key)]
            _expiry_date_str = str(_expiry_date).split()[0]
            if datetime.datetime.now().time() <= row['Entry_Time']:
                _ce_instrument = ATM_parser.get_strikes(self.kite, self.instrumentFile, _symbol_name,
                                                        _mapped_symbol_name,
                                                        _atm_ce,
                                                        "CE", _expiry_date_str, _exchange)
                _pe_instrument = ATM_parser.get_strikes(self.kite, self.instrumentFile, _symbol_name,
                                                        _mapped_symbol_name,
                                                        _atm_pe,
                                                        "PE", _expiry_date_str, _exchange)
                new_df_dict_[_key]['CE_Instrument'] = _ce_instrument
                new_df_dict_[_key]['PE_Instrument'] = _pe_instrument
                print(f"\n{Fore.BLACK + Back.LIGHTCYAN_EX}New ce instrument: {_ce_instrument}{Style.RESET_ALL}")
                print(f"{Fore.BLACK + Back.LIGHTCYAN_EX}New pe instrument: {_pe_instrument}{Style.RESET_ALL}\n")
        del self.df_dict_
        self.df_dict_ = deepcopy(new_df_dict_)
        del new_df_dict_
        try:
            pnl_df[
                ['Order_Entry_Time', 'Exit_Time', 'CE_Instrument', 'PE_Instrument', 'CE_TSL', 'PE_TSL',
                 'CE_Instrument_Entry_Price', 'PE_Instrument_Entry_Price', 'CE_Instrument_Exit_Price',
                 'PE_Instrument_Exit_Price', 'SL_CE', 'SL_PE', 'CE_Target', 'PE_Target', 'quantity',
                 'Transaction_Type', 'CE_Profit', 'PE_Profit', "VWAP_CE", "VWAP_PE"]
            ].to_csv(settings.DATA_FILES.get("POSITIONS_FILE_NAME"))
        except Exception as e:
            print(f"{Fore.BLACK + Back.LIGHTYELLOW_EX}Failed to write to positions file,"
                  f" Error: {e.__str__()}{Style.RESET_ALL}")

            # ---------- clear the positions file (show only headers) --------------
            pnl_df = pd.DataFrame(columns=app_data.POSITIONS_COLUMNS, index=None)
            pnl_df.to_csv(settings.DATA_FILES.get("POSITIONS_FILE_NAME"))
        self.algo_running = False

    # =========================== XXXX END XXXX =====================

    # =========================== TIMER METHODS =========================
    def algo_timeout_check(self):
        if self.stop_flag:
            self.stop_strategy_timer()
            return
        try:
            self.main_algorithm()
        except Exception as e:
            error_msg = f"Algorithm stopped, Error reason: {e.__str__()}"
            future_logger.critical(error_msg)
            self.stop_strategy_timer()
            self._do_error_stop(error_msg)

    def order_history_timeout_check(self):
        if self.stop_flag:
            self.stop_strategy_timer()
            return
        try:
            self.get_orders_history()
        except Exception as e:
            error_msg = f"Algorithm stopped, Error reason: {e.__str__()}"
            future_logger.critical(error_msg)
            self.stop_strategy_timer()
            self._do_error_stop(error_msg)

    def start_order_history_timer(self):
        if not self.order_history_timer:
            self.order_history_timer = QtCore.QTimer()
            self.order_history_timer.timeout.connect(self.order_history_timeout_check)
            self.order_history_timer.start(1000)  # run this timer at interval of 1sec
        else:
            future_logger.warning("Order history timer already running.")

    def start_algo_timer(self):
        if not self.algo_timer:
            self.algo_timer = QtCore.QTimer()
            self.algo_timer.timeout.connect(self.algo_timeout_check)
            self.algo_timer.start(1000)  # run this timer at interval of 1sec
            logger.info("Strategy Algorithm Started...")
        else:
            future_logger.warning("Algo timer already running.")

    # =========================== SLOTS OR UTILITY METHODS =================================
    def on_connect(self, ws, response):
        logger.debug("Connection established")
        self.web_socket = ws

    def subs(self, instrument_token):
        logger.debug(instrument_token)
        if not instrument_token:
            "Instrument Token is None.Exiting"
            self.stop_flag = True
            self.error_stop.emit("Instrument Token is None.Exiting")
            return
        self.web_socket.subscribe(instrument_token)
        self.web_socket.set_mode(self.web_socket.MODE_FULL, instrument_token)

    def get_order_history(self):
        order_history_ = pd.DataFrame(self.kite.orders())
        return order_history_

    def get_orders_history(self):
        """
        Gets executed after every 1sec.
        :return: 
        """
        try:
            self.orders_history = self.get_order_history()
        except Exception as e:
            logger.info(f" _ Error in getting order history: {e.__str__()}")

    def get_all_order_open_symbol(self, symbol_name):
        df_ = self.get_order_history()
        try:
            res = df_.loc[
                  (df_["tradingsymbol"] == symbol_name) & (
                          (df_["status"] == "OPEN") | (df_["status"] == "TRIGGER PENDING")),
                  :]
            return res
        except Exception:
            pass
        return df_

    def order_status(self, order_id):
        return self.orders_history[self.orders_history['order_id'] == order_id]['status'].values[0]

    def get_positions(self, symbol_name):
        positions_df = pd.DataFrame(self.kite.positions()['day'])
        try:
            df_res = positions_df.loc[positions_df["tradingsymbol"] == symbol_name, :]
        except Exception as e:
            return positions_df
        return df_res

    def close_position(self, symbol_name=None):
        # Cancelling the Open Orders
        try:
            result = self.get_positions(symbol_name=symbol_name)
            index_list = list(result.index)
            for x in range(0, len(result)):
                res = result.loc[index_list[x], :]
                quantity = res["quantity"]
                exchange = res["exchange"]
                symbol_name = res["tradingsymbol"]
                product = res["product"]
                # ------------ Place Sell Market Order ----------
                if quantity > 0 and product == "MIS":
                    order_id1 = self.kite.place_order(variety="regular", exchange=exchange,
                                                      tradingsymbol=symbol_name,
                                                      transaction_type="SELL", quantity=quantity,
                                                      product=product,
                                                      order_type="MARKET",
                                                      price=None, validity="DAY", disclosed_quantity=None,
                                                      trigger_price=None,
                                                      squareoff=None,
                                                      stoploss=None,
                                                      trailing_stoploss=None,
                                                      tag=None)
                # ------------ Place Buy Order ----------
                elif quantity < 0 and product == 'MIS':
                    order_id1 = self.kite.place_order(variety="regular", exchange=exchange,
                                                      tradingsymbol=symbol_name,
                                                      transaction_type="BUY", quantity=quantity * -1,
                                                      product=product,
                                                      order_type="MARKET",
                                                      price=None, validity="DAY", disclosed_quantity=None,
                                                      trigger_price=None,
                                                      squareoff=None,
                                                      stoploss=None,
                                                      trailing_stoploss=None,
                                                      tag=None)

                else:
                    logger.info("No Positions Found for the Symbol to Exit")
            logger.info('Closing Positions Now.')
            all_open_orders = self.get_all_order_open_symbol(symbol_name)
            index_list = list(all_open_orders.index)
            for x in range(0, len(index_list)):
                temp = all_open_orders.loc[index_list[x], :]
                order_id = temp["order_id"]
                variety = temp["variety"]
                self.kite.cancel_order(order_id=int(order_id), variety=variety)

        except Exception:
            logger.warning(sys.exc_info())
        return

    def get_instrument_token(self, Name, exchange_):
        exchange_ = exchange_.upper()
        assert Name in list(self.instrumentFile["tradingsymbol"]), "Name Not found in Instrument File We have a Problem"
        if exchange_ in ["NSE", "BSE", "NFO", "MCX", "CDS"]:
            try:
                return self.instrumentFile.loc[(self.instrumentFile["tradingsymbol"] == Name) & (
                        self.instrumentFile["exchange"] == exchange_), "instrument_token"].values[0]
            except Exception as e:
                logger.warning("Error Has Occured")
                return None
        else:
            try:
                return self.instrumentFile.loc[(self.instrumentFile["tradingsymbol"] == Name),
                                               "instrument_token"].values[0]
            except Exception as e:
                logger.warning("Error Has Occured")
                return None

    def on_ticks(self, ws: typing.Any, ticks):
        try:
            for tick in ticks:
                ts = tick['timestamp']
                if ts is None:
                    continue
                if tick['timestamp'] is not None and nine_fifteen <= tick['timestamp'] < three_thirty:
                    price = tick['last_price']
                    instrument_token = tick['instrument_token']
                    self.latest_ltp[instrument_token] = price

        except Exception as e:
            logger.warning(sys.exc_info())
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.warning(exc_type, fname, exc_tb.tb_lineno)
