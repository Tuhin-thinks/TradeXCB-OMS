import json
import multiprocessing
import typing

from PyQt5 import QtWidgets, QtGui, QtCore

from Libs.UI.Models_n_Delegates import Model_OMS
from Libs.Storage.app_data import OMS_TABLE_COLUMNS


class OMSTable(QtWidgets.QTableView):
    def __init__(self):
        super(OMSTable, self).__init__()

        self.__model = Model_OMS.OMSModel()
        self.setModel(self.__model)

        self.__button_delegate = Model_OMS.ButtonDelegate(self)
        self.setItemDelegateForColumn(OMS_TABLE_COLUMNS.index('Close Position?'), self.__button_delegate)

        QtCore.QTimer.singleShot(0, self.increase_col_space)

    def increase_col_space(self):
        total_table_width = self.viewport().width()
        per_col_width = int(total_table_width / self.__model.columnCount())
        if per_col_width < 100:
            return
        for col_index in range(self.__model.columnCount()):
            self.setColumnWidth(col_index, per_col_width)

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        super(OMSTable, self).resizeEvent(e)

    def update_data(self, data: typing.Dict[str, typing.Dict[str, typing.Any]]):
        self.__model.populate(data_dict=data)

    def set_cancel_order_queue(self, queue: multiprocessing.Queue):
        self.__button_delegate.set_cancel_orders_queue(queue)
