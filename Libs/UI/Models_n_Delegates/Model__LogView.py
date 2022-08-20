from PyQt5 import QtCore
from PyQt5.QtCore import Qt

from Libs.globals import *


class LogModel(QtCore.QAbstractTableModel):
    def __init__(self, header_labels, data=None):
        super(LogModel, self).__init__()
        self._data = data or []
        self.header_labels = header_labels

    def clear(self):
        self.beginResetModel()
        self._data = []
        self.endResetModel()

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter

    def get_data(self):
        """get complete logs data List[List]"""
        return [self.header_labels] + self._data

    @QtCore.pyqtSlot(list)
    def append_row(self, row: list):
        if len(row) == 4 and row not in self._data:
            row_count = self.rowCount()
            self.beginInsertRows(QtCore.QModelIndex(), row_count, row_count)
            self._data.append(row)
            self.endInsertRows()

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._data)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        if self._data:
            return len(self._data[0])
        else:
            return len(self.header_labels)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self.header_labels[section]).title()
            if orientation == Qt.Vertical:
                return str(section)
