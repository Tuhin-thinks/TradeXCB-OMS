from datetime import datetime

import pandas as pd
from PyQt5 import QtWidgets, QtGui, QtCore

from Libs.Files.TradingSymbolMapping import StrategiesColumn
from Libs.UI.CustomWidgets.StrategyBuilderDialog import StrategyBuilder
from Libs.UI.CustomWidgets.TradingSymbolTable import StrategyView
from Libs.UI.Interact import message
from Libs.globals import *
from Libs.icons_lib import Icons as icons


class strategy_frame(QtWidgets.QWidget):
    """
    Each strategy table is inside a strategy frame,
    it also holds the buttons and labels for adding, removing and saving table
    and a label for showing strategy name.
    """
    delete_strategy = QtCore.pyqtSignal()

    def __init__(self, strategy_table: 'StrategyView', parent=None, to_add_default_rows=False):
        super(strategy_frame, self).__init__(parent=parent)
        self.strategy_table = strategy_table
        self._parent = parent

        self.base_layout = QtWidgets.QGridLayout(self)

        # create button panel to add buttons (close strategy_name, add symbol, delete symbol)
        self.frame_button_panel = QtWidgets.QFrame(self)
        self.base_layout.addWidget(self.frame_button_panel)
        self.button_panel_layout = QtWidgets.QGridLayout(self.frame_button_panel)

        self.label_strategy_name = QtWidgets.QLabel(self.strategy_table.name().upper(), self.frame_button_panel)
        self.button_panel_layout.addWidget(self.label_strategy_name, 0, 0, 1, 1)
        self.label_strategy_name.setPalette(self._parent.palette())

        self.button_delete_strategy = QtWidgets.QPushButton(icons.get('close-strategy_name-icon'), f"Delete Strategy",
                                                            self.frame_button_panel)
        self.add_symbol = QtWidgets.QPushButton(icons.get('add-symbol-icon'), "Add Symbol", self.frame_button_panel)
        self.delete_symbol = QtWidgets.QPushButton(icons.get('delete-icon'), "Delete Symbol", self.frame_button_panel)

        for col, button in enumerate((self.button_delete_strategy, self.add_symbol, self.delete_symbol), 1):
            self.button_panel_layout.addWidget(button, 0, col)
            button.setMaximumWidth(200)
            button.setMinimumHeight(35)
            button.setPalette(self._parent.palette())  # for maintaining persistent theme coloring

        # create frame to hold the strategy_name table
        self.frame_table_holder = QtWidgets.QFrame(self)
        self.base_layout.addWidget(self.frame_table_holder)
        self.table_holder_layout = QtWidgets.QVBoxLayout(self.frame_table_holder)
        self.table_holder_layout.addWidget(self.strategy_table)

        self.button_delete_strategy.clicked.connect(self.confirm_delete)
        self.add_symbol.clicked.connect(self.add_symbol_row)
        self.delete_symbol.clicked.connect(self.delete_symbol_row)
        self.setPalette(self._parent.palette())

        if to_add_default_rows:  # only True, when manual addition is happening (and table is empty)
            _customizations: typing.List[typing.List[typing.Tuple]] = StrategiesColumn.strategy__customization_dict.get(
                self.strategy_table.name()
            )
            if _customizations:
                self.strategy_table.insert_row(_customizations)
            elif "pyramiding" in self.strategy_table.name().lower():
                self.launch_builder()

    def launch_builder(self):
        instr_df = pd.read_csv(settings.DATA_FILES.get('INSTRUMENTS_CSV'))
        instr_df['days2expire'] = (pd.to_datetime(instr_df.expiry).dt.date - datetime.today().date()).dt.days
        instr_df = instr_df[instr_df['days2expire'] < 120]
        name_exp_df = instr_df[instr_df['name'].isin(app_data.SYMBOL_LIST)].loc[:, ["name", "expiry"]]
        row_collection = StrategyBuilder(name_exp_df).exec_()
        if row_collection:
            self.strategy_table.insert_row(row_collection)

    @QtCore.pyqtSlot()
    def add_symbol_row(self):
        self.strategy_table.insert_row(None)

    @QtCore.pyqtSlot()
    def delete_symbol_row(self):
        self.strategy_table: QtWidgets.QTableView
        for model_index in self.strategy_table.selectedIndexes():
            row_index = model_index.row()
            res = self.strategy_table.remove_row(row_index)  # res can be False or SymbolName (returned from model)
            if res is not False:
                message.show_message(self, "Success", f"<b>row: {row_index}</b> removed successfully", "info")
            break

    @QtCore.pyqtSlot()
    def confirm_delete(self):
        res = QtWidgets.QMessageBox().question(self, "Confirm Delete Strategy ?",
                                               f"Are you sure you want to delete strategy: {self.strategy_table.name()}",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.Yes)
        if res == QtWidgets.QMessageBox.Yes:
            self.delete_strategy.emit()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """make style aware"""
        super().paintEvent(event)
        opt = QtWidgets.QStyleOption()
        p = QtGui.QPainter(self)
        s = self.style()
        s.drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, p, self)
