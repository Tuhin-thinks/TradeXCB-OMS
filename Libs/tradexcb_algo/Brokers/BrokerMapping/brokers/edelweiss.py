import json
import sys
import threading
import time
from importlib import import_module
from urllib.parse import urlparse

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
# import webdrivermanager
from webdrivermanager.chrome import ChromeDriverManager

from BrokerMapping.main_broker import Broker
from BrokerMapping import settings


class Edelweiss(Broker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        globals()["EdelweissAPIConnect"] = import_module("EdelweissAPIConnect")
        self.live_ltp_data = dict()  # symbolName -> price
        self.streaming_flag = 0
        self.edel_instruments_df = pd.read_csv(settings.EDEL_INSTRUMENTS_FILE)
        self.do_login()

    def get_reqId(self, api_key, UserId, password, dob):
        try:
            options = Options()
            options.add_argument('--headless')
            driver_path = ChromeDriverManager().download_and_install()[0]
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(f"https://www.edelweiss.in/api-connect/login?api_key={api_key}")
            wait = WebDriverWait(driver, 20)

            wait.until(EC.presence_of_element_located((By.XPATH, '//input[@class="input_field"]'))).send_keys(UserId)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.primary"))).submit()

            time.sleep(3.0)

            password_inp_field = driver.find_element(By.ID, "password")
            password_inp_field.send_keys(password)
            proceed_submit_button = driver.find_element(By.CSS_SELECTOR, "button.primary")
            proceed_submit_button.submit()

            time.sleep(1.0)

            # goes to next page, have to enter dob or yob
            yob_inp_ids = [f"yob-{i}" for i in range(4)]
            yob_segments = [ch for ch in str(dob)]
            for i, yob_id in enumerate(yob_inp_ids):
                yob_inp_field = driver.find_element(By.ID, yob_id)
                yob_inp_field.send_keys(yob_segments[i])

            proceed_submit_button_2 = driver.find_element(By.CSS_SELECTOR, "button.primary.submit_btn")
            proceed_submit_button_2.submit()

            time.sleep(1.0)

            # now page will redirect to localhost, have to get the request_id
            current_url = driver.current_url
            request_id = urlparse(current_url).query.split('=')[1]
            driver.close()
            return request_id
        except Exception as e:
            self.log_this(e, 'error')
            return None

    def do_login(self):
        """Logins with the broker and returns broker instance
        """
        try:
            USERID = self.credentials['USERID']
            PASSWORD = self.credentials['PASSWORD']
            API_KEY = self.credentials['API_KEY']
            API_SECRET = self.credentials['API_SECRET']
            DOB = self.credentials['DOB']
            request_id = self.get_reqId(API_KEY, USERID, PASSWORD, DOB)
            # print("request_id:", request_id)

            self.client = EdelweissAPIConnect.EdelweissAPIConnect(API_KEY, API_SECRET, request_id, True)
        except IndexError as i:
            self.log_this(f'{i} | Can not import the right Credential', 'error')
            self.client = ''
        except Exception as e:
            self.log_this(e, 'error')
            self.client = None

    def check_login(self):
        """Check if login was successful or not
        
        Returns:
            Boolean: 1 for success, 0 for failure
        """
        try:
            check_login_status = self.client.dc
            if check_login_status == True:
                return 1
            else:
                return 0
        except Exception as e:
            self.log_this(e, 'error')
            return 0

    def get_trading_symbol_csv(self, token, exchange):
        try:
            df_line = self.angel_instrument_df[
                (self.angel_instrument_df['token'] == token) & (self.angel_instrument_df['exch_seg'] == str(exchange))]
            tradingsymbol = df_line.iloc[-1]['symbol']
        except Exception as e:
            self.log_this(e, 'error')
            tradingsymbol = ''
        return tradingsymbol

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
        order_id = None
        message = 'Success'
        valadity_mapping = {
            "DAY": "DAY",
            "IOC": "IOC",
        }
        try:
            df_line = self.instrument_df[(self.instrument_df['tradingsymbol'] == kwargs['tradingsymbol']) & (
                        self.instrument_df['exchange'] == kwargs['exchange'])]

            streaming_symbol = df_line.iloc[-1]['exchange_token']

            exchange = kwargs['exchange']
            tradingsymbol = self.get_trading_symbol_csv(streaming_symbol, exchange)
            action = kwargs['transaction_type']
            duration = valadity_mapping[kwargs['validity']]
            order_type = kwargs['order_type']
            quantity = kwargs['quantity']
            limit_price = kwargs['price']
            product_code = kwargs['product']

            place_order = self.client.PlaceTrade(Trading_Symbol=tradingsymbol, Exchange=exchange, Action=action,
                                                 Duration=duration, Order_Type=order_type, Quantity=quantity,
                                                 Streaming_Symbol=str(streaming_symbol), Limit_Price=str(limit_price),
                                                 Disclosed_Quantity="0", TriggerPrice="0", ProductCode=product_code)

            order_id = place_order['data']
            if order_id == '':
                message = "Can't place Order"
                order_id = -1
            else:
                message = "Order place successfully"
                order_id = order_id['oid']
        except Exception as e:
            self.log_this(e, 'error')
            message = "Can't place Order " + str(e)
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
        try:
            canceled = self.client.CancelTrade(order_id)
            if canceled != '':
                msg = "Cancel Order Successfully"
                val = 1
            else:
                msg = "There is no active Order"
                val = -1
        except:
            msg = str(sys.exc_info())
            val = -1
        return int(val), str(msg)

    def get_ltp(self, tradingsymbols: list):
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
            self.streming_data(tradingsymbols)
            time.sleep(10)
        try:
            for symbol in tradingsymbols:
                if symbol in self.live_ltp_data.keys():
                    new_dict[symbol] = self.live_ltp_data[symbol]
                else:
                    new_dict[symbol] = 0

        except Exception as e:
            self.log_this(e, 'error')

        ltp_dataframe = pd.DataFrame(new_dict.items(), columns=['symbolName', 'price'])
        ltp_dataframe = ltp_dataframe.astype(convert_dict)
        return ltp_dataframe

    def streming_data(self, symbol_list: list):
        def getStreamingData(message):
            print('inside get streaming data')
            # print(type(message))
            print(message)
            try:
                msg_data = json.loads(message)
                symbol_token = str(msg_data['response']['data']['z3'])
                exchange_token = int(symbol_token.split('_')[0])
                exchange = symbol_token.split('_')[1]
                tradingsymbol = self.instrument_df[(self.instrument_df['exchange_token'] == exchange_token) & (
                            self.instrument_df['exchange'] == exchange)].iloc[0]['tradingsymbol']
                self.live_ltp_data[tradingsymbol] = msg_data['response']['data']['a9']
            except:
                print('error in get streaming data')
                print(sys.exc_info())

        try:
            self.streaming_flag = 1
            req_list = list()
            for symbol in symbol_list:
                exchange_token = self.instrument_df[self.instrument_df['tradingsymbol'] == symbol].iloc[-1][
                    'exchange_token']
                exchange = self.instrument_df[self.instrument_df['tradingsymbol'] == symbol].iloc[-1]['exchange']
                req_list.append(f'{exchange_token}_{exchange}')

            t1 = threading.Thread(target=EdelweissAPIConnect.Feed, args=(
            req_list, self.credentials['ACCID'], self.credentials['USERID'], getStreamingData, True, True))
            print('before start')
            t1.start()
        except Exception as e:
            self.log_this(e, 'error')

    def get_order_status(self, order_id: str):
        """
        Retrun the status of the order 
        Args:
            order_id: Unique order id of an order
        Return:
            str: Order status ['REJECTED', 'CANCELLED', 'PENDING', 'EXECUTED', 'ERROR']
        """
        try:
            order_status_df = self.client.OrderBook()['ord']
            if order_status_df == '':
                msg = "No active order present"
                self.log_this(msg, log_level='info')
                order_status = 'ERROR'
            else:
                order_status = pd.DataFrame(order_status_df)
                order_status = order_status[(order_status['ordID'] == order_id)]
                order_status = str(order_status.iloc[0]['sts'])
        except Exception as e:
            self.log_this(e, 'error')
            order_status = 'ERROR'

        return order_status

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
        df_columns = ['exc', 'trdSym', 'ltSz', 'prdCode', 'trsTyp',
                      'ordTyp', 'prc', 'dur', 'trgPrc', 'sts']
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
            order_history = self.client.OrderBook()
            if order_history != '':
                order_history = pd.DataFrame(order_history['ord'])
                order_history = order_history[df_columns]
                order_history.rename(columns={
                    'exc': 'exchange',
                    'trdSym': 'tradingsymbol',
                    'ltSz': 'quantity',
                    'prdCode': 'product',
                    'trsTyp': 'transaction_type',
                    'ordTyp': 'order_type',
                    'prc': 'price',
                    'dur': 'validity',
                    'trgPrc': 'stoploss',
                    'sts': 'orderstatus',
                }, inplace=True)
            else:
                order_history = pd.DataFrame([], columns=columns)
        except:
            message = str(sys.exc_info())
            self.log_this(message, 'error')
            order_history = pd.DataFrame([], columns=columns)

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
            exch_type = self.edel_instruments_df[self.edel_instruments_df['symbolname'] == tradingsymbol].iloc[0][
                'series']
            return exch_type
        except IndexError:
            self.log_this("Instrument not found", 'error')
            return 'NaN'
        except Exception as e:
            self.log_this(e, 'error')
            return "NaN"

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
        df_columns = ['exc', 'trdSym', 'byQty', 'avgByPrc', 'byAmt',
                      'slQty', 'avgSlPrc', 'slAmt', 'ntPL', 'ltp', 'mtm']
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
            positions = pd.DataFrame(self.client.NetPosition()['pos'])
            if not positions.empty:
                positions = positions[df_columns]
                positions['ProductType'] = "INTRADAY"
                positions['ExchType'] = positions['trdSym'].apply(self.get_exchange_type)
                positions.rename(columns={
                    "exc": "Exch",
                    "trdSym": "SymbolName",
                    "byQty": "BuyQty",
                    "avgByPrc": "BuyAvg",
                    "byAmt": "BuyValue",
                    "slQty": "SellQty",
                    "avgSlPrc": "SellAvg",
                    "slAmt": "SellValue",
                    "ntPL": "BookedProfitLoss",
                    "ltp": "LTP",
                    "mtm": "MTOM"
                }, inplace=True)
                positions.reindex(columns=columns)
            else:
                positions = pd.DataFrame([], columns=columns)
        except:
            message = str(sys.exc_info())
            self.log_this(message, 'error')

        positions = positions.astype(convert_dict)
        return positions

    def get_profitloss(self, df):
        currentprice = float(df[0])
        buyprice = float(df[1])
        profitloss = currentprice - buyprice
        return profitloss

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
            holdings = self.client.Holdings()['rmsHdg']
            if len(holdings) != 0:
                Qty = list()
                Exch = list()
                SymbolName = list()
                CurrentPrice = list()
                DpQty = list()
                BuyPrice = list()

                for dicts in holdings:
                    print(dicts['cncRmsHdg'])
                    Qty.append(dicts['cncRmsHdg']['qty'])
                    Exch.append(dicts['exc'])
                    CurrentPrice.append(dicts['ltp'])
                    SymbolName.append(dicts['trdSym'])
                    DpQty.append(dicts['totalQty'])
                    BuyPrice.append(dicts['cncRmsHdg']['hdgVl'])

                holdings = pd.DataFrame({
                    'Exch': Exch,
                    'SymbolName': SymbolName,
                    'Qty': Qty,
                    'BuyPrice': BuyPrice,
                    'CurrentPrice': CurrentPrice,
                    'DpQty': DpQty
                })

                ExchType = holdings['SymbolName']
                Profitandloss = holdings[['CurrentPrice', 'BuyPrice']]
                holdings['ExchType'] = ExchType.apply(self.get_exchange_type)
                holdings['ProfitAndLoss'] = Profitandloss.apply(self.get_profitloss, axis=1)

                holdings = holdings.reindex(columns=columns)
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
        try:
            margin = self.client.Limits()
            if margin == '':
                available_margin = 0
                used_margin = 0

            else:
                available_margin = margin['cshAvl']
                used_margin = margin['mrgUtd']['mrgUtd']

        except:
            message = str(sys.exc_info())
            self.log_this(message, 'error')

        return float(available_margin), float(used_margin)
