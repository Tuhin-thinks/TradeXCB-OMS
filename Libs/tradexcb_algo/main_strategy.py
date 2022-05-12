import json
import math
import multiprocessing
import sys
import time
import typing
import warnings
from datetime import datetime, timedelta

import numpy as np
import openpyxl
import pandas as pd

from Libs.Files import handle_user_details
from Libs.Files.TradingSymbolMapping import StrategiesColumn
from Libs.Storage import app_data, manage_local
from Libs.Utils import settings, exception_handler, calculations
from Libs.UI.Utils.Time__Profiler import ProfilerContext
from .TA_Lib import HA
from .main_broker_api.All_Broker import All_Broker

pd.set_option('expand_frame_repr', False)
warnings.simplefilter(action='ignore', category=FutureWarning)

logger = exception_handler.getAlgoLogger(__name__)

nine_fifteen = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
three_thirty = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
nine_sixteen = datetime.now().replace(hour=9, minute=16, second=0, microsecond=0)
datetime_format = '%Y-%m-%d %H:%M:%S'


def fix_values(value, tick_size):
    return round(int(value / tick_size) * tick_size, len(str(tick_size)))


# ------------ order management -----------------
def slice_calculation(lots_to_exec: int, n_slices: str, freeze_limit: int):
    if isinstance(n_slices, str) and n_slices.isdigit() and int(n_slices) > 0:
        n_slices = int(n_slices)
        if lots_to_exec >= n_slices:
            ind_slice_size = math.floor(lots_to_exec / n_slices)
        else:
            ind_slice_size = math.ceil(freeze_limit / n_slices)
    else:
        n_slices = math.ceil(lots_to_exec / (freeze_limit - 1))
        ind_slice_size = freeze_limit - 1
    if lots_to_exec // n_slices >= freeze_limit:
        n_slices = math.ceil(lots_to_exec / (freeze_limit - 1))
        ind_slice_size = freeze_limit - 1
    logger.debug(f"{lots_to_exec=} {n_slices=} {ind_slice_size=}")
    return n_slices, ind_slice_size


def place_orders(order_dict: typing.Dict, freeze_limits_dict: typing.Dict, symbol_name: str,
                 this_user: typing.Dict, order_type_str: str):
    """Place orders with lots more than allowed in lots freeze limit
    This function is called inside a loop to place orders for multiple users.

    :param order_type_str:
    :param order_dict: dictionary of order parameters
    :param freeze_limits_dict: allowed freeze limits from db
    :param symbol_name: symbol name (instruments.csv > name) to check freeze limits
    :param this_user: current user

    :return: typing.Optional[typing.Any]
    """
    lots_to_exec = int(this_user['No of Lots'])
    n_slices = this_user['Slices']  # this has to be in <'str'> or NoneType value
    freeze_limit: int = freeze_limits_dict[symbol_name]
    n_slices, ind_slice_size = slice_calculation(lots_to_exec, str(n_slices) if n_slices else None, freeze_limit)
    logger.debug(f"{n_slices=}, {ind_slice_size=}")
    order_details_list = []
    for i in range(n_slices):
        new_order = dict(order_dict)
        to_continue = False
        if ind_slice_size <= lots_to_exec and i < n_slices - 1:
            new_order['quantity'] = new_order['quantity'] * ind_slice_size
            lots_to_exec -= ind_slice_size
            to_continue = True
        elif lots_to_exec > 0:
            new_order['quantity'] = new_order['quantity'] * lots_to_exec
            lots_to_exec = 0
            to_continue = True
        if i == (n_slices - 1) and lots_to_exec != 0:  # last iteration
            new_order['quantity'] = new_order['quantity'] * lots_to_exec
            lots_to_exec = 0
            to_continue = True

        if to_continue:  # flag to check whether to continue or not
            logger.debug(f"Order details: {new_order} :: place_order")
            order_id, message = this_user['broker'].place_order(**new_order)
            if order_id:
                order_status = this_user['broker'].get_order_status(order_id)[0]
                logger.debug(f"Order status: {order_status} [line 95]")
                order_details_list.append({"order_id": order_id,
                                           "order": new_order,
                                           "quantity": new_order['quantity'],
                                           "status": order_status,
                                           "message": message})
                logger.info(f"{this_user['Name']} : {order_type_str} Order Placed, Order ID: {order_id}")
            else:
                logger.error(f"{this_user['Name']} : {order_type_str} Order Placement Failed, message: {message}")
    return order_details_list


