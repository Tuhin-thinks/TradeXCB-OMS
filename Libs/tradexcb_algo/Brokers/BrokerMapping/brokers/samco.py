import importlib
import sys
import numpy as np
import pandas as pd
import json
from importlib import import_module
from main_broker import Broker
from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge
# import_module('StocknoteAPIPythonBridge', 'snapi_py_client.snapi_bridge')
class Samco(Broker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_login()

    def do_login(self):
        """Logins with the broker and returns broker instance
        """

        try:
            userId = self.credentials['USER_ID']
            password = self.credentials['PASSWORD']
            yob = self.credentials['YOB']
            self.client = StocknoteAPIPythonBridge()
            login = self.client.login(body={
                "userId": userId,
                "password": password,
                "yob": yob
            })
            login_res = json.loads(login)
            if login_res['status'] == "Success":
                self.client.set_session_token(login_res['sessionToken'])
            else:
                self.log_this(f"Error in logging in for {userId} Broker {self.broker_name} " f" Error : {sys.exc_info()}")

        except Exception as e:
            self.log_this(f"Error in logging in for {userId} Broker {self.broker_name} ", log_level='error')

    def check_login(self):
        """Check if login was successful or not
        
        Returns:
            Boolean: 1 for success, 0 for failure
        """
        try:
            if self.client is not None:
                return 1
            else:
                return 0
        except Exception as e:
            self.log_this(f"Error in checking login for {self.broker_name} ", log_level='error')
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
        order_type_mapping = {'MARKET': 'MKT', 'LIMIT': 'L'}
        order_validity_mapping = {'DAY': 'DAY', 'IOC': 'IOC', 'TTL': ''}

        try:
            response = self.client.place_order(body={
                "symbolName": kwargs['tradingsymbol'],
                "exchange": kwargs['exchange'],
                "transactionType": kwargs['transaction_type'],
                "orderType": order_type_mapping[kwargs['order_type']],
                "price": '0' if 'price' not in kwargs else kwargs['price'],
                "quantity": kwargs['quantity'],
                "disclosedQuantity": None if 'disclosed_quantity' not in kwargs else kwargs['disclosed_quantity'],
                "orderValidity": order_validity_mapping[kwargs['validity']],
                "productType": kwargs['product'],
                "afterMarketOrderFlag":"NO"
            })
            response = json.loads(response)

            order_id, message = response['orderNumber'], response['statusMessage']
        except:
            order_id = None
            message = str(sys.exc_info())
            self.log_this(f"Error in Order Placement ")
            self.log_this(f"{str(sys.exc_info())}")
        
        return order_id, message

    def cancel_order(self, order_id):
        """Cancels order with the given id
        Args:
            order_id (str): Unique order id
        
        Returns:
            status_code <int>: -1 for failure, 1 for success
            message <str>: Message from the broker
        """
        message = None
        order_id = order_id
        try:
            cancel_order = self.client.cancel_order(order_number=order_id)
            cancel_order = json.loads(cancel_order)
            return 1, cancel_order['statusMessage']
        except:
            message = str(sys.exc_info())
            return -1, message

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
        order_history = pd.DataFrame()
        error_message = 'Error in Getting Order Book'

        columns = ['exchange','tradingsymbol','quantity','product','transaction_type','order_type','price','validity','stoploss','orderstatus']

        df_columns = ['exchange','tradingSymbol','totalQuanity','productCode','transactionType','orderType','orderPrice','orderValidity','triggerPrice','orderStatus']

        convert_dict = {
            "exchange": object, 
            "tradingsymbol": object, 
            "quantity": np.int64, 
            "product": object, 
            "transaction_type": object,
            "order_type": object,
            "price": np.float64,
            "validity": object,
            "stoploss": np.float64,
            "orderstatus": object
        }

        try:
            order_history = self.client.get_order_book()
            order_history = json.loads(order_history)
            order_history = pd.DataFrame(order_history['orderBookDetails'])
            if order_history.empty:
                error_message = 'No Orders Found'
                self.log_this(f"{error_message}", log_level='error')
                order_history = pd.DataFrame(columns=columns)
            else:
                order_history = order_history[df_columns]
                order_history.rename(columns={
                   'exchange':'exchange',
                   'tradingSymbol':'tradingsymbol',
                   'totalQuanity':'quantity',
                   'productCode':'product',
                   'transactionType':'transaction_type',
                   'orderType':'order_type',
                   'orderPrice':'price',
                   'orderValidity':'validity',
                   'triggerPrice':'stoploss',
                   'orderStatus':'orderstatus'
                }, inplace=True)
            
        except:
            message = str(sys.exc_info())
            self.log_this(message, 'error')
            order_history = pd.DataFrame(columns=columns)

        order_history.astype(convert_dict)
        return order_history

    def get_order_status(self, order_id):
        """
        Retrun the status of the order 
        Args:
            order_id: Unique order id of an order
        Return:
            str: Order status ['REJECTED', 'CANCELLED', 'PENDING', 'EXECUTED', 'ERROR']
        """
        order_status = ''
        error_message = 'Error in getting Order Status'

        try:
            order_status = self.client.get_order_status(order_number=order_id)
            order_status = json.loads(order_status)
            order_status = order_status['orderStatus']
        except Exception as e:
            self.log_this(f'{e}' + error_message, 'error')

        return order_status
    #Error in this function 
    
    def streaming_data(self, symbol_list:list):
        try:
            req_list = list()
            for symbol in symbol_list:
                exchange_token = self.instrument_df[self.instrument_df['tradingsymbol'] == symbol].iloc[-1]['exchange_token']
                exchange = self.instrument_df[self.instrument_df['tradingsymbol'] == symbol].iloc[-1]['exchange']

                req_list.append({
                    "symbol":f'{exchange_token}_{exchange}',
                })
            list1 = [{"symbol":"241002_MCX"}]
            self.client.set_streaming_data(list1)
            self.client.start_streaming()
        except Exception as e:
            self.log_this(f"Error in Streaming Data for {self.broker_name} ", log_level='error')
            self.log_this(e, log_level='error')
    #Incomplete function
    def get_ltp(self, tradingsymbol:list):
        """Returns the last traded price of the instrument
        
        Args:
            trading_symbols: List of unique trading symbols
        
        Returns:
            pd.DataFrame: 
                symbolName: Unique symbol
                price: Current price of the symbol
        """
        pass

    def get_exch_type(self, sym_exch):
        exchType = ''
        exchange = sym_exch[0]
        tradingsymbol = sym_exch[1]
        tradingsymbol = tradingsymbol.split('-')[0]
        try:
            exchType = self.instrument_df[(self.instrument_df['exchange'] == exchange) & (self.instrument_df['tradingsymbol'] == tradingsymbol)].iloc[0]['instrument_type']
        except Exception as e:
            self.log_this(f"Error in Getting Exchange Type for {self.broker_name} " + e, log_level='error')
            exchType = ''

        return exchType

    def get_product_type(self, productType):
        product_type = ''
        try:
            if productType == 'DAY':
                product_type = "INTRADAY"
            else:
                product_type = "DELIVERY"
        except Exception as e:
            self.log_this(f"Error in Getting Product Type for {self.broker_name} " + e, log_level='error')
            product_type = 'DAY'
        return product_type

    def get_values(self, df):
        one = np.float64(df[0])
        two = np.float64(df[1])
        if two == 0.0:
            return one
        else:
            return one/two

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
        columns = ['Exch', 'ExchType', 'SymbolName', 'BuyQty', 'BuyAvg', 'BuyValue',
                   'SellQty', 'SellAvg', 'SellValue', 'BookedProfitLoss', 'LTP',
                   'ProductType', 'MTOM']
        df_columns = ['exchange', 'tradingSymbol', 'buyQuantity', 'averageBuyPrice','boughtPrice','averageSellPrice', 'soldValue', 'realizedGainAndLoss', 'lastTradedPrice','markToMarketPrice']
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
            positions = json.loads(self.client.get_positions_data(position_type="DAY"))
            if positions['status'] == "Success":
                positions = pd.DataFrame(positions['positionDetails'])
                productType = positions['positionType']
                sellqty = positions[['soldValue','averageSellPrice']]
                exchtype = positions[['exchange','tradingSymbol']]
                positions = positions[df_columns]
                positions['SellQty'] = sellqty.apply(self.get_values, axis=1) 
                positions['ExchType'] = exchtype.apply(self.get_exch_type, axis=1)
                positions['ProductType'] = productType.apply(self.get_product_type)
                positions.rename(columns={
                    "exchange": "Exch",
                    "ExchType": "ExchType",
                    "tradingSymbol": "SymbolName", 
                    "buyQuantity": "BuyQty", 
                    "averageBuyPrice": "BuyAvg", 
                    "boughtPrice": "BuyValue",
                    "SellQty": "SellQty", 
                    "averageSellPrice": "SellAvg", 
                    "soldValue": "SellValue", 
                    "realizedGainAndLoss": "BookedProfitLoss",
                    "lastTradedPrice": "LTP",
                    "ProductType": "ProductType", 
                    "markToMarketPrice": "MTOM"
                }, inplace=True)

                positions = positions.reindex(columns=columns)
            else:
               positions = pd.DataFrame([], columns=columns) 
        except:
            message = str(sys.exc_info())
            self.log_this(f"Error in Getting Positions for {self.broker_name} " + message, log_level='error')
            positions = pd.DataFrame([], columns=columns)
        
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
        df_columns = ['exchange', 'tradingSymbol', 'holdingsQuantity', 'averagePrice', 'lastTradedPrice',
                      'totalGainAndLoss', 'sellableQuantity']
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
            holdings = json.loads(self.client.get_holding())
            if holdings['status'] == "Success":
                holdings = pd.DataFrame(holdings['holdingDetails'])
                holdings = holdings[df_columns]
                holdings['ExchType'] = holdings[['exchange','tradingsymbol']].apply(self.get_exch_type, axis=1)
                holdings.rename(columns={
                    "exchange": "Exch",
                    "ExchType": "ExchType",
                    "tradingSymbol": "SymbolName", 
                    "holdingsQuantity": "Qty", 
                    "averagePrice": "BuyPrice", 
                    "lastTradedPrice": "CurrentPrice",
                    "totalGainAndLoss": "ProfitAndLoss",
                    "sellableQuantity": "DpQty"
                }, inplace=True)

                holdings = holdings.reindex(columns=columns)
            else:
                holdings = pd.DataFrame([], columns=columns)
        except:
            message = str(sys.exc_info())
            self.log_this(f"Error in Getting Holdings for {self.broker_name} " + message, log_level='error')
            holdings = pd.DataFrame([], columns=columns)
            
        holdings = holdings.astype(convert_dict)
        return holdings

    def get_margin(self):
        """Returns user margin at the instant
        
        Returns:
            available_margin <float>: available margin for trade
            used_margin <float>: Used margin
        """
        margins = json.loads(self.client.get_limits())
        return float(margins['equityLimit']['netAvailableMargin']) , float(margins['equityLimit']['marginUsed'])