from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QFrame, QLineEdit, QLabel, QVBoxLayout, QComboBox, QSizePolicy


class Input_Type_1(QWidget):
    def __init__(self, label_text: str, lineEdit_placeholder_text: str = None, parent=None):
        super(Input_Type_1, self).__init__(parent=parent)

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(200)
        self.setMaximumWidth(280)

        self.frame = QFrame(self)
        self.v_layout = QVBoxLayout(self.frame)
        self.v_layout.setContentsMargins(5, 0, 5, 0)
        self.v_layout.setSpacing(2)

        self.lineEdit_frame = QLineEdit(self.frame)
        self.lineEdit_frame.setPalette(self.palette())
        self.lineEdit_frame.setMinimumSize(QtCore.QSize(80, 25))
        self.lineEdit_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.label_frame = QLabel(self.frame)
        self.label_frame.setAlignment(QtCore.Qt.AlignCenter)
        self.label_frame.setText(label_text)
        self.label_frame.setPalette(self.palette())

        self.v_layout.addWidget(self.label_frame)
        self.v_layout.addWidget(self.lineEdit_frame)

        # custom style sheet
        self.lineEdit_frame.setStyleSheet("color: black;\n"
                                          "border: 2px solid white;\n"
                                          "border-radius: 3px;\n"
                                          "margin: 2px;")

        if lineEdit_placeholder_text:
            self.lineEdit_frame.setPlaceholderText(lineEdit_placeholder_text)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super(Input_Type_1, self).paintEvent(event)
        opt = QtWidgets.QStyleOption()
        p = QtGui.QPainter(self)
        s = self.style()
        s.drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, p, self)

    def setPalette(self, palette: QtGui.QPalette) -> None:
        self.lineEdit_frame.setPalette(palette)
        self.label_frame.setPalette(palette)


class Input_Type_2(QWidget):
    def __init__(self, label_text: str, parent=None):
        super(Input_Type_2, self).__init__(parent=parent)

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(120)

        self.frame = QFrame(self)
        self.v_layout = QVBoxLayout(self.frame)
        self.v_layout.setContentsMargins(5, 0, 5, 0)
        self.v_layout.setSpacing(5)

        self.comboBox_options = QComboBox(self.frame)
        self.comboBox_options.setPalette(self.palette())
        self.comboBox_options.resize(QtCore.QSize(80, 30))
        self.label_frame = QLabel(self.frame)
        self.label_frame.setAlignment(QtCore.Qt.AlignCenter)
        self.label_frame.setText(label_text)
        self.label_frame.setPalette(self.palette())

        self.v_layout.addWidget(self.label_frame)
        self.v_layout.addWidget(self.comboBox_options)

    def setPalette(self, palette: QtGui.QPalette) -> None:
        self.comboBox_options.setPalette(palette)
        self.label_frame.setPalette(palette)
