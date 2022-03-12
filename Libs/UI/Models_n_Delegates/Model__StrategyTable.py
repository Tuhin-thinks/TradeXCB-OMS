import re
from datetime import datetime

import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

from Libs.Utils.string_view_manipulator import humanize_string
from Libs.globals import *

logger = exception_handler.getFutureLogger(__name__)


class Communicate(QtCore.QObject):
    data_changed = QtCore.pyqtSignal(int, object)
    update_expiry_date = QtCore.pyqtSignal(int, object)


class ChoiceBoxDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, owner, choices, header_labels: typing.List, col_index: int, extra_choices=None,
                 data_dict: typing.Dict = None):
        super().__init__(owner)
        self.items: typing.Any[pd.DataFrame, typing.List] = choices
        self.owner = owner
        self.header_labels = header_labels
        self.col_index = col_index
        self.col_name = self.header_labels[col_index]
        self.to_humanize = False
        self.has_extra_choices = False
        self.humanized_str_items = []
        self.strike_options = []
        self.c = Communicate()
        if self.header_labels[self.col_index] in ("buy_ltp", "sell_ltp", "buy_flag", "sell_flag", "exit_criteria"):
            self.to_humanize = True
            self.humanized_str_items = [humanize_string(x) for x in self.items]

        if self.col_name == "atm_strike":
            choices = []
            for i in range(-10, 11):
                if i == 0:
                    choices.append("ATM CE")
                    choices.append("ATM PE")
                    continue
                operator = "" if i < 0 else "+"
                atm_ce = f"ATM{operator}{i} CE"
                atm_pe = f"ATM{operator}{i} PE"
                choices.append(atm_ce)
                choices.append(atm_pe)
            self.strike_options = choices

        if self.header_labels[col_index] == 'expiry':  # for expiry, extra choices is dataframe
            self.items: 'pd.DataFrame' = extra_choices
            self.has_extra_choices = True
        self.data_dict = data_dict

    def paint(self, painter, option, index):
        if isinstance(self.parent(), QtWidgets.QAbstractItemView):
            self.parent().openPersistentEditor(index)
        super().paint(painter, option, index)

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QComboBox(parent)
        editor.setMaxVisibleItems(10)
        editor.currentIndexChanged.connect(self.commit_editor)
        editor.setPalette(self.owner.palette())  # to maintain the same color theme as parent (else renders white)
        if self.to_humanize:
            editor.addItems(list(map(humanize_string, self.items)))
        else:
            if not self.has_extra_choices:
                editor.addItems(list(map(str, self.items)))
            else:
                editor.addItems([])
        return editor

    def commit_editor(self):
        editor = self.sender()
        self.commitData.emit(editor)  # save the editor's current state to the model

    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        # --------- get symbol name -----------
        _index = index.model().index(index.row(), self.header_labels.index('Symbol Name'))
        symbol_name = index.model().data(_index, Qt.DisplayRole)
        # --------- get exchange -----------
        exchange_model_index = index.model().index(index.row(), self.header_labels.index('exchange'))
        exchange = index.model().data(exchange_model_index, Qt.DisplayRole)

        if self.has_extra_choices:
            if isinstance(self.items, pd.DataFrame) and self.col_name == "expiry":
                filters = (self.items['name'] == symbol_name) & (self.items['exchange'] == exchange)
                expiry_dates_list: typing.Union[list, object] = pd.to_datetime(self.items[filters]['expiry']).\
                    sort_values().dt.strftime("%Y-%m-%d").dropna().unique().tolist()
                editor: QtWidgets.QComboBox
                editor.clear()  # clear all previous choices
                editor.addItems(expiry_dates_list)  # add new choices, based on symbol name selection
                if value in expiry_dates_list:  # check if selected expiry date is in valid choices
                    _value_index = expiry_dates_list.index(value)
                    editor.setCurrentIndex(_value_index)  # set current choice as the current index
                else:
                    editor.setCurrentIndex(0)  # set current choice as the first index
                    self.setModelData(editor, index.model(), index)  # save the current choice to the model
                return

        if self.col_name == "Symbol Name":
            if exchange == "NSE":
                stock_options_df = self.data_dict['nse_options_df']
                symbol_names_series: pd.Series = stock_options_df[stock_options_df['exchange'] == exchange]['name']
            else:
                symbol_names_series: pd.Series = self.items[self.items['exchange'] == exchange]['name']
            symbol_names_list: typing.Union[list, object] = symbol_names_series.dropna().unique().tolist()
            editor: QtWidgets.QComboBox
            editor.clear()  # clear all previous choices
            editor.addItems(symbol_names_list)  # add new choices, based on exchange selection
            if value in symbol_names_list:  # check if selected symbol name is in valid choices
                _value_index = symbol_names_list.index(value)
                editor.setCurrentIndex(_value_index)  # set current choice as the current index
            else:
                editor.setCurrentIndex(0)  # set current choice as the first index
                self.setModelData(editor, index.model(), index)  # save the current choice to the model
            return
        elif self.col_name == "atm_strike":
            if exchange in ("CDS", "MCX", "NFO"):  # check if current exchange type supports CE/PE
                editor: QtWidgets.QComboBox
                editor.clear()  # clear all previous choices
                editor.addItems(self.strike_options)  # add new choices, default options
                if value in self.strike_options:  # check if selected atm strike option is in valid choices
                    _value_index = self.strike_options.index(value)
                    editor.setCurrentIndex(_value_index)  # set current choice as the current index
                else:
                    editor.setCurrentIndex(0)  # set current choice as the first index
                    self.setModelData(editor, index.model(), index)  # save the current choice to the model
                return
            else:  # for other exchanges, we don't have atm_strike options
                editor: QtWidgets.QComboBox
                editor.clear()  # clear all previous choices
        # --------------- for columns other than 'Expiry Date' --------------------------
        self.items: list
        try:
            if self.to_humanize:
                num = self.humanized_str_items.index(humanize_string(value))
            else:
                num = self.items.index(value)
            editor.setCurrentIndex(num)
        except ValueError as ve:
            editor.addItem(value)
            if self.to_humanize:
                self.humanized_str_items.append(value)
                num = len(self.humanized_str_items) - 1
            else:
                self.items.append(value)
                num = len(self.items) - 1
            editor.setCurrentIndex(num)
            logger.debug(f"New option added for {self.header_labels[self.col_index]}")

    def setModelData(self, editor, model, index):
        if self.to_humanize:
            index_ = editor.currentIndex()
            value = self.items[index_]
        else:
            value = editor.currentText()
        model.setData(index, value, QtCore.Qt.EditRole)
        # self.c.data_changed.emit(index, index, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class LineEditDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, name: typing.Union[None, str]):
        super(LineEditDelegate, self).__init__()
        self._name = name  # the column name in model
        self._pen_color = Qt.black
        self._opening_time = datetime.today().replace(hour=9, minute=15, second=0, microsecond=0)
        self._closing_time = datetime.today().replace(hour=15, minute=30, second=0, microsecond=0)
        self._fmt_time_string = '%H.%M.%S'

    def createEditor(self, parent: QtWidgets.QWidget, option: 'QtWidgets.QStyleOptionViewItem',
                     index: QtCore.QModelIndex) -> QtWidgets.QWidget:
        editor = QtWidgets.QLineEdit(parent)
        editor.setMaxLength(8)
        editor.setInputMask("99.99.99")
        return editor

    def setEditorData(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex) -> None:
        value = index.data(Qt.DisplayRole)
        if isinstance(editor, QtWidgets.QLineEdit):
            try:
                dt_inp_time = datetime.strptime(value, self._fmt_time_string).replace(year=datetime.today().year,
                                                                                      month=datetime.today().month,
                                                                                      day=datetime.today().day)
                if self._opening_time <= dt_inp_time <= self._closing_time:
                    self._pen_color = Qt.black
                    editor.setText(value)
                else:
                    self._pen_color = Qt.darkRed
                    editor.setText("")
                    logger.warning(f"Entered time must be within {self._opening_time.strftime('%H:%M')} and"
                                   f" {self._closing_time.strftime('%H:%M')}")
                    return
            except ValueError as ve:
                logger.warning(f"Invalid time for {self._name}, {ve.__str__()}")
                self._pen_color = Qt.darkRed

    def paint(self, painter: QtGui.QPainter, option: 'QtWidgets.QStyleOptionViewItem',
              index: QtCore.QModelIndex) -> None:
        option = QtWidgets.QStyleOptionViewItem(option)
        _pen = QtGui.QPen()
        _pen.setColor(self._pen_color)
        _pen.setWidth(2)
        painter.setPen(_pen)
        painter.drawRect(option.rect)
        super().paint(painter, option, index)

    def commit_editor(self):
        editor = self.sender()
        self.commitData.emit(editor)  # save the editor's current state to the model

    def setModelData(self, editor, model, index):
        value = editor.text()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class StrategyViewModel(QtCore.QAbstractTableModel):
    """Main model for Strategy Table"""

    def __init__(self, header_labels, data=None):
        super(StrategyViewModel, self).__init__()
        self.header_labels = header_labels
        self._data = data or []

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        data_ = self._data[index.row()][index.column()]
        if role == Qt.DisplayRole:
            if data_ in (None, 'None'):
                return 0
            return data_
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        if role == Qt.EditRole:
            return data_

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole and value != "":
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index, (QtCore.Qt.DisplayRole,))
            _column_name = self.header_labels[index.column()]
            if _column_name == 'Symbol Name':
                _index = self.index(index.row(), self.header_labels.index('expiry'))
                self.dataChanged.emit(_index, _index, (QtCore.Qt.DisplayRole,))
            elif _column_name == 'exchange':
                symb_model_index = self.index(index.row(), self.header_labels.index('Symbol Name'))
                self.dataChanged.emit(symb_model_index, symb_model_index, (QtCore.Qt.DisplayRole,))

                atm_model_index = self.index(index.row(), self.header_labels.index('atm_strike'))
                self.dataChanged.emit(atm_model_index, atm_model_index, (QtCore.Qt.DisplayRole,))
            return True
        return False

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def insert_row(self, data, position, rows=1):
        self.beginInsertRows(QtCore.QModelIndex(), position, position + rows - 1)
        self._data.append(data)
        self.endInsertRows()

    def append_row(self, data):
        """data is default data for each row"""
        self.insert_row(data, self.rowCount())

    def get_data(self) -> typing.List[typing.List]:
        return self._data

    def remove_row(self, row: int):
        if row < self.rowCount():
            self.beginRemoveRows(QtCore.QModelIndex(), row, row)
            data_list = self._data.pop(row)
            self.endRemoveRows()
            return data_list[self.header_labels.index('Symbol Name')]  # returns the symbol-name
        return False

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._data)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        if self._data:
            return len(self._data[0])
        else:
            return len(self.header_labels)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return humanize_string(str(self.header_labels[section]).upper())
            if orientation == Qt.Vertical:
                return str(section).upper()
