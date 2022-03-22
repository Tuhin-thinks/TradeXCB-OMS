from functools import lru_cache

import pandas as pd
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt

from Libs.globals import *
from Libs.Utils import string_view_manipulator as str_man


class PositionsModel(QtCore.QAbstractTableModel):
    def __init__(self, header_labels: typing.List, data=None):
        super(PositionsModel, self).__init__()
        self._data = None
        if data is None:
            data = pd.DataFrame(columns=app_data.POSITIONS_COLUMNS)
        self.populate(data)
        self.header_labels = header_labels

    def populate(self, data):
        """populate model with new data source"""
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def item(self, row: int, col: int):
        """to get each item, by row and column index from model"""
        if 0 <= row < self.rowCount() and 0 <= col < self.columnCount():
            return self.data(self.index(row, col), Qt.DisplayRole)

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        row, col = index.row(), index.column()

        if role == Qt.DisplayRole:
            _data = str(self._data.iat[row, col])
            if _data == "nan":
                _data = ""
            if self.header_labels[col] in ("Row_Type",):
                if _data == 'T':
                    _data = "Running"
                elif _data == 'F':
                    _data = "Closed"
                # _data = "Running" if _data == 'T' else 'Closed'
            elif self.header_labels[col] in ("entry_time", "exit_time"):  # remove microseconds for mentioned cols
                _data = (_data.split('.')[0] if '.' in _data else _data)
            elif str_man.is_match_decimal(_data):
                _data = str_man.is_match_decimal(_data)  # round up decimals up-to 3 places
            return _data.upper()

        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter

        if role == Qt.ForegroundRole:
            if self.header_labels[col].lower() == "profit":
                data = self._data.iat[row, col]
                if data < 0:
                    return QtGui.QColor("red")
                return QtGui.QColor(0, 255, 0)  # green color

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._data) if type(self._data) == list else self._data.shape[0]

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        if len(self.header_labels) > 0:
            return len(self.header_labels)
        else:
            return len(self.header_labels)

    def get_data(self):
        return self._data

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str_man.humanize_string(str(self.header_labels[section]).upper())
            if orientation == Qt.Vertical:
                return f"Column - {section}"
