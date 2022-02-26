from PyQt5 import QtCore

from Libs.globals import *


class WorkerSignals(QtCore.QObject):
    started = QtCore.pyqtSignal()
    result = QtCore.pyqtSignal(object)
    status = QtCore.pyqtSignal(str)
    stopped = QtCore.pyqtSignal()
    execute_this = QtCore.pyqtSignal(tuple)


class Worker(QtCore.QRunnable):
    """
    Worker thread
    """

    def __init__(self, fn: typing.Callable, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @QtCore.pyqtSlot()
    def run(self):
        """
        Your code goes in this function
        """
        self.signals.started.emit()
        ret = self.fn(*self.args, self.signals.execute_this)
        if ret:
            self.signals.result.emit(ret)
        self.signals.stopped.emit()


class OptDataUpdateWorker(QtCore.QRunnable):
    """
    Worker thread
    """

    def __init__(self, fn: typing.Callable, *args, **kwargs):
        super(OptDataUpdateWorker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @QtCore.pyqtSlot()
    def run(self):
        """
        Your code goes in this function
        """
        self.signals.started.emit()
        ret = self.fn(*self.args)
        if ret:
            self.signals.result.emit(ret)
        self.signals.stopped.emit()
