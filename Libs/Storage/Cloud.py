import json
import traceback as tb
from datetime import datetime
from urllib.parse import quote_plus

import pymysql
from PyQt5 import QtCore
from sqlalchemy import create_engine, Table, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.schema import MetaData

from Libs.Storage import encrypto
from Libs.globals import *

logger = exception_handler.getFutureLogger(__name__)


END_POINT = "clientstore-do-user-10490870-0.b.db.ondigitalocean.com"
PORT = "25060"
DB_NAME = "ClientStore"
DEFAULT_USERNAME = "tradexcb_oms_lt"
DEFAULT_PASSWORD = "tradebot_algobeacon"


class RequestRegistration:
    def __init__(self, user_name: str, password: str,
                 email_id: str, f_name: str,
                 l_name: str, phone: str, security_string: typing.Union[str, None], ui_logger: 'QtCore.pyqtSignal'):
        self.db_password = DEFAULT_PASSWORD
        self.db_username = DEFAULT_USERNAME

        self.logger = ui_logger
        self.user_name = user_name
        self.phone = phone
        self.l_name = l_name
        self.f_name = f_name
        self.email_id = email_id
        self._meta = MetaData()
        self.passwd = password
        self.security_string = security_string

    def create_connection(self, engine: typing.Literal["pymysql", "sqlalchemy"] = "sqlalchemy"):
        try:
            if engine == "sqlalchemy":
                connection_uri = f"mysql+pymysql://{self.db_username}:{quote_plus(self.db_password)}@{END_POINT}:{PORT}/{DB_NAME}?charset=utf8mb4"
                db_engine = create_engine(connection_uri)
                self._meta.reflect(bind=db_engine)
                return db_engine
            elif engine == "pymysql":
                conn = pymysql.connect(
                    host=END_POINT,
                    port=int(PORT),
                    user=self.db_username,
                    password=self.db_password,
                    db=DB_NAME,
                )
                return conn
        except Exception as e:
            logger.warning(f"Failed to connect to Server, {e.__str__()}", exc_info=True)

    def create_registration(self):
        """
        :returns code[
            0-> already registered ,
            1-> newly registered in cloud,
            -1-> registration failed
         ]
        """
        try:
            db_engine = self.create_connection()
            if not db_engine:
                return -1, "Access Denied, Cannot connect to Server"
        except OperationalError as e:
            traceback.print_exc()
            return -1, "Access Denied, Cannot register User."

        try:
            with db_engine.connect() as conn:
                table_user_req: Table = self._meta.tables['user_request_table']
                # if user is not registered with this mail id
                table_insert_stmt = table_user_req.insert().values(
                    {"first_name": self.f_name,
                     "last_name": self.l_name,
                     "user_name": self.user_name,
                     "email_id": self.email_id,
                     # upload encrypted password to cloud
                     "password": encrypto.generate_password_hash(self.passwd, self.email_id),
                     "phone": self.phone,
                     "security_string": self.security_string}
                )
                user_req_res = conn.execute(table_insert_stmt)
                user_id = user_req_res.inserted_primary_key[0]
                table_user_app_registry = self._meta.tables['user_app_registry']
                table_insert_stmt_2 = table_user_app_registry.insert().values(
                    {"app_id": settings.APP_ID,
                     "user_id": user_id}
                )
                conn.execute(table_insert_stmt_2)
                self.logger.emit("registration completed...")
            db_engine.dispose()
            db_engine = None
            return 1, "User Registration complete, Restart the application now."
        except Exception as e:
            self.logger.emit(f"Err occurred: {e.__str__()}")
            logger.critical(e.__str__(), exc_info=True)
            return -1, "some error occurred cannot register user"
        finally:
            if db_engine:
                db_engine.dispose()

    def check_registration_status(self):
        """
        To check registration status of a user
        :returns -1 if user not registered or invalid credentials
        string [pending/approved] is user is registered
        """
        conn = self.create_connection(engine="pymysql")
        if not conn:
            self.logger.emit("Access denied")
            return -1, "Access Denied/Cannot connect to Server"

        select_stmt = "select status from user_request_table where user_name=%s and email_id=%s;"
        cursor = conn.cursor()
        cursor.execute(select_stmt, (self.user_name, self.email_id))
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        cursor = None
        conn = None
        if data:
            return data[0], \
                   "User already registered"  # returns pending/approved (implies user is already registered)
        else:
            self.logger.emit("User not registered yet")
            return -1, ""

    def check_username_exists(self, username: str):
        """
        Checks whether a username is already taken or available,
        This step is done after username's basic validity check
        """
        db_engine = self.create_connection()
        if not db_engine:
            self.logger.emit("Access denied")
            return -1, "Access Denied, Cannot connect to Server"

        with db_engine.connect() as conn:
            user_req_table: Table = self._meta.tables['user_request_table']
            select_stmt = select(user_req_table.c.username).where(user_req_table.c.username == username)
            res_obj = conn.execute(select_stmt)
            data = res_obj.fetchone()
        db_engine.dispose()
        if data:
            return True, ""
        else:
            return False, ""