def place_market_orders(order_dict: typing.Dict, this_user: typing.Dict, order_details_list: typing.List[typing.Dict]):
    """
    Place market order.

    :param order_details_list: list of order details
    :param order_dict:
    :param this_user:
    :return:
    """
    broker = this_user['broker']

    new_order_details_list = []

    # iterate on orders
    for order_details in order_details_list:
        order_id = order_details['order_id']

        # ---- get order status ----
        order_status, status_message = broker.get_order_status(order_id=order_id)
        order_details['status'] = order_status
        order_details['message'] = status_message
        logger.debug(f"{this_user['Name']} : {order_details['order']['order_type']} Order Completed, order status: {order_status}, Order ID: {order_id}")
        if order_status == "COMPLETE":
            new_order_details_list.append(order_details)
            continue
        elif order_status == "REJECTED":
            new_order_details_list.append(order_details)
            logger.info(f"Order Rejected for {this_user['Name']} Order_id {order_id}")
        else:
            broker.cancel_order(order_id=order_id)
            order_dict['order_type'] = 'MARKET'
            order_dict['price'] = None
            new_order = dict(order_dict)
            new_order['quantity'] = order_details['quantity']  # use quantity from previous order (place order)
            logger.debug(f"Order details: {new_order} :: place_market_orders")
            order_id, message = broker.place_order(**new_order)
            if order_id:
                new_order_details_list.append({"order_id": order_id,
                                               "order": new_order,
                                               "quantity": new_order['quantity'],
                                               "status": broker.get_order_status(order_id=order_id)[0],
                                               "message": message})
                logger.info(f"{this_user['Name']}: Market Order Placed, Order_id:{order_id}")
            else:
                logger.error(f"{this_user['Name']}: Market Order Placement Failed, Order_id:{order_id}")
    return new_order_details_list


