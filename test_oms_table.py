import random
import sys
import typing

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

from Libs.UI.CustomWidgets import OrderManagerTable


def algo(manager_dict: typing.Dict):
    while manager_dict["run"]:
        user_df_dict = manager_dict["user_df_dict"]
        for row_key, user_row in user_df_dict.items():
            user_name = user_row['user_name']
            broker = user_row['broker']
            if random.randint(1, 10) == 5:
                manager_dict["user_df_dict"][row_key]["Status"] = "Order Placed"


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OMS Table")
        self.setGeometry(50, 50, 500, 500)
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        self.table = OrderManagerTable.OMSTable()
        self.setCentralWidget(self.table)

        # shortcuts for table management
        self.insert_row_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+I"), self)
        self.insert_row_shortcut.activated.connect(self.table.append_row)

        self.delete_row_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+D"), self)
        self.delete_row_shortcut.activated.connect(self.table.delete_row)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
