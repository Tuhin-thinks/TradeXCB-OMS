import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

from Libs.UI import PNL_Profits_Ui
from Libs.UI.CustomWidgets.PNL_Summary_TableView import PNLView
from Libs.UI.Interact import show_message


def load_pnl_fake_summary():
    df = pd.read_csv('PNLATRTS_All_User.csv')
    return df


class PNLProfitDialog(QtWidgets.QDialog):
    def __init__(self, data: pd.DataFrame = None):
        super(PNLProfitDialog, self).__init__()
        # close window when clicked outside
        self.ui = PNL_Profits_Ui.Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Profit and Loss")
        # self.pnl_summary_df = load_pnl_fake_summary()  # assign data from init args
        self.pnl_summary_df = data
        unique_users = list(map(str, self.pnl_summary_df.user_id.dropna().unique().tolist()))
        self.tableView = PNLView(self.pnl_summary_df, self)

        self.frame_button_panel = QtWidgets.QFrame(self)
        self.vboxLayout_button_panel = QtWidgets.QVBoxLayout(self.frame_button_panel)
        self.vboxLayout_button_panel.setContentsMargins(0, 0, 0, 0)
        self.vboxLayout_button_panel.setSpacing(0)

        self.combobox_users = QtWidgets.QComboBox(self.frame_button_panel)
        self.combobox_users.setMinimumWidth(150)
        self.combobox_users.setMaximumWidth(150)
        self.combobox_users.addItems(unique_users)
        self.combobox_users.currentTextChanged[str].connect(self.filter_by_user)
        self.combobox_users.setCurrentIndex(0)

        self.vboxLayout_button_panel.addWidget(self.combobox_users)

        self.frame_footer = QtWidgets.QFrame(self)
        self.frame_footer.setMaximumHeight(150)
        self.gridLayout_footer = QtWidgets.QGridLayout(self.frame_footer)
        # ----- create display labels -----
        label_value_mapping = {
            "Profit": "0",
            "User": "User:" + self.combobox_users.currentText(),
            "BUY Quantity": "0",
            "SELL Quantity": "0"
        }
        fixed_label_size = [100, 80]
        default_label_style = "font-weight: bold;"
        grid_row = 0
        grid_col = 0
        self.QLabel_mapping = {}
        for label_str, label_value in label_value_mapping.items():
            self.QLabel_mapping[label_str] = {}
            disp_label, value_label = self.create_display_set_labels(label_str, label_value, fixed_label_size,
                                                                     default_label_style,
                                                                     (grid_row, grid_col))
            self.QLabel_mapping[label_str]['disp_label'] = disp_label
            self.QLabel_mapping[label_str]['value_label'] = value_label
            grid_col += 1

        self.frame_layout = QtWidgets.QVBoxLayout(self.ui.frame)
        self.frame_layout.addWidget(self.frame_button_panel)
        self.frame_layout.addWidget(self.tableView)
        self.frame_layout.addWidget(self.frame_footer)

        # -------- set default values --------
        if unique_users:
            self.filter_by_user(unique_users[0])
        else:
            show_message(self, "No data found", "No positions data found to group by user", mode="error")
            QtCore.QTimer.singleShot(100, self.close)

    def filter_by_user(self, user_id):
        self.tableView.apply_filter(by="user_id", value=user_id)
        profit_amt = self.tableView.calculate_profit()
        buy_quantity, sell_quantity = self.tableView.calculate_quantity()
        self.QLabel_mapping['User']['value_label'].setText(f"{user_id}")
        self.QLabel_mapping['Profit']['value_label'].setText(str(profit_amt))
        self.QLabel_mapping['BUY Quantity']['value_label'].setText(str(buy_quantity))
        self.QLabel_mapping['SELL Quantity']['value_label'].setText(str(sell_quantity))
        if profit_amt > 0:
            self.QLabel_mapping['Profit']['disp_label'].setStyleSheet("font-weight:bold;"
                                                                      "color: green;")
            self.QLabel_mapping['Profit']['value_label'].setStyleSheet("font-weight:bold;"
                                                                       "color: green;")
        else:
            self.QLabel_mapping['Profit']['disp_label'].setStyleSheet("font-weight:bold;"
                                                                      "color: red;")
            self.QLabel_mapping['Profit']['value_label'].setStyleSheet("font-weight:bold;"
                                                                       "color: red;")

    def create_display_set_labels(self, label_text, value_text, label_size, label_style, grid_pos):
        label_display = QtWidgets.QLabel(self.frame_footer)
        label_display.setText(label_text)
        label_display.setAlignment(Qt.AlignCenter)
        label_display.setStyleSheet(label_style)
        label_display.setMaximumSize(*label_size)

        label_value = QtWidgets.QLabel(self.frame_footer)
        label_value.setText(value_text)
        label_value.setAlignment(Qt.AlignCenter)
        label_value.setStyleSheet(label_style)
        label_value.setMaximumSize(*label_size)

        self.gridLayout_footer.addWidget(label_display, *grid_pos)
        self.gridLayout_footer.addWidget(label_value, *(grid_pos[0] + 1, grid_pos[1]), 1, 1)
        return label_display, label_value


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    pnl_profit = PNLProfitDialog()
    pnl_profit.show()
    sys.exit(app.exec_())
