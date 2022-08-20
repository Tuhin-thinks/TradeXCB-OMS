import pandas as pd
import numpy as np
import sys
from importlib import import_module
from BrokerMapping.main_broker import Broker
from BrokerMapping.dependencies.MOFSLOPENAPI import MOFSLOPENAPI
class MotilalOswal(Broker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # globals()['dependencies.MOFSLOPENAPI'] = import_module("MOFSLOPENAPI")
        self.live_ltp_data = dict() # symbolName -> price
        self.streaming_flag = 0
        self.do_login()

    def do_login(self):
        """Logins with the broker and returns broker instance
        """
        try:
            username = self.credentials['USERNAME']
            password = self.credentials['PASSWORD']
            apikey = self.credentials['API_KEY']
            security_pin = self.credentials['SECURITYPIN']  # for mofsl, security pin is Two-fa
            host = self.credentials['HOST']

            self.log_this(f"Logging in the API for {username} Broker {self.broker_name}", log_level="info")

            endpoint = "https://uatopenapi.motilaloswal.com"
            if host == "LIVE":
                endpoint = "https://openapi.motilaloswal.com"
            self.broker = MOFSLOPENAPI(apikey, endpoint)
            response = self.broker.login(username, password, security_pin, username)
            print("SDK login response:", response)
        except:
            self.log_this(f"Error in logging in the API for {username} Broker {self.broker_name}", log_level="error")
            self.broker = None

    def check_login(self):
        """Check if login was successful or not
        
        Returns:
            Boolean: 1 for success, 0 for failure
        """
        try:
            if self.broker['status'] == 'Success':
                return 1
            else:
                return 0
        except Exception as e:
            self.log_this(f"Error in checking login [MOFSL - API], {e}", log_level="error")
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
        message = None
        tradingsymbol = kwargs['tradingsymbol']

        instrument_row = self.instrument_df[(self.instrument_df['tradingsymbol'] == kwargs['tradingsymbol']) & (
                self.instrument_df['exchange'] == kwargs['exchange'])]

        producttype_mapping = {
            "MIS": "NORMAL",
            "NRML": "NORMAL"

        }

        exchange = kwargs['exchange']  # for now hardcoded, todo: find a way to get this from the instrument row
        symbtoken = int(instrument_row.iloc[-1]['exchange_token'])
        buyorsell = kwargs["transaction_type"]
        ordertype = kwargs["order_type"]
        producttype = producttype_mapping[kwargs["product"]]
        orderduration = kwargs["validity"]
        price = float(kwargs['price'])
        triggerprice = float(kwargs['stoploss'])
        quantityinlot = int(kwargs["quantity"])  # todo: need use quantity in

        # # ----- optional params -----
        # disclosedquantity = kwargs.get("disclosed_quantity", 0)
        # amoorder = kwargs.get("amo_order", 0)
        # goodtilldate = kwargs.get("good_till_date", "")
        # algoid = kwargs.get("algoid", "")
        # tag = " "  # max 10 characters

        order_request = {
            "clientcode": self.credentials['USERNAME'],
            "exchange": exchange,
            "symboltoken": symbtoken,
            "buyorsell": buyorsell,
            "ordertype": ordertype,
            "producttype": producttype,
            "orderduration": orderduration,
            "price": price,
            "triggerprice":triggerprice,
            "quantityinlot": quantityinlot,
            "amoorder": "N"
        }
        try:
            # print(order_request)
            self.log_this(f"MOSL Order Request: {order_request}", log_level="info")
            response = self.broker.PlaceOrder(order_request)
            order_id = response['uniqueorderid']
            message = 'Success'
        except Exception as e:
            self.log_this(f"Error in placing order [MOFSL - API], {e.__str__()}", log_level="error")
            
        return order_id, message

    def cancel_order(self, order_id):
        """Cancels order with the given id
        Args:
            order_id (str): Unique order id
        
        Returns:
            status_code <int>: -1 for failure, 1 for success
            message <str>: Message from the broker
        """
        order_id = order_id
        error_message = f"Error in Cancelling Order {order_id}"

        try:
            response = self.broker.CancelOrder(order_id, self.credentials['USERNAME'])

            error_message = "Invalid Order Id Input Parameter"
            if response['message'] == error_message:
                self.log_this(response['message'], log_level='error')
        except Exception as e:
            self.log_this("Error in cancelling order [MOFSL]" + e.__str__(), log_level="error")

        if response['status'] != 'SUCCESS' :
            value = 0
            message = 'Order cancel failed'
        elif response['status'] != 'Success' and response['message'] == 'Order Is Already Rejected':
            value = 1
            message = 'Order Is Already Rejected'
        else : 
            value = 1
            message = 'Successfully cancel order'
        
        return int(value), message
        

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
        df_columns = ['exchange', 'symbol', 'orderqty', 'producttype', 'buyorsell',
                      'ordertype', 'price', 'orderduration', 'triggerprice']

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
        order_history = pd.DataFrame([], columns=columns)
        try:
            order_history = pd.DataFrame(self.broker.GetOrderBook(self.credentials['USERNAME'])['data'])
            if not order_history.empty:
                ForOrderStatus = order_history['uniqueorderid']
                order_history = order_history[df_columns]
                order_history.rename(columns = {
                    'triggerprice': 'stoploss',
                    'symbol':'tradingsymbol',
                    'orderqty':'quantity',
                    'producttype':'product',
                    'buyorsell':'transaction_type',
                    'ordertype':'order_type',
                    'orderduration':'validity',
                }, inplace=True)
                order_history['orderstatus'] = ForOrderStatus.apply(self.get_order_status)
            else:
                order_history = pd.DataFrame([], columns=columns)
        except:
            message = str(sys.exc_info())

        order_history = order_history.astype(convert_dict)
        return order_history

    #checking tomorrow's after market opne
    def get_ltp(self, tradingsymbols:list):
        """Returns the last traded price of the instrument
        
        Args:
            trading_symbols: List of unique trading symbols
        
        Returns:
            pd.DataFrame: 
                symbolName: Unique symbol
                price: Current price of the symbol
        """
        ltp = []
        symbol = []
        ltp_dataframe = pd.DataFrame([], columns=['symbolName', 'price'])
        convert_dict = {
            "symbolName": object,
            "price": np.float64
        }
        try:
            for tradingsymbol in tradingsymbols:
                df_line = self.instrument_df[self.instrument_df['tradingsymbol'] == tradingsymbol]
                exchange = df_line.iloc[-1]['exchange']
                dict_req = {
                    "clientcode": self.credentials['USERNAME'],
                    "exchange": 'NSE',
                    "symbol": 'CYIENT'
                }
                ltp_val = self.broker.GetLtp(dict_req)['data'][0]['ltp']
                ltp.append(ltp_val)
                symbol.append(tradingsymbol)
            
            ltp_dataframe = pd.DataFrame(data=list(zip(symbol, ltp)), columns=['symbolName', 'price'])

        except Exception as e:
            self.log_this(f"Error in getting LTP [MOFSL] ({exchange}, {tradingsymbols})" + e.__str__(), log_level="error")
        ltp_dataframe = ltp_dataframe.astype(convert_dict)
        return ltp_dataframe
    
    def get_streaming_data(self, symbol_list:list):

        # Mofsl.Register("BSE", "CASH", 532540)
        sd = self.broker.Register("NSE", "CASH", 3045)
        print(sd)

    def get_order_status(self, order_id: str) -> str:
        """
        Retrun the status of the order 
        Args:
            order_id: Unique order id of an order
        Return:
            str: Order status ['REJECTED', 'CANCELLED', 'PENDING', 'EXECUTED', 'ERROR']
        """
        try:
            order_status_data = self.broker.GetOrderBook(self.credentials['USERNAME'])['data']
            if order_status_data == "":
                msg = 'Currently no orders are placed'
                self.log_this(msg, log_level='info')
                order_status = 'ERROR'
            else:
                order_status_df = pd.DataFrame(order_status_data)
                order_status_df = order_status_df[(order_status_df['uniqueorderid'] == order_id)]
                order_status = order_status_df.iloc[0]['orderstatus']

        except:
            message = str(sys.exc_info())
            self.log_this(message, log_level='error')

        return str(order_status)

    #checking tomorrow's after market opne
    def get_exch(self,tradingsymbol:str):
        exchange = None
        try:
            tradingsymbol = tradingsymbol.split(' ')[0]
            instrument_row = self.instrument_df[(self.instrument_df['tradingsymbol'] == tradingsymbol)]
            exchange = instrument_row.iloc[0]['exchange']
        except Exception as e:
            self.log_this(f"Error in getting exchange [MOFSL] ({tradingsymbol})" + e.__str__(), log_level="error")
            exchange = ''

        return exchange
    #Incomplete function 
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
        columns = ['Exch', 'ExchType', 'SymbolName', 'Qty', 'BuyPrice', 'CurrentPrice','ProfitAndLoss', 'DpQty']
        df_columns = ['scripname','dpquantity','buyavgprice']
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
            holdings = pd.DataFrame(self.broker.GetDPHolding(self.credentials['USERNAME'])['data'])
            if not holdings.empty:
                holdings = holdings[df_columns]
                holdings['Exch'] = ''
                holdings['ExchType'] = ''
                holdings['Qty'] = ''
                holdings['CurrentPrice'] = ''
                holdings['ProfitAndLoss'] = ''
                holdings.rename(columns={
                    "scripname": "SymbolName", 
                    "dpquantity": "DpQty",
                    "buyavgprice": "BuyPrice"
                }, inplace=True)
                holdings = holdings.reindex(columns=columns)
            else:
                holdings = pd.DataFrame([], columns=columns)
        except:
            message = str(sys.exc_info())
            self.log_this(message, 'error')
            
        holdings = holdings.astype(convert_dict)
        return holdings
    
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

        #There is some confusion in the buyAvg and Buyvalue we get buyamount only for now is choosen buyAvg = buyamount

        df_columns = ['exchange','series','symbol', 'buyquantity', 'buyamount','sellquantity', 'sellamount', 'bookedprofitloss', 'LTP','marktomarket']
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
        
        # positions = pd.DataFrame([], columns=columns)
        try:
            positions = pd.DataFrame(self.broker.GetPosition(self.credentials['USERNAME'])['data'])
            if not positions.empty:
                buyval = positions[["buyquantity","buyamount"]]
                sellval = positions[["sellquantity","sellamount"]]
                positions = positions[df_columns]
                positions['ProductType'] = ''
                positions['BuyValue'] = buyval.apply(lambda x: x[0]*x[1])
                positions['SellValue'] = sellval.apply(lambda x: x[0]*x[1])
                positions.rename(columns={
                    "exchange": "Exch",
                    "series": "ExchType",
                    "symbol": "SymbolName", 
                    "buyquantity": "BuyQty", 
                    "buyamount": "BuyAvg", 
                    "sellquantity": "SellQty", 
                    "sellamount": "SellAvg", 
                    "bookedprofitloss": "BookedProfitLoss",
                    "marktomarket": "MTOM"
                }, inplace=True)
                positions = positions.reindex(columns=columns)
            else:
               positions = pd.DataFrame([], columns=columns) 
        except:
            message = str(sys.exc_info())
            self.log_this(message, 'error')
        
        positions = positions.astype(convert_dict)
        return positions

    def get_margin(self):
        """Returns user margin at the instant
        
        Returns:
            available_margin <float>: available margin for trade
            used_margin <float>: Used margin
        """
        try:
            marg = self.broker.GetReportMargin(self.credentials['USERNAME'])['data']

            avaliable_margin = marg[0]['equitycashmargin']
            used_margin = marg[0]['marginutilized']
        except Exception as e:
            self.log_this(e, 'error')
            avaliable_margin = 0.0
            used_margin = 0.0

        return float(avaliable_margin), float(used_margin)
