from datetime import datetime

import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

from Libs.UI import strategy_builder_dialog
from Libs.UI.Models_n_Delegates import Model__combobox_expiry
from Libs.globals import *


class StrategyBuilder(QtWidgets.QDialog):
    def __init__(self, name_exp_df: pd.DataFrame, parent=None):
        super(StrategyBuilder, self).__init__()
        self.name_exp_df = name_exp_df

        self.ui = strategy_builder_dialog.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowModality(Qt.ApplicationModal)

        self.ui.label_strategy_title.setText("<h2>Pyramiding Strategy Builder</h2>")
        self.vBoxScrollLayout = QtWidgets.QVBoxLayout()
        self.ui.scrollAreaWidgetContents.setLayout(self.vBoxScrollLayout)

        # ---------- set default values ----------
        self.ui.timeEdit_end_time.setTime(QtCore.QTime(15, 29, 00))

        self.ui.label_frequency.setText("Interval")
        self.ui.label_start_time.setText("Entry Time - start:")
        self.ui.label_end_time.setText("Entry Time - end:")

        self.is_validity = False
        self.defined_dict = {}
        self.export_values = []

        self.default_row = [('Transaction_Type', 'Sell'),
                            ('Exit_Time', '15.30.00'),
                            ('Expiry Date', ''),
                            ("Symbol Name", "NIFTY"),
                            ('CE_Instrument', 'ATM'),
                            ('PE_Instrument', 'ATM'),
                            ("Buy_Ltp_Percent", 0.5),
                            ("Sell_Ltp_Percent", 0.5),
                            ("Wait_Time", 30),
                            ("No. of lots", 1),
                            ("CE_target", 80),
                            ("PE_target", 80),
                            ("CE_Stoploss", 80),
                            ("PE_Stoploss", 80),
                            ("CE_TSL", 50),
                            ("PE_TSL", 80),
                            ("stoploss_type", "Percentage"),
                            ("target_type", "Percentage")]
        self.default_values = app_data.DEFAULT_DATA_ALL_FIELDS
        self.atm_choices = [f"ATM-{x}" for x in range(10, 0, -1)] + ['ATM'] + [f"ATM+{x}" for x in range(1, 11)]
        self.ui.pushButton_confirm.clicked.connect(self.confirm_pressed)
        self.ui.pushButton_close.clicked.connect(self.cancel_pressed)
        # self.ui.scrollArea.hide()  # hide scroll area, as it is not used in this version

        # ------------- add fields for required columns -----------------
        required_cols = ['Transaction_Type', 'Symbol Name', 'CE_Instrument', 'PE_Instrument',
                         "No. of lots", "Exit_Time"]
        for col in required_cols:
            if col in self.default_values:
                is_choice_field = col in ('CE_Instrument', 'PE_Instrument', 'Transaction_Type', 'Symbol Name')
                default_value = None
                if is_choice_field:
                    if col in ('CE_Instrument', 'PE_Instrument'):
                        options = self.atm_choices
                        default_value = "ATM"
                    elif col == 'Transaction_Type':
                        options = ['Buy', 'Sell']
                    elif col == 'Symbol Name':
                        options = app_data.SYMBOL_LIST
                        default_value = app_data.SYMBOL_LIST[0]
                        col2 = "Expiry Date"
                        self.options_model = Model__combobox_expiry.OptionsModel(name_exp_df)
                        # ------------ process data -------------
                        _unique_symb_names = app_data.SYMBOL_LIST
                        self.options_model.update_model(
                            _unique_symb_names[0])  # explicitly update model with current selection

                        # ----------- add unique symbol names to combo box -------------
                        self.add_predefined_option(col, self.default_values[col]['default_value'], QtWidgets.QComboBox,
                                                   options, default_value=default_value)
                        # ----------- add expiry date combo box -----------------
                        symbol_name_combobox = self.defined_dict['Symbol Name']
                        symbol_name_combobox.currentIndexChanged[str].connect(lambda x: self.options_model.update_model(x))
                        self.add_predefined_option(col2, self.default_values[col2]['default_value'], QtWidgets.QComboBox)
                        expiry_date_combobox = self.defined_dict['Expiry Date']
                        expiry_date_combobox.setModel(self.options_model)
                        continue  # don't proceed further to add another widget

                    self.add_predefined_option(col, self.default_values[col]['default_value'], QtWidgets.QComboBox, options,
                                               default_value=default_value)
                else:
                    self.add_predefined_option(col, str(self.default_values[col]['default_value']), QtWidgets.QLineEdit)

    def add_predefined_option(self, name: str, value: typing.AnyStr, widget: typing.Callable, options: typing.List = None,
                              default_value: str = None):
        if not value:
            value = ""
        option_widget = QtWidgets.QWidget()
        hBoxOptionLayout = QtWidgets.QHBoxLayout()
        hBoxOptionLayout.setContentsMargins(0, 0, 0, 0)
        option_widget.setLayout(hBoxOptionLayout)

        option_label = QtWidgets.QLabel(option_widget)
        option_label.setText(name)

        optionEntryField = widget(option_widget)
        if widget == QtWidgets.QLineEdit:
            optionEntryField.setText(value)
        elif widget == QtWidgets.QComboBox:
            optionEntryField: QtWidgets.QComboBox
            if options:
                optionEntryField.addItems(options)
                index = 0
                if default_value and default_value in options:
                    index = options.index(default_value)
                optionEntryField.setCurrentIndex(index)

        hBoxOptionLayout.addWidget(option_label)
        hBoxOptionLayout.addWidget(optionEntryField)

        self.vBoxScrollLayout.addWidget(option_widget)
        self.defined_dict.update({name: optionEntryField})

    def confirm_pressed(self):
        start_time = self.ui.timeEdit_start_time.time()
        end_time = self.ui.timeEdit_end_time.time()
        start_time_str = start_time.toString()
        end_time_str = end_time.toString()
        dt_tm_start_time = datetime.strptime(start_time_str, "%H:%M:%S")
        dt_tm_end_time = datetime.strptime(end_time_str, "%H:%M:%S")
        freq = self.ui.spinBox_freq.value()
        messageBox = QtWidgets.QMessageBox()
        if freq == 0:
            messageBox.warning(None, "Invalid Input", "Interval cannot be Zero", QtWidgets.QMessageBox.Ok)
            return
        if start_time >= end_time:
            messageBox.warning(None, "Invalid Input", "start time has to be lesser than end time",
                                          QtWidgets.QMessageBox.Ok)
            return
        max_freq = (dt_tm_end_time - dt_tm_start_time).seconds // 60
        if max_freq < freq:
            messageBox.warning(None, "Invalid Input",
                                          f"Maximum allowed interval for given start and end time is : "
                                          f"<b>{max_freq}</b>", QtWidgets.QMessageBox.Ok)
            return
        time_range = pd.date_range(start_time_str, end_time_str, freq=f"{freq}T")
        entry_times = [x.strftime("%H.%M.%S") for x in time_range]
        self.export_values = []
        for entry_time in entry_times:
            row_values = []
            for key, values in self.default_row:
                widget = self.defined_dict.get(key)
                if type(widget) == QtWidgets.QLineEdit:
                    text = widget.text()
                elif type(widget) == QtWidgets.QComboBox:
                    text = widget.currentText()
                if key in self.defined_dict:
                    row_values.append((key, text))
                else:
                    row_values.append((key, values))
            row_values.append(("Entry_Time", entry_time))

            self.export_values.append(
                row_values
            )
        self.accept()
        return

    def cancel_pressed(self):
        self.export_values = None
        self.reject()
        return

    def exec_(self) -> typing.List[typing.List[typing.Tuple]]:
        super(StrategyBuilder, self).exec_()
        return self.export_values
