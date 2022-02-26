from Libs.icons_lib import Icons as icons
from Libs.UI.CustomWidgets import Common_opt_chain_Table
import Libs.UI.home
from PyQt5 import QtCore, QtGui, QtWidgets


class DisplayFrame(QtWidgets.QWidget):
    export_instruments_data = QtCore.pyqtSignal(tuple)

    def __init__(self, table_name, header_labels, parent, global_parent):
        super(DisplayFrame, self).__init__(parent=parent)
        self._parent = parent
        self.table_name = table_name
        self.global_parent = global_parent
        self.global_parent_ui: 'Libs.UI.home.Ui_MainWindow' = global_parent.ui
        self.header_labels = header_labels
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.table_view = Common_opt_chain_Table.OptChainAnalysis_TableView(self.table_name, header_labels, self,
                                                                            self.global_parent)
        self.table_view.export_instruments_data.connect(global_parent.accept_export_instruments_data)
        temp_ = self.global_parent.custom_style_sheet.tableview("dark")
        self.table_view.setStyleSheet(temp_)
        self.table_view.update()
        self.table_view.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.table_proxy_model_instance = self.table_view.get_model_instance()

        self.base_layout = QtWidgets.QGridLayout(self)

        # create button panel to add buttons (close strategy_name, add symbol, delete symbol)
        if table_name == "SIGNALS":
            # tableView NIFTY/BANKNIFTY
            self.table_view_n_bn = Common_opt_chain_Table.OptChainAnalysis_TableView(self.table_name,
                                                                                     header_labels,
                                                                                     self.global_parent_ui.frame_signals_holder_filtered,
                                                                                     self.global_parent)
            self.table_view_n_bn.setStyleSheet(temp_)
            self.table_view_n_bn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.table_proxy_model_instance = self.table_view_n_bn.get_model_instance()
            self.frame_button_panel = self.global_parent_ui.frame_signals_button_panel
            self.global_parent_ui.gridLayout_signals_tab.addWidget(self.frame_button_panel, 0, 0, 1, 1)
        else:
            self.frame_button_panel = QtWidgets.QFrame(self)
            self.base_layout.addWidget(self.frame_button_panel, 0, 0, 1, 1)

        self.button_panel_layout = QtWidgets.QGridLayout(self.frame_button_panel)
        self.button_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.frame_button_panel.setMaximumHeight(35)

        self.button_export_table_data = QtWidgets.QPushButton(
            icons.get('export-icon'), "Save as Excel",
            self.frame_button_panel)

        for col, button in enumerate((self.button_export_table_data,), 1):
            self.button_panel_layout.addWidget(button, 0, col, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
            button.setMaximumWidth(150)
            button.setMinimumHeight(35)
            button.setPalette(self.global_parent.palette())  # for maintaining persistent theme coloring

        # create frame to hold the strategy_name table
        self.frame_table_holder = QtWidgets.QFrame(self)
        self.base_layout.addWidget(self.frame_table_holder, 1, 0, 1, 1)
        self.table_holder_layout = QtWidgets.QVBoxLayout(self.frame_table_holder)
        self.table_holder_layout.setContentsMargins(0, 0, 0, 0)
        self.table_holder_layout.setSpacing(0)
        self.table_holder_layout.addWidget(self.table_view)

        # ============ button click signals ============
        self.button_export_table_data.clicked.connect(self.save_table_data)

        if self.table_name == 'SIGNALS':
            # layout to hold filtered table
            self.base_layout_n_bn = QtWidgets.QGridLayout(self.global_parent_ui.frame_signals_holder_filtered)
            self.base_layout_n_bn.addWidget(self.table_view_n_bn, 0, 0, 1, 1)
            self.button_nifty_bank_nifty = QtWidgets.QPushButton("NIFTY/BANKNIFTY", self.frame_button_panel)
            self.button_nifty_bank_nifty.setMaximumWidth(150)
            self.button_nifty_bank_nifty.setMinimumWidth(140)
            self.button_nifty_bank_nifty.setMinimumHeight(35)
            self.button_nifty_bank_nifty.setStyleSheet(
                self.global_parent.custom_style_sheet.get_dark_style('pushbutton'))
            self.button_panel_layout.addWidget(self.button_nifty_bank_nifty, 0, 2,
                                               QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
            self.button_nifty_bank_nifty.clicked.connect(self.toggle_filtered_table)
            self.global_parent.palette_sensitive_widgets.append(self.table_view_n_bn)

        self.global_parent.palette_sensitive_widgets.append(self.table_view)
        self.setPalette(self.global_parent.palette())

    def toggle_filtered_table(self):
        """Display NIFTY/BANKNIFTY table or the complete table"""
        if self.button_nifty_bank_nifty.text() == "Show All":
            self.global_parent.pause_stylesheet_timer = True
            self.global_parent_ui.stackedWidget_signals.slideInPrev()
            self.button_nifty_bank_nifty.setText("NIFTY/BANKNIFTY")
            self.global_parent.pause_stylesheet_timer = False
            return
        self.global_parent.pause_stylesheet_timer = True
        self.global_parent_ui.stackedWidget_signals.slideInNext()
        self.button_nifty_bank_nifty.setText("Show All")
        self.global_parent.pause_stylesheet_timer = False

    def update_model_data(self, df):
        """update table's model with new dataframe :param: df"""
        self.table_view.update_model_data(df)
        if self.table_name == "SIGNALS":
            filtered_df = df[(df.tradingsymbol_CE.str.contains("NIFTY")) |
                             (df.tradingsymbol_CE.str.contains("BANKNIFTY"))]
            self.table_view_n_bn.update_model_data(filtered_df)

    def save_table_data(self):
        """Calls model's save data implementation to show a file dialog to save data"""
        self.table_view.save_data()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """make style aware"""
        super().paintEvent(event)
        opt = QtWidgets.QStyleOption()
        p = QtGui.QPainter(self)
        s = self.style()
        s.drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, p, self)
