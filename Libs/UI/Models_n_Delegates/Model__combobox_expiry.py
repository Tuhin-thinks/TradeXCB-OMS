import typing

import pandas as pd
from PyQt5 import QtCore
from PyQt5.QtCore import Qt


class OptionsModel(QtCore.QStringListModel):
    def __init__(self, data_df: typing.Union[None, 'pd.DataFrame'] = ...):
        super(OptionsModel, self).__init__()
        self._data = pd.DataFrame(columns=("name", "expiry"))  # this will be populated later (self.populate)
        self._df = data_df  # store this, will be used to apply filter
        self.populate(data_df)

    def populate(self, data_df: pd.DataFrame):
        """reset the model with new dataframe"""
        self.beginResetModel()
        self._data = data_df['expiry'].dropna().unique().tolist()
        self.endResetModel()

    def update_model(self, name_filter: str):
        """this function is responsible for filtering a combobox's data based on other combobox's selection"""
        self.beginResetModel()
        self._data = self._df[self._df['name'] == name_filter]['expiry'].dropna().unique().tolist()
        self.endResetModel()

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole and index.isValid():
            _row = index.row()
            _col = index.column()
            return self._data[_row]

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if role == Qt.DisplayRole:
            _row = index.row()
            _col = index.column()
            self._data[_row] = value
            return True
        return False

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._data)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._data[0])
