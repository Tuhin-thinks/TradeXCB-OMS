from PyQt5 import QtWidgets, QtCore, QtGui

from Libs.UI.CustomWidgets.TableView_OrderStatus import OrderStatusTableView


class OrderStatusView(QtWidgets.QDialog):
    def __init__(self, row_id: str, order_status_string: str, instrument_str: str):
        super().__init__()
        self.row_id = row_id
        self.instrument_str = instrument_str

        # show dialog as a one time popup
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint | QtCore.Qt.Popup)
        self.setStyleSheet("background-color: black; color: white;")

        # create a layout to the dialog
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # create a central frame
        self.central_frame = QtWidgets.QFrame(self)
        self.layout.addWidget(self.central_frame)

        # create a layout to the central frame
        self.central_frame_layout = QtWidgets.QVBoxLayout()
        self.central_frame.setLayout(self.central_frame_layout)

        # create a header frame
        self.header_frame = QtWidgets.QFrame(self.central_frame)

        # create a layout to the header frame
        self.header_frame_layout = QtWidgets.QHBoxLayout()
        self.header_frame.setLayout(self.header_frame_layout)

        # add header label
        self.header_label = QtWidgets.QLabel(self.header_frame)
        self.header_label.setText(self.add_html_style())
        self.header_frame_layout.addWidget(self.header_label)

        # add a listview to the central frame
        self.table_view = OrderStatusTableView(self.central_frame)
        self.table_view.setMinimumHeight(100)

        # create a model for the listview
        self.model = QtGui.QStandardItemModel()

        # create a list of items to be added to the listview
        self.list_items = []
        if "\n" in order_status_string:
            self.list_items = order_status_string.split("\n")

        self.model.clear()
        self.model.setHorizontalHeaderLabels(["User Name", "Order Status"])
        self.model.setRowCount(len(self.list_items))
        self.model.setColumnCount(2)
        for i in range(len(self.list_items)):
            if ':' in self.list_items[i]:
                item_text = self.list_items[i].split(":")
                self.model.setItem(i, 0, QtGui.QStandardItem(item_text[0]))
                self.model.setItem(i, 1, QtGui.QStandardItem(item_text[1]))

        self.table_view.set_model(self.model)

        # add all widgets to central frame
        self.central_frame_layout.addWidget(self.header_frame)
        self.central_frame_layout.addWidget(self.table_view)
        self.table_view.increase_col_space()

    def add_html_style(self):
        style_string = """
        <style>
        h2 {
            color: white;
            font-size: 14px;
            font-weight: bold;
            font-family: Arial;
            text-align: center;
        }
        h3 {
            color: white;
            font-size: 12px;
            font-weight: bold;
            font-family: Arial;
            text-align: left;
        }
        </style>
        <div>
        <h2>Order Status For All Users</h2>
        <h3>Row: $row_id$<br>$instrument_str$</h3>
        <div>
        """
        style_string = style_string.replace("$row_id$", self.row_id)
        style_string = style_string.replace("$instrument_str$", self.instrument_str)
        return style_string
