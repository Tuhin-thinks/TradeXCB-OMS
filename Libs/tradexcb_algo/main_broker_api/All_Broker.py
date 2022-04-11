import datetime
import json
import os
import sys
import threading
import urllib.parse as urlparse

import pandas as pd
import pyotp
import requests
# Alice Blue
from alice_blue import *
# Kite API
from kiteconnect import KiteConnect, KiteTicker
# Angel one API
from smartapi import SmartConnect

# IIFL API
from Libs.tradexcb_algo.Connect import XTSConnect
from Libs.tradexcb_algo.MarketDataSocketClient import MDSocket_io
from Libs.tradexcb_algo.main_broker_api import angel_helper, iifl_helper
from Libs.tradexcb_algo.main_broker_api import main_broker

Allcols = main_broker.Allcols


class All_Broker(main_broker.Broker):
    def __init__(self, **kwargs):
        """

        :param kwargs: Example {'Name': 'c',
                                 'Stock Broker Name': '',
                                 'apiKey': '',
                                 'apiSecret': '',
                                 'accountUserName': '',
                                 'accountPassword': '',
                                 'securityPin': nan,
                                 'totp_secret': '',
                                 'No of Lots': 1,
                                 'consumerKey': nan,
                                 'accessToken': nan,
                                 'host': nan,
                                 'source': nan,
                                 'market_appkey': nan,
                                 'market_secretkey': nan}
        """

        super().__init__(**kwargs)
        self.broker = None
        self.logger = self.get_logger(f"USER_{self.all_data_kwargs[Allcols.username.value]}")
        self.refreshtoken = None
        self.data = None
        self.do_login()
        self.latest_ltp = {}
        self.instrument_list = []
        self.instruments_map = dict()
        self.Instruments = list()
        self.web_socket = None

    def get_ltp(self, instrument_token):
        return self.latest_ltp[instrument_token]['ltp']

    def get_ltp_quote(self, instrument_token, name=None, exchange=None):
        if self.broker_name.lower() == 'zerodha':
            return self.broker.ltp(f"{exchange}:{name}")[f"{exchange}:{name}"]['last_price']

        if self.broker_name.lower() == 'iifl':
            if name == 'NIFTY 50':
                row = self.instrument_df[(self.instrument_df['name'] == 'NIFTY') & (
                        self.instrument_df['instrument_type'] == 'FUT')].sort_values(by='expiry').head(1).iloc[-1]
                name = row['tradingsymbol']
                exchange = row['exchange']
                instrument_token = int(row['instrument_token'])
            elif name == 'NIFTY BANK':
                row = self.instrument_df[(self.instrument_df['name'] == 'BANKNIFTY') & (
                        self.instrument_df['instrument_type'] == 'FUT')].sort_values(by='expiry').head(1).iloc[-1]
                name = row['tradingsymbol']
                exchange = row['exchange']
                instrument_token = int(row['instrument_token'])

            instrument_row = self.instrument_df[self.instrument_df['instrument_token'] == instrument_token]
            instrument_map = dict()
            instrument_map[instrument_token] = iifl_helper.get_symbol_from_token(
                instrument_row.iloc[-1]['exchange_token'], instrument_row.iloc[-1]['exchange'])
            instrument_map[instrument_row.iloc[-1]['exchange_token']] = instrument_token
            Instrument = [{'exchangeSegment': iifl_helper.get_exchange_number(instrument_row.iloc[-1]['exchange']),
                           'exchangeInstrumentID': int(
                               instrument_map[instrument_token].iloc[-1]['ExchangeInstrumentID'])}]
            ltp = self.market_api.get_quote(Instrument, 1502, 'JSON')
            ltp = json.loads(ltp['result']['listQuotes'][0])['Touchline']['LastTradedPrice']
            return ltp

    def get_ltp_vwap(self, tradingsymbols):
        instrument_map = dict()
        Instrument = list()
        if self.broker_name.lower() == 'iifl':
            for tradingsymbol in tradingsymbols:
                instrument_row = self.instrument_df[self.instrument_df['tradingsymbol'] == tradingsymbol]
                instrument_map[tradingsymbol] = iifl_helper.get_symbol_from_token(
                    instrument_row.iloc[-1]['exchange_token'], instrument_row.iloc[-1]['exchange'])
                instrument_map[instrument_row.iloc[-1][
                    'exchange_token']] = f"{instrument_row.iloc[-1]['exchange']}:{tradingsymbol}"
                Instrument.append(
                    {'exchangeSegment': iifl_helper.get_exchange_number(instrument_row.iloc[-1]['exchange']),
                     'exchangeInstrumentID': int(instrument_map[tradingsymbol].iloc[-1]['ExchangeInstrumentID'])})
            ltp = self.market_api.get_quote(Instrument, 1502, 'JSON')
            list_of_quotes = ltp['result']['listQuotes']
            list_of_quotes = [json.loads(x) for x in list_of_quotes]
            result = {instrument_map[x['ExchangeInstrumentID']]: {'last_price': x['Touchline']['LastTradedPrice'],
                                                                  'average_price': x['Touchline']['AverageTradedPrice']}
                      for x in list_of_quotes}

            return result

    def get_live_ticks(self):

        if self.broker_name.lower() == 'zerodha':
            def on_ticks(ws, ticks):
                # print(ticks)
                try:
                    for x in ticks:
                        # print("One Tick : ", x)
                        ts = x['timestamp']
                        if ts is None:
                            continue

                        price = x['last_price']
                        instrument_token = x['instrument_token']
                        ts = ts.replace(second=0, microsecond=0)
                        if instrument_token not in self.latest_ltp:
                            self.latest_ltp[instrument_token] = {"ltp": None}
                        self.latest_ltp[instrument_token]['ltp'] = price
                except:
                    print(sys.exc_info())
                    self.log_this(log_message="Error in on_ticks", log_level="error")

            def on_connect(ws, response):
                print("I am in On Connect")

                self.web_socket = ws
                subs(self.instrument_list)

            def subs(instrument_token):
                print(instrument_token)
                assert instrument_token is not None, "Instrument Token is None.Exiting"

                self.web_socket.subscribe(instrument_token)
                self.web_socket.set_mode(self.web_socket.MODE_FULL, instrument_token)
                return

            kws = KiteTicker(self.all_data_kwargs[Allcols.apikey.value], self.data["access_token"],
                             self.all_data_kwargs[Allcols.username.value])
            kws.debug = False
            kws.on_ticks = on_ticks
            kws.on_connect = on_connect
            kws.connect(threaded=True)

            return

        if self.broker_name.lower() == 'iifl':

            for each_instrument in self.instrument_list:
                instrument_row = self.instrument_df[self.instrument_df['instrument_token'] == each_instrument]
                self.instruments_map[each_instrument] = iifl_helper.get_symbol_from_token(
                    instrument_row.iloc[-1]['exchange_token'], instrument_row.iloc[-1]['exchange'])
                self.instruments_map[instrument_row.iloc[-1]['exchange_token']] = each_instrument
                self.Instruments.append(
                    {'exchangeSegment': iifl_helper.get_exchange_number(instrument_row.iloc[-1]['exchange']),
                     'exchangeInstrumentID': int(
                         self.instruments_map[each_instrument].iloc[-1]['ExchangeInstrumentID'])})

            def on_connect():
                """Connect from the socket."""
                # response = xt.send_subscription(Instruments, 1505)
                response = self.market_api.send_subscription(self.Instruments, 1501)
                # response = self.market_api.send_subscription(self.Instruments, 1510)
                # response = self.market_api.send_subscription(self.Instruments, 1502)
                print('Sent Subscription request!', response)

            def on_message(data):
                print('I received a message!')
                self.logger.info(f"Received a  message: {data}")
                self.logger.info("The web socket was disconnected and is getting Connected Again Here: ")

            def on_disconnect():
                self.logger.info(f"Market Socket is Disconnected")
                print('Market Data Socket disconnected!')

            # Callback for error
            def on_error(data):
                """Error from the socket."""
                self.logger.info(f"Market Data Error {data} ")

            def on_message1501_json_full(data):
                try:
                    # print('I received a 1501 Level1,Touchline message!' + data)
                    # self.logger.info(f"1501 Touchline Message Received: {data} {type(data)}")
                    data = json.loads(data)
                    # print(data)
                    self.latest_ltp[self.instruments_map[data["ExchangeInstrumentID"]]]['ltp'] = data['Touchline'][
                        'LastTradedPrice']

                except:
                    self.logger.info(f"Error in 1501 json full")

            self.soc.on_connect = on_connect
            self.soc.on_message = on_message
            self.soc.on_message1501_json_full = on_message1501_json_full
            self.soc.on_disconnect = on_disconnect
            self.soc.on_error = on_error

            # Event listener
            self.el = self.soc.get_emitter()
            self.el.on('connect', on_connect)
            self.el.on('message', on_message)
            self.el.on('1501-json-full', on_message1501_json_full)
            threading.Thread(target=self.soc.connect).start()
            # time.sleep(5)
            return

    def subscribe_instrument(self, instrument_tokens):
        if self.broker_name.lower() == 'iifl':
            instrument_map = dict()
            Instrument = list()
            for tradingsymbol in instrument_tokens:
                instrument_row = self.instrument_df[self.instrument_df['instrument_token'] == tradingsymbol]
                instrument_map[tradingsymbol] = iifl_helper.get_symbol_from_token(
                    instrument_row.iloc[-1]['exchange_token'], instrument_row.iloc[-1]['exchange'])
                instrument_map[instrument_row.iloc[-1][
                    'exchange_token']] = f"{instrument_row.iloc[-1]['exchange']}:{tradingsymbol}"
                Instrument.append(
                    {'exchangeSegment': iifl_helper.get_exchange_number(instrument_row.iloc[-1]['exchange']),
                     'exchangeInstrumentID': int(instrument_map[tradingsymbol].iloc[-1]['ExchangeInstrumentID'])})
            response = self.market_api.send_subscription(Instrument, 1501)
        elif self.broker_name.lower() == 'zerodha':
            self.web_socket.subscribe(instrument_tokens)
            self.web_socket.set_mode(self.web_socket.MODE_FULL, instrument_tokens)

    def get(self, name):
        if name == 'username':
            return self.all_data_kwargs[Allcols.username.value]

    def do_login(self):
        username = self.all_data_kwargs[Allcols.username.value]
        password = self.all_data_kwargs[Allcols.password.value]
        apikey = self.all_data_kwargs[Allcols.apikey.value]
        # app_id = self.all_data_kwargs[Allcols.apikey.value]
        secretkey = self.all_data_kwargs[Allcols.apisecret.value]
        totp_code = self.all_data_kwargs[Allcols.totp_secret.value]
        security_pin = self.all_data_kwargs[Allcols.pin.value]
        # access_token = self.all_data_kwargs[Allcols.access_token.value]
        host = self.all_data_kwargs[Allcols.host.value]
        # consumer_key = self.all_data_kwargs[Allcols.consumer_key.value]
        source = self.all_data_kwargs[Allcols.source.value]
        market_appkey = self.all_data_kwargs['market_appkey']
        market_secretkey = self.all_data_kwargs['market_secretkey']

        self.log_this(f"Logging in the API for {username} Broker {self.broker_name}", log_level="info")

        if self.broker_name.lower() == 'zerodha':
            try:
                login_url = "https://kite.trade/connect/login?api_key=" + str(apikey)
                request_token = ""
                session = requests.Session()
                session.headers.update(
                    {
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3'})
                session.get(login_url)
                res0 = session.get(login_url)
                res1 = session.post("https://kite.zerodha.com/api/login",
                                    data={'user_id': username,
                                          'password': password})
                data = json.loads(res1.text)
                # print("Data", data)
                authenticator_totp = pyotp.TOTP(totp_code)
                res2 = session.post("https://kite.zerodha.com/api/twofa",
                                    data={'user_id': username,
                                          'request_id': data['data']["request_id"],
                                          'twofa_value': authenticator_totp.now()})
                print(res0.url + "&skip_session=true")
                try:
                    res = session.get(res0.url + "&skip_session=true")
                    print(res.url)
                    parsed = urlparse.urlparse(res.history[1].headers['location'])
                    request_token = urlparse.parse_qs(parsed.query)['request_token'][0]
                except Exception as e:
                    self.log_this(f"Error in getting request token for {username} Broker {self.broker_name}",
                                  log_level="error")

                session.close()
                kite = KiteConnect(api_key=apikey)
                print("request token:", request_token)
                data = kite.generate_session(request_token, api_secret=secretkey)
                self.data = data
                app = KiteConnect(apikey)
                app.set_access_token(data['access_token'])
                self.broker = app

            except:
                self.broker = None
                self.log_this(f"Error in logging in for {username} Broker : {self.broker_name}"
                              f" Error : {sys.exc_info()}")


        elif self.broker_name.lower() == 'iifl':
            try:
                self.market_api = XTSConnect(market_appkey, market_secretkey, source)
                response = self.market_api.marketdata_login()
                # iifl_helper.download_master_file(self.market_api)
                # print(self.broker.get_profile())
                self.broker = XTSConnect(apikey, secretkey, source, host)

                self.market_token = response['result']['token']
                print(f"Token : {self.market_token}")
                self.userid = response['result']['userID']
                self.soc = MDSocket_io(self.market_token, self.userid)
                self.broker.interactive_login()
                # sys.exit(0)
                # Connecting to Marketdata socket
                iifl_helper.download_master_file(self.market_api)

            except:
                self.broker = None
                self.log_this(
                    f"Error in logging in for {username} Broker : {self.broker_name} Error : {sys.exc_info()}")


        elif self.broker_name.lower() == 'alice blue':
            try:
                access_token = AliceBlue.login_and_get_access_token(username=str(int(username)), password=str(password),
                                                                    twoFA=str(int(security_pin)),
                                                                    api_secret=str(secretkey), app_id=str(apikey))
                self.log_this(f"Access Token : {access_token}")
                self.broker = AliceBlue(username=str(int(username)), password=str(password), access_token=access_token)
            except:
                self.broker = None
                self.log_this(
                    f"Error in logging in for {username} Broker : {self.broker_name} Error : {sys.exc_info()}")


        elif self.broker_name.lower() == 'angel':
            try:
                obj = SmartConnect(api_key=apikey)
                data = obj.generateSession(username, password)
                self.data = data
                refreshToken = data['data']['refreshToken']
                self.refreshtoken = refreshToken  # This
                self.broker = obj
            except:

                self.broker = None
                self.log_this(
                    f"Error in logging in for {username} Broker : {self.broker_name} Error : {sys.exc_info()}")

    def place_order(self, **kwargs):
        """

        :param kwargs: kwargs = {'variety' :'regular',
                                'exchange' : 'NFO',
                                'tradingsymbol' : 'NIFTY2230317500CE',
                                'quantity':50,
                                 'product' : "MIS",
                                'transaction_type' : 'BUY',
                                'order_type' :'MARKET',
                                'price': None,
                                'validity': 'DAY',
                                'disclosed_quantity' : None ,
                                'trigger_price' :None ,
                                'squareoff' : None ,
                                'stoploss' : None ,
                                'trailing_stoploss' : None,
                                'tag' : None }
        :return: order_id,message
        """
        order_id = None
        message = 'success'
        tradingsymbol = kwargs['tradingsymbol']
        instrument_row = self.instrument_df[(self.instrument_df['tradingsymbol'] == kwargs['tradingsymbol']) & (
                self.instrument_df['exchange'] == kwargs['exchange'])]

        if self.broker_name.lower() == 'zerodha':
            try:
                order_id = self.broker.place_order(variety=kwargs['variety'],
                                                   exchange=kwargs['exchange'],
                                                   tradingsymbol=kwargs['tradingsymbol'],
                                                   quantity=kwargs['quantity'], product=kwargs['product'],
                                                   transaction_type=kwargs['transaction_type'],
                                                   order_type=kwargs['order_type'],
                                                   price=None if 'price' not in kwargs else kwargs['price'],
                                                   validity=KiteConnect.VALIDITY_DAY,
                                                   disclosed_quantity=None if 'disclosed_quantity' not in kwargs else
                                                   kwargs['disclosed_quantity'],
                                                   trigger_price=None if 'trigger_price' not in kwargs else kwargs[
                                                       'trigger_price'],
                                                   squareoff=None if 'squareoff' not in kwargs else kwargs['squareoff'],
                                                   stoploss=None if 'stoploss' not in kwargs else kwargs['stoploss'],
                                                   trailing_stoploss=None if 'trailing_stoploss' not in kwargs else
                                                   kwargs['trailing_stoploss'],
                                                   tag=None)
            except:
                order_id = None
                message = str(sys.exc_info())
                self.log_this(f"Error in Order Placement ")
                self.log_this(f"{str(sys.exc_info())}")


        elif self.broker_name.lower() == 'iifl':
            exchange_map = {'NSE': self.broker.EXCHANGE_NSECM, 'NFO': self.broker.EXCHANGE_NSEFO}
            order_map = {'MARKET': 'MARKET', 'LIMIT': 'LIMIT', 'SL-M': "STOPMARKET", 'SL': "STOPLIMIT"}

            try:
                response = self.broker.place_order(
                    exchangeSegment=exchange_map[kwargs['exchange']],
                    exchangeInstrumentID=int(instrument_row['exchange_token'].iloc[-1]),
                    productType=kwargs['product'],
                    orderType=order_map[kwargs['order_type']],
                    orderSide=kwargs['transaction_type'],
                    timeInForce=kwargs['validity'],
                    disclosedQuantity=0 if kwargs['disclosed_quantity'] is None else kwargs['disclosed_quantity'],
                    orderQuantity=kwargs['quantity'],
                    limitPrice=0 if kwargs['price'] is None or 'price' not in kwargs else kwargs['price'],
                    stopPrice=0 if kwargs['trigger_price'] is None else kwargs['trigger_price'],
                    orderUniqueIdentifier="454845")
                order_id = response['result']['AppOrderID']
            except:
                order_id = None
                message = str(sys.exc_info())
                self.log_this(f"Error in Order Placement ")
                self.log_this(f"{str(sys.exc_info())}")


        elif self.broker_name.lower() == 'alice blue':
            transaction_map = {'BUY': TransactionType.Buy, 'SELL': TransactionType.Sell}
            order_map = {'MARKET': OrderType.Market, 'LIMIT': OrderType.Limit, 'SL-M': OrderType.StopLossMarket,
                         'SL': OrderType.StopLossLimit}
            product_map = {'MIS': ProductType.Intraday, 'NRML': ProductType.Delivery, 'CNC': ProductType.Delivery}
            try:
                instrument = None
                instrument = self.broker.get_instrument_by_token(kwargs['exchange'],
                                                                 int(instrument_row['exchange_token'].iloc[-1]))

                response = self.broker.place_order(transaction_type=transaction_map[kwargs['transaction_type']],
                                                   instrument=instrument,
                                                   quantity=kwargs['quantity'],
                                                   order_type=order_map[kwargs['order_type']],
                                                   product_type=product_map[kwargs['product']],
                                                   price=0.0 if kwargs['price'] is None else float(kwargs['price']),
                                                   trigger_price=None if 'trigger_price' not in kwargs or kwargs[
                                                       'trigger_price'] is None else float(kwargs['trigger_price']),
                                                   stop_loss=None if 'stoploss' not in kwargs or kwargs[
                                                       'stoploss'] is None else kwargs['stoploss'],
                                                   square_off=None if 'squareoff' not in kwargs or kwargs[
                                                       'squareoff'] is None else kwargs['squareoff'],
                                                   trailing_sl=None if 'trailing_stoploss' not in kwargs or kwargs[
                                                       'trailing_stoploss'] is None else kwargs['trailing_stoploss'],
                                                   is_amo=False)
                order_id = response['data']['oms_order_id']
            except:
                order_id = None
                message = str(sys.exc_info())
                self.log_this(f"Error in Order Placement")
                self.log_this(f"{str(sys.exc_info())}")


        elif self.broker_name.lower() == 'angel':
            product_map = {'MIS': 'INTRADAY', 'NRML': 'CARRYFORWARD', 'CNC': 'DELIVERY'}
            order_map = {'MARKET': 'MARKET', 'LIMIT': 'LIMIT', 'SL': 'STOPLOSS_LIMIT', 'SL-M': 'STOPLOSS_MARKET'}
            variety = 'NORMAL' if kwargs['order_type'] in ['LIMIT', 'MARKET'] else 'STOPLOSS'
            try:
                orderparams = {
                    "variety": variety,
                    "tradingsymbol": angel_helper.get_symbol_from_token(str(instrument_row['exchange_token'].iloc[-1]),
                                                                        kwargs['exchange']),
                    "symboltoken": str(instrument_row['exchange_token'].iloc[-1]),
                    "transactiontype": kwargs['transaction_type'],
                    "exchange": kwargs['exchange'],
                    "ordertype": order_map[kwargs['order_type']],
                    "producttype": product_map[kwargs['product']],
                    "duration": kwargs['validity'],
                    "price": "0" if kwargs['price'] is None else str(kwargs['price']),
                    "squareoff": "0" if 'squareoff' not in kwargs or kwargs['squareoff'] is None else str(
                        kwargs['squareoff']),
                    "stoploss": "0" if 'stoploss' not in kwargs or kwargs['stoploss'] is None else str(
                        kwargs['stoploss']),
                    "triggerprice": "0" if 'trigger_price' not in kwargs or kwargs['trigger_price'] is None else str(
                        kwargs['trigger_price']),
                    "quantity": str(kwargs['quantity']

                                    )
                }
                response = self.broker.placeOrder(orderparams)
                order_id = response
            except:
                order_id = None
                message = str(sys.exc_info())
                self.log_this(f"Error in Order Placement")
                self.log_this(f"{str(sys.exc_info())}")

        return order_id, message

    def cancel_order(self, order_id):
        '''

        :param kwargs:
        :return:
        '''
        message = 'success'
        order_id = order_id
        error_message = f"Error in Cancelling Order {order_id}"

        if self.broker_name.lower() == 'zerodha':
            try:
                orders_history = self.get_order_book()
                order_row = orders_history[orders_history['order_id'].astype(str) == str(order_id)]
                order_id = self.broker.cancel_order(variety=order_row.iloc[-1]['variety'], order_id=order_id)
            except:
                order_id = None
                message = str(sys.exc_info())
                self.log_this(error_message)
                self.log_this(f"{str(sys.exc_info())}")

        elif self.broker_name.lower() == 'iifl':
            try:
                order_history = pd.DataFrame(self.broker.get_order_book()['result'])
                order_row = order_history[order_history['AppOrderID'].astype(str) == str(order_id)]
                self.broker.cancel_order(appOrderID=order_id,
                                         orderUniqueIdentifier=order_row.iloc[-1]['OrderUniqueIdentifier'])
            except:
                order_id = None
                message = str(sys.exc_info())
                self.log_this(error_message)
                self.log_this(f"{str(sys.exc_info())}")


        elif self.broker_name.lower() == 'alice blue':
            try:
                orders_history = self.get_order_book()
                order_row = orders_history[orders_history['oms_order_id'].astype(str) == str(order_id)]
                order_id = self.broker.cancel_order(order_id)
            except:
                order_id = None
                message = str(sys.exc_info())
                self.log_this(error_message)
                self.log_this(f"{str(sys.exc_info())}")


        elif self.broker_name.lower() == 'angel':
            try:
                orders_history = self.get_order_book()
                order_row = orders_history[orders_history['orderid'] == str(order_id)]
                variety = order_row.iloc[-1]['variety']
                order_id = self.broker.cancelOrder(variety=variety, order_id=order_id)
            except:
                order_id = None
                message = str(sys.exc_info())
                self.log_this(error_message)
                self.log_this(f"{str(sys.exc_info())}")

        return message

    def get_order_status(self, order_id):
        '''

        :return:
        '''
        order_status = None
        error_message = 'Error in getting Order Status'
        message = None

        if self.broker_name.lower() == 'zerodha':
            try:

                order_history = pd.DataFrame(self.broker.orders())
                order_status = order_history[order_history['order_id'] == str(order_id)]['status'].iloc[-1]
                if order_status == 'OPEN':
                    order_status = 'PENDING'

            except:

                message = str(sys.exc_info())
                self.log_this(error_message)
                self.log_this(f"{str(sys.exc_info())}")

        elif self.broker_name.lower() == 'iifl':
            try:

                order_history = pd.DataFrame(self.broker.get_order_book()['result'])
                order_status = \
                    order_history[order_history['AppOrderID'].astype(str) == str(order_id)]['OrderStatus'].iloc[-1]
                if order_status.lower() == 'filled':
                    order_status = 'complete'
                if order_status.lower() == 'new':
                    order_status = 'pending'
                if order_status.lower() in ['cancelled', 'rejected', 'complete', 'pending']:
                    order_status = order_status.upper()


            except:

                message = str(sys.exc_info())
                self.log_this(error_message)
                self.log_this(f"{str(sys.exc_info())}")

        elif self.broker_name.lower() == 'alice blue':
            try:
                orders = self.broker.get_order_history()
                order_history = pd.DataFrame(orders['data']['pending_orders'] + orders['data']['completed_orders'])
                order_status = \
                    order_history[order_history['oms_order_id'].astype(str) == str(order_id)]['order_status'].iloc[-1]
                if order_status == 'open':
                    order_status = 'pending'
                if order_status in ['cancelled', 'rejected', 'complete', 'pending']:
                    order_status = order_status.upper()
            except:

                message = str(sys.exc_info())
                self.log_this(error_message)
                self.log_this(f"{str(sys.exc_info())}")

        elif self.broker_name.lower() == 'angel':
            try:
                order_history = pd.DataFrame(self.broker.orderBook()['data'])
                order_status = order_history[order_history['orderid'] == order_id]['status'].iloc[-1]
                if order_status == 'open':
                    order_status = 'pending'
                if order_status in ['cancelled', 'rejected', 'complete', 'pending']:
                    order_status = order_status.upper()
            except:

                message = str(sys.exc_info())
                self.log_this(error_message)
                self.log_this(f"{str(sys.exc_info())}")

        return order_status, message

    def get_order_book(self):
        order_history = pd.DataFrame()
        error_message = 'Error in Getting Order Book'
        if self.broker_name.lower() == 'zerodha':
            try:

                order_history = pd.DataFrame(self.broker.orders())
                return order_history

            except:
                message = str(sys.exc_info())
                self.log_this(error_message)
                self.log_this(f"{str(sys.exc_info())}")

        elif self.broker_name.lower() == 'iifl':
            try:

                order_history = pd.DataFrame(self.broker.get_order_book()['result'])
                return order_history


            except:
                self.log_this(error_message)
                self.log_this(f"{str(sys.exc_info())}")

        elif self.broker_name.lower() == 'alice blue':
            try:
                cols = ['validity', 'user_order_id', 'trigger_price', 'transaction_type', 'trading_symbol',
                        'remaining_quantity', 'rejection_reason', 'quantity', 'product', 'price', 'order_type',
                        'order_tag', 'order_status', 'order_entry_time', 'oms_order_id', 'nest_request_id', 'lotsize',
                        'login_id', 'leg_order_indicator', 'instrument_token', 'filled_quantity', 'exchange_time',
                        'exchange_order_id', 'exchange', 'disclosed_quantity', 'client_id', 'average_price']
                orders = self.broker.get_order_history()
                if 'pending_orders' in orders['data'] and 'completed_orders' in orders['data']:
                    order_history = pd.DataFrame(orders['data']['pending_orders'] + orders['data']['completed_orders'])
                else:
                    order_history = pd.DataFrame(columns=cols)
                return order_history
            except:
                self.log_this(error_message)
                self.log_this(f"{str(sys.exc_info())}")

        elif self.broker_name.lower() == 'angel':
            try:
                order_history = pd.DataFrame(self.broker.orderBook()['data'])
                return order_history
            except:

                message = str(sys.exc_info())
                self.log_this(error_message)
                self.log_this(f"{str(sys.exc_info())}")

        return order_history

    def get_data(self, instrument_token, timeframe: str, timeframesuffix: str, from_dt: datetime.datetime,
                 to_dt: datetime.datetime):
        """

        :param instrument_token:
        :param timeframe:
        :param timeframesuffix:
        :param from_dt:
        :param to_dt:
        :return: DataFrame
        """
        df = pd.DataFrame()
        message = None
        error_message = 'Error in getting data'

        instrument_row = self.instrument_df[self.instrument_df['instrument_token'] == int(instrument_token)]

        if self.broker_name.lower() == 'zerodha':
            try:
                if timeframe == '1':
                    interval = 'minute'
                else:
                    interval = str(timeframe) + str(timeframesuffix)
                df = self.broker.historical_data(instrument_token=int(instrument_token), interval=interval,
                                                 from_date=from_dt, to_date=to_dt)

                for x in range(0, len(df)):
                    df[x]['date'] = df[x]['date'].replace(tzinfo=None)
                df = pd.DataFrame(df)
                df.set_index('date', inplace=True)
                message = 'success'
            except Exception as e:
                self.logger.critical(f"Error is getting data: {str(e)}", exc_info=True)

        elif self.broker_name.lower() == 'iifl':
            # instrument_iifl_row = iifl_helper.get_symbol_from_token(instrument_row.iloc[-1]['exchange_token'],instrument_row.iloc[-1]['exchange'])
            import datetime
            to_dt = datetime.datetime.now()
            from_dt = to_dt - datetime.timedelta(days=5)
            to_dt = int(to_dt.timestamp())
            from_dt = int(from_dt.timestamp())
            try:
                res = self.broker.get_ohlc(
                    exchangeSegment=int(iifl_helper.get_exchange_number(instrument_row.iloc[-1]['exchange'])),
                    exchangeInstrumentID=int(instrument_row.iloc[-1]['exchange_token']), startTime=from_dt,
                    endTime=to_dt, compressionValue=int(timeframe) * 60)
                res = res['result']['dataReponse']
                res = res.split(',')
                final_res = []
                for each_elem in res:
                    final_res.append(each_elem.split('|'))

                df = pd.DataFrame(final_res,
                                  columns=['time', 'open', 'high', 'low', 'close', 'volume', 'open_interest', 'None'])
                df = df[['time', 'open', 'high', 'low', 'close', 'volume', 'open_interest']]
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df['time'] = df['time'].apply(lambda x: x.replace(second=0))
                df['date'] = df['time'] + pd.Timedelta(minutes=int(int(timeframe) * 60 / 60))
                df['open'] = df['open'].astype(float)
                df['high'] = df['high'].astype(float)
                df['low'] = df['low'].astype(float)
                df['close'] = df['close'].astype(float)
                df['volume'] = df['volume'].astype(int)
                df.index = df['date']
                return df
            except:
                message = str(sys.exc_info())
                self.log_this(error_message)
                self.log_this(f"{str(sys.exc_info())}")

        return df, message

    def log_this(self, log_message, log_level='error'):
        try:
            if log_level == 'info':
                self.logger.info(log_message)
            else:
                self.logger.critical(
                    f"Username : {self.get(name='username')} Broker: {self.broker_name} {str(log_message)}",
                    exc_info=True)
        except Exception as e:
            self.logger.critical(f"Error in logging a message {e.__str__()}", exc_info=True)


if __name__ == '__main__':
    df = pd.read_excel('multi.xls', sheet_name='User Details')
    df = df.tail(3)

    df_dict = df.to_dict('index')
    print(df)
    import time

    # time.sleep(5)
    all_brokers = dict()
    all_orders = dict()
    for key, value in df_dict.items():
        print(value)
        all_brokers[key] = All_Broker(**value)
        time.sleep(1)
