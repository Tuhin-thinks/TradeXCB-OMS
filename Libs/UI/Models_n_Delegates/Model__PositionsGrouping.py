import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt


class PositionsGroupingModel(QtCore.QAbstractTableModel):
    def __init__(self, header_labels, data: pd.DataFrame, parent=None):
        super(PositionsGroupingModel, self).__init__(parent)
        self.data = None
        self.__proxy_data = None
        self.header_labels = header_labels
        self.populate(data)

    def populate(self, data: pd.DataFrame):
        self.beginResetModel()
        self.data = data
        self.__proxy_data = data.copy()
        self.endResetModel()

    def rowCount(self, parent=None):
        return self.data.shape[0]

    def columnCount(self, parent=None):
        return len(self.header_labels)

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == Qt.DisplayRole:
            data = str(self.__proxy_data.iloc[row, index.column()])
            return data

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.header_labels[section]
        else:
            return str(section + 1)

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    # ------ custom functions ------
    def set_filter(self, by_colum, value):
        self.beginResetModel()
        self.__proxy_data = self.data[self.data[by_colum] == value]
        self.endResetModel()

    def calculate_profit(self):
        return self.__proxy_data['profit'].sum()

    def calculate_quantity(self):
        buy_quantity = self.__proxy_data[self.__proxy_data['Trend'].str.lower() == 'buy']['quantity'].sum()
        sell_quantity = self.__proxy_data[self.__proxy_data['Trend'].str.lower() == 'sell']['quantity'].sum()
        return buy_quantity, sell_quantity
