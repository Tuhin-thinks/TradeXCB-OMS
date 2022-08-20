import multiprocessing
import os
import sys
import time
import typing
import warnings
from datetime import datetime, timedelta

import numpy as np
import openpyxl
import pandas as pd
from pandas.core.common import SettingWithCopyWarning
import talib

from Libs.Files import handle_user_details
from Libs.Files.TradingSymbolMapping import StrategiesColumn
from Libs.Storage import app_data
from Libs.Utils import settings, exception_handler, calculations
from .TA_Lib import HA
from .main_broker_api.All_Broker import All_Broker
from .static import ta_lib_ext

pd.set_option('expand_frame_repr', False)
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=SettingWithCopyWarning)

logger = exception_handler.getAlgoLogger(__name__)

nine_fifteen = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
three_thirty = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
nine_sixteen = datetime.now().replace(hour=9, minute=16, second=0, microsecond=0)
to_dt = datetime.now()
from_dt = to_dt - timedelta(days=5)
to_dt = to_dt.strftime('%Y-%m-%d')
datetime_format = '%Y-%m-%d %H:%M:%S'


# ------------ function to add new rows in run-time ------------
def add_rows(old_instruments_df_dict, main_broker, users_df_dict,
             first_run=False):
    # Workbook
    wb = openpyxl.load_workbook(settings.DATA_FILES['tradexcb_excel_file'])
    instrument_sheet = wb['Sheet1']
    # load openpyexcel sheet to dataframe
    instruments_df = pd.DataFrame(instrument_sheet.values)
    columns = instruments_df.iloc[0]
    instruments_df.columns = columns
    instruments_df = instruments_df.iloc[1:]
    instruments_df = instruments_df.astype(StrategiesColumn.tradexcb_numeric_columns)

    # instruments_df = instrument_sheet.range('A1').options(pd.DataFrame, header=1, index=False,
    #                                                       expand='table').value

    instruments_df['running_trend'] = None
    instruments_df['multiplier'] = None
    instruments_df['entry_price'] = None
    instruments_df['entry_time'] = None
    instruments_df['exit_price'] = None
    instruments_df['exit_time'] = None
    instruments_df['status'] = 0
    instruments_df['target_price'] = None
    instruments_df['sl_price'] = None
    instruments_df['Row_Type'] = 'T'
    instruments_df['profit'] = None
    instruments_df['Trend'] = None
    instruments_df['run_done'] = 0
    instruments_df['vwap_last'] = 0
    instruments_df['quantity'] = 1
    instruments_df['close_positions'] = 0
    instruments_df_dict = instruments_df.to_dict('index')
    for each_instrument in instruments_df_dict:
        this_instrument = instruments_df_dict[each_instrument]
        this_instrument['entry_order_ids'] = {
            x: {'order_id': None, 'order_status': None, 'broker': users_df_dict[x]['broker']} for x in users_df_dict}
        this_instrument['exit_order_ids'] = {
            x: {'order_id': None, 'order_status': None, 'broker': users_df_dict[x]['broker']} for x in users_df_dict}

        row = All_Broker.instrument_df[
            (All_Broker.instrument_df['tradingsymbol'] == this_instrument['instrument'])]
        this_instrument['instrument_row'] = row
        this_instrument['instrument_token'] = int(row.iloc[-1]['instrument_token'])
        this_instrument['tradingsymbol'] = row.iloc[-1]['tradingsymbol']
        this_instrument['lot_size'] = int(row.iloc[-1]['lot_size'])
        this_instrument['order'] = None
        this_instrument['tick_size'] = row.iloc[-1]['tick_size']
        this_instrument['quantity'] = this_instrument['quantity'] * this_instrument['lot_size']
        this_instrument['exchange_token'] = row.iloc[-1]['exchange_token']
    instrument_list = [instruments_df_dict[x]['instrument_token'] for x in instruments_df_dict]

    main_broker.instrument_list = instrument_list
    if first_run:
        try:
            main_broker.get_live_ticks()
            logger.debug("Getting Live Ticks")
            logger.debug("Waiting 5secs...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error in getting live ticks {sys.exc_info()}", exc_info=True)
            raise ValueError(f"Error in getting live ticks {sys.exc_info()}")

    for each_instrument in instrument_list:
        if each_instrument not in main_broker.latest_ltp:
            main_broker.latest_ltp[each_instrument] = {'ltp': None}
    main_broker.subscribe_instrument(main_broker.instrument_list)

    for each_key in instruments_df_dict:
        if each_key not in old_instruments_df_dict:
            old_instruments_df_dict[each_key] = dict(instruments_df_dict[each_key])

    return old_instruments_df_dict, instruments_df


# ------------ xxx end xxx ------------

