import sys

from PyQt5 import QtWidgets, QtGui

from Libs.UI.CustomWidgets import OrderManagerTable
from Libs.tradexcb_algo.AlgoManager import AlgoManager


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OMS Table")
        self.setGeometry(50, 50, 500, 500)
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QtWidgets.QVBoxLayout(self.central_widget)

        self.table = OrderManagerTable.OMSTable()
        self.central_layout.addWidget(self.table)

        self.button_frame = QtWidgets.QFrame()
        self.central_layout.addWidget(self.button_frame)
        self.button_frame_layout = QtWidgets.QHBoxLayout()
        self.button_frame.setLayout(self.button_frame_layout)
        self.button_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.button_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.button_frame.setLineWidth(1)
        self.button_frame.setMidLineWidth(0)
        self.button_frame.setObjectName("button_frame")

        self.start_algo_button = QtWidgets.QPushButton("Start Algo")
        self.start_algo_button.clicked.connect(self.start_algo)
        self.button_frame_layout.addWidget(self.start_algo_button)

    def start_algo(self):
        self.strategy_algorithm_object = AlgoManager()
        self.table.set_cancel_order_queue(self.strategy_algorithm_object.get_cancel_order_queue())
        self.strategy_algorithm_object.error_stop.connect(self.error_stop_trade_algorithm)
        self.strategy_algorithm_object.orderbook_data.connect(self.update_orderbook_data)
        self.strategy_algorithm_object.start_algo(0)  # pass paper_trade value (0 for live trade)

    def error_stop_trade_algorithm(self, error_message):
        print(error_message)

    def update_orderbook_data(self, orderbook_data):
        self.table.update_data(orderbook_data)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
