import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from Libs.UI.Models_n_Delegates import Model__PositionsGrouping
from Libs.Storage import app_data


class PNLView(QtWidgets.QTableView):
    def __init__(self, summary_data: pd.DataFrame, parent=None):
        super(PNLView, self).__init__(parent=parent)

        self.summary_df = summary_data
        self._model = Model__PositionsGrouping.PositionsGroupingModel(header_labels=app_data.POSITIONS_COLUMNS,
                                                                      data=self.summary_df)
        self.setModel(self._model)

    def get_source_model_instance(self):
        return self._model

    def apply_filter(self, by, value):
        if by == "user_id":
            self._model.set_filter(by, value)

    def calculate_profit(self):
        return self._model.calculate_profit()

    def calculate_quantity(self):
        return self._model.calculate_quantity()
