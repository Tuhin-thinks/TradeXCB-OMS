from typing import Tuple, Union
from PyQt5 import QtCore

from Libs.Storage import manage_local as localdb, Cloud
from Libs.Storage import encrypto


class CheckRegObj(QtCore.QObject):
    """Object class to check registration status of app user"""
    status = QtCore.pyqtSignal(object)  # returns registration status
    message = QtCore.pyqtSignal(object)  # pop-up message box
    reg_log = QtCore.pyqtSignal(object)  # real-time status
    extra_sig = QtCore.pyqtSignal()  # an extra signal to perform single statement operation on emit

    def __init__(self, u_name, f_name, l_name, email_id, password_plain, phone_no, security_string=None):
        super(CheckRegObj, self).__init__()
        self.uname = u_name
        self.f_name = f_name
        self.l_name = l_name
        self.email_id = email_id
        self.password = password_plain
        self.phone = phone_no
        self.security_string = security_string

    def _check_status(self) -> Union[Tuple[int, str, 'Cloud.RequestRegistration'], None]:
        req_reg = Cloud.RequestRegistration(
            user_name=self.uname,
            password=self.password,
            email_id=self.email_id,
            f_name=self.f_name,
            l_name=self.l_name,
            phone=self.phone,
            security_string=self.security_string,
            ui_logger=self.reg_log
        )
        status_code, message = req_reg.check_registration_status()
        return status_code, message, req_reg

    def check_status(self):
        status_code, message, _ = self._check_status()
        if status_code == -1:
            self.message.emit(message)
            self.status.emit(("-1", None))
        elif type(status_code) == str:  # if user is already registered (returned from check_registration_status)
            self.status.emit((status_code, (self.uname, self.email_id)))  # emits either registration approved/pending
        self.extra_sig.emit()

    def register_user(self):
        """Create new user Registration in user_request_table"""
        status_code, message, req_reg = self._check_status()

        if status_code == -1 and message == "":  # user not registered yet
            code_, message_ = req_reg.create_registration()
            if code_ == 1:  # new registration complete
                self.status.emit("pending")
                localdb.insert_user_data(self.f_name, self.l_name, self.uname, self.password,
                                         self.email_id, self.phone)
            self.message.emit(message_)

        elif type(status_code) == str:  # if user is already registered (returned from check_registration_status)
            self.status.emit(status_code)  # emits either registration approved/pending
            if status_code.lower() == "approved":
                message = "User registration confirmed, Please try Login."
                self.message.emit(message)
            else:
                self.message.emit("User registered, wait until activated.")
        self.extra_sig.emit()

    def check_available_username(self, username):
        status_code, message, req_reg = self._check_status()
        if status_code == -1 and message == "":  # user not registered yet
            code_, message = req_reg.check_username_exists(username)
            if code_ is True:
                self.status.emit("Username already taken")


class CheckLogin(QtCore.QObject):
    """
    check in `user` table to find if there are any user with same username and password
    """
    status = QtCore.pyqtSignal(object)  # returns login status
    message = QtCore.pyqtSignal(object)  # pop-up message box
    reg_log = QtCore.pyqtSignal(object)  # real-time status
    extra_sig = QtCore.pyqtSignal()  # an extra signal to perform single statement operation on emit

    def __init__(self, u_name: str, password: str, email_id: str, raw_passwd=True):
        """
        Initialize for after login operations

        :param u_name: username to check for login validity
        :param password: plain text password to check for login validity
        :param email_id: email-id to decrypt/encrypt user password
        :param raw_passwd: If true -> means, password is raw text, else password in encoded
        """
        super(CheckLogin, self).__init__()
        self.email_id = email_id
        self.uname = u_name
        self.password_dec = None
        if not raw_passwd:
            self.password_enc = password
        else:
            self.password_dec = password
            self.password_enc = encrypto.generate_password_hash(password, self.email_id)  # encrypted app password

    def reset_password(self, new_password: str):
        login_manager = Cloud.CloudLoginManager(self.uname, self.email_id, self.password_enc)
        status_code, message, user_data = login_manager.reset_password(new_password)
        self.reg_log.emit(message)
        self.status.emit((status_code, user_data))
        self.extra_sig.emit()

    def check_security_string(self, hashed_sec_string: str):
        login_manager = Cloud.CloudLoginManager(self.uname, self.email_id, self.password_enc)
        status_code, message = login_manager.check_security_hash(hashed_sec_string)
        self.reg_log.emit(message)
        self.status.emit((status_code, message, (self.uname, self.email_id)))
        self.extra_sig.emit()

    def check_user_table(self):
        login_manager = Cloud.CloudLoginManager(self.uname, self.email_id, self.password_enc)
        status_code, message, user_data = login_manager.perform_login(plain_passwd=self.password_dec)
        # self.message.emit(message)
        self.status.emit((status_code, message, user_data))
        self.extra_sig.emit()

    def update_login_time(self):
        login_manager = Cloud.CloudLoginManager(self.uname, self.email_id, self.password_enc)
        message = login_manager.update_login_time()
        self.reg_log.emit(message)
        self.extra_sig.emit()

    @QtCore.pyqtSlot()
    def update_logout_time(self):
        login_manager = Cloud.CloudLoginManager(self.uname, self.email_id, self.password_enc)
        message = login_manager.update_logout_time()
        self.reg_log.emit(message)
        self.extra_sig.emit()
