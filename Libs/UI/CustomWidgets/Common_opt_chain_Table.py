from PyQt5 import QtWidgets, QtGui, QtCore

import Libs.globals
from Libs.Files import handle__SaveOpen
from Libs.UI.CustomWidgets import PopupList
from Libs.UI.Models_n_Delegates import Model__ExcelView
from Libs.UI.Proxies import TableProxies

logger = Libs.globals.exception_handler.getFutureLogger(__name__)


class OptChainAnalysis_TableView(QtWidgets.QTableView):
    message_log = QtCore.pyqtSignal(tuple)
    export_instruments_data = QtCore.pyqtSignal(tuple)

    def __init__(self, table_name, header_labels, parent, global_parent):
        super(OptChainAnalysis_TableView, self).__init__(parent=parent)
        self.table_name = table_name
        self.column_index = None
        self.global_parent = global_parent
        self.filter_listWidget = None
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.header_labels = header_labels

        self._model = Model__ExcelView.ExcelViewModel(self.header_labels)
        self.proxy_model = TableProxies.ExcelViewProxy(self)
        self.proxy_model.setSourceModel(self._model)
        self.setModel(self.proxy_model)

        # shortcut to resize cells to contents
        size_adjust_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+R"), self)
        size_adjust_shortcut.activated.connect(self.resizeColumnsToContents)

        self.setSelectionBehavior(self.SelectRows)

        self.verticalHeader().setVisible(False)
        self.horizontal_header = self.horizontalHeader()
        self.horizontal_header.sectionClicked.connect(self.header_section_clicked)
        self.manage_col_space()
        self.setPalette(global_parent.palette())

    def export_instruments(self, ce_instrument, pe_instrument, strategy, symbol_name, *_):
        self.export_instruments_data.emit((ce_instrument, pe_instrument, strategy, symbol_name))

    def get_model_instance(self):
        """
        Returns model instance (proxy-model) to be used inside NIFTY/BANKNIFTY table
        :return:
        """
        return self.model()

    def manage_col_space(self):
        cols_ = self.model().columnCount()
        for col_index in range(cols_):
            if self.columnWidth(col_index) < 150:
                self.setColumnWidth(col_index, 150)  # add extra space for each column

    def manage_height(self):
        height = self.parent().size().height()
        self.setMinimumHeight(height - 10)

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        """In response to table's resize, columns are also resize keeping the width ratio fixed"""
        self.manage_col_space()
        self.manage_height()
        super(OptChainAnalysis_TableView, self).resizeEvent(e)

    def update_model_data(self, df):
        self._model.populate(df[self.header_labels])

    def save_data(self):
        """called when user press save as excel button"""
        save_path = handle__SaveOpen.save_file(self, "Save data as CSV", '', "CSV(*.csv)")
        if save_path:
            df_ = self._model.get_data()
            df_.to_csv(save_path, index=False)
            logger.info("Exported as *.csv successfully.")

    def clear(self):
        """clear all data from model"""
        self.model().clear()

    # =============================== THIS PART DEALS WITH COLUMN FILTERING ==========================
    @QtCore.pyqtSlot(int)
    def header_section_clicked(self, section: int):
        self.column_index = section
        header_section_width = self.columnWidth(section)
        df_ = self.model().get_data()
        valuesUnique = list(sorted([str(x) for x in df_.iloc[:, self.column_index].unique().tolist()]))
        header_pos = self.mapToParent(
            self.horizontal_header.pos())  # will be inherited by QTableView subclasses, so, self is QTableView
        posY = header_pos.y() + self.horizontal_header.height()
        posX = header_pos.x() + self.horizontal_header.sectionViewportPosition(self.column_index)
        valuesUnique.insert(0, "All")

        self.filter_listWidget = PopupList.SelectionList(
            size=QtCore.QSize(header_section_width + 5, 150),
            parent=self.parent()
        )
        self.filter_listWidget.setMaximumWidth(header_section_width)
        self.filter_listWidget.move(QtCore.QPoint(posX, posY))
        _ = [self.filter_listWidget.takeItem(0) for _ in range(self.filter_listWidget.count())]
        self.filter_listWidget.addItems(valuesUnique)

        self.filter_listWidget.itemClicked.connect(self.on_signalMapper_mapped)
        self.filter_listWidget.show()

    def on_signalMapper_mapped(self, listWidgetItem: QtWidgets.QListWidgetItem):
        item_text = listWidgetItem.text()
        self.filter_listWidget.hide()
        if item_text == "All":
            self.displayAll_triggered()
            return
        filterColumn = self.column_index
        filterString = QtCore.QRegExp(item_text,
                                      QtCore.Qt.CaseSensitive,
                                      QtCore.QRegExp.FixedString)

        self.proxy_model.setFilterRegExp(filterString)
        self.proxy_model.setFilterKeyColumn(filterColumn)

    def displayAll_triggered(self):
        filterColumn = self.column_index
        filterString = QtCore.QRegExp("",
                                      QtCore.Qt.CaseInsensitive,
                                      QtCore.QRegExp.RegExp)

        self.proxy_model.setFilterRegExp(filterString)
        self.proxy_model.setFilterKeyColumn(filterColumn)

    def deleteLater(self) -> None:
        """when tableview is destroyed, stop observer instance"""
        self.file_observer.stop()
        super(OptChainAnalysis_TableView, self).deleteLater()

    def setPalette(self, palette: QtGui.QPalette) -> None:
        """make stylesheet sensitive"""
        for child in self.findChildren(QtWidgets.QWidget):
            child.setPalette(self.global_parent.palette())
        super(OptChainAnalysis_TableView, self).setPalette(palette)
