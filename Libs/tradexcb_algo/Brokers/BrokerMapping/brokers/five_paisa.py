import json
import sys
import threading
import time
from importlib import import_module

import numpy as np
import pandas as pd

from BrokerMapping.main_broker import Broker


class FivePaisa(Broker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        globals()["py5paisa"] = import_module("py5paisa")
        self.live_ltp_data = dict()  # symbolName -> price
        self.streaming_flag = 0
        self.do_login()

    def do_login(self):
        """Logins with the broker and returns broker instance
        """
        try:
            cred = {
                "APP_NAME": self.credentials['APP_NAME'],
                "APP_SOURCE": self.credentials['APP_SOURCE'],
                "USER_ID": self.credentials['USER_ID'],
                "PASSWORD": self.credentials['APP_PASSWORD'],
                "USER_KEY": self.credentials['USER_KEY'],
                "ENCRYPTION_KEY": self.credentials['ENCRYPTION_KEY']
            }
            self.client = py5paisa.FivePaisaClient(
                email=self.credentials['EMAIL'],
                passwd=self.credentials['WEB_PASSWORD'],
                dob=self.credentials['DOB'],
                cred=cred)

            self.client.login()
        except IndexError as I:
            self.log_this(I, 'error')

        except Exception as e:
            self.log_this(e, 'error')
            self.client = ''

    def check_login(self):
        """Return if login session is successful

        Returns:
            bool: 1 for success, 0 for failure
        """
        try:
            if self.client.client_code == "INVALID CODE" or self.client.client_code == "":
                return 0
        except Exception as e:
            self.log_this(e, 'error')
            return 0
        return 1

    def get_scrip_code(self, tradingsymbol):
        """Returns scrip code for trading symbol

        Args:
            tradingsymbol (str): unique trading symbol

        Returns:
            str: scrip code
        """
        try:
            scrip_code = int(
                self.instrument_df[self.instrument_df['tradingsymbol'] == tradingsymbol].iloc[0]['exchange_token'])
            return scrip_code
        except IndexError:
            self.log_this("Instrument not found", 'error')
            return None, "Instrument not found"
        except Exception as e:
            self.log_this(e, 'error')
            return None, "Error raised"

    def get_exchange(self, tradingsymbol):
        """Returns exchange for the given trading symbol

        Args:
            tradingsymbol (str): unique trading symbol

        Returns:
            str: exchange
        """
        exchange_mapping = {
            "CDS": "N",
            "BSE": "B",
            "MCX": "M",
            "NFO": "N",
            "NSE": "N",
            "BCD": "B"
        }

        try:
            exchange = str(
                exchange_mapping[
                    self.instrument_df[self.instrument_df['tradingsymbol'] == tradingsymbol].iloc[0]['exchange']])
            return exchange
        except IndexError:
            self.log_this("Instrument not found", 'error')
            return None, "Instrument not found"
        except Exception as e:
            self.log_this(e, 'error')
            return None, "Error raised"

    def get_exchange_type(self, tradingsymbol):
        """Returns exchange type for the given trading symbol

        Args:
            tradingsymbol (str): unique trading symbol

        Returns:
            str: exchange type
        """

        exchange_type_mapping = {
            "EQ": "C",
            "CE": "D",
            "PE": "D",
            "FUT": "D",
            "MCX": "D"
        }

        try:
            exchange_type = str(
                exchange_type_mapping[self.instrument_df[self.instrument_df['tradingsymbol'] == tradingsymbol].iloc[0][
                    'instrument_type']])
            return exchange_type
        except IndexError:
            self.log_this("Instrument not found", 'error')
            return None, "Instrument not found"
        except Exception as e:
            self.log_this(e, 'error')
            return None, "Error raised"

    def place_order(self, **kwargs):
        """Places order with the broker

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
        order_id = None
        message = "Success"
        try:
            m = self.client.place_order(**{
                "OrderType": kwargs['transaction_type'],
                "Exchange": self.get_exchange(kwargs['tradingsymbol']),
                "ExchangeType": self.get_exchange_type(kwargs['tradingsymbol']),
                "ScripCode": self.get_scrip_code(kwargs['tradingsymbol']),
                "Qty": kwargs['quantity'],
                "Price": 0 if kwargs['order_type'] == 'MARKET' else kwargs['price'],
                "IsIntraday": "true",
                "StopLossPrice": 0 if kwargs['stoploss'] == None else kwargs['stoploss'],
                "IsStopLossOrder": True if kwargs['stoploss'] != None else False
            })
            order_id = int(m['BrokerOrderID'])
            message = m['Message']
        except Exception as e:
            self.log_this(e, 'error')
            message = "Error raised"
            order_id = -1
        return int(order_id), str(message)

    def cancel_order(self, order_id: str):
        """Cancels order with the given id
        Args:
            order_id (str): Unique order id
        
        Returns:
            status_code <int>: -1 for failure, 1 for success
            message <str>: Message from the broker
        """
        try:
            m = self.client.cancel_order(
                exch_order_id=order_id
            )
            message = str(m['Message'])
            val = int(m['Status'])
        except Exception as e:
            self.log_this(e, 'error')
            message = "Error raised"
            val = -1
        return int(val), str(message)

    def get_ltp(self, tradingsymbols: list):
        """Returns the last traded price of the instrument
        
        Args:
            trading_symbols: List of unique trading symbols
        
        Returns:
            pd.DataFrame: 
                symbolName: Unique symbol
                price: Current price of the symbol
        """
        try:
            if self.streaming_flag == 0:
                self.start_streaming(tradingsymbols)
                time.sleep(1)

            new_dict = dict()
            for symbol in tradingsymbols:
                if symbol in self.live_ltp_data.keys():
                    new_dict[symbol] = self.live_ltp_data[symbol]
                else:
                    new_dict[symbol] = 0
        except Exception as e:
            self.log_this(e, 'error')
            for symbol in tradingsymbols:
                new_dict[symbol] = 0

        return pd.DataFrame(new_dict.items(), columns=['symbolName', 'price'])

    def start_streaming(self, symbol_lists: list):
        """Subsribes to the symbols, and starts there live streaming

        Args:
            symbol_lists (list): List containing symbols for stock/option/derivative
        """
        try:
            def on_message(ws, message):
                print(message)
                message = json.loads(message)
                for symbol_data in message:
                    token = symbol_data['Token']
                    trading_symbol = str(
                        self.instrument_df[self.instrument_df['exchange_token'] == token].iloc[0]['tradingsymbol'])
                    price = symbol_data['LastRate']
                    self.live_ltp_data[trading_symbol] = price

            self.streaming_flag = 1
            request_list = list()
            print("symbol list : ", symbol_lists)
            for symbol in symbol_lists:
                request_list.append({
                    "Exch": self.get_exchange(symbol),
                    "ExchType": self.get_exchange_type(symbol),
                    "ScripCode": self.get_scrip_code(symbol)
                })

            req_data = self.client.Request_Feed('mf', 's', request_list)  # MarketFeedV3, Subscribe
            self.client.connect(req_data)
            t1 = threading.Thread(target=self.client.receive_data, args=(on_message,))
            t1.start()
        except Exception as e:
            self.log_this(e, 'error')

    def get_order_status(self, order_id: str):
        '''
        Returns order status for the given order id
        Args:

            exch (str): exchange
            order_id (str): order id
        Returns:
                'status': status of the order
        '''
        try:
            order_status_data = self.client.order_book()
            if order_status_data == '':
                msg = 'Currently no orders are placed'
                self.log_this(msg, log_level='info')

            else:
                order_status_df = pd.DataFrame(order_status_data)
                order_status_df = order_status_df[(order_status_df['BrokerOrderId'] == int(order_id))]
                order_status = order_status_df.iloc[-1]['OrderStatus']

        except:
            message = str(sys.exc_info())
            self.log_this(message, log_level='error')
            order_status = ''

        return str(order_status)

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
        df_columns = ['Exch', 'ScripName', 'Qty', 'BuySell', 'AtMarket',
                      'Rate', 'DelvIntra', 'SLTriggerRate', 'OrderStatus']
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
            order_history = pd.DataFrame(self.client.order_book())
            if not order_history.empty:
                order_history = order_history[df_columns]
                order_history.rename(columns={
                    'Exch': 'exchange',
                    'ScripName': 'tradingsymbol',
                    'Qty': 'quantity',
                    'BuySell': 'transaction_type',
                    'AtMarket': 'order_type',
                    'Rate': 'price',
                    'DelvIntra': 'validity',
                    'SLTriggerRate': 'stoploss',
                    'OrderStatus': 'orderstatus'
                }, inplace=True)
                order_history['product'] = 'NaN'
                order_history = order_history.reindex(columns=columns)
            else:
                order_history = pd.DataFrame([], columns=columns)
        except:
            message = str(sys.exc_info())
            self.log_this(message, log_level='error')
            order_history = pd.DataFrame([], columns=columns)

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
        columns = ['Exch', 'ExchType', 'SymbolName', 'BuyQty', 'BuyAvg', 'BuyValue',
                   'SellQty', 'SellAvg', 'SellValue', 'BookedProfitLoss', 'LTP', 'ProductType', 'MTOM']
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
            "BookedProfitAndLoss": np.float64,
            "LTP": np.float64,
            "ProductType": object,
            "MTOM": np.float64
        }
        try:
            obj = self.client.positions()
            if len(obj) != 0:

                position_dataframe = pd.DataFrame(obj)
                position_dataframe = position_dataframe[
                    ['Exch', 'ExchType', 'ScripName', 'BuyQty', 'BuyAvgRate', 'BuyValue', 'SellQty', 'SellAvgRate',
                     'SellValue', 'BookedPL', 'LTP', 'OrderFor', 'MTOM']]

                position_dataframe.rename(columns={
                    'OrderFor': 'ProductType',
                    'ScripName': 'SymbolName',
                    'BookedPL': 'BookedProfitAndLoss',
                    'SellAvgRate': 'SellAvg',
                    'BuyAvgRate': 'BuyAvg'
                }, inplace=True)

            else:
                position_dataframe = pd.DataFrame(columns=columns)

        except Exception as e:
            self.log_this(e, 'error')
            position_dataframe = pd.DataFrame(columns=columns)

        position_dataframe.astype(convert_dict)
        return position_dataframe

    def get_remapping_exchType(self, symbol):
        try:
            exch_type = self.instrument_df[self.instrument_df['tradingsymbol']
                                           == symbol['Symbol']].iloc[-1]['instrument_type']
            return exch_type
        except IndexError:
            self.log_this("Instrument not found", 'error')
            return None, "Instrument not found"
        except Exception as e:
            self.log_this(e, 'error')
            return None, "Error raised"

    def get_remapping_exch(self, symbol):
        try:
            exch = self.instrument_df[self.instrument_df['tradingsymbol']
                                      == symbol['Symbol']].iloc[0]['exchange']
            return exch
        except IndexError:
            self.log_this("Instrument not found", 'error')
            return None, "Instrument not found"
        except Exception as e:
            self.log_this(e, 'error')
            return None, "Error raised"

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
        columns = ['Exch', 'ExchType', 'SymbolName', 'Qty', 'BuyPrice', 'CurrentPrice', 'ProfitAndLoss', 'DpQty']
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
        try:
            obj = self.client.holdings()
            if len(obj) != 0:
                holding_dataFrame = pd.DataFrame(obj)
                holding_dataFrame = holding_dataFrame[[
                    'Exch', 'Symbol', 'Quantity', 'CurrentPrice', 'DPQty']]
                ForSymbol = holding_dataFrame[['Symbol']]
                holding_dataFrame['BuyPrice'] = 0
                holding_dataFrame['ProfitAndLoss'] = 0

                holding_dataFrame.rename(columns={
                    'Symbol': 'SymbolName',
                    'Quantity': 'Qty',
                    'DPQty': 'DpQty'
                }, inplace=True)

                holding_dataFrame['ExchType'] = ForSymbol.apply(
                    self.get_remapping_exchType, axis=1)
                holding_dataFrame['Exch'] = ForSymbol.apply(
                    self.get_remapping_exch, axis=1)

                holding_dataFrame = holding_dataFrame.reindex(
                    columns=['Exch', 'ExchType', 'SymbolName', 'Qty', 'BuyPrice', 'CurrentPrice', 'ProfitAndLoss',
                             'DpQty'])

            else:
                holding_dataFrame = pd.DataFrame(columns=['Exch', 'ExchType', 'SymbolName',
                                                          'Qty', 'BuyPrice', 'CurrentPrice', 'ProfitAndLoss', 'DpQty'])

        except Exception as e:
            self.log_this(e, 'error')
            columns = ['Exch', 'ExchType', 'SymbolName', 'Qty', 'BuyPrice', 'CurrentPrice', 'ProfitAndLoss', 'DpQty']
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
            holding_dataFrame = pd.DataFrame(columns=columns)
        holding_dataFrame.astype(convert_dict)
        return holding_dataFrame

    def get_margin(self):
        """Returns user margin at the instant
        
        Returns:
            available_margin <float>: available margin for trade
            used_margin <float>: Used margin
        """
        available_margin = 0.0
        used_margin = 0.0
        try:
            obj = self.client.margin()
            available_margin = obj[0]['AvailableMargin']
            used_margin = -obj[0]['Mgn4Position']
        except Exception as e:
            self.log_this(e, 'error')
            available_margin = 0.0
            used_margin = 0.0

        return available_margin, used_margin
