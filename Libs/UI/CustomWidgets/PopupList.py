from PyQt5 import QtWidgets, QtCore, QtGui

MAX_WAIT_TIME = 5 * 1000  # maximum seconds to wait before closing the popup selection list


class SelectionList(QtWidgets.QListWidget):
    def __init__(self, size, parent=None):
        super(SelectionList, self).__init__(parent=parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.resize(size)

        self._close_timer = None
        self.init_close_timer()

    def focusOutEvent(self, e: QtGui.QFocusEvent) -> None:
        self.close()
        super(SelectionList, self).focusOutEvent(e)

    def init_close_timer(self):
        if not self._close_timer:
            self._close_timer = QtCore.QTimer()
            self._close_timer.timeout.connect(self.close_ui)
            self._close_timer.start(MAX_WAIT_TIME)

    def close_ui(self):
        if self._close_timer:
            self._close_timer.stop()
            self._close_timer = None
        self.close()

    def enterEvent(self, a0: QtCore.QEvent) -> None:
        if self._close_timer:
            self._close_timer.stop()
            self._close_timer = None
        super(SelectionList, self).enterEvent(a0)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        # self.init_close_timer()
        self.close_ui()
        super(SelectionList, self).leaveEvent(event)

    def deleteLater(self) -> None:
        self.close_ui()
        super(SelectionList, self).deleteLater()
