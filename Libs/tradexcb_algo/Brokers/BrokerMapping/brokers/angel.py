import sys
from importlib import import_module

import numpy as np
import pandas as pd

from BrokerMapping.main_broker import Broker


class Angel(Broker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        globals()["smartapi"] = import_module("smartapi")
        self.do_login()

    # Done
    def do_login(self):
        """Logins with the broker and returns broker instance
        """
        try:
            USERNAME = self.credentials['USERNAME']
            PASSWORD = self.credentials['PASSWORD']
            API_KEY = self.credentials['API_KEY']
            client = smartapi.SmartConnect(api_key=API_KEY)
            self.data = client.generateSession(USERNAME, PASSWORD)
            self.refersh_token = self.data['data']['refreshToken']
            self.client = client
        except Exception as e:
            self.log_this(e, 'error')
            self.client = None

    # Done
    def check_login(self):
        """Check if login was successful or not
        
        Returns:
            Boolean: 1 for success, 0 for failure
        """
        try:
            check_login_status = self.client
            if check_login_status != None:
                return 1
            else:
                return 0
        except Exception as e:
            return 0

    # Trading symbol using the web request
    def get_trading_symbol(self, token, exchange):
        trading_symbols = ''
        try:
            import requests
            import time

            while True:
                try:
                    master_file = pd.read_json(requests.get(
                        'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json').text)
                    break
                except:
                    time.sleep(1)
                    continue

            row = master_file[(master_file['token'] == str(token)) & (master_file['exch_seg'] == str(exchange))]
            trading_symbols = row.iloc[-1]['symbol']
        except Exception as e:
            self.log_this(e, 'error')
            trading_symbols = None
        return trading_symbols

    # Trading symbol using the instrument file
    def get_trading_symbol_csv(self, token, exchange):
        try:
            df_line = self.angel_instrument_df[
                (self.angel_instrument_df['token'] == token) & (self.angel_instrument_df['exch_seg'] == str(exchange))]
            tradingsymbol = df_line.iloc[-1]['symbol']
        except Exception as e:
            self.log_this(e, 'error')
            tradingsymbol = ''
        return tradingsymbol

    # Done
    def place_order(self, **kwargs):
        """

        Args: 
            kwargs: {
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
            order_id: unique id
            message: message returned from the broker
        """
        try:
            df_line = self.instrument_df[(self.instrument_df['tradingsymbol'] == kwargs['tradingsymbol']) & (
                        self.instrument_df['exchange'] == kwargs['exchange'])]

            symbol_token = f"{str(df_line.iloc[-1]['exchange_token'])}"
            tradingsymbol = self.get_trading_symbol_csv(int(symbol_token), kwargs['exchange'])

            product_type = {
                "MIS": "INTRADAY",
                "CNC": "DELIVERY",
                "NRML": "CARRYFORWARD"
            }

            orderparams = {
                "variety": "NORMAL",
                "tradingsymbol": tradingsymbol,
                "symboltoken": str(symbol_token),
                "transactiontype": str(kwargs['transaction_type']),
                "exchange": str(kwargs['exchange']),
                "ordertype": str(kwargs['order_type']),
                "producttype": product_type[kwargs['product']],
                "duration": str(kwargs['validity']),
                "price": str(kwargs['price']),
                "squareoff": "0",
                "stoploss": "0" if kwargs['stoploss'] == None else kwargs['stoploss'],
                "quantity": str(kwargs['quantity'])
            }
            order = self.client.placeOrder(orderparams=orderparams)

            if order == "":
                message = "Error in placeOrder"
            else:
                message = "placeOrder Successfully!"
        except Exception as e:
            message = str(sys.exc_info())
            order = -1
            self.log_this(e, 'error')

        return int(order), str(message)

    # Done
    def cancel_order(self, order_id):
        """Cancels order with the given id
        Args:
            order_id (str): Unique order id
        
        Returns:
            status_code <int>: -1 for failure, 1 for success
            message <str>: Message from the broker
        """
        message = None
        value = 1
        try:
            cancel_order = self.client.cancelOrder(variety="NORMAL", order_id=order_id)
            message = cancel_order['message']
        except Exception as e:
            message = str(sys.exc_info())
            value = 0
            self.log_this(e, 'error')
        return int(value), str(message)

    def get_ltp_dataset(self, df):
        '''
            arg: 
                df = dataFrame
            Return: 
                ltp_val: float ltp value
        '''
        ltp_val = 0.0
        try:
            exchange = df['exchange']
            producttype = df['tradingsymbol']
            symboltoken = df['symboltoken']
            ltp = self.client.ltpData(exchange, producttype, symboltoken)
            ltp_val = ltp['data']['ltp']
        except Exception as e:
            self.log_this(e, 'error')
            ltp_val = 0.0

        return ltp_val

    # This ltp function is working but used the api not socket
    def get_ltp(self, tradingsymbols: list):
        """Returns the last traded price of the instrument
        
        Args:
            trading_symbols: List of unique trading symbols
        
        Returns:
            pd.DataFrame: 
                symbolName: Unique symbol
                price: Current price of the symbol
        """
        ltp_dict = dict()
        convert_dict = {
            'symbolName': object,
            'price': np.float64
        }
        ltp_dataframe = pd.DataFrame([], columns=['symbolName', 'price'])
        try:
            for tradingsymbol in tradingsymbols:
                df_line = self.instrument_df[(self.instrument_df['tradingsymbol'] == tradingsymbol)]
                exchange = df_line.iloc[-1]['exchange']
                symboltoken = df_line.iloc[-1]['exchange_token']
                trading_symbol = self.get_trading_symbol_csv(symboltoken, exchange)
                try:
                    ltp_data = self.client.ltpData(exchange=exchange, tradingsymbol=trading_symbol,
                                                   symboltoken=str(symboltoken))
                    ltp_data = ltp_data['data']['ltp']
                    ltp_dict[tradingsymbol] = str(ltp_data)

                except Exception as e:
                    self.log_this(e, 'error')
                    ltp_dict[tradingsymbol] = 0.0

            ltp_dataframe = pd.DataFrame(ltp_dict.items(), columns=['symbolName', 'price'])
        except Exception as e:
            self.log_this(e, 'error')

        ltp_dataframe = ltp_dataframe.astype(convert_dict)
        return ltp_dataframe

    # Checking Pending
    def streaming_data(self, symbol_list: list):
        from smartapi import SmartWebSocket
        # feed_token=092017047
        FEED_TOKEN = self.client.getfeedToken()
        CLIENT_CODE = self.credentials['USERNAME']
        # token="mcx_fo|224395"
        token = "EXCHANGE|TOKEN_SYMBOL"  # SAMPLE: nse_cm|2885&nse_cm|1594&nse_cm|11536&nse_cm|3045
        # token="mcx_fo|226745&mcx_fo|220822&mcx_fo|227182&mcx_fo|221599"
        task = "cn"  # mw|sfi|dp

        exchange_mapping = {
            "NSE": "nse_cm",
            "BSE": "bse_cm",
            "MCX": "mcx_fo",
            "NFO": "nfo_fo",
            "CDS": "cds_fo",
            "NCDEX": "ncx_fo"
        }
        token_string = ""
        for symbol in symbol_list:
            exchange_token = str(
                self.instrument_df[self.instrument_df['tradingsymbol'] == symbol].iloc[-1]['exchange_token'])
            exchange = exchange_mapping[
                self.instrument_df[self.instrument_df['tradingsymbol'] == symbol].iloc[-1]['exchange']]
            token_string += f"{exchange}|{exchange_token}&"

        token_string = token_string[:-1]
        print(token_string)
        ss = SmartWebSocket(FEED_TOKEN, CLIENT_CODE)

        def on_message(ws, message):
            print(message)
            print(ws)

        def on_open(ws):
            print("on open")
            # task = 'cn'
            # ss.subscribe(task,token_string)
            task = 'mw'
            ss.subscribe(task, token_string)

        def on_error(ws, error):
            print(error)

        def on_close(ws):
            print("Close")

        # Assign the callbacks.
        ss._on_open = on_open
        ss._on_message = on_message
        ss._on_error = on_error
        ss._on_close = on_close

        ss.connect()

        # Done

    def get_order_status(self, order_id: str):
        """
        Retrun the status of the order 
        Args:
            order_id: Unique order id of an order
        Return:
            str: Order status ['REJECTED', 'CANCELLED', 'PENDING', 'EXECUTED', 'ERROR']
        """
        try:
            order_status_data = self.client.orderBook()['data']
            if order_status_data == "":
                msg = 'Currently no orders are placed'
                self.log_this(msg, log_level='info')
                order_status = 'ERROR'
            else:
                order_status_df = pd.DataFrame(order_status_data)
                order_status_df = order_status_df[(order_status_df['orderid'] == order_id)]
                order_status = order_status_df.iloc[-1]['orderstatus']

        except:
            message = str(sys.exc_info())
            self.log_this(message, log_level='error')

        return str(order_status)

    # Done
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
        df_columns = ['exchange', 'tradingsymbol', 'quantity', 'producttype', 'transactiontype',
                      'ordertype', 'price', 'duration', 'stoploss', 'orderstatus']
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
            order_history = pd.DataFrame(self.client.orderBook()['data'])
            if not order_history.empty:
                order_history = order_history[df_columns]
                order_history.rename(
                    columns={'exchange': 'exchange', 'tradingsymbol': 'tradingsymbol', 'quantity': 'quantity',
                             'producttype': 'product', 'transactiontype': 'transaction_type', 'ordertype': 'order_type',
                             'price': 'price',
                             'duration': 'validity',
                             'stoploss': 'stoploss', 'orderstatus': 'orderstatus'}, inplace=True)
            else:
                order_history = pd.DataFrame([], columns=columns)
        except:
            message = str(sys.exc_info())
            self.log_this(message, log_level='error')

        order_history = order_history.astype(convert_dict)
        return order_history

    # Done
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
        try:
            position = self.client.position()
            if position['data'] != None:
                # Making the data Frame from the Response of the self.client.position
                position_dataFrame = pd.DataFrame(position['data'])
                # Making two different for the ltp and position
                ForLtp = position_dataFrame[['exchange', 'tradingsymbol', 'symboltoken']]
                position_dataFrame = position_dataFrame[
                    ['exchange', 'symbolgroup', 'symbolname', 'buyqty', 'buyavgprice', 'buyamount', 'sellqty',
                     'sellavgprice', 'sellamount', 'producttype']]

                position_dataFrame.rename(
                    columns={'exchange': 'Exch', 'symbolgroup': 'ExchType', 'symbolname': 'SymbolName',
                             'buyqty': 'BuyQty', 'buyavgprice': 'BuyAvg', 'buyamount': 'BuyValue', 'sellqty': 'SellQty',
                             'sellavgprice': 'SellAvg', 'sellamount': 'SellValue', 'producttype': 'ProductType'},
                    inplace=True)

                # Get the ltp values in the dataFrame with the help of the self.get_ltp function
                position_dataFrame['LTP'] = ForLtp.apply(self.get_ltp_dataset, axis=1)

                position_dataFrame['BookedProfitLoss'] = 0
                position_dataFrame['MTOM'] = 0

                # Re-arrangign the column and we have to return
                position_dataFrame.reindex(
                    columns=['Exch', 'ExchType', 'SymbolName', 'BuyQty', 'BuyAvg', 'BuyValue', 'SellQty', 'SellAvg',
                             'SellValue', 'BookedProfitLoss', 'LTP', 'ProductType', 'MTOM'])


            else:
                # Creating the empty dataFrame
                position_dataFrame = pd.DataFrame(
                    columns=['Exch', 'ExchType', 'SymbolName', 'BuyQty', 'BuyAvg', 'BuyValue', 'SellQty', 'SellAvg',
                             'SellValue', 'BookedProfitLoss', 'LTP', 'ProductType', 'MTOM'])

            position_dataFrame.astype(convert_dict)
            return position_dataFrame

        except Exception as e:
            self.log_this(e, log_level='error')
            columns = ['Exch', 'ExchType', 'SymbolName', 'BuyQty', 'BuyAvg', 'BuyValue',
                       'SellQty', 'SellAvg', 'SellValue', 'BookedProfitLoss', 'LTP', 'ProductType', 'MTOM']

            df = pd.DataFrame(columns=columns)
            df.astype(convert_dict)
            return df

    # Those two function to seperate the symbolname into two part first symbol and second exchange
    def tradingsymbol_seperator_name(self, df):
        '''
            :df = DataFrame
        '''
        trading_symbol = ''
        try:
            seperate = str(df['tradingsymbol'])
            sep = seperate.split("-")
            trading_symbol = sep[0]
        except Exception as e:
            self.log_this(e, log_level='error')
            trading_symbol = ''

        return trading_symbol

    def tradingsymbol_seperator_exch(self, df):
        '''
            :df = DataFrame
        '''
        exchange = None
        try:
            seperate = str(df['tradingsymbol'])
            sep = seperate.split("-")
            exchange = sep[1]
        except Exception as e:
            self.log_this(e, log_level='error')
            exchange = ''

        return exchange

    # Done but can't check without holdings
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
        convert_dict = {
            "Exch": object,
            "ExchType": object,
            "SymbolName": object,
            "Qty": np.int64,
            "BuyPrice": np.float64,
            "CurrentPrice": np.float64,
            "ProfitAndLoss": np.float64,
            "DpQty": np.int64
        }
        columns = ['Exch', 'ExchType', 'SymbolName', 'Qty', 'BuyPrice', 'CurrentPrice', 'ProfitAndLoss', 'DpQty']
        try:
            holding = self.client.holding()
            if holding['data'] != None:
                holding_dataFrame = pd.DataFrame(holding['data'])

                symbol_data = holding_dataFrame[['tradingsymbol']]  # This dataFrame for the Symbol and exch seperator
                price_data = holding_dataFrame['exchange', 'tradingsymbol']  # This dataFrame for get the price value

                position_data = self.client.position()  # This is for getting the symbol token
                position_data = pd.DataFrame(position_data['data'])
                symbol_token = position_data['symboltoken']
                For_CurrentPrice = price_data.join(symbol_token)

                holding_dataFrame = holding_dataFrame[['exchange', 'quantity', 'realisedquantity', 'profitandloss']]

                holding_dataFrame['SymbolName'] = symbol_data.apply(self.tradingsymbol_seperator_name, axis=1)
                holding_dataFrame['ExchType'] = symbol_data.apply(self.tradingsymbol_seperator_exch, axis=1)

                holding_dataFrame['BuyPrice'] = '0'
                # holding_dataFrame['CurrentPrice'] = get the by the help of the ltp function
                holding_dataFrame['CurrentPrice'] = For_CurrentPrice.apply(self.get_ltp, axis=1)

                holding_dataFrame.rename(
                    columns={'profitandloss': 'ProfitAndLoss', 'quantity': 'Qty', 'realisedquantity': 'DpQty',
                             'exchange': 'Exch'}, inplace=True)

                holding_dataFrame = holding_dataFrame.reindex(columns=columns)

            else:
                # Returning the empty the dataFrame in case when we don't have the any holding
                holding_dataFrame = pd.DataFrame([], columns=columns)
            holding_dataFrame = holding_dataFrame.astype(convert_dict)
            return holding_dataFrame

        except Exception as e:
            self.log_this(e, log_level='error')

            df = pd.DataFrame(columns=columns)
            df = df.astype(convert_dict)
            return df

    # Done
    def get_margin(self):
        """Returns user margin at the instant
        
        Returns:
            available_margin <float>: available margin for trade
            used_margin <float>: Used margin
        """
        available_margin = 0.0
        used_margin = 0.0
        try:
            margin = self.client.rmsLimit()
            margin_data = margin['data']
            available_margin = float(margin_data['availablecash'])
            used_margin = float(margin_data['utiliseddebits'])
        except Exception as e:
            self.log_this(e, log_level='error')
            available_margin = 0.0
            used_margin = 0.0
        return available_margin, used_margin
