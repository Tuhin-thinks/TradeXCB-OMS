from PyQt5 import QtWidgets, QtCore
from Libs.UI.Interact import show_message
from Libs.icons_lib import Icons


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(551, 154)
        Dialog.setMinimumSize(QtCore.QSize(0, 123))
        Dialog.setMaximumSize(QtCore.QSize(16777215, 154))
        Dialog.setStyleSheet(u"""
QWidget{
    background-color: black;
    color: white;
    font: 12pt "Serif";
}
#Dialog{
    border: 1px solid white;
    border-radius: 5px 10px;
}
""")
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.lineEdit = QtWidgets.QLineEdit(Dialog)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setStyleSheet(u"QLineEdit{\n"
                                    "	border: none;\n"
                                    "	border-bottom: 2px solid white;\n"
                                    "}\n"
                                    "\n"
                                    "QLineEdit:hover{\n"
                                    "	padding-left: 2px;\n"
                                    "	border-color: grey;\n"
                                    "}")

        self.gridLayout.addWidget(self.lineEdit, 1, 0, 1, 1)

        self.frame = QtWidgets.QFrame(Dialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, 0)
        self.horizontalSpacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
                                                      QtWidgets.QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pushButton = QtWidgets.QPushButton(self.frame)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setMinimumSize(QtCore.QSize(100, 0))
        self.pushButton.setMaximumSize(QtCore.QSize(120, 16777215))
        self.pushButton.setStyleSheet("""
QPushButton::hover{
    background-color: rgb(30, 30, 30);
    color: rgb(208, 208, 208);
    border: 1px solid rgb(30, 30, 30);
    border-radius: 5px;
    padding-left: 5px;
    padding-right: 5px;
}
QPushButton::pressed{
    margin-top: 2px;
    margin-bottom: 2px;
}""")
        close_icon = Icons.get("close-strategy_name-icon")
        self.close_button = QtWidgets.QPushButton(close_icon, "", self.frame)
        self.close_button.setObjectName(u"pushButton_close")
        self.close_button.setMinimumSize(QtCore.QSize(100, 0))
        self.close_button.setMaximumSize(QtCore.QSize(120, 16777215))
        self.close_button.setStyleSheet("""
QPushButton{
    background-color: rgb(255, 0, 0);
    border: 1px solid red;
    border-radius: 5px;
    padding-left: 5px;
    padding-right: 5px;
}
QPushButton:hover{
    background-color: rgb(214, 0, 0);
    border: 1px solid red;
    border-radius: 3px;
}
QPushButton:pressed{
    margin-top: 2px;
    margin-bottom: 2px;
}
""")

        self.horizontalLayout.addWidget(self.close_button)
        self.horizontalLayout.addWidget(self.pushButton)

        self.gridLayout.addWidget(self.frame, 2, 0, 1, 1)

        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName(u"label")
        self.label.setMaximumSize(QtCore.QSize(16777215, 50))
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtCore.QCoreApplication.translate("Dialog", u"Dialog", None))
        self.lineEdit.setPlaceholderText(QtCore.QCoreApplication.translate("Dialog", u"someone@mail.com", None))
        self.pushButton.setText(QtCore.QCoreApplication.translate("Dialog", u"confirm", None))
        self.close_button.setText(QtCore.QCoreApplication.translate("Dialog", u"Close", None))
        self.label.setText(QtCore.QCoreApplication.translate("Dialog", u"Enter your registered Email-ID", None))


class EmailInputDialog(QtWidgets.QDialog):
    def __init__(self):
        super(EmailInputDialog, self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)

        self.ui.pushButton.clicked.connect(self.check_inp)
        self.ui.close_button.clicked.connect(self.reject_dialog)

    def check_inp(self):
        text = self.ui.lineEdit.text()
        if not text:
            show_message(self, "Invalid Input", "Email field cannot be empty.", mode="warning")
        else:
            self.accept()

    def reject_dialog(self):
        self.reject()

    def exec_(self):
        super(EmailInputDialog, self).exec_()
        return self.ui.lineEdit.text()
