import string

from email_validator import validate_email, EmailNotValidError

from Libs.UI import user_login, Interact, api_inp_dialog
from Libs.Storage.app_data import broker_api_fields


def validate_reg_inp(user_name, f_name, l_name, email_id, password, phone, security_string, parent_ui: "user_login.Ui_MainWindow"):
    """
    :return bool flag
    """
    # ========================== validate : user_name ===========================
    flag = True
    message_ = ""
    if any((ch not in string.digits + string.ascii_letters for ch in user_name)):
        message_ += "*Username can only contain letters and digits."
        flag = False
    if len(user_name) < 6:
        message_ += "\n*Username cannot be less than 6 characters."
        flag = False

    if not flag:
        parent_ui.label_problem_username_create.setText(message_)
        return flag

    # ========================== validate : first name ===========================
    message_ = ""
    flag = True
    if not f_name.strip():
        message_ = "*Required Field."
        flag = False
    if any((ch not in string.ascii_letters for ch in f_name)):
        message_ += (", " if message_ else "") + "name cannot have special characters/digits;"
        flag = False

    if not flag:
        parent_ui.label_problem_first_name_create.setText(message_)
        return flag
    # ========================== validate : last name ===========================
    message_ = ""
    flag = True
    if not l_name.strip():
        message_ = "*Required Field."
        flag = False
    if any((ch not in string.ascii_letters for ch in l_name)):
        message_ += (", " if message_ else "") + "Name cannot have special characters/digits;"
        flag = False
        return flag
    # =========================== validate: email id =============================
    message_ = ""
    if not email_id.strip():
        message_ = "*Required Field."
        flag = False
        return flag
    try:
        validate_email(email_id)
    except EmailNotValidError:
        message_ += (", " if message_ else "") + "Invalid email-id;"
        flag = False
    if not flag:
        parent_ui.label_problem_create_email_id.setText(message_)
        return flag
    # ========================= validate: password ====================================

    if len(password) < 8:
        parent_ui.label_problem_password_create.setText("Password needs to be minimum 8 characters.")
        flag = False
        return flag

    # ========================== validate: phone========================================
    if len(phone) < 10:
        parent_ui.label_problem_mobile_no.setText("Invalid mobile number.")
        flag = False
        return flag

    return flag


def validate_login_inp(user_id: str, password: str, parent_ui: "user_login.Ui_MainWindow") -> bool:
    """
    currently user_id the username of user
    """
    flag = True
    if any((ch not in string.digits + string.ascii_letters for ch in user_id)):
        parent_ui.label_problem_userid.setText("Invalid username")
        flag = False
    if len(password) < 8:
        parent_ui.label_problem_password_2.setText("Password too short")
        flag = False
    return flag


def validate_api_inp(parent_ui: "api_inp_dialog", parent):
    details_dict = {"Stock Broker Name": parent_ui.comboBox_stock_broker_name.currentText()}
    userName = parent_ui.lineEdit_account_userName.text()
    if not userName:
        Interact.show_message(parent, "Incomplete Field", "<b>Username</b> field incomplete, please fill all the field before pressing submit.", "warning")
        return
    details_dict["Account User Name"] = userName

    api_secret = parent_ui.lineEdit_api_secret.text()
    if not api_secret:
        Interact.show_message(parent, "Incomplete Field", "<b>API Secret</b> field incomplete, please fill all the field before pressing submit.", "warning")
        return
    details_dict["API Secret"] = api_secret

    api_key = parent_ui.lineEdit_api_key.text()
    if not api_key:
        Interact.show_message(parent, "Incomplete Field", "<b>API Key</b> field incomplete, please fill up all the fields before pressing submit.", "warning")
        return
    details_dict["API Key"] = api_key

    totp_secret = parent_ui.lineEdit_totp_secret.text()
    if not totp_secret:
        Interact.show_message(parent, "Incomplete Field", "<b>TOTP Secret</b> field incomplete, please fill up all the fields before pressing submit.", "warning")
        return
    details_dict["TOTP Secret"] = totp_secret

    password = parent_ui.lineEdit_account_password.text()
    if not password:
        Interact.show_message(parent, "Incomplete Field", "<b>Account Password</b> field incomplete, please fill up all the fields before pressing submit.", "warning")
        return
    details_dict["Account Password"] = password

    sec_pin = parent_ui.lineEdit_account_sec_pin.text()
    if not sec_pin:
        Interact.show_message(parent, "Incomplete Field", "<b>Security Pin</b> field incomplete, please fill up all the fields before pressing submit.", "warning")
        return
    details_dict["Security Pin"] = sec_pin
    return details_dict


def is_valid_broker_field(broker_name: str, column_name: str):
    if not broker_name:  # for empty broker name show all the fields
        return True
    broker_name = broker_name.lower()
    fields_list = broker_api_fields[broker_name]
    common_fields = broker_api_fields["common_fields"]
    if column_name in fields_list:
        return True
    elif column_name in common_fields:
        return True
    else:
        return False
