import json
import re
import sys
import urllib.parse as urlparse
from importlib import import_module

import numpy as np
import pandas as pd
import pyotp
import requests

from BrokerMapping.main_broker import Broker


class Zerodha(Broker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        globals()['kiteconnect'] = import_module("kiteconnect")
        self.do_login()

    def do_login(self):
        """Logins with the broker and returns broker instance
        """
        try:
            username = self.credentials['USERNAME']
            password = self.credentials['PASSWORD']
            apikey = self.credentials['API_KEY']
            secretkey = self.credentials['SECRET_KEY']
            totp_code = self.credentials['TOTP_CODE']

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
                header_string = res2.headers['Set-Cookie']
                pattern = r"enctoken=(?P<token>.+?)\;"
                self.enctoken = re.search(pattern, header_string).groupdict()['token']
            except Exception as e:
                self.log_this(f"Error in getting request-token/enc-token for {username} Broker {self.broker_name}",
                              log_level="error")

            session.close()
            kite = kiteconnect.KiteConnect(api_key=apikey)
            print("request token:", request_token)
            data = kite.generate_session(request_token, api_secret=secretkey)
            self.data = data
            app = kiteconnect.KiteConnect(apikey)
            app.set_access_token(data['access_token'])
            self.client = app

        except:
            self.client = None
            self.log_this(f"Error in logging in for {username} Broker : {self.broker_name}"
                          f" Error : {sys.exc_info()}")

    def check_login(self):
        """Check if login was successful or not
        
        Returns:
            Boolean: 1 for success, 0 for failure
        """
        try:
            if self.data['access_token'] != None:
                return 1
            else:
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
        order_id = None
        message = 'success'

        try:
            order_id = self.client.place_order(
                variety = 'regular',
                exchange = kwargs['exchange'],
                tradingsymbol = kwargs['tradingsymbol'],
                quantity = kwargs['quantity'],
                product = kwargs['product'],
                transaction_type = kwargs['transaction_type'],
                order_type = kwargs['order_type'],
                price = kwargs['price'],
                validity=kwargs['validity'],
                stoploss=kwargs['stoploss']
            )
        except:
            order_id = -1
            message = str(sys.exc_info())
            self.log_this(f"Error in placing order for {kwargs['tradingsymbol']} Broker {self.broker_name}" + message,'error')
            
        return int(order_id), str(message)
    
    def cancel_order(self, order_id: str):
        """Cancels order with the given id

        Args:
            order_id (str): Unique order id
        
        Returns:
            status_code <int>: -1 for failure, 1 for success
            message <str>: Message from the broker
        """
        message = 'success'
        order_id = order_id

        try:
            orders_history = self.get_order_book()
            order_row = orders_history[orders_history['order_id'].astype(str) == str(order_id)]
            order_id = self.client.cancel_order(variety=order_row.iloc[-1]['variety'], order_id=order_id)
            return 1, message
        except:
            order_id = None
            message = str(sys.exc_info())
            return -1, message    
    
    def get_exchange(self, tradingsymbol):
        """Returns exchange for the given trading symbol

        Args:
            tradingsymbol (str): unique trading symbol

        Returns:
            str: exchange
        """
        try:
            exchange = str(
                self.instrument_df[self.instrument_df['tradingsymbol'] == tradingsymbol].iloc[0]['exchange'])
            return exchange
        except IndexError:
            self.log_this("Instrument not found", 'error')
            return None, "Instrument not found"
        except Exception as e:
            self.log_this(e, 'error')
            return None, "Error raised"

    def get_order_status(self, order_id: str):
        """
        Retrun the status of the order 
        Args:
            order_id: Unique order id of an order
        Return:
            str: Order status ['REJECTED', 'CANCELLED', 'PENDING', 'EXECUTED', 'ERROR']
        """
        return self._format_response(self._get("order.info", url_args={"order_id": order_id}))

    def get_ltp(self, trading_symbols: list):
        """Returns the last traded price of the instrument
        
        Args:
            trading_symbols: List of unique trading symbols
        
        Returns:
            pd.DataFrame: 
                symbolName: Unique symbol
                price: Current price of the symbol
        """
        new_list = []
        try:
            for symbol in trading_symbols:
                new_list.append(f"{self.get_exchange(symbol)}:{symbol}")
            
            data = self.client.ltp(new_list)
            ltp_data = dict()
            for symbol in data.keys():
                tradingsymbol = symbol.split(":")[1]
                price = data[symbol]['last_price']
                ltp_data[tradingsymbol] = price
        except Exception as e:
            self.log_this(e, 'error')
            ltp_data = {}
            for symbol in trading_symbols:
                ltp_data[symbol] = 0

        return pd.DataFrame(ltp_data.items(), columns=['symbolName', 'price'])

    def get_order_book(self):
        """Returns all the orders that have been placed today
        
        Returns:
            pd.DataFrame: {
                'exchange' : [BCD, CDS, BSE, MCX, NFO, NSE], - <object>
                'tradingsymbol' : '',  <str>
                'quantity': int, <int> 
                'product' : [MIS, CNC, NRML], <object> 
                'transaction_type' : [BUY, SELL], - <object>
                'order_type' : [MARKET, LIMIT], - <object> 
                'price': [int, None], - <int> 
                'validity': [DAY, IOC, TTL], <object> 
                'stoploss' : [float, None], - <float> 
                'orderstatus': <str>
            }
        """
        columns = ['exchange', 'tradingsymbol', 'quantity', 'product', 'transaction_type',
                   'order_type', 'price', 'validity', 'stoploss', 'orderstatus']
        df_columns = ['exchange', 'tradingsymbol', 'quantity', 'product', 'transaction_type',
                      'order_type', 'price', 'validity', 'trigger_price', 'status']
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
            order_history = pd.DataFrame(self.client.orders())
            if not order_history.empty:
                order_history = order_history[df_columns]
                order_history.rename(columns = {'trigger_price': 'stoploss', 'status': 'orderstatus'}, inplace=True)
            else:
                order_history = pd.DataFrame([], columns=columns)
        except:
            message = str(sys.exc_info())

        order_history = order_history.astype(convert_dict)
        return order_history
    
    def get_exchange_type(self, tradingsymbol):
        """Returns exchange type for the given trading symbol

        Args:
            tradingsymbol (str): unique trading symbol

        Returns:
            str: exchange type, None
        """
        try:
            exch_type = self.instrument_df[self.instrument_df['tradingsymbol'] == tradingsymbol].iloc[0]['instrument_type']
            return exch_type
        except IndexError:
            self.log_this("Instrument not found", 'error')
            return None, "Instrument not found"
        except Exception as e:
            self.log_this(e, 'error')
            return None, "Error raised"
    
    def get_positions(self):
        """Returns active positions of the user
        
        Returns:
            pd.DataFrame: {
                Exch: [BCD, CDS, BSE, MCX, NFO, NSE] - object
                ExchType: ["EQ", "CE", "PE" , "FUT", "MCX"] - object
                SymbolName: str 
                BuyQty: int 
                BuyAvg: float
                BuyValue: float
                SellQty: int
                SellAvg: float
                SellValue: float
                BookedProfitLoss: float
                LTP: float
                ProductType: [INTRADAY, DELIVERY] - object 
                MTOM: float
            }
        """
        columns = ['Exch', 'ExchType', 'SymbolName', 'BuyQty', 'BuyAvg', 'BuyValue',
                   'SellQty', 'SellAvg', 'SellValue', 'BookedProfitLoss', 'LTP',
                   'ProductType', 'MTOM']
        df_columns = ['exchange', 'tradingsymbol', 'buy_quantity', 'buy_price', 'buy_value',
                      'sell_quantity', 'sell_price', 'sell_value', 'pnl', 'last_price',
                      'product', 'm2m']
        convert_dict = {
            "Exch": object,
            "ExchType": object,
            "SymbolName": object,
            "BuyQty": np.int64,
            "BuyAvg": np.float64,
            "BuyValue": np.float64,
            "SellQty": np.int64,
            "SellAvg": np.float64,
            "SellValue": np.float64,
            "BookedProfitLoss": np.float64,
            "LTP": np.float64,
            "ProductType": object,
            "MTOM": np.float64
        }
        
        positions = pd.DataFrame([], columns=columns)
        try:
            positions = pd.DataFrame(self.client.positions()['net'])
            if not positions.empty:
                positions = positions[df_columns]
                positions['ExchType'] = positions['tradingsymbol'].apply(lambda x: self.get_exchange_type(x))
                positions.rename(columns={
                    "exchange": "Exch",
                    "ExchType": "ExchType",
                    "tradingsymbol": "SymbolName", 
                    "buy_quantity": "BuyQty", 
                    "buy_price": "BuyAvg", 
                    "buy_value": "BuyValue",
                    "sell_quantity": "SellQty", 
                    "sell_price": "SellAvg", 
                    "sell_value": "SellValue", 
                    "pnl": "BookedProfitLoss",
                    "last_price": "LTP",
                    "product": "ProductType", 
                    "m2m": "MTOM"
                }, inplace=True)
            else:
               positions = pd.DataFrame([], columns=columns) 
        except:
            message = str(sys.exc_info())
        
        positions = positions.astype(convert_dict)
        return positions
    
    def get_holdings(self):
        """Returns a list of all the holdings of the user
        
        Returns:
            pd.DataFrame: {
                Exch: [BCD, CDS, BSE, MCX, NFO, NSE] - <object>
                ExchType: ["EQ", "CE", "PE" , "FUT", "MCX"] - <object>
                SymbolName: str
                Qty: int
                BuyPrice: float
                CurrentPrice: float
                ProfitAndLoss: float
                DpQty: int
            }
        """
        columns = ['Exch', 'ExchType', 'SymbolName', 'Qty', 'BuyPrice', 'CurrentPrice',
                   'ProfitAndLoss', 'DpQty']
        df_columns = ['exchange', 'tradingsymbol', 't1_quantity', 'average_price', 'last_value',
                      'pnl', 'quantity']
        convert_dict = {
            "Exch": object,
            "ExchType": object,
            "SymbolName": object,
            "Qty": np.int64,
            "BuyPrice": np.float64,
            "CurrentPrice": np.float64,
            "ProfitAndLoss": np.float64,
            "DpQty": np.int64,
        }
        holdings = pd.DataFrame([], columns=columns)
        try:
            holdings = pd.DataFrame(self.client.holdings())
            if not holdings.empty:
                holdings = holdings[df_columns]
                holdings['ExchType'] = holdings['tradingsymbol'].apply(lambda x: self.get_exchange_type(x))
                holdings.rename(columns={
                    "exchange": "Exch",
                    "ExchType": "ExchType",
                    "tradingsymbol": "SymbolName", 
                    "t1_quantity": "Qty", 
                    "average_price": "BuyPrice", 
                    "last_value": "CurrentPrice",
                    "pnl": "ProfitAndLoss",
                    "quantity": "DpQty"
                }, inplace=True)
            else:
                holdings = pd.DataFrame([], columns=columns)
        except:
            message = str(sys.exc_info())
            self.log_this(message, 'error')
            
        holdings = holdings.astype(convert_dict)
        return holdings
    
    def get_margin(self):
        """Returns user margin at the instant
        
        Returns:
            available_margin <float>: available margin for trade
            used_margin <float>: Used margin
        """
        margins = self.client.margins()['equity']
        return float(margins['available']['live_balance']), float(margins['utilised']['debits'])
