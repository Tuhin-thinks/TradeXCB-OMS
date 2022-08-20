import sys
import time

import numpy as np
import pandas as pd
import requests

from BrokerMapping.dependencies.finvasia_helper import ShoonyaApiPy
from BrokerMapping.main_broker import Broker


class Finvasia(Broker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.live_ltp_data = dict()
        self.streaming_flag = 0
        self.do_login()

    def do_login(self):
        """Logins with the broker and returns broker instance
        """
        self.client = ShoonyaApiPy()
        try:
            res = self.client.login(
                userid=self.credentials['USER_ID'],
                password=self.credentials['PASSWORD'],
                twoFA=self.credentials['DOB'],
                vendor_code=self.credentials['VENDER_CODE'],
                api_secret=self.credentials['API_SECRET'],
                imei=self.credentials['IMEI']
            )
            self.connection_stat = res['stat']
        except requests.exceptions.ConnectionError as e:
            print("Connection with the broker unsuccessful", e)
            self.connection_stat == "connection error"
        except Exception as e:
            self.log_this(e, 'error')
            self.connection_stat == "connection error"

    def check_login(self):
        """Return if login was successful or not
        """
        try:
            if self.connection_stat == "ok":
                return 1
            return 0
        except Exception as e:
            self.log_this(e, 'error')
            return 0

    def place_order(self, **kwargs):
        """place order with the provided kwargs
        
        Args:
            kwargs (dict) : {
                'exchange' : [BCD, CDS, BSE, MCX, NFO, NSE],
                'tradingsymbol' : '',
                'quantity': int,
                'product' : [MIS, CNC, NRML],
                'transaction_type' : [BUY, SELL],
                'order_type' : [MARKET, LIMIT],
                'price': [int, None],
                'validity': [DAY, IOC, TTL],
                'stoploss' : [float, None],
            }
        
        Returns:
            int: Unique order id of the order
            str : Message from the client
        """
        message = "Success"
        order_id = None
        try:
            if kwargs['order_type'] == "MARKET":
                price_type = "MKT" if kwargs['stoploss'] == None else "SL-MKT"
            else:
                price_type = "LMT" if kwargs['stoploss'] == None else "SL-LMT"

            res = self.client.place_order(
                buy_or_sell='B' if kwargs['transaction_type'] == "BUY" else 'S',
                product_type='C' if kwargs['product'] == "CNC" else 'M',
                exchange=kwargs['exchange'],
                tradingsymbol=kwargs['tradingsymbol'] if kwargs['exchange'] not in ["NSE", "NFO"] else kwargs[
                                                                                                           'tradingsymbol'] + "-EQ",
                quantity=kwargs['quantity'],
                price_type=price_type,
                price=kwargs['price'],
                trigger_price=None if kwargs['stoploss'] == None else kwargs['stoploss'],
                retention='DAY',
                discloseqty=None
            )
            order_id = int(res['norenordno'])
            message = res['stat']
        except Exception as e:
            self.log_this(e, 'error')
            message = "Error"
            order_id = -1

        return order_id, message

    def cancel_order(self, order_id: str):
        """Cancels order with the given id

        Args:
            order_id (str): Unique order id
        
        Returns:
            status_code <int>: -1 for failure, 1 for success
            message <str>: Message from the broker
        """
        message = "Success"
        order_id = None
        try:
            ret = self.client.cancel_order(orderno=order_id)
            order_id = 0 if ret['stat'] != 'ok' else 1
            message = ret['stat']

        except Exception as e:
            self.log_this(e, 'error')
            order_id = -1
            message = 'Error'

        return order_id, message

    def get_order_status(self, order_id: str):
        pass

    def get_ltp(self, trading_symbols: list) -> pd.DataFrame:

        """Returns the last traded price of the instrument
        
        Args:
            trading_symbols: List of unique trading symbols
        
        Returns:
            pd.DataFrame: 
                symbolName: Unique symbol
                price: Current price of the symbol
        """
        new_dict = dict()
        convert_dict = {
            'symbolName': object,
            'price': np.float64,
        }
        if self.streaming_flag == 0:
            self.start_streaming(trading_symbols)
            time.sleep(10)
        try:
            for symbol in trading_symbols:
                if symbol in self.live_ltp_data.keys():
                    new_dict[symbol] = self.live_ltp_data[symbol]
                else:
                    new_dict[symbol] = 0

        except Exception as e:
            self.log_this(e, 'error')

        ltp_dataframe = pd.DataFrame(new_dict.items(), columns=['symbolName', 'price'])
        ltp_dataframe.astype(convert_dict)
        return ltp_dataframe

    def start_streaming(self, tradingsymbols: list):
        feed_opened = False

        def event_handler_order_update(order):
            print(f"order feed {order}")

        def event_handler_feed_update(tick_data):
            print(f"feed update {tick_data}")

        def open_callback():
            global feed_opened
            feed_opened = True

        req_list = []
        for symbol in tradingsymbols:
            df_line = self.instrument_df[(self.instrument_df['tradingsymbol'] == symbol)].iloc[-1]
            exchange = df_line['exchange']
            exchange_token = df_line['exchange_token']
            req_list.append(f'{exchange}|{exchange_token}')

        self.client.start_websocket(order_update_callback=event_handler_order_update,
                                    subscribe_callback=event_handler_feed_update, socket_open_callback=open_callback)

        while (feed_opened == False):
            pass

        self.client.subscribe(req_list)

    def get_order_book(self):
        """Returns all the orders that have been placed today
        
        Returns:
            pd.DataFrame: {
                'exchange' : [BCD, CDS, BSE, MCX, NFO, NSE], - <object>
                'tradingsymbol' : '',  <object>
                'quantity': int, <np.int64> 
                'product' : [MIS, CNC, NRML], <object> 
                'transaction_type' : [BUY, SELL], - <object>
                'order_type' : [MARKET, LIMIT], - <object> 
                'price': [int, None], - <np.int64> 
                'validity': [DAY, IOC, TTL], <object> 
                'stoploss' : [float, None], - <np.float64> 
                'orderstatus': <object>
            }
        """
        columns = ['exchange', 'tradingsymbol', 'quantity', 'product', 'transaction_type',
                   'order_type', 'price', 'validity', 'stoploss', 'orderstatus']
        df_columns = ['exch', 'tsym', 'qty', 'trantype', 'prd',
                      'prctyp', 'prc', 'ret', 'status']
        convert_dict = {
            "exchange": object,
            "tradingsymbol": str,
            "quantity": np.int64,
            "product": object,
            "transaction_type": object,
            "order_type": object,
            "price": np.float64,
            "validity": object,
            "stoploss": np.float64,
            "orderstatus": object
        }

        order_history = pd.DataFrame([], columns=columns)
        try:
            order_history = pd.DataFrame(self.client.get_order_book())
            if not order_history.empty:
                if "trgprc" in order_history.columns:
                    temp = order_history['trgprc']
                    temp = temp.where(pd.notnull(temp), None)
                    order_history = order_history[df_columns]
                    order_history['trgprc'] = temp
                else:
                    order_history = order_history[df_columns]
                    order_history['trgprc'] = None
                order_history.rename(columns={
                    'exch': 'exchange',
                    'tsym': 'tradingsymbol',
                    'qty': "quantity",
                    "trantype": "transaction_type",
                    "prctyp": "order_type",
                    "prc": "price",
                    "ret": "validity",
                    "prd": "product",
                    "trgprc": "stoploss",
                    "status": "orderstatus"
                }, inplace=True)
            else:
                order_history = pd.DataFrame([], columns=columns)
        except:
            message = str(sys.exc_info())
            self.log_this(message, 'error')

        order_history = order_history.astype(convert_dict)
        return order_history

    def get_positions(self):
        """Returns active positions of the user
        
        Returns:
            pd.DataFrame: {
                Exch: [BCD, CDS, BSE, MCX, NFO, NSE] - <object>
                ExchType: ["EQ", "CE", "PE" , "FUT", "MCX"] - <object>
                SymbolName: <object> 
                BuyQty: <np.int64> 
                BuyAvg: <np.float64>
                BuyValue: <np.float64>
                SellQty: <np.int64>
                SellAvg: <np.float64>
                SellValue: <np.float64>
                BookedProfitLoss: <np.float64>
                LTP: <np.float64>
                ProductType: [INTRADAY, DELIVERY] - <object> 
                MTOM: <np.float64>
            }
        """
        self.client.get_positions()

    def get_holdings(self):
        """Returns a list of all the holdings of the user
        
        Returns:
            pd.DataFrame: {
                Exch: [BCD, CDS, BSE, MCX, NFO, NSE] - <object>
                ExchType: ["EQ", "CE", "PE" , "FUT", "MCX"] - <object>
                SymbolName: <object>
                Qty: <np.int64>
                BuyPrice: <np.float64>
                CurrentPrice: <np.float64>
                ProfitAndLoss: <np.float64>
                DpQty: <np.int64>
            }
        """
        self.client.get_holdings()

    def get_margin(self):
        """Returns user margin at the instant
        
        Returns:
            available_margin <float>: available margin for trade
            used_margin <float>: Used margin
        """
        available_margin = 0.0
        used_margin = 0.0
        try:
            margin = self.client.get_limits()
            available_margin = margin['cash']
            if 'marginused' in margin.keys():
                used_margin = margin['marginused']
            else:
                margin_used = 0.0
        except Exception as e:
            self.log_this(e, 'error')

        return float(available_margin), float(used_margin)
