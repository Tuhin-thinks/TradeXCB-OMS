from datetime import datetime
from copy import deepcopy
import multiprocessing
import typing
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt

from Libs.Storage import app_data
from Libs.Utils.exception_handler import getFutureLogger

checklist = ("executed", "placed", "complete", "open")
logger = getFutureLogger(__name__)


class ButtonDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(ButtonDelegate, self).__init__(parent)
        self._is_clicked_dict = {}
        self.cancel_orders_queue = None

    def set_cancel_orders_queue(self, cancel_orders_queue: multiprocessing.Queue):
        self.cancel_orders_queue = cancel_orders_queue

    def paint(self, painter: QtGui.QPainter, option: 'QtWidgets.QStyleOptionViewItem', index: QtCore.QModelIndex) -> None:
        __model = index.model()
        row, col = index.row(), index.column()
        __status_index = __model.index(row, app_data.OMS_TABLE_COLUMNS.index("Order Status"))
        status = __model.data(__status_index) or ""
        if col == app_data.OMS_TABLE_COLUMNS.index("Close Position?") and any((x in status.lower() for x in checklist)):
            self.parent().openPersistentEditor(index)
        super().paint(painter, option, index)

    def createEditor(self, parent: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        self._is_clicked_dict[index.row()] = False
        push_button = QtWidgets.QPushButton(parent)
        push_button.move(option.rect.topLeft())
        push_button.setText("Close Position")
        push_button.setPalette(self.parent().palette())
        push_button.clicked.connect(lambda: self.close_position(index))
        return push_button

    def setEditorData(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex):
        editor.blockSignals(True)
        __model = index.model()
        __status_index = __model.index(index.row(), app_data.OMS_TABLE_COLUMNS.index("Order Status"))

        # --------- handling close position button based on status---------
        if index.column() == app_data.OMS_TABLE_COLUMNS.index("Close Position?"):
            self._is_clicked_dict.clear()
            status_value = __model.data(__status_index) or ""
            if any((x in status_value.lower() for x in checklist)):
                editor.setEnabled(True)
            else:
                editor.setEnabled(False)
        editor.blockSignals(False)

    def setModelData(self, editor: QtWidgets.QWidget, model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex):
        close_position = 1 if self._is_clicked_dict.get(index.row()) else 0
        # editor.setDisabled(True)  # disable the button (close position press one time only)
        model.setData(index, close_position, role=Qt.EditRole)  # entry point for user-algo interaction

    def updateEditorGeometry(self, editor: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        editor.setGeometry(option.rect)

    # --------- my custom functions ---------
    def close_position(self, index: QtCore.QModelIndex):
        self._is_clicked_dict[index.row()] = True
        instr_df_key_col_index = app_data.OMS_TABLE_COLUMNS.index("instrument_df_key")
        __instrument_df_key_index = index.model().index(index.row(), instr_df_key_col_index)
        __instrument_df_key = index.model().data(__instrument_df_key_index)
        try:
            self.cancel_orders_queue.put(int(__instrument_df_key))  # put the row key to the queue
        except ValueError:
            pass
        self.commit_editor()

    def commit_editor(self):
        editor = self.sender()
        self.commitData.emit(editor)


class OMSModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        super(OMSModel, self).__init__(parent)
        self.__data = {}
        self.__key_list = []
        self.header_labels = app_data.OMS_TABLE_COLUMNS

    def rowCount(self, parent=QtCore.QModelIndex()):
        if self.__data:
            return max([len(self.__data[x]) for x in self.__key_list])
        return len(self.__data)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.header_labels)

    def populate(self, data_dict: typing.Dict[str, typing.List[typing.Any]]):
        if self.__data != data_dict:
            self.beginResetModel()
            del self.__data
            self.__data = deepcopy(data_dict)
            self.__key_list = list(data_dict.keys())
            self.endResetModel()

    def data(self, index, role=Qt.DisplayRole):
        col_name = self.header_labels[index.column()]
        if role == Qt.DisplayRole:
            if col_name == "Close Position?":
                return ""
            return str(self.__data[col_name][index.row()])
        elif role == Qt.EditRole:
            if col_name == "Close Position?":
                return ""
            return str(self.__data[col_name][index.row()])
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if not index.isValid():
            return False
        col_name = self.header_labels[index.column()]
        if role == Qt.EditRole and col_name in ("Close Position?",):
            if value == 1:
                logger.info(f"Close Requested for row: {index.row()} [{datetime.now()}]")
            self.__data[col_name][index.row()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlags:
        col_name = self.header_labels[index.column()]
        # if col_name in ("Stoploss", "Target", "MODIFY", "Close Position?"):
        if col_name in ("Close Position?",):
            order_status = self.__data["Order Status"][index.row()]
            if order_status and any((x in order_status.lower() for x in checklist)):
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.header_labels[section]
            else:
                return section + 1
