"""
Contains the class used for the API Details table view.
"""
import typing
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from Libs.Storage import app_data
from Libs.UI.Models_n_Delegates import Model__API_Det


class API_Det_TableView(QtWidgets.QTableView):
    def __init__(self):
        super(API_Det_TableView, self).__init__()
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self._model = Model__API_Det.Model_API_Det(parent=None, data=None)
        self.setModel(self._model)
        self.setItemDelegate(Model__API_Det.Delegate_API_Det(parent=self))
        self.setItemDelegateForColumn(app_data.API_DETAILS_COLUMNS.index('Slices'),
                                      Model__API_Det.Delegate_Slices(parent=self))
        self.setItemDelegateForColumn(1, Model__API_Det.Delegate_Broker_Type(parent=self))
        self.resizeColumnsToContents()

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        self.increase_col_space()
        super(API_Det_TableView, self).resizeEvent(e)

    def increase_col_space(self) -> None:
        extra_space_factor = 5
        for col in range(self._model.columnCount()):
            if col in (0, 1):
                self.setColumnWidth(col, 150)
            else:
                col_width = self.columnWidth(col)
                if col_width < 100:
                    col_width += extra_space_factor
                    self.setColumnWidth(col, col_width)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == Qt.Key_Delete:  # delete a row from table
            try:
                selected_row = self.selectedIndexes()[0].row()
                self._model.delete_row(selected_row)
            except IndexError:
                pass
        super(API_Det_TableView, self).keyPressEvent(event)

    def insertRow(self):
        self._model.append_empty_row()

    def get_rows(self) -> typing.List[typing.Dict[str, typing.Any]]:
        all_rows = self._model.get_all_row_data()
        export_list = []
        for row in all_rows:
            row_dict = dict(zip(app_data.API_DETAILS_COLUMNS, row))
            export_list.append(row_dict)
        return export_list

    def set_data(self, data: typing.List[typing.Dict[str, typing.Any]]):
        self._model.set_data([list(row.values()) for row in data])
        self.increase_col_space()
