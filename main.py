import multiprocessing
import pprint
import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow

from Libs.Concurrency import Validator, Worker
from Libs.Storage import manage_local as localdb, encrypto
from Libs.UI import Interact, user_login
from Libs.UI.CustomWidgets import (email_input_widget, security_question_widget, reset_password_dialog,
                                   DisclaimerDialog)
from Libs.UI.Utils import field_validator
from Libs.globals import *
from Libs.icons_lib import Icons
from Libs.Utils.config import prepare_files

BASE_DIR = os.path.dirname(__file__)
ICONS_DIR = os.path.join(BASE_DIR, 'Libs', 'UI', 'icons')

logger = exception_handler.getFutureLogger(__name__)


# noinspection PyUnusedLocal
class LoginWindow(QMainWindow):
    """Login/Register Window"""

    def __init__(self):
        super(LoginWindow, self).__init__()

        self.reset_passwd_obj = None
        self.reset_password_thread = None
        self._processing_request = False
        self.logout_thread_t_update = None
        self.logout_check_obj_t_update = None
        self.login_check_obj_t_update = None
        self.login_thread_t_update = None
        self.reg_check_thread = None
        self.reg_check_obj = None
        self.login_check_obj = None
        self.login_thread = None
        self.home_window = None
        self.registered = False
        self.approved = False
        self.ui = user_login.Ui_MainWindow()
        self.ui.setupUi(self)

        self.resize(QtCore.QSize(1096, 920))

        logo_pixmap = Icons.get_pixmap("current_app_logo-full")
        self.ui.label_logo.setPixmap(logo_pixmap)
        self.ui.label_logo_2.setPixmap(logo_pixmap)

        # set default window as login window
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.checkBox_agreelicenseAgreement.setDisabled(True)
        self.ui.checkBox_agreelicenseAgreement_register.setDisabled(True)
        self.ui.checkBox_remember_passwd.setChecked(True)
        self.ui.checkBox_remember_passwd.setDisabled(True)
        self.ui.label_problem_login.setOpenExternalLinks(True)  # to open links in browser

        def add_icons():
            # custom icons for lineEdit
            self.ui.lineEdit_userid.addAction(Icons.get("user-icon"), QtWidgets.QLineEdit.LeadingPosition)
            self.ui.lineEdit_password.addAction(Icons.get("passwd-icon"), QtWidgets.QLineEdit.LeadingPosition)
            self.ui.lineEdit_username_create.addAction(Icons.get("user-icon"), QtWidgets.QLineEdit.LeadingPosition)
            self.ui.lineEdit_first_name_create.addAction(Icons.get("pen-icon"), QtWidgets.QLineEdit.LeadingPosition)
            self.ui.lineEdit_last_name_create.addAction(Icons.get("pen-icon"), QtWidgets.QLineEdit.LeadingPosition)
            self.ui.lineEdit_create_email_id.addAction(Icons.get("mail-icon"), QtWidgets.QLineEdit.LeadingPosition)
            self.ui.lineEdit_password_create.addAction(Icons.get("passwd-icon"), QtWidgets.QLineEdit.LeadingPosition)
            self.ui.lineEdit_mobile_no.addAction(Icons.get("mobile-icon"), QtWidgets.QLineEdit.LeadingPosition)

        add_icons()

        def change_user_window(index):
            self.setWindowTitle(
                f"User {'Login' if index == 0 else 'Registration'} {settings.APP_NAME} {settings.App_VERSION} {settings.EXTENSION}")
            self.ui.stackedWidget.setCurrentIndex(index)

        change_user_window(0)  # default window is login window

        self.ui.pushButton_signin.clicked.connect(self.login)
        self.ui.pushButton_createAccount.clicked.connect(lambda x: change_user_window(1))
        self.ui.pushButton_to_loginpage.clicked.connect(lambda x: change_user_window(0))
        self.ui.pushButton_create_acc.clicked.connect(self.register)
        self.ui.pushButton_forgotPasswd.clicked.connect(self.forgot_password)

        self.thread_pool = QtCore.QThreadPool()

        # check registration status data from local db
        code, user_d_dict = localdb.get_to_fill_data()
        if code == 1:  # if user is registered only then program will check for registration status
            user_name = user_d_dict.get('user_name')
            f_name = user_d_dict.get('f_name')
            l_name = user_d_dict.get('l_name')
            email_id = user_d_dict.get('email_id')
            password_dec = user_d_dict.get('password')  # plain text from AES (auto)
            phone = user_d_dict.get('phone')
            self.ui.pushButton_forgotPasswd.setDisabled(True)
            self.fill_data(user_name, password_dec, f_name, l_name, email_id, phone)

        self.launch_utility_processes()

    @staticmethod
    def launch_utility_processes():
        process = multiprocessing.Process(target=prepare_files).start()

    def fill_data(self, user_name, password_dec, f_name, l_name, email_id, phone):
        args = (user_name, password_dec, f_name, l_name, email_id, phone)
        if None in args or '' in args:
            return
        # registration window
        self.ui.lineEdit_first_name_create.setText(f_name)
        self.ui.lineEdit_last_name_create.setText(l_name)
        self.ui.lineEdit_create_email_id.setText(email_id)
        self.ui.lineEdit_mobile_no.setText(phone)
        self.ui.lineEdit_username_create.setText(user_name)
        self.ui.lineEdit_password_create.setText(password_dec)

        # login window
        self.ui.lineEdit_userid.setText(user_name)
        self.ui.lineEdit_password.setText(password_dec)

        self.ui.pushButton_forgotPasswd.setDisabled(False)  # allow forgot password use when user is registered
        self.ui.pushButton_signin.setDisabled(False)
        self.ui.pushButton_create_acc.setDisabled(True)  # cannot create multiple accounts from same app

    def forgot_password(self):
        """
        Gets called when user pressed forgot password button
        :return:
        """
        user_name = self.ui.lineEdit_userid.text()
        email_id = email_input_widget.EmailInputDialog().exec_()
        if user_name and email_id:
            self.check_is_logged_in(user_name, None, None, email_id, None, None)  # before app launch
        else:
            Interact.show_message(self, "Cannot do this operation",
                                  "Please enter 'user name' and email-id and try again.", "warning")

    @QtCore.pyqtSlot(object)
    def get_reg_data(self, args):
        status, _ = args
        line_edits = (self.ui.lineEdit_username_create,
                      self.ui.lineEdit_first_name_create,
                      self.ui.lineEdit_last_name_create,
                      self.ui.lineEdit_create_email_id,
                      self.ui.lineEdit_password_create,
                      self.ui.lineEdit_mobile_no)

        def setter(values):
            for index, value in enumerate(values):
                line_edits[index].setText(value)

        code, user_d_dict = localdb.get_to_fill_data()
        if code == 1 and user_d_dict:  # registered data available for client
            user_name = user_d_dict['user_name']
            f_name = user_d_dict['f_name']
            l_name = user_d_dict['l_name']
            password_dec = user_d_dict['password']  # password returned from ...to_fill_data() is decrypted
            email_id = user_d_dict['email_id']
            phone = user_d_dict['phone']
            if status == "-1":  # user not registered yet
                self.ui.stackedWidget.setCurrentIndex(1)
                self.ui.pushButton_create_acc.setDisabled(False)  # disable create account button when sig-in approved
            elif status == "registered":
                self.ui.stackedWidget.setCurrentIndex(0)
                self.ui.pushButton_create_acc.setDisabled(True)  # disable create account button when sig-in approved
            elif status == "approved":  # autofill login details (when login approved)
                self.ui.lineEdit_userid.setText(user_name)
                self.ui.lineEdit_password.setText(password_dec)
                self.ui.lineEdit_userid.setFocus()
                self.ui.pushButton_signin.setDisabled(False)  # enable sign-in button
                self.ui.pushButton_create_acc.setDisabled(True)  # disable create account button when sig-in approved
            elif status == "pending":
                self.ui.stackedWidget.setCurrentIndex(0)
                Interact.show_message(self, "User Registered", "Wait until account has been activated.", "info")
                self.ui.pushButton_create_acc.setDisabled(True)  # disable create account button when sig-in approved

            # set text to fields
            setter((user_name, f_name, l_name, email_id, password_dec, phone))
        else:  # not yet registered
            self.ui.stackedWidget.setCurrentIndex(1)

    @QtCore.pyqtSlot(object)
    def recv_reg_status(self, status):
        if status == "approved":  # if status is approved take user to login window
            self.ui.stackedWidget.setCurrentIndex(0)
            self.ui.pushButton_signin.setEnabled(True)  # user can log in now
            self.ui.pushButton_create_acc.setDisabled(True)
        if status == "pending":
            self.ui.stackedWidget.setCurrentIndex(0)
            self.ui.pushButton_create_acc.setDisabled(True)

    @QtCore.pyqtSlot(object)
    def recv_reg_status__forgot_passwd(self, args):
        status, user_data = args
        if status == "approved":  # if status is approved take user to login window
            user_name, email_id = user_data
            sec_op = security_question_widget.SecurityQuestionDialog().exec_()
            if sec_op[0] and sec_op[1]:  # check if
                security_question, security_answer = sec_op
                hashed_string = encrypto.generate_hash(security_question, security_answer)
                self.check_security_hash(hashed_string, user_name, email_id)
        else:
            Interact.show_message(self, "Operation Failed", "User not yet registered", "warning")

    @QtCore.pyqtSlot(object)
    def recv_sec_check_status(self, args):
        status, message, user_data = args
        user_name, email_id = user_data
        if status == 0:  # security question + answer matched
            res, new_password = reset_password_dialog.ResetPassword().exec_()
            if not res:
                Interact.show_message(self, "Password Reset cancelled",
                                      "Password reset process is cancelled",
                                      mode="info")
                return
            else:
                self.reset_password(user_name, email_id, new_password)
        else:
            Interact.show_message(self, "Security answer didn't match", message, "warning")

    def recv_reset_passwd_status(self, args):
        code, message = args
        status, message = args
        if status == 0:  # security question + answer matched

            Interact.show_message(self, "Password reset complete",
                                  "Password reset process is complete, restart app & login with new credentials.",
                                  mode="info")
            localdb.logout()
            self.close()
        else:
            Interact.show_message(self, "Reset Operation Failed", "Failed to reset password", "error")

    def complete_reset_request(self):
        try:
            self.reset_password_thread.quit()
            self.reset_password_thread.wait(5)
            try:
                self.reg_check_obj.disconnect()
            except Exception as e:
                pass
        except Exception as e:
            pass

    def reset_password(self, user_name, email_id, new_password):
        self.reset_password_thread = QtCore.QThread()
        self.reset_passwd_obj = Worker.CheckLogin(user_name, None, email_id, raw_passwd=False)
        self.reset_passwd_obj.status.connect(self.recv_reset_passwd_status)
        self.reset_passwd_obj.reg_log.connect(self.show_status)
        self.reset_passwd_obj.message.connect(self.show_message)
        self.reset_passwd_obj.extra_sig.connect(self.complete_reset_request)
        self.reset_passwd_obj.moveToThread(self.reset_password_thread)
        self.reset_password_thread.started.connect(partial(self.reset_passwd_obj.reset_password, new_password))
        self.reset_password_thread.start()

    def check_security_hash(self, security_hash: str, user_name: str, mail_id: str):
        """
        Gets Called after registration status is returned "approved"
        :param mail_id: user entered mail-id (forwarded)
        :param user_name: user entered user_name (forwarded)
        :param security_hash: hashed security question and answer
        :return:
        """
        self.login_thread = QtCore.QThread()
        self.login_check_obj = Worker.CheckLogin(user_name, None, mail_id, raw_passwd=False)
        self.login_check_obj.status.connect(self.recv_sec_check_status)
        self.login_check_obj.reg_log.connect(self.show_status)
        self.login_check_obj.message.connect(self.show_message)
        self.login_check_obj.extra_sig.connect(self.complete_login_request)
        self.login_check_obj.moveToThread(self.login_thread)
        self.login_thread.started.connect(partial(self.login_check_obj.check_security_string, security_hash))
        self.login_thread.start()

    @QtCore.pyqtSlot(object)
    def show_message(self, message):
        Interact.show_message(self, "User Registration", message, mode='info')

    @QtCore.pyqtSlot(object)
    def show_status(self, status_log):
        self.ui.statusbar.showMessage(status_log, len(status_log) * 100)

    @QtCore.pyqtSlot()
    def complete_reg_request(self):
        try:
            self.reg_check_thread.quit()
            self.reg_check_thread.wait(5)
            try:
                self.reg_check_obj.disconnect()
            except Exception as e:
                pass
        except Exception as e:
            pass

    def check_is_logged_in(self, *args):
        """
        Check if user is logged in, result is used to decide whether to check forgot password or not
        user_name and email_id are valid one's, all other fields are None
        """
        self.reg_check_obj = Worker.CheckRegObj(*args)
        self.reg_check_thread = QtCore.QThread()
        self.reg_check_obj.status.connect(self.recv_reg_status__forgot_passwd)
        self.reg_check_obj.message.connect(self.show_message)
        self.reg_check_obj.reg_log.connect(self.show_status)
        self.reg_check_obj.extra_sig.connect(self.complete_reg_request)
        self.reg_check_obj.moveToThread(self.reg_check_thread)
        self.reg_check_thread.started.connect(self.reg_check_obj.check_status)
        self.reg_check_thread.start()

    def check_reg(self, *args):
        """
        Gets called when registration input validator marks input data as valid
        :param args: user_name, f_name, l_name, email_id, password, phone
        """
        # password raw_passwd will encrypt and use the passwd for validation
        self.reg_check_obj = Worker.CheckRegObj(*args)
        self.reg_check_thread = QtCore.QThread()
        self.reg_check_obj.status.connect(self.recv_reg_status)
        self.reg_check_obj.message.connect(self.show_message)
        self.reg_check_obj.reg_log.connect(self.show_status)
        self.reg_check_obj.extra_sig.connect(partial(self.complete_reg_request))
        self.reg_check_obj.moveToThread(self.reg_check_thread)
        self.reg_check_thread.started.connect(self.reg_check_obj.register_user)
        self.reg_check_thread.start()

    def register(self):
        """
        Gets called when user pressed the "create account" button
        :return:
        """

        def reset_fields():
            """utility function: Reset input fields"""
            self.ui.label_problem_username_create.clear()
            self.ui.label_problem_first_name_create.clear()
            self.ui.label_problem_last_name_create.clear()
            self.ui.label_problem_create_email_id.clear()
            self.ui.label_problem_password_create.clear()
            self.ui.label_problem_mobile_no.clear()

        reset_fields()
        user_name = self.ui.lineEdit_username_create.text()
        f_name = self.ui.lineEdit_first_name_create.text()
        l_name = self.ui.lineEdit_last_name_create.text()
        email_id = self.ui.lineEdit_create_email_id.text()
        password_plain = self.ui.lineEdit_password_create.text()
        phone = self.ui.lineEdit_mobile_no.text()

        sec_op = security_question_widget.SecurityQuestionDialog().exec_()
        if sec_op[0] and sec_op[1]:  # check if
            security_question, security_answer = sec_op
            self.validate_reg_inp(user_name, f_name, l_name, email_id, password_plain, phone,
                                  encrypto.generate_hash(security_question, security_answer),
                                  self.ui)
        else:
            Interact.show_message(self, "Cancelled", "Registration process has been cancelled", "info")

    def validate_reg_inp(self, *args):
        """
        <pre>Launches a QRunnable to check validity of user's input data and construct error messages</pre>
        :param args: user_name, f_name, l_name, email_id, password_plain, phone, self.ui
        :return: None
        """
        validator_run = Validator.ValidatorRunnable(field_validator.validate_reg_inp, *args)
        validator_run.signals.result.connect(partial(self.get_reg_validator_results, (args,)))
        self.thread_pool.start(validator_run)

    def get_reg_validator_results(self, data: tuple, flag: bool):
        """
        Get validation results, proceed to check registration status, if flag is true
        - flag, becomes false, when one or more fields, doesn't satisfy preset conditions
        """
        if not flag:
            return
        user_name, f_name, l_name, email_id, password_plain, phone, security_string, _ = data[0]
        self.check_reg(user_name, f_name, l_name, email_id, password_plain, phone, security_string)

    # ========================================== LOGIN ===============================================

    def login(self):
        """Perform login process, if entered details are valid"""
        self.show_disclaimer()

        if not self._processing_request:
            self._processing_request = True
            gui_username = self.ui.lineEdit_userid.text()
            plain_txt_password = self.ui.lineEdit_password.text()
            self.ui.pushButton_signin.setDisabled(True)
            if gui_username and plain_txt_password:
                self.validate_login_inp(gui_username, plain_txt_password, self.ui)
            else:
                Interact.show_message(self, "Empty Fields", "Please fill both username and password to login.\n",
                                      mode="warning")

    def get_login_validator_results(self, data: tuple, flag: bool):
        """
        Get results from login validation and process to check valid login creds,
        <if flag is true>
            [valid login creds]
        <else>
            [show error message on UI]
        """
        if flag:
            user_name, password_dec, _ = data[0]  # validated data from the UI (user input)
            code_, dict_ = localdb.get_to_fill_data()
            email_id = dict_.get("email_id")
            if code_ == 1 and email_id:
                self.check_login(user_name, password_dec, email_id)
            else:
                input_dialog = email_input_widget.EmailInputDialog()
                email_id = input_dialog.exec_()
                if email_id:
                    self.check_login(user_name, password_dec, email_id)
                    return
                self._processing_request = False
                self.ui.label_problem_login.setText("Cannot Login with given credentials.")
                self.ui.pushButton_signin.setDisabled(False)

    def recv_login_status(self, args: tuple):
        """
        receives returned data from Worker.check_user_table
        :param args: first_name, last_name, user_name, password_dec, email_id, phone
        :return:
        """
        status, message, user_data = args
        if status == -1:
            self.ui.label_problem_login.setText(message)
        elif status == 0:
            localdb.insert_user_data(*user_data)
            self.ui.label_problem_login.setText("Login Success")
            self.update_login_time()  # this will update login time and open api window

    def check_login(self, user_name, password, mail_id):
        """
        Validate login data from cloud database,
        This function gets called after user input data has been validated by login validator

        :param user_name: entered username
        :param password: entered password [plain text]
        :param mail_id: entered mail_id
        :return: None
        """
        self.login_thread = QtCore.QThread()
        self.login_check_obj = Worker.CheckLogin(user_name, password, mail_id)
        self.login_check_obj.status.connect(self.recv_login_status)
        self.login_check_obj.reg_log.connect(self.show_status)
        self.login_check_obj.message.connect(self.show_message)
        self.login_check_obj.extra_sig.connect(self.complete_login_request)
        self.login_check_obj.moveToThread(self.login_thread)
        self.login_thread.started.connect(self.login_check_obj.check_user_table)
        self.login_thread.start()

    @QtCore.pyqtSlot()
    def complete_login_request(self):
        self.ui.pushButton_signin.setEnabled(True)
        self._processing_request = False

        try:
            self.login_thread.wait(1)
            self.login_thread.quit()
        except Exception as e:
            pass
        try:
            self.login_check_obj.disconnect()
        except Exception as e:
            pass

    def validate_login_inp(self, *args):
        validator_run = Validator.ValidatorRunnable(field_validator.validate_login_inp, *args)
        validator_run.signals.result.connect(partial(self.get_login_validator_results, (args,)))
        self.thread_pool.start(validator_run)

    def update_login_time(self):
        """
        Create a connection with database and updates login time for current user
        :return: None
        """
        # get user login data (for validation) and update login time
        logger.debug("updating login time")
        code, user_d_dict = localdb.get_to_fill_data()
        user_name = user_d_dict.get('user_name')
        email_id = user_d_dict.get('email_id')
        password_dec = user_d_dict.get('password')

        self.login_thread_t_update = QtCore.QThread()
        self.login_check_obj_t_update = Worker.CheckLogin(user_name, password_dec, email_id)  # update login time
        self.login_check_obj_t_update.status.connect(self.show_status)
        self.login_check_obj_t_update.reg_log.connect(self.show_status)
        self.login_check_obj_t_update.message.connect(self.show_message)
        self.login_check_obj_t_update.extra_sig.connect(self.login_time_updated)
        self.login_check_obj_t_update.moveToThread(self.login_thread_t_update)
        self.login_thread_t_update.started.connect(self.login_check_obj_t_update.update_login_time)
        self.login_thread_t_update.start()
        logger.debug("update thread started...")

    def update_logout_time(self):
        """
        Create a connection with database and updates login time for current user
        Threads not used here because, with thread it'll directly close the main UI thread and this child thread will
        never be executed.

        :return: None
        """
        # get user login data (for validation) and update login time
        code, user_d_dict = localdb.get_to_fill_data()
        user_name = user_d_dict.get('user_name')
        email_id = user_d_dict.get('email_id')
        password_dec = user_d_dict.get('password')

        self.logout_check_obj_t_update = Worker.CheckLogin(user_name, password_dec, email_id)  # update login time
        self.logout_check_obj_t_update.status.connect(self.show_status)
        self.logout_check_obj_t_update.reg_log.connect(self.show_status)
        self.logout_check_obj_t_update.message.connect(self.show_message)
        self.logout_check_obj_t_update.extra_sig.connect(self.logout_time_updated)
        self.logout_check_obj_t_update.update_logout_time()

    @staticmethod
    def show_disclaimer():
        """Open disclaimer window"""
        value = localdb.get_user_preference_table("hide-disclaimer")
        if not value or value == "0":
            disclaimer_window = DisclaimerDialog.DisclaimerDialog()
            to_hide = disclaimer_window.exec_()
            localdb.set_user_preference_table({"hide-disclaimer": to_hide})

    # ====================================== OPEN API WINDOW =========================================
    @QtCore.pyqtSlot()
    def login_time_updated(self):
        logger.debug("control back to main thread...")
        try:
            self.login_thread_t_update.wait(1)
            self.login_thread_t_update.quit()
        except Exception as e:
            pass
        try:
            self.login_check_obj_t_update.disconnect()
        except Exception as e:
            pass
        logger.debug("opening application window")
        self.open_api_det_window()

    @QtCore.pyqtSlot()
    def logout_time_updated(self):
        try:
            self.logout_thread_t_update.wait(1)
            self.logout_thread_t_update.quit()
        except Exception as e:
            pass
        try:
            self.logout_check_obj_t_update.disconnect()
        except Exception as e:
            pass

    def open_api_det_window(self):
        """
        :return: None
        """
        from Libs.api_home import ApiHome
        self.home_window = ApiHome(self.geometry())
        self.home_window.window_closed.connect(self.update_logout_time)
        self.home_window.show()
        logger.debug("Application window displayed, closing login window")
        self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if event.spontaneous():
            messageButton = QtWidgets.QMessageBox().question(self, "close window",
                                                             "Are you sure you want to close the application?",
                                                             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                             QtWidgets.QMessageBox.Yes)
            if messageButton == QtWidgets.QMessageBox.Yes:
                event.accept()
                super(LoginWindow, self).closeEvent(event)
            else:
                event.ignore()
        else:
            event.accept()
            super(LoginWindow, self).closeEvent(event)


def run_app():
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    w = LoginWindow()
    # w = ApiHome()
    w.show()
    app.exec_()


def test():
    from Libs.Files import handle_user_details
    data = handle_user_details.read_user_api_details()  # for testing
    pprint.PrettyPrinter().pprint(data)


if __name__ == '__main__':
    if os.name == 'nt':
        multiprocessing.freeze_support()
    run_app()
