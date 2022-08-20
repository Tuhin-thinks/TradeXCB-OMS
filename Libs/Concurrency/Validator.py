from typing import Callable
from PyQt5 import QtCore


class ValidatorSignals(QtCore.QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exc type, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    """
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)
    result = QtCore.pyqtSignal(object)


class ValidatorRunnable(QtCore.QRunnable):
    """
    Worker thread
    :param args: Arguments to make available to the run code
    :param kwargs: Keywords arguments to make available to the run code

    """

    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = ValidatorSignals()

    @QtCore.pyqtSlot()
    def run(self):
        """
        Initialise the runner function with passed self.args, self.kwargs.
        """
        res = self.fn(*self.args, **self.kwargs)
        self.signals.result.emit(res)