def main(manager_dict: dict, cancel_orders_queue: multiprocessing.Queue):
    """
    Main function to run the strategy

    :param cancel_orders_queue: storing all keys for instruments_df_dict
        (rows for which close_position has to be made 1)

    :param manager_dict: Dictionary to handle the shared data
    -> manager_dict keys:
        - 'algo_running': bool to check if the algo is running
        - 'algo_error': to store the algo error message
        - 'force_stop': Boolean to stop the strategy algo (don't modify inside algo)
        - 'orderbook_data': to store the orderbook data
    :return: None
    """
    # Variables
    paper_trade = manager_dict['paper_trade']
    users_df_dict = None
    main_broker: typing.Union[None, All_Broker] = None
    users_df = None
    instruments_df: typing.Union[None, pd.DataFrame] = None
    # instruments_df_dict = None

    # DO login for All users
    process_name = 'User Login Process'
    try:
        logger.info(f"Doing {process_name}")
        api_data = handle_user_details.read_user_api_details()
        if api_data is None:
            manager_dict['algo_error'] = f"{process_name} failed, No API details found"
            manager_dict['algo_running'] = False
            logger.critical("No API details found")

        users_df = pd.DataFrame(api_data)  # read all data from sqlite
        users_df['No of Lots'] = users_df['No of Lots'].astype(int)
        users_df.index = users_df['Name']
        # users_df = users_df.tail(1)
        users_df['broker'] = None
        users_df_dict = users_df.to_dict('index')
        for each_key in users_df_dict:
            try:
                this_user = users_df_dict[each_key]
                this_user['broker'] = All_Broker(**this_user)
            except:
                logger.warning(f"Error in Logging in for Name : {each_key} Error : {sys.exc_info()}", exc_info=True)
                manager_dict['algo_error'] = f"{process_name} failed, Error in Logging in for Name : {each_key}"
                manager_dict['algo_running'] = False
                return
    except:
        logger.warning(f"Error in {process_name}. Error : {sys.exc_info()} ", exc_info=True)
        manager_dict['algo_error'] = f"{process_name} failed, Error : {sys.exc_info()}"
        manager_dict['algo_running'] = False
        return

    process_name = 'Setting Main Broker'
    try:
        logger.info(f"{process_name} for Data Feed")
        main_broker: All_Broker = users_df_dict[list(users_df_dict.keys())[0]][
            'broker']  # Main Broker for Getting LTPs and Historic Data
        assert main_broker.broker_name.lower() in ['zerodha',
                                                   'iifl'], f"Main Broker for Data Feed is not ZERODHA or IIFL"
    except Exception as e:
        logger.critical(f"Error in {process_name}", exc_info=True)
        manager_dict['algo_running'] = False
        manager_dict['algo_error'] = f"{process_name} failed, Error : {sys.exc_info()}"
        return
    process_name = 'Getting All Instruments to Trade'
    manager_dict['update_rows'] = 0  # flag variable to check if any row has been updated (controlled externally)
    instruments_df_dict = {}
    try:
        instruments_df_dict, instruments_df = add_rows(instruments_df_dict, main_broker,
                                                       users_df_dict,
                                                       first_run=True)
    except Exception as e:
        logger.critical(f"Error in {process_name}", exc_info=True)
        manager_dict['algo_running'] = False
        manager_dict['algo_error'] = f"{process_name} failed, Error : {sys.exc_info()}, {e.__str__()}"
        return
    logger.info(f"Starting Strategy")
    final_df = pd.DataFrame(columns=list(instruments_df.columns) + ['ltp', 'tradingsymbol'])
    logger.info(f"{main_broker.latest_ltp}")

    while manager_dict['force_stop'] is False:
        time.sleep(1)  # wait for 1 second/iteration
        if manager_dict['update_rows'] == 1:
            manager_dict['update_rows'] = 0
            instruments_df_dict, instruments_df = add_rows(instruments_df_dict, main_broker,
                                                           users_df_dict)
            # reset final df, as new rows have been added
            final_df = pd.DataFrame(columns=list(instruments_df.columns) + ['ltp', 'tradingsymbol'])

        if datetime.now() < nine_sixteen:
            continue

        final_df = final_df[['tradingsymbol', 'exchange', 'quantity', 'timeframe', 'multiplier', 'entry_price',
                             'entry_time', 'exit_price', 'exit_time', 'target_price', 'sl_price', 'Row_Type',
                             'profit', 'ltp']]
        final_df['Trend'] = np.where(final_df['multiplier'] == 1, 'BUY', 'SELL')

        final_all_user_df = pd.DataFrame()
        for each_user in users_df_dict:
            try:
                this_user = users_df_dict[each_user]
                if this_user['broker'] is None:
                    continue

                no_of_lots = this_user['No of Lots']
                final_df_temp = final_df.copy(deep=True)
                final_df_temp['quantity'] = final_df_temp['quantity'] * no_of_lots
                final_df_temp['profit'] = (final_df_temp['ltp'] - final_df_temp['entry_price']) * final_df_temp[
                    'quantity'] * final_df_temp['multiplier']
                final_df_temp['user_id'] = this_user['accountUserName']
                final_all_user_df = final_all_user_df.append(final_df_temp, ignore_index=True)
            except Exception as e:
                logger.critical(f"{sys.exc_info()}", exc_info=True)
                manager_dict['algo_error'] = f"{process_name} failed, Error : {sys.exc_info()}"
                manager_dict['algo_running'] = False
                return

        final_all_user_df.to_csv(
            settings.DATA_FILES.get('POSITIONS_FILE_PATH'))  # PNL of all users by the lot executed by the user

        order_book_dict = dict()
        for each_user in users_df_dict:
            try:
                this_user = users_df_dict[each_user]
                if this_user['broker'] is None:
                    continue

                order_book: pd.DataFrame = this_user['broker'].get_order_book()
                order_book['username'] = this_user['accountUserName']
                if this_user['broker'].broker_name in order_book_dict:
                    order_book_dict[this_user['broker'].broker_name].append(order_book, ignore_index=True)
                else:
                    order_book_dict[this_user['broker'].broker_name] = order_book
            except Exception as e:
                logger.critical(f"{sys.exc_info()}", exc_info=True)
                manager_dict['algo_error'] = f"{process_name} failed, Error : {sys.exc_info()}"
                manager_dict['algo_running'] = False
                return

        final_df = final_df[final_df['Row_Type'] != 'T']  # keep only F type rows (reason?)

        for each_key in order_book_dict:
            try:
                order_book_dict[each_key] = list(order_book_dict[each_key].to_dict('index').values())
            except Exception as e:
                logger.critical(f"Error in Creating Order Book {e.__str__()}", exc_info=True)

        # This contains Orderbook of all the clients
        # ------- cannot export broker instance ----------
        orderbook_export_data = {x: [] for x in app_data.OMS_TABLE_COLUMNS}
        for each_key in instruments_df_dict:
            row_data = instruments_df_dict[each_key]
            orderbook_export_data["Instrument"].append(row_data['tradingsymbol'])
            orderbook_export_data["Entry Price"].append(row_data['entry_price'])
            entry_time = row_data['entry_time']
            if isinstance(entry_time, datetime):
                if entry_time.date() == datetime.now().date():
                    orderbook_export_data["Entry Time"].append(entry_time.strftime("%H:%M:%S"))
                else:
                    continue
            else:
                orderbook_export_data["Entry Time"].append(entry_time)
            orderbook_export_data["Exit Price"].append(row_data['exit_price'])

            exit_time = row_data['exit_time']
            if isinstance(exit_time, datetime):
                orderbook_export_data["Exit Time"].append(exit_time.strftime("%H:%M:%S"))
            else:
                orderbook_export_data["Exit Time"].append(exit_time)
            orderbook_export_data["Order Type"].append(row_data['order_type'])
            orderbook_export_data["Quantity"].append(row_data['quantity'])
            orderbook_export_data["Product Type"].append(row_data['product_type'])
            orderbook_export_data["Stoploss"].append(row_data['stoploss'])
            orderbook_export_data["Target"].append(row_data['target'])

            # concatenate order status for all users
            order_status = ""
            row_order_details = row_data.get("entry_order_ids")
            if row_order_details is not None:
                for each_user, this_user_order_details in row_order_details.items():
                    this_user = users_df_dict[each_user]
                    _status = this_user_order_details["order_status"]
                    order_status += f"{this_user['Name']} : {_status}\n"

            orderbook_export_data["Order Status"].append(order_status)
            orderbook_export_data["instrument_df_key"].append(each_key)  # will be used to reference in close positions

        orderbook_export_data["Close Position?"] = [0] * len(orderbook_export_data["instrument_df_key"])
        manager_dict['orderbook_data'] = orderbook_export_data  # pass the dictionary to the UI

        # --------------- look for to be closed positions ---------------
        while True:
            try:
                row_key = cancel_orders_queue.get_nowait()
                if row_key is not None:
                    row_data = instruments_df_dict[row_key]
                    row_data['close_positions'] = 1  # close the positions
                    logger.debug("closing position for row_key : {}".format(row_key))
                else:
                    break
            except Exception as e:
                break
        # --------------- run the main strategy ---------------
        curr_date = datetime.now()
        process_name = 'Main Strategy'
        for each_key in instruments_df_dict:
            try:
                this_instrument = instruments_df_dict[each_key]
                this_instrument['transaction_type'] = this_instrument['transaction_type'].upper()
                ltp = main_broker.latest_ltp[this_instrument['instrument_token']]['ltp']

                if (int((curr_date - nine_fifteen).seconds / 60) % this_instrument['timeframe'] > 0) or (
                        int((curr_date - nine_fifteen).seconds / 60) % this_instrument['timeframe'] == 0 and
                        curr_date.second > 30) and this_instrument['run_done'] == 1:
                    this_instrument['run_done'] = 0

                if int((curr_date - nine_fifteen).seconds / 60) % this_instrument[
                    'timeframe'] == 0 and curr_date.second <= 30 and (this_instrument['run_done'] == 0 and
                                                                      this_instrument['status'] == 0):
                    this_instrument['run_done'] = 1
                    logger.info(f"Running the {process_name} for {this_instrument['tradingsymbol']}")
                    df = main_broker.get_data(this_instrument['instrument_token'],
                                              str(int(this_instrument['timeframe'])), 'minute', from_dt, to_dt)[0]

                    df = df[df.index < datetime.now().replace(microsecond=0, second=0)]
                    time_df_col = df.index
                    df = HA(df, ohlc=['open', 'high', 'low', 'close'])
                    # print(df.tail(5))  # TODO: Remove this
                    df.index = time_df_col
                    df = calculations.get_vwap(df)
                    df['SUPERTREND'] = ta_lib_ext.SuperTrend(df, this_instrument['ATR TS Period'],
                                                             this_instrument['ATR TS Multiplier'],
                                                             ohlc=['HA_open', 'HA_high', 'HA_low', 'HA_close'])
                    this_instrument['vwap_last'] = df['vwap'].tail(2).head(1).values[0]
                    vwap = df['vwap'].tail(1).values[0]

                    atr_trend_bullish = 0
                    atr_trend_bearish = 0

                    if this_instrument['ATRTS'] == 'YES':
                        if this_instrument['atrts_signal'] == 'new':
                            atr_trend_bearish = 1 if ((df['SUPERTREND'].tail(1).head(1).values[0] == 'down') & (
                                    df['SUPERTREND'].tail(2).head(1).values[0] == 'up')) else 0
                            atr_trend_bullish = 1 if ((df['SUPERTREND'].tail(1).head(1).values[0] == 'up') & (
                                    df['SUPERTREND'].tail(2).head(1).values[0] == 'down')) else 0
                        if this_instrument['atrts_signal'] == 'existing':
                            atr_trend_bearish = 1 if (df['SUPERTREND'].tail(1).head(1).values[0] == 'down') else 0
                            atr_trend_bullish = 1 if (df['SUPERTREND'].tail(1).head(1).values[0] == 'up') else 0

                    else:
                        atr_trend_bullish = 1
                        atr_trend_bearish = 1

                    logger.info(f" Bearish trend : {atr_trend_bearish} Bullish trend : {atr_trend_bullish}")

                    vwap_trend_bullish = 0
                    vwap_trend_bearish = 0

                    logger.info(f"Previous Vwap : {this_instrument['vwap_last']} Now Vwap : {vwap}")
                    if this_instrument['vwap'] == 'YES' and this_instrument['vwap_last'] != 0:

                        if this_instrument['vwap_signal'] == 'new':
                            vwap_trend_bullish = 1 if (df['HA_close'].tail(1).head(1).values[0] > vwap) and (
                                    df['HA_close'].tail(2).head(1).values[0] < this_instrument['vwap_last']) else 0
                            vwap_trend_bearish = 1 if (df['HA_close'].tail(1).head(1).values[0] < vwap) and (
                                    df['HA_close'].tail(2).head(1).values[0] > this_instrument['vwap_last']) else 0

                        if this_instrument['vwap_signal'] == 'existing':
                            vwap_trend_bullish = 1 if (df['HA_close'].tail(1).head(1).values[0] > vwap) else 0
                            vwap_trend_bearish = 1 if (df['HA_close'].tail(1).head(1).values[0] < vwap) else 0
                    else:
                        vwap_trend_bullish = 1
                        vwap_trend_bearish = 1

                    this_instrument['vwap_last'] = vwap

                    ma_trend_bullish = 0
                    ma_trend_bearish = 0
                    if this_instrument['moving_average'] == 'YES':
                        df['moving_average'] = talib.MA(df['HA_close'],
                                                        timeperiod=int(this_instrument['moving_average_period']))
                        row_name = 'moving_average'
                        if this_instrument['moving_average_signal'] == 'new':
                            ma_trend_bullish = 1 if (df[row_name].tail(1).values[0] < df['HA_close'].tail(1).values[
                                0]) and (df[row_name].tail(2).head(1).values[0] >=
                                         df['HA_close'].tail(2).head(1).values[0]) else 0
                            ma_trend_bearish = 1 if (df[row_name].tail(1).values[0] >= df['HA_close'].tail(1).values[
                                0]) and (df[row_name].tail(2).head(1).values[0] < df['HA_close'].tail(2).head(1).values[
                                0]) else 0
                        if this_instrument['moving_average_signal'] == 'existing':
                            ma_trend_bullish = 1 if (df[row_name].tail(1).values[0] < df['HA_close'].tail(1).values[
                                0]) else 0
                            ma_trend_bearish = 1 if (df[row_name].tail(1).values[0] >= df['HA_close'].tail(1).values[
                                0]) else 0

                    else:
                        ma_trend_bullish = 1
                        ma_trend_bearish = 1

                    if this_instrument['use_priceba'] == 'YES':
                        price_above_trend_bullish = 1 if ltp > this_instrument['buy_above'] else 0
                        price_above_trend_bearish = 0
                    else:
                        price_above_trend_bearish = 1
                        price_above_trend_bullish = 1

                    if this_instrument['use_pricesb'] == 'YES':
                        price_trend_bearish = 1 if ltp < this_instrument['sell_below'] else 0
                        price_trend_bullish = 0
                    else:
                        price_trend_bearish = 1
                        price_trend_bullish = 1
                    # print all values for debugging, TODO: remove this later
                    print(f"""
{price_above_trend_bullish=}
{price_trend_bullish=}
{ma_trend_bullish=}
{vwap_trend_bullish=}
{atr_trend_bullish=}""")

                    print(f"""
{price_above_trend_bearish=}
{price_trend_bearish=}
{ma_trend_bearish=}
{vwap_trend_bearish=}
{atr_trend_bearish=}
{this_instrument['multiplier']=} != -1
{this_instrument['transaction_type']=} == 'SELL'""")
                    logger.info(f"{price_above_trend_bullish=} and {price_trend_bullish=} and {ma_trend_bullish=} and "
                                f"{vwap_trend_bullish=} and {atr_trend_bullish=} and "
                                f"{this_instrument['multiplier']} != 1 and {this_instrument['transaction_type']} == 'BUY'")

                    logger.info(f"{price_above_trend_bearish} and {price_trend_bearish} and {ma_trend_bearish} and"
                                f" {price_trend_bearish} and {vwap_trend_bearish} and {atr_trend_bearish} and"
                                f" {this_instrument['multiplier']} != -1 and"
                                f" {this_instrument['transaction_type']} == 'SELL'")

                    if price_above_trend_bullish and price_trend_bullish and ma_trend_bullish and \
                            vwap_trend_bullish and atr_trend_bullish and \
                            this_instrument['multiplier'] != 1 and this_instrument['transaction_type'].upper() == 'BUY':
                        logger.info(f" In Buy Loop. for {this_instrument['tradingsymbol']}\n"
                                    f"Buy Signal has been Activated for {this_instrument['tradingsymbol']}")
                        this_instrument['status'] = 1
                        this_instrument['multiplier'] = 1

                        this_instrument['entry_price'] = calculations.fix_values(
                            df['HA_close'].tail(1).values[0] * (1 - this_instrument['buy_ltp_percent'] / 100),
                            this_instrument['tick_size'])
                        this_instrument['entry_time'] = datetime.now()
                        if this_instrument['target_type'].lower() == 'percentage':
                            this_instrument['target_price'] = calculations.fix_values(
                                this_instrument['entry_price'] * (1 + this_instrument['target'] / 100),
                                this_instrument['tick_size'])
                        elif this_instrument['target_type'].lower() == 'value':
                            this_instrument['target_price'] = calculations.fix_values(
                                this_instrument['entry_price'] + this_instrument['target'],
                                this_instrument['tick_size'])

                        if this_instrument['stoploss_type'].lower() == 'percentage':
                            this_instrument['sl_price'] = calculations.fix_values(
                                this_instrument['entry_price'] * (1 - this_instrument['stoploss'] / 100),
                                this_instrument['tick_size'])

                        elif this_instrument['stoploss_type'].lower() == 'value':
                            this_instrument['sl_price'] = calculations.fix_values(
                                this_instrument['entry_price'] - this_instrument['multiplier'] * this_instrument[
                                    'stoploss'], this_instrument['tick_size'])

                        if paper_trade == 0:
                            order = {'variety': 'regular',
                                     'exchange': this_instrument['exchange'],
                                     'tradingsymbol': this_instrument['tradingsymbol'],
                                     'quantity': int(this_instrument['quantity']),
                                     'product': this_instrument['product_type'],
                                     'transaction_type': this_instrument['transaction_type'],
                                     'order_type': this_instrument['order_type'],
                                     'price': this_instrument['entry_price'],
                                     'validity': 'DAY',
                                     'disclosed_quantity': None,
                                     'trigger_price': None,
                                     'squareoff': None,
                                     'stoploss': None,
                                     'trailing_stoploss': None,
                                     'tag': None}
                            this_instrument['order'] = order
                            for each_user in users_df_dict:
                                this_user = users_df_dict[each_user]
                                try:
                                    new_order = dict(order)
                                    new_order['quantity'] = int(new_order['quantity'] * this_user['No of Lots'])
                                    order_id, message = this_user['broker'].place_order(
                                        **new_order)  # placing fresh order
                                    this_instrument['entry_order_ids'][each_user]['order_id'] = order_id
                                    logger.info(f"Order Placed for {each_user} Order_id {order_id}")
                                except:
                                    logger.warning(f"Error in Sell Order Placement for {this_user['Name']}"
                                                   f" Error {sys.exc_info()}", exc_info=True)

                        logger.info(f" Instrument_Details : {this_instrument}")

                    elif (price_above_trend_bearish and price_trend_bearish and ma_trend_bearish and
                          vwap_trend_bearish and atr_trend_bearish and
                          this_instrument['multiplier'] != -1 and this_instrument[
                              'transaction_type'].upper() == 'SELL'):
                        logger.info(f" In Sell Loop. for {this_instrument['tradingsymbol']}")
                        logger.info(f" Sell Signal has been Activated for {this_instrument['tradingsymbol']}")
                        this_instrument['status'] = 1
                        this_instrument['multiplier'] = -1

                        this_instrument['entry_price'] = calculations.fix_values(
                            df['HA_close'].tail(1).values[0] * (1 - this_instrument['sell_ltp_percent'] / 100),
                            this_instrument['tick_size'])
                        this_instrument['entry_time'] = datetime.now()
                        if this_instrument['order_type'] == 'MARKET':
                            this_instrument['entry_price'] = ltp

                        if this_instrument['target_type'].lower() == 'percentage':
                            this_instrument['target_price'] = calculations.fix_values(
                                this_instrument['entry_price'] * (1 - this_instrument['target'] / 100),
                                this_instrument['tick_size'])
                        elif this_instrument['target_type'].lower() == 'value':
                            this_instrument['target_price'] = calculations.fix_values(
                                this_instrument['entry_price'] - this_instrument['target'],
                                this_instrument['tick_size'])

                        if this_instrument['stoploss_type'].lower() == 'percentage':
                            this_instrument['sl_price'] = calculations.fix_values(
                                this_instrument['entry_price'] * (1 + this_instrument['stoploss'] / 100),
                                this_instrument['tick_size'])

                        elif this_instrument['stoploss_type'].lower() == 'value':
                            this_instrument['sl_price'] = calculations.fix_values(
                                this_instrument['entry_price'] - this_instrument['multiplier'] * this_instrument[
                                    'stoploss'], this_instrument['tick_size'])

                        if paper_trade == 0:
                            order = {'variety': 'regular',
                                     'exchange': this_instrument['exchange'],
                                     'tradingsymbol': this_instrument['tradingsymbol'],
                                     'quantity': int(this_instrument['quantity']),
                                     'product': this_instrument['product_type'],
                                     'transaction_type': this_instrument['transaction_type'],
                                     'order_type': this_instrument['order_type'],
                                     'price': ltp,
                                     'validity': 'DAY',
                                     'disclosed_quantity': None,
                                     'trigger_price': None,
                                     'squareoff': None,
                                     'stoploss': None,
                                     'trailing_stoploss': None,
                                     'tag': None}

                            this_instrument['order'] = order
                            for each_user in users_df_dict:
                                this_user = users_df_dict[each_user]
                                try:

                                    new_order = dict(order)
                                    new_order['quantity'] = int(new_order['quantity'] * this_user['No of Lots'])
                                    order_id, message = this_user['broker'].place_order(**new_order)
                                    this_instrument['entry_order_ids'][each_user]['order_id'] = order_id
                                    logger.info(f"Sell Order Placed for {each_user} Order_id {order_id}")
                                except:
                                    logger.info(f"Error in Sell Order Placement for {this_user['Name']}"
                                                f" Error {sys.exc_info()}", exc_info=True)

                        logger.info(f" Instrument_Details : {this_instrument}")

                if this_instrument['status'] == 1:
                    if paper_trade == 1:  #

                        if ltp * this_instrument['multiplier'] <= (this_instrument['entry_price'] *
                                                                   this_instrument['multiplier']):
                            logger.info(f"Entry has been taken for {this_instrument['tradingsymbol']}")
                            this_instrument['entry_time'] = datetime.now()
                            this_instrument['status'] = 2
                            continue

                        if datetime.now() > this_instrument['entry_time'] + timedelta(
                                minutes=int(this_instrument['wait_time'])):
                            logger.info(f" Cancelling the Placed Order for {this_instrument['tradingsymbol']}")
                            this_instrument['Row_Type'] = 'T'
                            this_instrument['multiplier'] = None
                            this_instrument['entry_price'] = None
                            this_instrument['entry_time'] = None
                            this_instrument['exit_price'] = None
                            this_instrument['exit_time'] = None
                            this_instrument['status'] = 0
                            this_instrument['entry_order_id'] = None
                            this_instrument['target_price'] = None
                            this_instrument['sl_price'] = None
                            this_instrument['sl_order_id'] = None
                            this_instrument['target_order_id'] = None
                            continue

                    if paper_trade == 0:
                        if (ltp * this_instrument['multiplier']
                                <= this_instrument['entry_price'] * this_instrument['multiplier']):
                            for each_user in this_instrument['entry_order_ids']:
                                this_user = users_df_dict[each_user]
                                this_user_order_details = this_instrument['entry_order_ids'][each_user]
                                broker = this_user_order_details['broker']
                                order_id = this_user_order_details['order_id']
                                order_status, status_message = broker.get_order_status(order_id=order_id)
                                this_user_order_details['order_status'] = order_status
                                if order_status == 'COMPLETE':
                                    continue
                                elif order_status == 'REJECTED':
                                    logger.info(f"Order Rejected for {each_user} having Order ID : {order_id}")
                                    continue
                                else:

                                    order = this_instrument['order']
                                    order['order_type'] = 'MARKET'
                                    order['price'] = None
                                    broker.cancel_order(order_id=order_id)
                                    new_order = dict(order)
                                    new_order['quantity'] = int(new_order['quantity'] *
                                                                this_user['No of Lots'])
                                    order_id, message = broker.place_order(**new_order)
                                    this_instrument['entry_order_ids'][each_user]['order_id'] = order_id
                                    logger.info(f"Order Placed for {each_user} Order_id {order_id}")

                            logger.info(f" Entry has been taken for {this_instrument['tradingsymbol']} ")
                            this_instrument['entry_time'] = datetime.now()
                            this_instrument['status'] = 2

                            if this_instrument['stoploss_type'] != 'No SL Order':
                                # Place SL Order
                                order = {'variety': 'regular',
                                         'exchange': this_instrument['exchange'],
                                         'tradingsymbol': this_instrument['tradingsymbol'],
                                         'quantity': int(this_instrument['quantity']),
                                         'product': this_instrument['product_type'],
                                         'transaction_type': calculations.reverse_txn_type(
                                             this_instrument['transaction_type']),
                                         'order_type': 'SL',
                                         'price': this_instrument['sl_price'],
                                         'validity': 'DAY',
                                         'disclosed_quantity': None,
                                         'trigger_price': calculations.get_adjusted_trigger_price(
                                             this_instrument['transaction_type'],
                                             this_instrument['sl_price'],
                                             this_instrument['tick_size']),
                                         'squareoff': None,
                                         'stoploss': None,
                                         'trailing_stoploss': None,
                                         'tag': None}

                                for each_user in users_df_dict:
                                    this_user = users_df_dict[each_user]
                                    try:
                                        new_order = dict(order)
                                        new_order['quantity'] = int(new_order['quantity'] * this_user['No of Lots'])
                                        order_id, message = this_user['broker'].place_order(**new_order)
                                        this_instrument['exit_order_ids'][each_user]['order_id'] = order_id
                                        logger.info(f"Order Placed for {each_user} Order_id {order_id}")
                                    except:
                                        logger.critical(f"Error in SL Order Placement for {this_user['Name']} "
                                                        f"Error {sys.exc_info()}", exc_info=True)

                                continue

                if this_instrument['status'] == 2:  # Order Placed was executed
                    this_instrument['ltp'] = ltp
                    this_instrument['profit'] = (ltp - this_instrument['entry_price']) * this_instrument['multiplier'] * \
                                                this_instrument['quantity'] * this_instrument['lot_size']
                    final_df = final_df[final_df['Row_Type'] != 'T']
                    this_instrument['Row_Type'] = 'T'
                    final_df = final_df.append(this_instrument, ignore_index=True)

                    # logger.info(f"{ltp} {this_instrument['multiplier']} {this_instrument['target_price']} {this_instrument['sl_price']}")
                    if ltp * this_instrument['multiplier'] >= (this_instrument['target_price'] *
                                                               this_instrument['multiplier']) and this_instrument['target_type'] != 'No Target Order':
                        logger.info(f"Target has been Hit for {this_instrument['tradingsymbol']}")
                        this_instrument['exit_time'] = datetime.now()
                        this_instrument['exit_price'] = ltp
                        this_instrument['status'] = 0
                        this_instrument['vwap_signal'] = 'new'
                        this_instrument['atrts_signal'] = 'new'
                        this_instrument['moving_average_signal'] = 'new'
                        # Cancel Pending SL Order and Placing a Market Order
                        if paper_trade == 0:
                            for each_user in users_df_dict:
                                this_user = users_df_dict[each_user]
                                try:
                                    order_id = this_instrument['exit_order_ids'][each_user]['order_id']
                                    order_status, message = this_user['broker'].get_order_status(order_id)
                                    this_instrument['exit_order_ids'][each_user]['order_status'] = order_status
                                    if order_status == 'PENDING':
                                        this_user['broker'].cancel_order(order_id)
                                        if this_instrument["transaction_type"] == "BUY":
                                            txn_type = "SELL"
                                        else:
                                            txn_type = "BUY"
                                        order = {'variety': 'regular',
                                                 'exchange': this_instrument['exchange'],
                                                 'tradingsymbol': this_instrument['tradingsymbol'],
                                                 'quantity': int(this_instrument['quantity']),
                                                 'product': this_instrument['product_type'],
                                                 'transaction_type': txn_type,
                                                 'order_type': 'MARKET',
                                                 'price': None,
                                                 'validity': 'DAY',
                                                 'disclosed_quantity': None,
                                                 'trigger_price': None,
                                                 'squareoff': None,
                                                 'stoploss': None,
                                                 'trailing_stoploss': None,
                                                 'tag': None}
                                        new_order = dict(order)
                                        new_order['quantity'] = int(new_order['quantity'] * this_user['No of Lots'])
                                        order_id, message = this_user['broker'].place_order(**new_order)
                                        this_instrument['exit_order_ids'][each_user]['order_id'] = order_id
                                        logger.info(f"Order Placed for {each_user} Order_id {order_id}")
                                    elif order_status == 'COMPLETE':
                                        this_user['broker'].cancel_order(order_id)
                                except:
                                    logger.critical(
                                        f"Error in Closing Order Placement for {this_user['Name']} Error {sys.exc_info()}",
                                        exc_info=True)

                        # final_df = final_df[final_df['Row_Type']!='T']
                        this_instrument['Row_Type'] = 'F'
                        final_df = final_df.append(this_instrument, ignore_index=True)

                        this_instrument['Row_Type'] = 'T'
                        this_instrument['multiplier'] = None
                        this_instrument['entry_price'] = None
                        this_instrument['entry_time'] = None
                        this_instrument['exit_price'] = None
                        this_instrument['exit_time'] = None
                        this_instrument['status'] = 0
                        this_instrument['entry_order_id'] = None
                        this_instrument['target_price'] = None
                        this_instrument['sl_price'] = None
                        this_instrument['sl_order_id'] = None
                        this_instrument['target_order_id'] = None

                    elif (ltp * this_instrument['multiplier'] <=
                          this_instrument['sl_price'] * this_instrument['multiplier']):

                        logger.info(f"Stoploss has been Hit for {this_instrument['tradingsymbol']}")
                        this_instrument['exit_time'] = datetime.now()
                        this_instrument['exit_price'] = ltp
                        this_instrument['status'] = 0
                        this_instrument['vwap_signal'] = 'new'
                        this_instrument['atrts_signal'] = 'new'
                        this_instrument['moving_average_signal'] = 'new'

                        # Cancel Pending SL Order and Placing a Market Order
                        if paper_trade == 0:
                            for each_user in users_df_dict:
                                this_user = users_df_dict[each_user]
                                try:
                                    order_id = this_instrument['exit_order_ids'][each_user]['order_id']
                                    order_status, message = this_user['broker'].get_order_status(order_id)
                                    this_instrument['exit_order_ids'][each_user]['order_status'] = order_status
                                    time.sleep(1)
                                    if order_status == 'PENDING':
                                        this_user['broker'].cancel_order(order_id)
                                        time.sleep(1)
                                        if this_instrument["transaction_type"] == "BUY":
                                            txn_type = "SELL"
                                        else:
                                            txn_type = "BUY"
                                        order = {'variety': 'regular',
                                                 'exchange': this_instrument['exchange'],
                                                 'tradingsymbol': this_instrument['tradingsymbol'],
                                                 'quantity': int(this_instrument['quantity']),
                                                 'product': this_instrument['product_type'],
                                                 'transaction_type': txn_type,
                                                 'order_type': 'MARKET',
                                                 'price': None,
                                                 'validity': 'DAY',
                                                 'disclosed_quantity': None,
                                                 'trigger_price': None,
                                                 'squareoff': None,
                                                 'stoploss': None,
                                                 'trailing_stoploss': None,
                                                 'tag': None}
                                        new_order = dict(order)
                                        new_order['quantity'] = int(new_order['quantity'] * this_user['No of Lots'])
                                        order_id, message = this_user['broker'].place_order(**new_order)
                                        this_instrument['exit_order_ids'][each_user]['order_id'] = order_id
                                        logger.info(f"Order Placed for {each_user} Order_id {order_id}")
                                    elif order_status == 'COMPLETE':
                                        this_user['broker'].cancel_order(order_id)
                                except Exception as e:
                                    logger.critical(f"Error in Closing Order Placement for {this_user['Name']}"
                                                    f" Error {sys.exc_info()}", exc_info=True)

                        # final_df = final_df[final_df['Row_Type'] != 'T']
                        this_instrument['Row_Type'] = 'F'
                        final_df = final_df.append(this_instrument, ignore_index=True)

                        this_instrument['Row_Type'] = 'T'
                        this_instrument['multiplier'] = None
                        this_instrument['entry_price'] = None
                        this_instrument['entry_time'] = None
                        this_instrument['exit_price'] = None
                        this_instrument['exit_time'] = None
                        this_instrument['status'] = 0
                        this_instrument['entry_order_id'] = None
                        this_instrument['target_price'] = None
                        this_instrument['sl_price'] = None
                        this_instrument['sl_order_id'] = None
                        this_instrument['target_order_id'] = None

                    if this_instrument['close_positions'] == 1:

                        this_instrument['exit_time'] = datetime.now()
                        this_instrument['exit_price'] = ltp
                        this_instrument['status'] = 0
                        this_instrument['vwap_signal'] = 'new'
                        this_instrument['atrts_signal'] = 'new'
                        this_instrument['moving_average_signal'] = 'new'
                        # Cancel Pending SL Order and Placing a Market Order
                        if paper_trade == 0:
                            for each_user in users_df_dict:
                                this_user = users_df_dict[each_user]
                                try:
                                    order_id = this_instrument['exit_order_ids'][each_user]['order_id']
                                    order_status, message = this_user['broker'].get_order_status(order_id)
                                    this_instrument['exit_order_ids'][each_user]['order_status'] = order_status
                                    if order_status == 'PENDING':
                                        this_user['broker'].cancel_order(order_id)
                                        txn_type = calculations.reverse_txn_type(this_instrument['transaction_type'])
                                        order = {'variety': 'regular',
                                                 'exchange': this_instrument['exchange'],
                                                 'tradingsymbol': this_instrument['tradingsymbol'],
                                                 'quantity': int(this_instrument['quantity']),
                                                 'product': this_instrument['product_type'],
                                                 'transaction_type': txn_type,
                                                 'order_type': 'MARKET',
                                                 'price': None,
                                                 'validity': 'DAY',
                                                 'disclosed_quantity': None,
                                                 'trigger_price': None,
                                                 'squareoff': None,
                                                 'stoploss': None,
                                                 'trailing_stoploss': None,
                                                 'tag': None}
                                        new_order = dict(order)
                                        new_order['quantity'] = int(new_order['quantity'] * this_user['No of Lots'])
                                        order_id, message = this_user['broker'].place_order(**new_order)
                                        this_instrument['exit_order_ids'][each_user]['order_id'] = order_id
                                        logger.info(f"Order Placed for {each_user} Order_id {order_id}")
                                    elif order_status == 'COMPLETE':
                                        this_user['broker'].cancel_order(order_id)
                                except Exception:
                                    logger.critical(f"Error in Closing Order Placement for {this_user['Name']}"
                                                    f" Error {sys.exc_info()}", exc_info=True)

                        # final_df = final_df[final_df['Row_Type'] != 'T']
                        this_instrument['Row_Type'] = 'F'
                        final_df = final_df.append(this_instrument, ignore_index=True)

                        this_instrument['Row_Type'] = 'T'
                        this_instrument['multiplier'] = None
                        this_instrument['entry_price'] = None
                        this_instrument['entry_time'] = None
                        this_instrument['exit_price'] = None
                        this_instrument['exit_time'] = None
                        this_instrument['status'] = 0
                        this_instrument['entry_order_id'] = None
                        this_instrument['target_price'] = None
                        this_instrument['sl_price'] = None
                        this_instrument['sl_order_id'] = None
                        this_instrument['target_order_id'] = None

                        # Cancel the SL Order placed and Place an opposite Limit Order which with Buffer and Close open position
                        this_instrument['close_positions'] = 0
                        continue
            except Exception as e:
                logger.critical(f'Error in {process_name} Strategy Function. {e.__str__()}', exc_info=True)
                manager_dict['algo_error'] = f"Error in Strategy Function, Error: {sys.exc_info()}"
                manager_dict['algo_running'] = False
                return


if __name__ == '__main__':
    # instruments_df_dict = dict()
    main(manager_dict={'paper_trade': 0, 'algo_running': True, 'fore_stop': True, 'algo_error': None},
         cancel_orders_queue=multiprocessing.Queue())
