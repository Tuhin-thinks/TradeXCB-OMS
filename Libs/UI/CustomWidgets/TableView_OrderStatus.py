from PyQt5 import QtWidgets, QtCore, QtGui


class OrderStatusTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.__model = None
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.horizontalHeader().setVisible(True)
        self.verticalHeader().setVisible(False)

    def increase_col_space(self):
        total_table_width = self.viewport().width()
        per_col_width = int(total_table_width / self.__model.columnCount())
        if per_col_width < 100:
            return
        for col_index in range(self.__model.columnCount()):
            self.setColumnWidth(col_index, per_col_width)

    def set_model(self, model):
        self.__model = model
        self.setModel(model)

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        super().resizeEvent(e)
        self.increase_col_space()
