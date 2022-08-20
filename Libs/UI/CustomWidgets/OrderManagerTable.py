import multiprocessing
import typing

from PyQt5 import QtWidgets, QtGui, QtCore

from Libs.Storage.app_data import OMS_TABLE_COLUMNS
from Libs.UI.CustomWidgets import Order_StatusViewDialog
from Libs.UI.Models_n_Delegates import Model_OMS


class OMSTable(QtWidgets.QTableView):
    def __init__(self):
        super(OMSTable, self).__init__()

        self._status_view_dialog = None
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

    def update_data(self, data: typing.Dict[str, typing.List[typing.Any]]):
        self.__model.populate(data_dict=data)

    def set_cancel_order_queue(self, queue: multiprocessing.Queue):
        self.__button_delegate.set_cancel_orders_queue(queue)

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        super(OMSTable, self).mousePressEvent(e)

        if e.button() == QtCore.Qt.LeftButton:
            # get the cell index, for the tableview when left-clicked
            index = self.indexAt(e.pos())
            if index.isValid():
                # get the row and column index
                row = index.row()
                col = index.column()
                if OMS_TABLE_COLUMNS[col] == "Order Status":
                    # get the data from the model
                    order_status = self.__model.data(index, QtCore.Qt.DisplayRole)
                    row_id = self.__model.data(self.__model.index(row, OMS_TABLE_COLUMNS.index("instrument_df_key")),
                                               QtCore.Qt.DisplayRole)
                    instr_col_name = "Instrument"
                    instrument_symbol = self.__model.data(
                        self.__model.index(row, OMS_TABLE_COLUMNS.index(instr_col_name)),
                        QtCore.Qt.DisplayRole)
                    self._status_view_dialog = Order_StatusViewDialog.OrderStatusView(row_id=row_id,
                                                                                      order_status_string=order_status,
                                                                                      instrument_str=instrument_symbol)
                    self._status_view_dialog.show()
