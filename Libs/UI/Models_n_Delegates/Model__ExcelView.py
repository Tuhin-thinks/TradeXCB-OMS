import datetime

import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt

from Libs.Utils import string_view_manipulator as str_man
from Libs.globals import *

logger = exception_handler.getFutureLogger(__name__)


class ExcelViewModel(QtCore.QAbstractTableModel):
    def __init__(self, header_labels, data=None):
        super(ExcelViewModel, self).__init__()
        self.header_labels = header_labels
        self._data = data or pd.DataFrame(columns=self.header_labels)
        self.fresh_highlight_bg = None
        self.fresh_highlight_fg = None
        self.max_col_values = {}
        self.min_col_values = {}

        self.num_c_bg_props = {'h': 240, 's': 170}  # blue for high values
        self.num_c_bg2_props = {'h': 0, 's': 255}  # red for low values

    def clear(self):
        self.beginResetModel()
        self._data = pd.DataFrame(columns=self.header_labels)
        self.max_col_values = {}
        self.min_col_values = {}
        self.endResetModel()

    def item(self, row: int, col: int):
        """to get each item, by row and column index from model"""
        if 0 <= row < len(self._data) and 0 <= col < len(self._data[0]):
            return self.data(self.index(row, col), Qt.DisplayRole)

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            _data = str(self._data.iat[index.row(), index.column()])
            if _data.lower() in ("none", "nat", "nan"):  # replace these keywords by empty string
                _data = ""
            try:
                current_header = self.header_labels[index.column()].lower()
                if 'timestamp' in current_header:  # convert float timestamp to datetime string
                    _data = str(datetime.datetime.fromtimestamp(float(_data)))
            except ValueError:  # not all timestamps are decimal values
                pass
            if "time" in self.header_labels[index.column()].lower():  # remove microseconds from timestamps
                return _data.split('.')[0] if '.' in _data else _data
            return str_man.is_match_decimal(_data)
        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter

        # ---------------------- BACKGROUND COLORS --------------------
        if role == Qt.BackgroundColorRole:
            text = self._data.iat[index.row(), index.column()]
            header_name = self.header_labels[index.column()]
            if "fresh" in str(text).lower():
                self.fresh_highlight_bg = index.column()
                return QtGui.QColor(255, 191, 0)  # amber
            elif 0 < index.column() < len(self.header_labels) and\
                    "fresh" in str(self._data.iat[index.row(), index.column()-1]).lower() and \
                    "time" in header_name.lower() and\
                    self.fresh_highlight_bg and self.fresh_highlight_bg == (index.column() - 1):
                self.fresh_highlight_bg = None
                return QtGui.QColor(255, 191, 0)  # amber

            # ------------------------ crossover color maps ----------------------
            above_below_check_cols = ("delta_crossover", "vwap_crossover")
            if any((x in header_name.lower() for x in above_below_check_cols)) and "below" in text.lower():
                return QtGui.QColor(255, 0, 0)  # deep-red

            elif any((x in header_name.lower() for x in above_below_check_cols)) and "above" in text.lower():
                return QtGui.QColor(107, 255, 8)  # light-green (to be reviewed)

            # ---------------- bearish bullish color maps -----------------
            if "mid bearish" in str(text).lower():
                return QtGui.QColor(255, 85, 0)  # light-red
            elif 'bearish' in str(text).lower():
                return QtGui.QColor(255, 0, 0)  # deep-red
            elif 'mild bullish' in str(text).lower():
                return QtGui.QColor(107, 255, 8)  # light-green (to be reviewed)
            elif 'bullish' in str(text).lower():
                return QtGui.QColor(0, 156, 0)  # deep-green

            # ---------------- numerical column heat maps ---------------
            if header_name.lower() in app_data.numerical_columns:
                max_col_value = self.max_col_values.get(header_name.lower())
                min_col_value = self.min_col_values.get(header_name.lower())
                _low_value = False
                try:
                    if not max_col_value:
                        max_value = self._data[header_name].max()
                        min_value = self._data[header_name].min()
                        self.max_col_values[header_name.lower()] = max_value
                        self.min_col_values[header_name.lower()] = min_value
                        max_col_value = self.max_col_values.get(header_name.lower())
                        min_col_value = self.min_col_values.get(header_name.lower())
                    intensity_ratio = np.divide(np.subtract(float(text), min_col_value), np.subtract(max_col_value, min_col_value))

                    hsv_value = intensity_ratio * 255
                    if pd.isna(hsv_value):
                        hsv_value = 0
                    if intensity_ratio < 0.5:
                        _low_value = True
                except (ValueError, TypeError) as e:
                    hsv_value = 1
                    _low_value = True

                if _low_value:
                    hsv_c_tuple = (self.num_c_bg2_props['h'], self.num_c_bg2_props['s'], int(hsv_value))
                else:
                    hsv_c_tuple = (self.num_c_bg_props['h'], self.num_c_bg_props['s'], int(hsv_value))
                return QtGui.QColor.fromHsv(*hsv_c_tuple)

        # --------------- FONT COLORS --------------------
        if role == Qt.ForegroundRole:
            text = self._data.iat[index.row(), index.column()]
            header_name = self.header_labels[index.column()]
            if "fresh" in str(text).lower():
                self.fresh_highlight_fg = index.column()
                return QtGui.QColor(0, 0, 0)  # black

            elif "time" in header_name.lower() and self.fresh_highlight_fg and self.fresh_highlight_fg == (
                    index.column() - 1):
                self.fresh_highlight_fg = None
                return QtGui.QColor(0, 0, 0)  # black

            # ------------------ CROSSOVER COLOR MAPS --------------------
            above_below_check_cols = ("delta_crossover", "vwap_crossover")
            if any((x in header_name.lower() for x in above_below_check_cols)) and "below" in text.lower():
                return QtGui.QColor(255, 255, 255)  # black

            elif any((x in header_name.lower() for x in above_below_check_cols)) and "above" in text.lower():
                return QtGui.QColor(0, 0, 0)  # black

            # ------------------ BEARISH-BULLISH COLOR MAPS --------------------
            if "mid bearish" in str(text).lower():
                return QtGui.QColor(0, 0, 0)  # black
            elif 'bearish' in str(text).lower():
                return QtGui.QColor(0, 0, 0)  # black
            elif 'mild bullish' in str(text).lower():
                return QtGui.QColor(0, 0, 0)  # black
            elif 'bullish' in str(text).lower():
                return QtGui.QColor(0, 0, 0)  # black

            # ---------------- numerical column heat maps [font color] ---------------
            if header_name.lower() in app_data.numerical_columns:
                return QtGui.QColor(255, 255, 255)  # black

    def dataAt(self, row: int, col: int):
        return self.data(self.index(row, col), Qt.DisplayRole)

    def get_data(self):
        """Gets the model's complete data [as dataframe]"""
        return self._data

    def populate(self, df):
        """Reset the model"""
        self.beginResetModel()
        self._data = df.copy()
        self.max_col_values = {}
        self.endResetModel()

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._data)

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self.header_labels)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                header_string = str_man.humanize_string(str(self.header_labels[section]).upper())
                header_string = str_man.map_shorts(header_string)
                return header_string
            if orientation == Qt.Vertical:
                return str(section)
