from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt


class CompleterComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(CompleterComboBox, self).__init__(parent=parent)
        self.time_now = None
        self.to_change = None
        self.to_wait = 0
        self.initial_textChange = True
        self.completion_timer = None
        self.timer_running = False
        self.search_margin = 2  # minimum number of characters required to initiate a valid search
        self.wait_time = 1500  # wait for 1.5secs before completion popup appears
        self.setEditable(True)
        self.setFocusPolicy(Qt.StrongFocus)

    def view(self) -> QtWidgets.QAbstractItemView:
        return self.completer_.popup()

    def text_changed(self, text):
        if self.initial_textChange:
            self.initial_textChange = False
            return
        if len(text) > self.search_margin:
            self.to_change = True
            self.time_now = 0  # set filter after 2 sec of user stops typing
            if not self.timer_running:
                self.delay_timer()
                self.timer_running = True

    def delay_timer(self):
        self.to_wait = self.wait_time
        self.time_now = 0
        self.timer_running = False
        self.completion_timer = QtCore.QTimer(self)
        self.completion_timer.timeout.connect(self.time_out)
        self.completion_timer.start(self.wait_time)
        self.timer_running = True

    def time_out(self):
        if self.timer_running:
            self.time_now += self.wait_time
            if self.time_now > self.to_wait and self.to_change:
                self.change_filter()
                self.to_change = False
                self.time_now = 0

    def change_filter(self):
        text = self.lineEdit().text()
        if len(text) > self.search_margin:
            if " " in text:
                tokens = text.split(" ")
                pattern = ".*".join(tokens)
                pattern = f"^{pattern}"
            else:
                pattern = f"^{text}.*"
            self.pFilterModel.setFilterRegularExpression(QtCore.QRegularExpression(pattern, QtCore.QRegularExpression.CaseInsensitiveOption))
            self.showPopup()
        else:
            self.pFilterModel.invalidateFilter()

    def setModel(self, model: QtCore.QAbstractItemModel) -> None:
        self.completer_ = QtWidgets.QCompleter(self)
        self.setCompleter(self.completer_)
        self.completer_.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        self.setEditable(True)
        self.completer_.setPopup(self.view())
        self.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self.lineEdit().textEdited.connect(self.text_changed)
        self.completer_.activated.connect(self.setTextIfCompleterIsClicked)
        self.pFilterModel = QtCore.QSortFilterProxyModel(self)
        self.pFilterModel.setSourceModel(model)
        self.completer_.setModel(self.pFilterModel)
        self.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        # self.pFilterModel.setFilterKeyColumn(0)
        super(CompleterComboBox, self).setModel(self.pFilterModel)

    def setModelColumn(self, column: int):
        self.completer_.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(CompleterComboBox, self).setModelColumn(column)

    def setTextIfCompleterIsClicked(self, text):
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)
            self.timer_running = False
            self.to_change = False
            self.to_wait = self.wait_time
            self.hidePopup()
