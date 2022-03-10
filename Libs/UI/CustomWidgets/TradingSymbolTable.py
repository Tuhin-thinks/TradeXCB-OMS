from copy import deepcopy

import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui

from Libs.Concurrency import CSV_Loader as Loader
from Libs.Files.TradingSymbolMapping import StrategiesColumn
from Libs.UI.Models_n_Delegates import Model__StrategyTable
from Libs.globals import *

logger = exception_handler.getFutureLogger(__name__)


class StrategyView(QtWidgets.QTableView):
    def __init__(self, strategy: str, header_labels: typing.Union[typing.Iterable, None] = None, global_parent=None):
        super(StrategyView, self).__init__()
        self.name_expiry_df: typing.Union[None, pd.DataFrame] = None
        self.global_parent = global_parent
        self.default_data = []
        self.header_labels = header_labels or []
        self.strategy = strategy
        self.setMinimumHeight(250)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.setCornerButtonEnabled(False)

        self.header_labels = StrategiesColumn.strategy_dict[strategy]
        self._model = Model__StrategyTable.StrategyViewModel(self.header_labels)
        self.setModel(self._model)

        self.resizeColumnsToContents()
        self.increase_col_space()

        # ------- initial data setup ------------
        self.load_symbol_names()
        self.fill_default_data()

        self.setPalette(self.global_parent.palette())

        for child in self.findChildren(QtWidgets.QWidget):
            child.setPalette(global_parent.palette())

    def increase_col_space(self) -> None:
        extra_space_factor = 5
        for col in range(self._model.columnCount()):
            if col == self.header_labels.index("Symbol Name"):
                self.setColumnWidth(col, 200)
            elif col in (0, 3, 4, 7, 8, 9, 11, 12, 13, 14, 15, 17, 19, 22, 23, 24, 27, 29, 30):
                self.setColumnWidth(col, 150)
            else:
                col_width = self.columnWidth(col)
                if col_width < 100:
                    col_width += extra_space_factor
                    self.setColumnWidth(col, col_width)

    def load_symbol_names(self):
        self.loader_thread = QtCore.QThread(self)
        self.loader_obj = Loader.SymbLoader()
        self.loader_obj.loaded.connect(self.data_loaded)
        self.loader_obj.completed.connect(self.destroy_loader)
        self.loader_obj.moveToThread(self.loader_thread)
        self.loader_thread.started.connect(self.loader_obj.load_symbol_names)
        self.loader_thread.start()

    def load_saved_values(self, table_data: typing.List[typing.List]):
        for row in table_data:
            self.append_row(row)

    @QtCore.pyqtSlot(object)
    def data_loaded(self, args: tuple):
        """
        args: tuple(symbol names list, check_df)
        check_df :Dataframe object, with columns [symbolNames, exchangeString]
        """
        data = args[0]  # list of symbol names
        instruments_df = args[1]

        # ----- create list of symbol names for nse stock options ----------
        filters = (instruments_df['exchange'] == 'NSE') & (instruments_df['instrument_type'] == 'EQ') &\
                  (instruments_df['name'] != '')
        nse_options_df = instruments_df[filters]

        self.name_expiry_df = instruments_df[['name', 'expiry', 'exchange']]
        symbol_col = self.header_labels.index('Symbol Name')
        self._symb_names_delegate = Model__StrategyTable.ChoiceBoxDelegate(self, self.name_expiry_df, self.header_labels, symbol_col,
                                                                           data_dict={'nse_options_df': nse_options_df})
        self.setItemDelegateForColumn(symbol_col, self._symb_names_delegate)

        exp_col = self.header_labels.index('expiry')
        self._delegate_exp_date = Model__StrategyTable.ChoiceBoxDelegate(self,
                                                                         None, self.header_labels, exp_col,
                                                                         extra_choices=self.name_expiry_df)
        self.setItemDelegateForColumn(exp_col, self._delegate_exp_date)
        logger.debug("Delegates added")

    def destroy_loader(self):
        try:
            self.loader_thread.quit()
            self.loader_thread.wait(100)
            while True:
                try:
                    self.loader_obj.disconnect()
                except TypeError:
                    break
        except Exception as loader_exec:
            logger.critical(f"cannot terminate loader thread, {loader_exec.__str__()}", exc_info=True)

    def fill_default_data(self):
        """fill row with default data"""
        no_errors_ = True
        self.default_data = []
        for column_name in self.header_labels:
            try:
                col_index = self.header_labels.index(column_name)
                column_info_dict = app_data.DEFAULT_DATA_ALL_FIELDS.get(column_name)
                if column_info_dict:  # if some columns are removed from default values json, this will not break the code
                    is_dropdown = column_info_dict.get("dropdown")  # value should be either true/false
                    if is_dropdown:
                        choices = column_info_dict.get("dropdown_values") or []
                        self.setItemDelegateForColumn(col_index,
                                                      Model__StrategyTable.ChoiceBoxDelegate(self,
                                                                                             list(map(str, choices)),
                                                                                             self.header_labels,
                                                                                             col_index))
                if column_name == "Symbol Name":
                    self.default_data.append("NIFTY")  # default symbol name
                    continue
                elif column_name == "atm_strike":
                    self.default_data.append("ATM CE")
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

                    self.setItemDelegateForColumn(col_index,
                                                  Model__StrategyTable.ChoiceBoxDelegate(self,
                                                                                         list(map(str, choices)),
                                                                                         self.header_labels,
                                                                                         col_index))
                    continue

                self.default_data.append(str(column_info_dict.get("default_value")))
            except Exception as e:
                no_errors_ = False
                logger.warning(e.__str__() + f'For column name: {column_name}', exc_info=True)

        if no_errors_:
            logger.info(f"New strategy added: {self.strategy}")

    def remove_row(self, row: int):
        res = self._model.remove_row(row)
        return res

    def insert_row(self, customizations: typing.Union[typing.List[typing.List[typing.Tuple]], None] = None):
        if customizations:
            for row in customizations:
                _copy_data = dict(zip(self.header_labels, self.default_data.copy()))
                for _to_chg_key, _custom_value in row:
                    _copy_data[_to_chg_key] = _custom_value
                _symbol_name = _copy_data.get("Symbol Name")
                try:
                    if "expiry" not in _copy_data:
                        _copy_data["expiry"] = self.name_expiry_df[self.name_expiry_df.name ==
                                                                        _symbol_name].iloc[0].expiry
                except (KeyError, IndexError, NameError):
                    pass
                self._model.append_row(list(_copy_data.values()))
        else:
            data_dict = dict(zip(self.header_labels, self.default_data))
            # sort by recent expiry date for the given symbol name and exchange
            try:
                expiry_date = pd.to_datetime(
                    self.name_expiry_df[
                        (self.name_expiry_df.name == data_dict['Symbol Name']) &
                        (self.name_expiry_df.exchange == data_dict['exchange'])
                    ].expiry).sort_values().unique()[0]
                expiry_str = pd.to_datetime(expiry_date).strftime("%Y-%m-%d")
                data_dict["expiry"] = expiry_str
            except (IndexError, ValueError, TypeError):
                logger.warning(f"Expiry date not found for symbol: {data_dict['Symbol Name']} and "
                               f"exchange: {data_dict['exchange']}")
            self._model.append_row(list(data_dict.values()))

    def append_row(self, data_row_list):
        """
        Receives a tuple: data_row_list: List[str], status: bool

        :param data_row_list: list, list of table rows
        :return: None
        """
        self._model.append_row(data_row_list)

    def name(self):
        """get strategy name"""
        return self.strategy

    def save(self) -> typing.List[typing.Dict]:
        """
        Gather data from UI and save to excel
        :return strategy name, list of rows (dicts)
        """
        return_data = self._model.get_data()
        complete_data = []
        default_fields_data_all = deepcopy(app_data.DEFAULT_DATA_ALL_FIELDS)
        for row in return_data:
            to_save = dict()
            # to_save[key] = value["default_value"]
            to_save.update(dict(zip(self.header_labels + ['strategy_name'], row + [self.strategy])))
            complete_data.append(to_save)

        return complete_data

    def setPalette(self, palette: QtGui.QPalette) -> None:
        for child in self.findChildren((QtWidgets.QComboBox, QtWidgets.QLineEdit, QtWidgets.QLabel)):
            child.setPalette(self.global_parent.palette())
        super(StrategyView, self).setPalette(palette)
