import random
import typing
import time
import datetime
import multiprocessing
from PyQt5 import QtCore
from . import main_strategy

from Libs.Utils import exception_handler
from Libs.Storage import app_data

logger = exception_handler.getAlgoLogger(__name__)


def algo(manager_dict: typing.Dict, cancel_orders_queue: multiprocessing.Queue):
    print(manager_dict)
    while manager_dict["algo_running"]:
        orderbook_data_dict = {col: [] for col in app_data.OMS_TABLE_COLUMNS}
        __temp = {'Instrument': ['NIFTY2231717500CE', 'NIFTY2231716300PE', 'NIFTY2231717500CE',
                                              'NIFTY2231716300PE'],
                               'Entry Price': [5.35, None, None, 11.55],
                               'Entry Time': [datetime.datetime(2022, 3, 16, 15, 20, 6, 385140),
                                              None, None, datetime.datetime(2022, 3, 16, 15, 20, 17, 68007)],
                               'Exit Price': [None, None, None, None],
                               'Exit Time': [None, None, None, None],
                               'Order Type': ['LIMIT', 'LIMIT', 'LIMIT', 'LIMIT'],
                               'Quantity': [50, 50, 50, 50],
                               'Product Type': ['MIS', 'MIS', 'MIS', 'MIS'],
                               'Stoploss': [50.0, 50.0, 50.0, 50.0],
                               'Target': [20.0, 20.0, 20.0, 20.0],
                               'Order Status': [random.choice(["Placed", "Pending",
                                                               "Cancelled", "Waiting",
                                                               "Executed"]) for _ in range(4)],
                               'instrument_df_key': [1, 2, 3, 4],
                               'Close Position?': []}
        for col in app_data.OMS_TABLE_COLUMNS:
            orderbook_data_dict[col] = __temp[col]
        manager_dict['orderbook_data'] = orderbook_data_dict

        while True:
            try:
                row_key = cancel_orders_queue.get_nowait()
                if row_key is not None:
                    print("To close position at row key:", row_key)
                else:
                    break
            except Exception as e:
                break

        time.sleep(3)
        # print("Running Algo", end="\r\n")


class AlgoManager(QtCore.QObject):
    error_stop = QtCore.pyqtSignal(str)
    orderbook_data = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super(AlgoManager, self).__init__(parent)
        self._monitor_timer = None
        self.manager_dict = multiprocessing.Manager().dict()  # to handle shared data between processes
        self.cancel_order_queue = multiprocessing.Queue()

    def get_cancel_order_queue(self):
        return self.cancel_order_queue

    def start_algo(self, paper_trade: int):
        # algo_process = multiprocessing.Process(target=main_strategy.main,
        #                                        args=(self.manager_dict, self.cancel_order_queue))
        algo_process = multiprocessing.Process(target=main_strategy.main,
                                               args=(self.manager_dict, self.cancel_order_queue))
        self.manager_dict['paper_trade'] = paper_trade
        self.manager_dict['algo_running'] = True
        self.manager_dict['algo_error'] = None
        self.manager_dict['force_stop'] = False
        self.manager_dict['orderbook_data'] = None
        algo_process.start()
        self.start_algo_monitor()

    def stop_algo(self):
        self.manager_dict['force_stop'] = True  # activate force-stop, it'll stop the algo in the next iteration

    def start_algo_monitor(self):
        self._monitor_timer = QtCore.QTimer()
        self._monitor_timer.timeout.connect(self.algo_monitor)
        self._monitor_timer.start(1500)
        logger.debug('Algo monitoring started')

    def algo_monitor(self):
        if not self.manager_dict.get('algo_running'):
            self.error_stop.emit(self.manager_dict.get('algo_error'))
            self._monitor_timer.stop()
            logger.debug('Algo monitoring stopped')
            self.manager_dict['algo_error'] = None
        else:
            # logger.debug("Algo is running, checking Orderbook data...")
            orderbook_data = self.manager_dict.get('orderbook_data')
            if isinstance(orderbook_data, dict):
                self.orderbook_data.emit(orderbook_data)