class CloudLoginManager:
    def __init__(self, user_name: str, email_id: str, password_enc: str = None):
        self.email_id = email_id
        self.user_name = user_name
        self.password_enc = password_enc  # enc password
        self._meta = MetaData()

    def create_connection(self, engine="sqlalchemy"):
        if engine == "sqlalchemy":
            try:
                connection_uri = f"mysql+pymysql://{DEFAULT_USERNAME}:{quote_plus(DEFAULT_PASSWORD)}@{END_POINT}:{PORT}/{DB_NAME}?charset=utf8mb4"
                db_engine = create_engine(connection_uri)
                self._meta.reflect(bind=db_engine)
                return db_engine
            except Exception as e:
                logger.critical(f"Failed to connect to server. {e.__str__()}", exc_info=True)
                tb.print_tb(e.__traceback__)
                tb.print_exc()

        elif engine == "pymysql":
            try:
                conn = pymysql.connect(
                    host=END_POINT,
                    port=int(PORT),
                    user=DEFAULT_USERNAME,
                    password=DEFAULT_PASSWORD,
                    db=DB_NAME,
                )
                return conn
            except Exception as e:
                logger.critical(f"Failed to connect to server. {e.__str__()}", exc_info=True)

    def check_security_hash(self, hashed_string: str):
        """
        Matched security question against database
        :param hashed_string:
        :return:
        """
        connection = self.create_connection("pymysql")
        if not connection:
            return -1, "Access Denied, Cannot connect to Server", ()
        cursor = connection.cursor()

        security_check_query = '''
        SELECT
            user_request_table.security_string
        FROM
            user_request_table
                INNER JOIN
            user_app_registry ON user_app_registry.app_id = %s
                AND user_request_table.email_id = %s
                AND user_request_table.user_name = %s;'''

        cursor.execute(security_check_query, (settings.APP_ID,
                                              self.email_id,
                                              self.user_name))
        data = cursor.fetchone()
        if data:
            if data[0] == hashed_string:
                return 0, "Security question & answer matched."
            elif data[0] is None:
                return -1, "No security question/answer found for this user credentials."
            else:
                return -1, "Wrong security question or answer."
        else:
            return -1, "Invalid login credentials."

    @staticmethod
    def check_account_validity(cursor, user_id):
        query = """SELECT valid_from, valid_to from auth_users where user_request_id=%s;"""
        cursor.execute(query, (user_id,))
        data = cursor.fetchone()
        if data:
            return data
        else:
            return None

    def perform_login(self, plain_passwd:str):
        connection = self.create_connection(engine="pymysql")
        if not connection:
            return -1, "Access Denied, Cannot connect to Server", ()
        cursor = connection.cursor()

        password_check_query_ = """
SELECT
    user_request_table.user_id, password
FROM
    user_request_table
        INNER JOIN
    user_app_registry ON user_app_registry.app_id = %s
        AND user_request_table.email_id = %s
        AND user_request_table.user_name = %s
        AND user_app_registry.user_id = user_request_table.user_id;"""
        cursor.execute(password_check_query_, (settings.APP_ID, self.email_id, self.user_name))
        user_id__passwd = cursor.fetchone()

        if user_id__passwd and (user_id__passwd[1] == self.password_enc):  # login success if password matches
            data = self.check_account_validity(cursor, user_id__passwd[0])
            if data is None:
                return -1, f"<b>Free Trial Completed</b><br>Visit <a href=\"{settings.SITE_LINK}\">{settings.SITE_LINK}</a> for further information.", ()
            valid_from_dt_tm = data[0]
            valid_to_dt_tm = data[1]
            if None in (valid_from_dt_tm, valid_to_dt_tm):
                return -1, f"<b>Invalid authorization</b><br>Please Visit <a href=\"{settings.SITE_LINK}\">{settings.SITE_LINK}</a> for support/help.", ()
            if valid_from_dt_tm <= datetime.now() <= valid_to_dt_tm:
                print(f"License valid till: {valid_to_dt_tm}")
            else:
                return -1, f"<b>Free Trial Completed</b><br>Visit <a href=\"{settings.SITE_LINK}\">{settings.SITE_LINK}</a> for further information.", ()

            user_data_query = f"select first_name, last_name, user_name, password, email_id, phone from user_request_table where user_id=%s;"
            cursor.execute(user_data_query, (user_id__passwd[0],))
            first_name, last_name, user_name, password_enc, email_id, phone = cursor.fetchone()
            cursor.close()
            connection.close()
            return 0, "Login Success", (first_name, last_name, user_name, plain_passwd, email_id, phone)
        else:
            cursor.close()
            connection.close()
            return -1, "Login Denied", ()

    def get_user_request_id(self):
        connection = self.create_connection(engine="pymysql")
        if connection is None:
            return -1, None, None
        cursor = connection.cursor()
        get_user_id_query = """SELECT user_id from user_request_table where user_name=%s and email_id=%s;"""
        cursor.execute(get_user_id_query, (self.user_name, self.email_id))
        data = cursor.fetchone()
        if data:
            cursor.close()
            return 0, connection, data[0]
        else:
            cursor.close()
            return -1, None, None

    def update_login_time(self):
        status, connection, user_id = self.get_user_request_id()
        if connection is None or status == -1:
            return "Cannot connect to Server"
        cursor = connection.cursor()
        update_login_query = """INSERT INTO user_log (user_id, login_time) VALUES (%s, %s)
         ON DUPLICATE KEY UPDATE login_time=%s;"""
        time_stamp = datetime.now()
        cursor.execute(update_login_query, (user_id, time_stamp, time_stamp))
        connection.commit()
        cursor.close()
        connection.close()
        return "Updated login time"

    def update_logout_time(self):
        status, connection, user_id = self.get_user_request_id()
        if connection is None or status == -1:
            return "Cannot connect to Server"
        cursor = connection.cursor()
        update_logout_query = """INSERT INTO user_log (user_id, logout_time) VALUES (%s, %s)
                 ON DUPLICATE KEY UPDATE logout_time=%s;"""
        time_stamp = datetime.now()
        cursor.execute(update_logout_query, (user_id, time_stamp, time_stamp))
        connection.commit()
        cursor.close()
        connection.close()
        return "Updated logout time"

    def reset_password(self, new_password: str):
        connection = self.create_connection(engine="pymysql")
        if not connection:
            return -1, "Access Denied, Cannot connect to Server", ()
        cursor = connection.cursor()

        reset_password_query = """
        UPDATE user_request_table set password=%s where user_name=%s and email_id=%s;
        """
        cursor.execute(reset_password_query, (encrypto.encrypt_db_pass(new_password, self.email_id),
                                              self.user_name, self.email_id))
        connection.commit()
        cursor.close()
        connection.close()
        return 0, "Password has been reset successfully.", ()


