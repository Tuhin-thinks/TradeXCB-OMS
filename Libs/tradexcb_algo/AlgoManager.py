import multiprocessing
from PyQt5 import QtCore
from . import main_strategy


class AlgoManager(QtCore.QObject):
    error_stop = QtCore.pyqtSignal(str)
    orderbook_data = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super(AlgoManager, self).__init__(parent)
        self._monitor_timer = None
        self.manager_dict = multiprocessing.Manager().dict()  # to handle shared data between processes

    def start_algo(self):
        algo_process = multiprocessing.Process(target=main_strategy.main,
                                               args=(self.manager_dict,))
        algo_process.start()
        self.manager_dict['algo_running'] = True
        self.manager_dict['algo_error'] = None
        self.manager_dict['force_stop'] = False
        self.manager_dict['orderbook_data'] = None
        self.start_algo_monitor()

    def stop_algo(self):
        self.manager_dict['force_stop'] = True  # activate force-stop, it'll stop the algo in the next iteration

    def start_algo_monitor(self):
        self._monitor_timer = QtCore.QTimer()
        self._monitor_timer.timeout.connect(self.algo_monitor)
        self._monitor_timer.start(1000)

    def algo_monitor(self):
        if not self.manager_dict.get('algo_running'):
            self.error_stop.emit(self.manager_dict.get('algo_error'))
            self._monitor_timer.stop()
            self.manager_dict['algo_error'] = None
        else:
            self.orderbook_data.emit(self.manager_dict.get('orderbook_data'))
