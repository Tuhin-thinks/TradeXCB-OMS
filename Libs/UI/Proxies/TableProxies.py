from PyQt5 import QtCore


class PositionsProxy(QtCore.QSortFilterProxyModel):
    def __init__(self, parent):
        super(PositionsProxy, self).__init__(parent=parent)

    def item(self, *args):
        return self.sourceModel().item(*args)

    def get_data(self):
        return self.sourceModel().get_data()


class ExcelViewProxy(QtCore.QSortFilterProxyModel):
    def __init__(self, owner):
        super(ExcelViewProxy, self).__init__(parent=owner)

    def append_row(self, *args):
        self.sourceModel().append_row(*args)

    def clear(self):
        self.sourceModel().clear()

    def item(self, *args):
        self.sourceModel().item(*args)

    def get_data(self):
        return self.sourceModel().get_data()


class LogProxyModel(QtCore.QSortFilterProxyModel):

    def insert_row(self, row_data: list):
        self.sourceModel().append_row(row_data)

    def clear(self):
        self.sourceModel().clear()
