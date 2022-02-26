from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

from Libs.UI import disclaimer_dialog
from Libs.Utils import settings


class DisclaimerDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(DisclaimerDialog, self).__init__(parent=parent)
        self.setWindowTitle(f"Disclaimer - {settings.APP_NAME} {settings.App_VERSION} {settings.EXTENSION}")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.ui = disclaimer_dialog.Ui_Dialog()
        self.ui.setupUi(self)

        self.setFixedSize(QtCore.QSize(750, 500))
        # self.ui.scrollArea.verticalScrollBar().setHidden(True)
        self.ui.scrollArea.horizontalScrollBar().setHidden(True)
        self.ui.label_heading.setText("<h2>Disclaimer</h2>")

        center_pos = QtWidgets.QApplication.desktop().geometry().center()
        x = center_pos.x() - 250
        y = center_pos.y() - 250
        _new_center = QtCore.QPoint(x, y)
        print(_new_center)
        QtCore.QTimer.singleShot(50, lambda: self.move(_new_center))

        self.show_pref = False

        self.ui.pushButton_confirm_discliamer.clicked.connect(self.confirm_pressed)

    @QtCore.pyqtSlot()
    def confirm_pressed(self):
        self.show_pref = self.ui.checkBox_no_show_disclaimer.isChecked()
        self.accept()
        self.close()

    def exec_(self) -> bool:
        super(DisclaimerDialog, self).exec_()
        return self.show_pref

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            event.ignore()
        else:
            super(DisclaimerDialog, self).keyPressEvent(event)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        event.ignore()
