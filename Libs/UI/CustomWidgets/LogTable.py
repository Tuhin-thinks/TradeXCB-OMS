import csv

from Libs.globals import *
from Libs.UI.Models_n_Delegates.Model__LogView import LogModel
from Libs.UI.Proxies.TableProxies import LogProxyModel
from Libs.UI.Utils import FS__EventHandLer
from PyQt5 import QtCore, QtGui, QtWidgets

logger = exception_handler.getFutureLogger(__name__)


class LogView(QtWidgets.QTableView):
    filter_role_changed = QtCore.pyqtSignal(str)

    def __init__(self, global_parent, parent=None):
        super(LogView, self).__init__(parent=parent)
        self.global_parent = global_parent
        self.handler = None

        height_threshold = 150
        self.setMinimumHeight(height_threshold)
        self.setMaximumHeight(height_threshold)
        
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.verticalHeader().setVisible(False)

        self._model = LogModel(("Timestamp", "Logs", "Message", "Source"))
        self.proxy_model = LogProxyModel(self)
        self.proxy_model.setSourceModel(self._model)
        self.setModel(self.proxy_model)

        self.watch_loc = os.path.join(settings.LOG_FILE_DIR, "FutureLogs.log")
        self.filter_role_changed.connect(self.change_filter_role)

        self.start_check()
        self.setPalette(self.global_parent.palette())

    @QtCore.pyqtSlot(str)
    def change_filter_role(self, role_name: str):
        """
        To change proxy model filter regex
        :param role_name:
            future: show future logs only
            all: show all logs
        :return:
        """
        if role_name == "future":
            pattern = r"^(?!dev_trash)"  # todo: decide action plan for filter regex
            self.proxy_model.setFilterRegularExpression(
                QtCore.QRegularExpression(pattern, QtCore.QRegularExpression.CaseInsensitiveOption))
            self.proxy_model.setFilterKeyColumn(3)  # filter on source column
        else:  # all
            self.proxy_model.setFilterWildcard("")
            self.proxy_model.setFilterKeyColumn(3)

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        """In response to table's resize, columns are also resize keeping the width ratio fixed"""
        tot_width = e.size().width()
        self.setColumnWidth(0, int(tot_width * 0.2))
        self.setColumnWidth(1, int(tot_width * 0.2))
        self.setColumnWidth(2, int(tot_width * 0.6))

        super(LogView, self).resizeEvent(e)

    @QtCore.pyqtSlot(object)
    def insert_data(self, args):
        """insert new data, gets called when the FutureLogs file is modified"""
        time_stamp, log_level, message, source = args
        if all(args):
            self.model().insert_row([time_stamp, log_level, message, source])
            self.scrollToBottom()

    def start_check(self):
        """start checking FutureLog file for modification"""
        self.handler = FS__EventHandLer.FS_LogModifyHandler(self.watch_loc)
        # self.file_observer.schedule(handler, watch_loc, recursive=True)
        self.handler.file_changed.connect(self.insert_data)
        # self.file_observer.start()

    def clear(self):
        """clear all data from model"""
        self.model().clear()

    def save_data(self, path):
        """save all logs to csv file"""
        if path:
            data = self._model.get_data()
            with open(path, 'w') as writer:
                logs_writer = csv.writer(writer, delimiter=',', lineterminator='\n')
                logs_writer.writerows(data)

    def deleteLater(self) -> None:
        """when tableview is destroyed, stop observer instance"""
        super(LogView, self).deleteLater()

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        column = 2
        row = 0
        if self.selectionModel().selection().indexes():
            for i in self.selectionModel().selection().indexes():
                row, column = i.row(), i.column()
            if column != 2:
                return
            menu = QtWidgets.QMenu()
            copy_action = menu.addAction("Copy Message")
            glob_pos = event.globalPos()
            action = menu.exec_(glob_pos)
            if action == copy_action:
                QtWidgets.QApplication.clipboard().setText(self.model().data(self.model().index(row, column)),
                                                           QtGui.QClipboard.Clipboard)

    def setPalette(self, palette: QtGui.QPalette) -> None:
        """make stylesheet sensitive"""
        for child in self.findChildren(QtWidgets.QWidget):
            child.setPalette(self.global_parent.palette())
        super(LogView, self).setPalette(palette)
