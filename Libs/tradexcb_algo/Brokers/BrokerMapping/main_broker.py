from abc import abstractmethod, ABC
from typing import Literal
from xmlrpc.client import Boolean
import pandas as pd

from utils.exception_handler import getFutureLogger
import settings


class Broker(ABC):
    """Abstract class for broker object, contains all basic functions necessary for a broker instance
    Args:
        ABC (Abstract Class): Makes class abstract
    """

    def __init__(self, **kwargs):
        self.credentials = kwargs
        self.broker_name = kwargs['Stock Broker Name']
        self.logger = self.get_logger(f"BROKER_{self.broker_name}")
        self.instrument_df = pd.read_csv(settings.INSTRUMENTS_FILE)
        self.angel_instrument_df = pd.read_csv(settings.ANGEL_INSTRUMENT_FILE)
        self.client = ""  # Broker session object

    @staticmethod
    def get_logger(name):
        logger = getFutureLogger(name)
        return logger

    def log_this(self, log_message, log_level: Literal["info", "error", "debug"] = 'error') -> None:
        """Generates log entry using the custom logger
        Args:
            log_message (str): Log message to post
            log_level (str, optional): info, error, debug. Defaults to 'error'.
        """
        try:
            if log_level == 'info':
                self.logger.info(log_message)
            elif log_level == 'debug':
                self.logger.debug(log_message)
            else:
                self.logger.critical(f"Broker: {self.broker_name} {str(log_message)}", exc_info=True)
        except Exception as e:
            self.logger.critical(f"Error in logging a message {e.__str__()}", exc_info=True)

    @abstractmethod
    def do_login(self) -> None:
        """Logins with the broker and returns broker instance
        """
        pass

    @abstractmethod
    def check_login(self) -> Boolean:
        """Check if login was successful or not
        
        Returns:
            Boolean: 1 for success, 0 for failure
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def cancel_order(self, order_id: str):
        """Cancels order with the given id
        Args:
            order_id (str): Unique order id
        
        Returns:
            status_code <int>: -1 for failure, 1 for success
            message <str>: Message from the broker
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_ltp(self, trading_symbols: list) -> pd.DataFrame:
        """Returns the last traded price of the instrument
        
        Args:
            trading_symbols: List of unique trading symbols
        
        Returns:
            pd.DataFrame: 
                symbolName: Unique symbol
                price: Current price of the symbol
        """
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> str:
        """
        Retrun the status of the order 

        Args:
            order_id: Unique order id of an order

        Return:
            str: Order status ['REJECTED', 'CANCELLED', 'PENDING', 'EXECUTED', 'ERROR']
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_margin(self):
        """Returns user margin at the instant
        
        Returns:
            available_margin <float>: available margin for trade
            used_margin <float>: Used margin
        """
        pass
