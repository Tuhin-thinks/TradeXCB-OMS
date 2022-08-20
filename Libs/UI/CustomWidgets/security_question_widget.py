import typing
from typing import Tuple, Any

from PyQt5 import QtCore, QtWidgets
from Libs.UI.Interact import show_message


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(723, 447)
        Dialog.setMinimumSize(QtCore.QSize(723, 447))
        Dialog.setMaximumSize(QtCore.QSize(723, 447))
        Dialog.setStyleSheet("""
QWidget{
    background-color: black;
    color: white;
    font: 10pt \"Serif\";
}
#Dialog{
    border: 1px solid white;
    border-radius: 5px 10px;
}""")
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtWidgets.QFrame(Dialog)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.verticalLayout_2.addItem(spacerItem)
        self.label = QtWidgets.QLabel(self.frame)
        self.label.setMaximumSize(QtCore.QSize(16777215, 45))
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.comboBox_seq_question = QtWidgets.QComboBox(self.frame)
        self.comboBox_seq_question.setStyleSheet("""
QComboBox{
    border: 1px solid white;
    background-color: rgb(115, 115, 115);
    border-radius: 5px;
    padding: 5px;
}

QComboBox:on{
    background-color: rgb(0, 170, 255);
    padding-left: 4px;
}""")
        self.comboBox_seq_question.setObjectName("comboBox_seq_question")
        self.comboBox_seq_question.addItem("")
        self.comboBox_seq_question.addItem("")
        self.comboBox_seq_question.addItem("")
        self.comboBox_seq_question.addItem("")
        self.comboBox_seq_question.addItem("")
        self.verticalLayout_2.addWidget(self.comboBox_seq_question)
        self.verticalLayout.addWidget(self.frame)
        self.frame_2 = QtWidgets.QFrame(Dialog)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.gridLayout = QtWidgets.QGridLayout(self.frame_2)
        self.gridLayout.setObjectName("gridLayout")
        self.label_ur_answer = QtWidgets.QLabel(self.frame_2)
        self.label_ur_answer.setObjectName("label_ur_answer")
        self.gridLayout.addWidget(self.label_ur_answer, 0, 0, 1, 1)
        self.lineEdit_seq_answer = QtWidgets.QLineEdit(self.frame_2)
        self.lineEdit_seq_answer.setStyleSheet("""
QLineEdit{
    border: none;
    border-bottom: 2px solid white;
}

QLineEdit:hover{
    padding-left: 2px;
    border-color: grey;
}""")
        self.lineEdit_seq_answer.setObjectName("lineEdit_seq_answer")
        self.gridLayout.addWidget(self.lineEdit_seq_answer, 0, 1, 1, 1)
        self.frame_3 = QtWidgets.QFrame(self.frame_2)
        self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_3.setObjectName("frame_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame_3)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.pushButton_dismiss = QtWidgets.QPushButton(self.frame_3)
        self.pushButton_dismiss.setMinimumSize(QtCore.QSize(0, 40))
        self.pushButton_dismiss.setMaximumSize(QtCore.QSize(200, 16777215))
        self.pushButton_dismiss.setStyleSheet("""
QPushButton{
    border: 1px solid red;
    border-radius: 10px;
    padding: 5px;
    padding-left: 5px;
    padding-right: 5px;
}
QPushButton::hover{
    background-color: rgba(255, 0, 0, 170);
    color: rgb(208, 208, 208);
    border: 1px solid rgb(0, 121, 182);
}
QPushButton::pressed{
    margin-top: 2px;
    margin-bottom: 2px;
}""")
        self.pushButton_dismiss.setObjectName("pushButton_dismiss")
        self.horizontalLayout.addWidget(self.pushButton_dismiss)
        self.pushButton_confirm = QtWidgets.QPushButton(self.frame_3)
        self.pushButton_confirm.setMinimumSize(QtCore.QSize(0, 40))
        self.pushButton_confirm.setMaximumSize(QtCore.QSize(200, 16777215))
        self.pushButton_confirm.setStyleSheet("""
QPushButton{
    border: 1px solid rgb(99, 99, 99);
    border-radius: 10px;
    padding: 5px;
    padding-left: 5px;
    padding-right: 5px;
}
QPushButton::hover{
    background-color: rgb(0, 153, 229);
    color: rgb(208, 208, 208);
    border: 1px solid rgb(0, 121, 182);
}
QPushButton::pressed{
    margin-top: 2px;
    margin-bottom: 2px;
}""")
        self.pushButton_confirm.setObjectName("pushButton_confirm")
        self.horizontalLayout.addWidget(self.pushButton_confirm)
        self.gridLayout.addWidget(self.frame_3, 1, 0, 1, 2)
        self.verticalLayout.addWidget(self.frame_2)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setWhatsThis(_translate("Dialog", "This is useful to reset your password"))
        self.label.setText(_translate("Dialog", "*Select a Security question that only you can answer"))
        self.comboBox_seq_question.setItemText(0, _translate("Dialog", "What is your nickname?"))
        self.comboBox_seq_question.setItemText(1, _translate("Dialog", "What is your pet\'s name?"))
        self.comboBox_seq_question.setItemText(2, _translate("Dialog", "What is your date of birth?"))
        self.comboBox_seq_question.setItemText(3, _translate("Dialog", "What city you were born in?"))
        self.comboBox_seq_question.setItemText(4,
                                               _translate("Dialog", "What was the make and model of your first car?"))
        self.label_ur_answer.setText(_translate("Dialog", "*Your answer:"))
        self.pushButton_dismiss.setText(_translate("Dialog", "Dismiss"))
        self.pushButton_confirm.setText(_translate("Dialog", "Confirm"))


class SecurityQuestionDialog(QtWidgets.QDialog):
    def __init__(self):
        super(SecurityQuestionDialog, self).__init__()

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.input_ok = False

        self.ui.pushButton_confirm.clicked.connect(self.confirm_clicked)
        self.ui.pushButton_dismiss.clicked.connect(self.dismiss_clicked)

    def confirm_clicked(self):
        security_answer = self.ui.lineEdit_seq_answer.text()
        if not security_answer.strip():
            show_message(self, "Security Field Empty", "Security answer cannot be empty please enter a valid answer!",
                         "warning")
            self.input_ok = False
            return
        else:
            self.input_ok = True
            self.accept()

    def dismiss_clicked(self):
        self.input_ok = False
        self.reject()

    def exec_(self) -> Tuple[Any, Any]:
        super(SecurityQuestionDialog, self).exec_()
        if self.input_ok:
            return self.ui.comboBox_seq_question.currentText(), self.ui.lineEdit_seq_answer.text()
        else:
            return None, None