def place_close_orders(order_dict: typing.Dict, this_user: typing.Dict, order_details_list: typing.List[typing.Dict]):
    """
    Place close order.

    :param order_details_list:
    :param order_dict:
    :param this_user:
    :return:
    """
    broker = this_user['broker']
    for index, order_details in enumerate(order_details_list):
        order_id = order_details['order_id']
        order_status, status_message = broker.get_order_status(order_id=order_id)
        order_details_list[index]['status'] = order_status
        order_details_list[index]['message'] = status_message
        logger.debug(f"{this_user['Name']} : {order_details['order']['order_type']} Order Status: {order_status}, Order ID: {order_id}")
        if order_status == "COMPLETE":
            broker.cancel_order(order_id=order_id)
        elif order_status == "PENDING":
            broker.cancel_order(order_id=order_id)
            new_order_dict = dict(order_dict)
            new_order_dict['quantity'] = order_details['quantity']
            logger.debug(f"Order details: {new_order_dict} :: place_close_orders")
            order_id, message = broker.place_order(**new_order_dict)
            if order_id:
                order_details_list[index]['order_id'] = order_id
                order_details_list[index]['order'] = new_order_dict
                order_details_list[index]['status'] = broker.get_order_status(order_id=order_id)[0]
                order_details_list[index]['message'] = message
                logger.info(f"{this_user['Name']}: Close Order Placed, Order_id:{order_id}")
            else:
                logger.error(f"{this_user['Name']}: Close Order Placement Failed, Order_id:{order_id}")

    return order_details_list


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
            each_user: {"order_details_list": [],
                        'broker': users_df_dict[each_user]['broker']} for each_user in users_df_dict}
        this_instrument['exit_order_ids'] = {
            each_user: {"order_details_list": [],
                        "broker": users_df_dict[each_user]['broker']} for each_user in users_df_dict}

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
            logger.error(f"Error in getting live ticks {e.__str__()}", exc_info=True)
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
    to_dt = datetime.now()
    from_dt = calculations.get_last_2_wk_days()[0]
    # DO login for All users
    process_name = 'User Login Process'
    try:
        logger.info(f"Doing {process_name}")
        api_data = handle_user_details.read_user_api_details()
        if api_data is None:
            manager_dict['algo_error'] = f"{process_name} failed, No API details found"
            manager_dict['algo_running'] = False
            logger.critical("No API details found")
            return

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
            except Exception as e:
                logger.warning(f"Error in Logging in for Name : {each_key} Error : {e.__str__()}", exc_info=True)
                manager_dict['algo_error'] = f"{process_name} failed, Error in Logging in for Name : {each_key}"
                manager_dict['algo_running'] = False
                return
    except Exception as e:
        logger.warning(f"Error in {process_name}. Error : {e.__str__()} ", exc_info=True)
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
    # load freeze limits from database
    freeze_limits_dict: typing.Dict[str, typing.Dict] = json.loads(
        manage_local.get_user_preference_table("freeze_limits"))

    while manager_dict['force_stop'] is False:
        time.sleep(1)  # wait for 1 second/iteration
        if manager_dict['update_rows'] == 1:
            manager_dict['update_rows'] = 0
            instruments_df_dict, instruments_df = add_rows(instruments_df_dict, main_broker,
                                                           users_df_dict)
            # reset final df, as new rows have been added
            # TODO: Verify this
            final_df = pd.DataFrame(columns=list(instruments_df.columns) + ['ltp', 'tradingsymbol'])

        if datetime.now() < nine_sixteen:
            continue

        _cols = ['tradingsymbol', 'exchange', 'quantity', 'timeframe', 'multiplier', 'entry_price', 'ltp',
                 'entry_time', 'exit_price', 'exit_time', 'target_price', 'sl_price', 'Row_Type', 'profit']
        final_df = final_df[_cols]
        final_df['Trend'] = np.where(final_df['multiplier'] == 1, 'BUY', 'SELL')

        # ---------- generate/update positions file ----------
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
            settings.DATA_FILES.get('POSITIONS_FILE_PATH'))  # TODO PNL of all users by the lot executed by the user
        # ---------- [DONE] generate/update positions file ----------

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

        final_df = final_df[final_df['Row_Type'] != 'T']

        for each_key in order_book_dict:
            try:
                order_book_dict[each_key] = list(order_book_dict[each_key].to_dict('index').values())
            except Exception as e:
                logger.critical(f"Error in Creating Order Book {e.__str__()}", exc_info=True)

        # This contains Orderbook of all the clients
        orderbook_export_data = {x: [] for x in app_data.OMS_TABLE_COLUMNS}
        for each_key in instruments_df_dict:
            row_data = instruments_df_dict[each_key]
            entry_time = row_data['entry_time']
            entry_price = row_data['entry_price']
            # if entry_time is None or entry_price is None:
            #     continue
            if isinstance(entry_time, datetime):
                if entry_time.date() == datetime.now().date():
                    orderbook_export_data["Entry Time"].append(entry_time.strftime("%H:%M:%S"))
                else:
                    continue
            elif isinstance(entry_time, str):
                orderbook_export_data["Entry Time"].append(entry_time)
            else:
                orderbook_export_data["Entry Time"].append(entry_time)  # todo: verify this
                # continue  # for NoneType don't show them in orderbook
            orderbook_export_data["Instrument"].append(row_data['tradingsymbol'])
            orderbook_export_data["Entry Price"].append(entry_price)
            orderbook_export_data["Exit Price"].append(row_data['exit_price'])

            exit_time = row_data['exit_time']
            if isinstance(exit_time, datetime):
                orderbook_export_data["Exit Time"].append(exit_time.strftime("%H:%M:%S"))
            else:
                orderbook_export_data["Exit Time"].append(exit_time)
            orderbook_export_data["Order Type"].append(row_data['order_type'])
            orderbook_export_data["Quantity"].append(row_data['quantity'])
            orderbook_export_data["Product Type"].append(row_data['product_type'])
            orderbook_export_data["Stoploss"].append(row_data['sl_price'])
            orderbook_export_data["Target"].append(row_data['target_price'])

            # concatenate order status for all users
            order_status = ""
            row_order_details = row_data.get("entry_order_ids")
            if row_order_details is not None:
                for each_user, this_user_order_details in row_order_details.items():
                    this_user = users_df_dict[each_user]
                    order_details_list = this_user_order_details["order_details_list"]
                    for each_order_details in order_details_list:
                        order_status += f"{this_user['Name']} : {each_order_details['status']}\n"

            orderbook_export_data["Order Status"].append(order_status)
            orderbook_export_data["instrument_df_key"].append(each_key)  # will be used to reference in close positions

        orderbook_export_data["Close Position?"] = [0] * len(orderbook_export_data["instrument_df_key"])
        manager_dict['orderbook_data'] = orderbook_export_data  # pass the dictionary to the UI

        # --------------- look for to be closed positions ---------------
        with ProfilerContext("Look for to be closed positions"):
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
        # -----------------------------------------------------------

        for each_key in instruments_df_dict:
            try:
                this_instrument = instruments_df_dict[each_key]
                this_instrument['transaction_type'] = this_instrument['transaction_type'].upper()
                ltp = main_broker.latest_ltp[this_instrument['instrument_token']]['ltp']
                this_instrument['ltp'] = ltp
                if (int((curr_date - nine_fifteen).seconds / 60) % this_instrument['timeframe'] > 0) or (
                        int((curr_date - nine_fifteen).seconds / 60) % this_instrument['timeframe'] == 0 and
                        curr_date.second > 30) and this_instrument['run_done'] == 1:
                    this_instrument['run_done'] = 0

                if int((curr_date - nine_fifteen).seconds / 60) % this_instrument[
                    'timeframe'] == 0 and curr_date.second <= 30 and (this_instrument['run_done'] == 0 and
                                                                      this_instrument['status'] == 0):
                    this_instrument['run_done'] = 1
                    logger.info(f"Running the {process_name} for {this_instrument['tradingsymbol']}")
                    with ProfilerContext("Getting historical data"):
                        df = main_broker.get_data(this_instrument['instrument_token'],
                                                  str(int(this_instrument['timeframe'])), 'minute', from_dt, to_dt)[0]

                    df = df[df.index < datetime.now().replace(microsecond=0, second=0)]
                    time_df_col = df.index
                    df = HA(df, ohlc=['open', 'high', 'low', 'close'])
                    df.index = time_df_col
                    if this_instrument['multiplier'] != 1 and this_instrument['transaction_type'].upper() == 'BUY':
                        logger.info(f" In Buy Loop. for {this_instrument['tradingsymbol']}\n"
                                    f"Buy Signal has been Activated for {this_instrument['tradingsymbol']}")
                        this_instrument['status'] = 1
                        this_instrument['multiplier'] = 1

                        this_instrument['entry_price'] = fix_values(
                            df['HA_close'].tail(1).values[0] * (1 - this_instrument['buy_ltp_percent'] / 100),
                            this_instrument['tick_size'])
                        this_instrument['entry_time'] = datetime.now()
                        if this_instrument['target_type'].lower() == 'percentage':
                            this_instrument['target_price'] = fix_values(
                                this_instrument['entry_price'] * (1 + this_instrument['target'] / 100),
                                this_instrument['tick_size'])
                        elif this_instrument['target_type'].lower() == 'value':
                            this_instrument['target_price'] = fix_values(
                                this_instrument['entry_price'] + this_instrument['target'],
                                this_instrument['tick_size'])

                        if this_instrument['stoploss_type'].lower() == 'percentage':
                            this_instrument['sl_price'] = fix_values(
                                this_instrument['entry_price'] * (1 - this_instrument['stoploss'] / 100),
                                this_instrument['tick_size'])

                        elif this_instrument['stoploss_type'].lower() == 'value':
                            this_instrument['sl_price'] = fix_values(
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
                                    order_details_list = place_orders(order_dict=order,
                                                                      freeze_limits_dict=freeze_limits_dict,
                                                                      symbol_name=this_instrument['Symbol Name'],
                                                                      this_user=this_user,
                                                                      order_type_str="Sell")
                                    this_instrument[
                                        'entry_order_ids'][each_user]['order_details_list'] = order_details_list
                                except Exception as e:
                                    logger.warning(f"Error in Sell Order Placement for {this_user['Name']}"
                                                   f" Error {e.__str__()}", exc_info=True)

                        logger.info(f" Instrument_Details : {this_instrument}")

                    elif (this_instrument['multiplier'] != -1 and
                          this_instrument['transaction_type'].upper() == 'SELL'):
                        logger.info(f" In Sell Loop. for {this_instrument['tradingsymbol']}")
                        logger.info(f" Sell Signal has been Activated for {this_instrument['tradingsymbol']}")
                        this_instrument['status'] = 1
                        this_instrument['multiplier'] = 1

                        this_instrument['entry_price'] = fix_values(
                            df['HA_close'].tail(1).values[0] * (1 - this_instrument['sell_ltp_percent'] / 100),
                            this_instrument['tick_size'])
                        this_instrument['entry_time'] = datetime.now()
                        if this_instrument['order_type'] == 'MARKET':
                            this_instrument['entry_price'] = ltp

                        if this_instrument['target_type'].lower() == 'percentage':
                            this_instrument['target_price'] = fix_values(
                                this_instrument['entry_price'] * (1 - this_instrument['target'] / 100),
                                this_instrument['tick_size'])
                        elif this_instrument['target_type'].lower() == 'value':
                            this_instrument['target_price'] = fix_values(
                                this_instrument['entry_price'] - this_instrument['target'],
                                this_instrument['tick_size'])

                        if this_instrument['stoploss_type'].lower() == 'percentage':
                            this_instrument['sl_price'] = fix_values(
                                this_instrument['entry_price'] * (1 + this_instrument['stoploss'] / 100),
                                this_instrument['tick_size'])

                        elif this_instrument['stoploss_type'].lower() == 'value':
                            this_instrument['sl_price'] = fix_values(
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
                                    order_details_list = place_orders(order_dict=order,
                                                                      freeze_limits_dict=freeze_limits_dict,
                                                                      symbol_name=this_instrument['Symbol Name'],
                                                                      this_user=this_user,
                                                                      order_type_str="Sell")
                                    this_instrument[
                                        'entry_order_ids'][each_user]['order_details_list'] = order_details_list
                                except Exception as e:
                                    logger.info(f"Error in Sell Order Placement for {this_user['Name']}"
                                                f" Error {e.__str__()}", exc_info=True)

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
                                new_order_details_list = place_market_orders(
                                    order_dict=this_instrument['order'],
                                    this_user=this_user,
                                    order_details_list=this_instrument['entry_order_ids'][each_user][
                                        'order_details_list'])
                                this_instrument['entry_order_ids'][each_user][
                                    'order_details_list'] = new_order_details_list

                            logger.info(f"Entry has been taken for {this_instrument['tradingsymbol']} ")
                            this_instrument['entry_time'] = datetime.now()
                            this_instrument['status'] = 2
                            # Place SL Order
                            order = {'variety': 'regular',
                                     'exchange': this_instrument['exchange'],
                                     'tradingsymbol': this_instrument['tradingsymbol'],
                                     'quantity': int(this_instrument['quantity']),  # TODO: Need to check
                                     'product': this_instrument['product_type'],
                                     'transaction_type': 'SELL',
                                     'order_type': 'SL',
                                     'price': this_instrument['sl_price'],
                                     'validity': 'DAY',
                                     'disclosed_quantity': None,
                                     'trigger_price': this_instrument['sl_price'] - this_instrument['tick_size'] if
                                     this_instrument['transaction_type'] == 'BUY' else this_instrument['sl_price'] + 1 *
                                                                                       this_instrument['tick_size'],
                                     'squareoff': None,
                                     'stoploss': None,
                                     'trailing_stoploss': None,
                                     'tag': None}

                            for each_user in users_df_dict:
                                this_user = users_df_dict[each_user]
                                try:
                                    new_order = dict(order)
                                    new_order_details_list = place_orders(order_dict=new_order,
                                                                          freeze_limits_dict=freeze_limits_dict,
                                                                          symbol_name=this_instrument['Symbol Name'],
                                                                          this_user=this_user, order_type_str='SL')
                                    this_instrument[
                                        'exit_order_ids'][each_user]['order_details_list'] = new_order_details_list
                                except Exception as e:
                                    logger.critical(f"Error in SL Order Placement for {this_user['Name']} "
                                                    f"Error {e.__str__()}", exc_info=True)

                            continue

                if this_instrument['status'] == 2:  # Order Placed was executed
                    this_instrument['profit'] = (ltp - this_instrument['entry_price']) * this_instrument['multiplier'] * \
                                                this_instrument['quantity'] * this_instrument['lot_size']
                    final_df = final_df[final_df['Row_Type'] != 'T']
                    this_instrument['Row_Type'] = 'T'
                    final_df = final_df.append(this_instrument, ignore_index=True)

                    if ltp * this_instrument['multiplier'] >= (this_instrument['target_price'] *
                                                               this_instrument['multiplier']):
                        logger.info(f"Target has been Hit for {this_instrument['tradingsymbol']}")
                        this_instrument['exit_time'] = datetime.now()
                        this_instrument['exit_price'] = ltp
                        this_instrument['status'] = 0
                        # Cancel Pending SL Order and Placing a Market Order
                        if paper_trade == 0:
                            for each_user in users_df_dict:
                                this_user = users_df_dict[each_user]
                                try:
                                    order = {'variety': 'regular',
                                             'exchange': this_instrument['exchange'],
                                             'tradingsymbol': this_instrument['tradingsymbol'],
                                             'quantity': int(this_instrument['quantity']),
                                             'product': this_instrument['product_type'],
                                             'transaction_type': 'SELL',
                                             'order_type': 'MARKET',
                                             'price': None,
                                             'validity': 'DAY',
                                             'disclosed_quantity': None,
                                             'trigger_price': None,
                                             'squareoff': None,
                                             'stoploss': None,
                                             'trailing_stoploss': None,
                                             'tag': None}

                                    # ----------- place exit orders -----------------
                                    new_order_details_list = place_close_orders(order_dict=order,
                                                                                this_user=this_user,
                                                                                order_details_list=
                                                                                this_instrument['exit_order_ids'][
                                                                                    each_user]['order_details_list'])
                                    this_instrument['exit_order_ids'][each_user][
                                        'order_details_list'] = new_order_details_list
                                    # -------------------------------------------------

                                except Exception as e:
                                    logger.critical(
                                        f"Error in Closing Order Placement for {this_user['Name']} Error {e.__str__()}",
                                        exc_info=True)
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

                        # Cancel Pending SL Order and Placing a Market Order
                        if paper_trade == 0:
                            for each_user in users_df_dict:
                                this_user = users_df_dict[each_user]
                                try:
                                    order = {'variety': 'regular',
                                             'exchange': this_instrument['exchange'],
                                             'tradingsymbol': this_instrument['tradingsymbol'],
                                             'quantity': int(this_instrument['quantity']),
                                             'product': this_instrument['product_type'],
                                             'transaction_type': 'SELL',
                                             'order_type': 'MARKET',
                                             'price': None,
                                             'validity': 'DAY',
                                             'disclosed_quantity': None,
                                             'trigger_price': None,
                                             'squareoff': None,
                                             'stoploss': None,
                                             'trailing_stoploss': None,
                                             'tag': None}
                                    new_order_details_list = place_close_orders(order_dict=order,
                                                                                this_user=this_user,
                                                                                order_details_list=this_instrument[
                                                                                    'exit_order_ids'][each_user][
                                                                                    'order_details_list'])
                                    this_instrument['exit_order_ids'][
                                        each_user]['order_details_list'] = new_order_details_list
                                except Exception as e:
                                    logger.critical(f"Error in Closing Order Placement for {this_user['Name']}"
                                                    f" Error {sys.exc_info()}", exc_info=True)

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
                        if paper_trade == 0:
                            for each_user in users_df_dict:
                                this_user = users_df_dict[each_user]
                                try:
                                    order = {'variety': 'regular',
                                             'exchange': this_instrument['exchange'],
                                             'tradingsymbol': this_instrument['tradingsymbol'],
                                             'quantity': int(this_instrument['quantity']),
                                             'product': this_instrument['product_type'],
                                             'transaction_type': 'SELL',
                                             'order_type': 'MARKET',
                                             'price': None,
                                             'validity': 'DAY',
                                             'disclosed_quantity': None,
                                             'trigger_price': None,
                                             'squareoff': None,
                                             'stoploss': None,
                                             'trailing_stoploss': None,
                                             'tag': None}
                                    new_order_details_list = place_close_orders(order_dict=order,
                                                                                this_user=this_user,
                                                                                order_details_list=this_instrument[
                                                                                    'exit_order_ids'][each_user][
                                                                                    'order_details_list'])
                                    this_instrument['exit_order_ids'][
                                        each_user]['order_details_list'] = new_order_details_list
                                except Exception as e:
                                    logger.critical(f"Error in Closing Order Placement for {this_user['Name']}"
                                                    f" Error {e.__str__()}", exc_info=True)

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

                        # Cancel the SL Order placed and Place a opposite Limit Order which with Buffer and Close open position
                        this_instrument['close_positions'] = 0
                        continue
            except Exception as e:
                logger.critical(f'Error in {process_name} Strategy Function. {e.__str__()}', exc_info=True)
                manager_dict['algo_error'] = f"Error in Strategy Function, Error: {sys.exc_info()}"
                manager_dict['algo_running'] = False
                return


if __name__ == '__main__':
    main(manager_dict={'paper_trade': 0, 'algo_running': True, 'fore_stop': True, 'algo_error': None},
         cancel_orders_queue=multiprocessing.Queue())
