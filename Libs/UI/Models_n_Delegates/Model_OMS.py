import typing
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt

from Libs.Storage import app_data


class ButtonDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(ButtonDelegate, self).__init__(parent)
        self._is_clicked_dict = {}

    def paint(self, painter: QtGui.QPainter, option: 'QtWidgets.QStyleOptionViewItem', index: QtCore.QModelIndex) -> None:
        __model = index.model()
        row, col = index.row(), index.column()
        __status_index = __model.index(row, app_data.OMS_TABLE_COLUMNS.index("Status"))
        status = __model.data(__status_index) or ""
        if (col == app_data.OMS_TABLE_COLUMNS.index("CLOSE_Position") and
                ("executed" in status.lower() or "placed" in status.lower())):
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
        __status_index = __model.index(index.row(), app_data.OMS_TABLE_COLUMNS.index("Status"))

        # --------- handling close position button based on status---------
        if index.column() == app_data.OMS_TABLE_COLUMNS.index("CLOSE_Position"):
            status_value = __model.data(__status_index) or ""
            if "executed" in status_value.lower() or "placed" in status_value.lower():
                editor.setEnabled(True)
            else:
                editor.setEnabled(False)
        editor.blockSignals(False)

    def setModelData(self, editor: QtWidgets.QWidget, model: QtCore.QAbstractItemModel, index: QtCore.QModelIndex):
        close_position = "YES" if self._is_clicked_dict[index.row()] else "NO"
        print("setting close position to:", close_position)
        editor.setDisabled(True)  # disable the button (close position press one time only)
        model.setData(index, close_position)  # entry point for user-algo interaction

    def updateEditorGeometry(self, editor: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        editor.setGeometry(option.rect)

    # --------- my custom functions ---------
    def close_position(self, index: QtCore.QModelIndex):
        print("closing position for index:", index.row())
        self._is_clicked_dict[index.row()] = True
        self.commit_editor()

    def commit_editor(self):
        editor = self.sender()
        self.commitData.emit(editor)


class OMSModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        super(OMSModel, self).__init__(parent)
        self.__data = []
        self.header_labels = app_data.OMS_TABLE_COLUMNS

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__data)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.header_labels)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        elif role == Qt.DisplayRole:
            return self.__data[index.row()][index.column()]
        elif role == Qt.EditRole:
            return self.__data[index.row()][index.column()]
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if not index.isValid():
            return False
        col_name = self.header_labels[index.column()]
        # if role == Qt.EditRole and col_name in ("Stoploss", "Target", "MODIFY", "CLOSE_Position"):
        if role == Qt.EditRole and col_name in ("Stoploss", "Target", "MODIFY", "CLOSE_Position", "Status"):
            self.__data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            if col_name == "Status":
                close_pos_model_index = self.index(index.row(), app_data.OMS_TABLE_COLUMNS.index("CLOSE_Position"))
                self.dataChanged.emit(close_pos_model_index, close_pos_model_index)
            return True
        return False

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        col_name = self.header_labels[index.column()]
        if col_name in ("Stoploss", "Target", "MODIFY", "CLOSE_Position"):
            order_status = self.__data[index.row()][self.header_labels.index('Status')]
            if order_status and ("placed" in order_status.lower() or "executed" in order_status.lower()):
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
            return Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.header_labels[section]
            else:
                return section + 1

    # -------- custom functions --------
    def append_row(self, row: typing.List[typing.Any] = None):
        if not row:
            row = [None] * len(self.header_labels)
        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
        self.__data.append(row)
        self.endInsertRows()

    def delete_row(self, row: int):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        self.__data.pop(row)
        self.endRemoveRows()
