import pandas as pd
from Libs.globals import *
from Libs.UI.CustomWidgets import PopupList
from Libs.UI.Models_n_Delegates import Model__PositionsTable
from Libs.UI.Proxies import TableProxies
from Libs.UI.Utils import FS__EventHandLer
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

logger = exception_handler.getFutureLogger(__name__)


class PositionsView(QtWidgets.QTableView):
    def __init__(self, parent, global_parent):
        super(PositionsView, self).__init__(parent=parent)
        self.column_index = None
        self.global_parent = global_parent
        self.filter_listWidget = None
        # ============= LABEL CHANGES ===============
        global_parent.ui.label_optionscalc_l.setText("Buy Qty : ")
        global_parent.ui.label_options_cal_c.setText("Sell Qty : ")
        global_parent.ui.label_options_calc_r.setText("Profit&Loss : ")

        custom_font = QtGui.QFont(self.font().family(), (12 if os.name == 'posix' else 11))
        self.global_parent.ui.label_optionscalc_l.setFont(custom_font)
        self.global_parent.ui.label_options_cal_c.setFont(custom_font)
        self.global_parent.ui.label_options_calc_r.setFont(custom_font)

        # shortcut to resize cells to contents
        size_adjust_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+R"), self)
        size_adjust_shortcut.activated.connect(self.resizeColumnsToContents)

        self.setSelectionBehavior(self.SelectRows)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.watch_loc = settings.DATA_FILES.get("POSITIONS_FILE_PATH")  # check for filenames positions log
        self.handler = FS__EventHandLer.Position_CSVModifyHandler(self.watch_loc)
        self.handler.file_changed.connect(self.reset_model_data)
        self.header_labels = app_data.POSITIONS_COLUMNS
        self._model = Model__PositionsTable.PositionsModel(self.header_labels)
        self.proxy_model = TableProxies.PositionsProxy(self)
        self.proxy_model.setSourceModel(self._model)
        self.setModel(self.proxy_model)
        self.verticalHeader().setVisible(False)

        self.start_check()  # start the check (Threaded)

        self.horizontalHeader: 'QtWidgets.QHeaderView' = self.horizontalHeader()
        self.horizontalHeader.sectionClicked.connect(self.header_section_clicked)
        self.setPalette(global_parent.palette())
        # todo: finalize this
        QtCore.QTimer.singleShot(2000, partial(self.setStyleSheet, self.global_parent.custom_style_sheet.tableview("dark")))

    def manage_col_space(self):
        """manage column space to fit all columns in view"""
        self.resizeColumnsToContents()

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        self.manage_col_space()
        super(PositionsView, self).resizeEvent(e)

    def display_profit_calculations(self, df_):
        # -------- sell & buy qty ----------
        sell_qty = df_[df_["Transaction_Type"] == "Sell"]["quantity"].sum()
        self.global_parent.ui.label_options_cal_c.setText(f"Sell Qty : {sell_qty}")
        buy_qty = df_[df_["Transaction_Type"] == "Buy"]["quantity"].sum()
        self.global_parent.ui.label_optionscalc_l.setText(f"Buy Qty : {buy_qty}")

        #  ------- Profit & Loss ----------
        tot_profit = df_["CE_Profit"].dropna().sum() + df_["PE_Profit"].dropna().sum()
        if tot_profit < 0:
            style_sheet = "QLabel { color: red;}"
        else:
            style_sheet = "QLabel { color: rgb(0, 255, 0);}"
        self.global_parent.ui.label_options_calc_r.setText(f"Profit&Loss : {round(tot_profit, 2)}")
        self.global_parent.ui.label_options_calc_r.setStyleSheet(style_sheet)

    @QtCore.pyqtSlot(object)
    def reset_model_data(self, args):
        """insert new data, gets called when the FutureLogs file is modified"""
        positions_df = args[0]
        # take everything except the first columns from positions_df (first column is the index)
        try:
            to_drop_cols = ("name", "multiplier")
            _ = [positions_df.drop(columns=[col_], inplace=True) for col_ in to_drop_cols
                 if col_ in positions_df.columns]
            to_show_cols = positions_df.columns.tolist()
            self._model = Model__PositionsTable.PositionsModel(header_labels=to_show_cols,
                                                               data=positions_df)
            self.proxy_model = TableProxies.PositionsProxy(self)
            self.proxy_model.setSourceModel(self._model)
            self.setModel(self.proxy_model)
            self.display_profit_calculations(positions_df)
        except Exception:
            # logger.warning("skip updating positions file", exc_info=True)
            pass
        self.scrollToBottom()

    def start_check(self):
        """start checking FutureLog file for modification"""
        self.handler.update_view()  # update view emits - file-changed signal to update the model
        logger.info("Positions Logging started")

    def get_data(self) -> pd.DataFrame:
        return self._model.get_data()

    def save_data(self, path: str):
        """Export data to external file"""
        if path:
            df = self._model.get_data()
            df.to_csv(path, index=False)
            logger.info("Positions data saved successfully.")

    # =============================== THIS PART DEALS WITH COLUMN BASED FILTERING ==========================
    @QtCore.pyqtSlot(int)
    def header_section_clicked(self, section: int):
        self.column_index = section
        header_section_width = self.columnWidth(section)
        valuesUnique = list(
            set([str(self.proxy_model.item(row, self.column_index)) for row in range(self.proxy_model.rowCount())]))
        header_pos = self.mapToParent(
            self.horizontalHeader.pos())  # will be inherited by QTableView subclasses, so, self is QTableView
        posY = header_pos.y() + self.horizontalHeader.height()
        posX = header_pos.x() + self.horizontalHeader.sectionViewportPosition(self.column_index)
        valuesUnique = list(sorted(valuesUnique))
        valuesUnique.insert(0, "All")

        self.filter_listWidget = PopupList.SelectionList(
            size=QtCore.QSize(header_section_width+5, 150),
            parent=self.parent()
        )
        self.filter_listWidget.move(QtCore.QPoint(posX, posY))
        _ = [self.filter_listWidget.takeItem(0) for _ in range(self.filter_listWidget.count())]
        self.filter_listWidget.addItems(valuesUnique)

        self.filter_listWidget.itemClicked.connect(self.on_signalMapper_mapped)
        self.filter_listWidget.show()

    def on_signalMapper_mapped(self, listWidgetItem: QtWidgets.QListWidgetItem):
        item_text = listWidgetItem.text()
        self.filter_listWidget.close()
        if item_text == "All":
            self.displayAll_triggered()
            return
        filterColumn = self.column_index
        self.proxy_model.setFilterFixedString(item_text)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(filterColumn)

    def displayAll_triggered(self):
        filterColumn = self.column_index
        filterString = QtCore.QRegExp("",
                                      QtCore.Qt.CaseInsensitive,
                                      QtCore.QRegExp.RegExp
                                      )

        self.proxy_model.setFilterRegExp(filterString)
        self.proxy_model.setFilterKeyColumn(filterColumn)

    def deleteLater(self) -> None:
        """when tableview is destroyed, stop observer instance"""
        super(PositionsView, self).deleteLater()

    def setPalette(self, palette: QtGui.QPalette) -> None:
        """make stylesheet sensitive"""
        super(PositionsView, self).setPalette(palette)
