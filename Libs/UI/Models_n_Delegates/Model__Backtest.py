import pandas as pd
from PyQt5 import QtCore
from PyQt5.QtCore import Qt

from Libs.globals import *
from Libs.Utils import string_view_manipulator as str_man

logger = exception_handler.getFutureLogger(__name__)


class BT_CSV_View(QtCore.QAbstractTableModel):
    def __init__(self, header_labels, data=None):
        super(BT_CSV_View, self).__init__()
        self.header_labels = header_labels
        self._data = data or pd.DataFrame(columns=self.header_labels)

    def clear(self):
        self.beginResetModel()
        self._data = pd.DataFrame(columns=self.header_labels)
        self.endResetModel()

    def item(self, row: int, col: int):
        """to get each item, by row and column index from model"""
        if 0 <= row < len(self._data) and 0 <= col < len(self._data[0]):
            return self.data(self.index(row, col), Qt.DisplayRole)

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            _data = str(self._data.iat[index.row(), index.column()])
            return str_man.is_match_decimal(_data)
        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter

    def get_data(self):
        """Gets the model's complete data"""
        return self._data

    def populate(self, df):
        """Reset the model"""
        self.beginResetModel()
        self._data = df.copy()
        self.endResetModel()

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._data)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.header_labels)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str_man.humanize_string(str(self.header_labels[section]).upper())
            if orientation == Qt.Vertical:
                return str(section)
