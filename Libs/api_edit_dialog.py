from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

from Libs.UI import api_inp_dialog
from Libs.Storage import app_data
from Libs.UI.Utils import field_validator
from Libs.Files import handle_user_details
from Libs.globals import *


class APIDialog(QtWidgets.QDialog):
    submit_clicked = QtCore.pyqtSignal(dict)

    def __init__(self, custom_style_sheet, theme_name: str, parent_palette: 'QtGui.QPalette', parent=None):
        super(APIDialog, self).__init__(parent=parent)

        self.setWindowModality(Qt.ApplicationModal)
        self.mode = 'dark' if theme_name.startswith('Dark') else 'light'
        self.custom_style_sheet = custom_style_sheet
        self.parent_palette = parent_palette

        self.ui = api_inp_dialog.Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle(f"User API Details - {settings.APP_NAME} {settings.App_VERSION} {settings.EXTENSION}")

        self.ui.comboBox_stock_broker_name.addItems(app_data.BROKER_NAMES)
        # -------- fix broker name to zerodha only -------------
        self.ui.comboBox_stock_broker_name.setCurrentIndex(0)
        self.ui.comboBox_stock_broker_name.setDisabled(True)

        # set user settings to lineEdit
        details_dict = handle_user_details.read_user_settings()
        self.fill_user_details(details_dict)

        self.ui.pushButton_submit_api_details.clicked.connect(self.api_submit_clicked)
        self.ui.pushButton_edit_api_details.clicked.connect(self.api_edit_clicked)

        self.reset_stylesheet()

    def fill_user_details(self, details_dict):
        broker_name = details_dict.get("Stock Broker Name")
        if broker_name:
            broker_choice_index = app_data.BROKER_NAMES.index(broker_name)
            self.ui.comboBox_stock_broker_name.setCurrentIndex(broker_choice_index)
        self.ui.lineEdit_account_userName.setText(details_dict.get("Account User Name"))
        self.ui.lineEdit_api_secret.setText(details_dict.get("API Secret"))
        self.ui.lineEdit_api_key.setText(details_dict.get("API Key"))
        self.ui.lineEdit_totp_secret.setText(details_dict.get("TOTP Secret"))
        self.ui.lineEdit_account_password.setText(details_dict.get("Account Password"))
        self.ui.lineEdit_account_sec_pin.setText(details_dict.get("Security Pin"))

    def reset_stylesheet(self):
        dark_style_3 = self.custom_style_sheet.bg_gradient_frame(mode=self.mode, palette=self.parent_palette)
        self.ui.frame_bg_gradient_frame.setStyleSheet(dark_style_3)

        inp_det_frame_style = self.custom_style_sheet.api_inp_details_frame(mode=self.mode,
                                                                            palette=self.parent_palette)
        self.ui.frame_api_details_inp.setStyleSheet(inp_det_frame_style)
        self.ui.label_8.setText("<h2>User API Details</h2>")

    @QtCore.pyqtSlot()
    def api_edit_clicked(self):
        self.ui.frame_api_inp_fields.setDisabled(False)

    @QtCore.pyqtSlot()
    def api_submit_clicked(self):
        res_dict = field_validator.validate_api_inp(self.ui, self)
        if not res_dict:
            return
        else:
            self.submit_clicked.emit(res_dict)  # emit api details to be used for authorization
            save_res = handle_user_details.save_user_details(res_dict)
            if save_res:
                self.ui.frame_api_inp_fields.setDisabled(True)
            self.close()