class DownloadTableData:
    def __init__(self, user_name: str, email_id: str, password: str):
        self.email_id = email_id
        self.user_name = user_name
        self.password = password  # password dec
        self._meta = MetaData()

    def create_connection(self, engine="sqlalchemy"):
        if engine == "sqlalchemy":
            try:
                connection_uri = f"mysql+pymysql://{DEFAULT_USERNAME}:{quote_plus(DEFAULT_PASSWORD)}@{END_POINT}:{PORT}/{DB_NAME}?charset=utf8mb4"
                db_engine = create_engine(connection_uri)
                self._meta.reflect(bind=db_engine)
                return db_engine
            except Exception as e:
                logger.critical(f"Failed to connect to Server, {e.__str__()}")

        elif engine == "pymysql":
            try:
                conn = pymysql.connect(
                    host=END_POINT,
                    port=int(PORT),
                    user=DEFAULT_USERNAME,
                    password=DEFAULT_PASSWORD,
                    db=DB_NAME,
                )
                return conn
            except Exception as e:
                logger.critical(f"Failed to connect to database, {e.__str__()}")

    def download_data(self, time_frame: int) -> typing.Tuple[int, typing.Any]:
        """download table data for a specific time frame
        time_frame: 5, 10 or 15, thus any [(number % 5) - 1] is the index for the view names to access.
        """

        connection = self.create_connection(engine='pymysql')
        if not connection:
            return -1, "Access Denied, Cannot connect to Server"
        cursor = connection.cursor()
        table_name = ("five_minutes_frame", "ten_minutes_frame", "fifteen_minutes_frame")[(time_frame // 5) - 1]
        cursor.execute(f"select table_data from {table_name};")
        data = cursor.fetchone()
        cursor.close()
        connection.close()
        if data:
            json_data = data[0]
            json_records = json.loads(json.loads(json_data))  # loads list of dataframes (to_json)
            return 0, json_records
        else:
            return -1, f"Cannot load table data for time frame: {table_name}"

    def get_notifications(self, limit_days: int) -> typing.Tuple[int, typing.Any]:
        connection = self.create_connection(engine="pymysql")
        if not connection:
            return -1, "Access denied, cannot connect to Server"

        try:
            cursor = connection.cursor()
            table_name = "notifications"

            cursor.execute(f"""
            select notification_time, notification_text from {table_name} where
            (target_app_id={settings.APP_ID} or target_app_id=0) and (target_app_version='{settings.App_VERSION}'
            or target_app_version is null);""")

            data = cursor.fetchall()
            cursor.close()
            connection.close()
            if not data:
                return 1, "No notifications"
            else:
                last_notification = None
                notifications = []
                for row in data:
                    date_time = row[0]
                    if (datetime.today() - date_time).days <= limit_days:
                        notification_text = row[1]
                        # notifications.append((date_time, notification_text))
                        last_notification = [(date_time, notification_text)]
                return 0, last_notification
        except Exception as e:
            logger.critical(f"Failed to fetch notifications: {e.__str__()}", exc_info=True)
            return -1, f"Failed to fetch notifications: {e.__str__()}"
