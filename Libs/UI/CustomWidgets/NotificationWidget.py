from datetime import datetime
from PyQt5 import QtWidgets, QtGui


class NotificationWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, view_port_width=250):
        super(NotificationWidget, self).__init__(parent=parent)

        self._frame = QtWidgets.QFrame()
        self._main_layout = QtWidgets.QVBoxLayout(self)
        self._main_layout.addWidget(self._frame)
        self._frame_layout = QtWidgets.QVBoxLayout(self._frame)

        self.message_label = QtWidgets.QLabel(self._frame)
        self.message_label.setMaximumWidth(view_port_width)
        self.message_label.setWordWrap(True)
        self.date_time_label = QtWidgets.QLabel(self._frame)

        self._frame_layout.addWidget(self.message_label)
        self._frame_layout.addWidget(self.date_time_label)

        self._frame_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._frame_layout.setSpacing(1)
        self._main_layout.setSpacing(0)

        self.message_label.setOpenExternalLinks(True)
        self.date_time_label.setStyleSheet("QLabel { color: grey; background-color: transparent;}")
        self.message_label.setStyleSheet("QLabel { color: #df73ff;"
                                         "background-color: rgba(0, 0, 0, 0);"
                                         "padding-left: 2px;}")

    def set_notif_time(self, notif_time: datetime):
        self.date_time_label.setText(notif_time.strftime("%d-%m-%Y %H:%M"))
        font = QtGui.QFont("Serif", 6, 75)
        self.date_time_label.setFont(font)

    def set_notif_message(self, text: str):
        self.message_label.setText(text)
