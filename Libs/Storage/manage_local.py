import json
import os
import sqlite3
import traceback as tb
import typing
from sqlite3 import Error
from typing import Tuple, Dict

from sqlalchemy import create_engine, Table, String, MetaData, func, select, Integer, Column
from sqlalchemy.dialects.sqlite import Insert
from sqlalchemy.engine.mock import MockConnection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateTable

from Libs.globals import exception_handler
from . import encrypto

BASE = os.path.realpath(os.path.dirname(__file__))
LOCAL_DB_PATH = os.path.join(BASE, "locorum")
logger = exception_handler.getFutureLogger("Local_Store_Manager")


def create_connection(engine: typing.Literal['sqlalchemy', 'sqlite3'] = "sqlalchemy"):
    if engine == "sqlalchemy":
        try:
            db_engine: 'MockConnection' = create_engine(f"sqlite:///{LOCAL_DB_PATH}",
                                                        connect_args={'check_same_thread': False})
            meta = MetaData()
            meta.reflect(bind=db_engine)
            return db_engine, meta
        except Exception as e:
            logger.critical(f"Error connecting sqlite db: {tb.print_tb(e.__traceback__)}")
    elif engine == "sqlite3":
        try:
            conn = sqlite3.connect(LOCAL_DB_PATH, check_same_thread=False)
            return conn
        except Error:
            return None


def count_rows():
    """count number of rows in user_data table"""
    try:
        db_engine, meta = create_connection()
        with db_engine.connect() as conn:
            table_user_data: Table = meta.tables['user_data']
            count_stmt = select(func.count(table_user_data.c.db_user_name))
            row_count_ = conn.execute(count_stmt).scalar()
        db_engine.dispose()
        return row_count_
    except (AttributeError, KeyError):
        return 0


def pack_data(user_data, decrypt_passwd=False) -> Tuple[int, Dict]:
    """
    to pack user details row into a dictionary
    :param decrypt_passwd: whether to decrypt password or not
    :param user_data: tuple of user data
    :return: Dict
    """
    user_name_ = user_data[0]
    f_name_ = user_data[1]
    l_name_ = user_data[2]
    password_enc_ = user_data[3]
    email_id_ = user_data[4]
    phone_ = user_data[5]
    return 1, {
        "user_name": user_name_,
        "f_name": f_name_,
        "l_name": l_name_,
        "password": (password_enc_ if not decrypt_passwd else encrypto.decrypt_db_pass(password_enc_, email_id_)),
        "email_id": email_id_,
        "phone": phone_
    }


def create_tables():
    """Create local storage table from scratch"""

    db_engine, meta = create_connection()
    conn = db_engine.connect()
    if not conn:
        print("Failed to connect to database")
        return

    row_count = count_rows()
    flag = row_count == 0

    table_user_details = Table("user_data", meta,
                               Column("user_name", String(120), primary_key=True, nullable=False),
                               Column("f_name", String(50)),
                               Column("l_name", String(50)),
                               Column("password", String(120), nullable=False),
                               Column("email_id", String(60)),
                               Column("phone", String(30)),
                               extend_existing=True
                               )

    t_create_query = CreateTable(table_user_details, if_not_exists=True)
    conn.execute(t_create_query)

    table_app_config = Table("APP_CONFIG", meta,
                             Column("FIELD_NAME", String(120), primary_key=True, nullable=False, unique=True),
                             Column("FIELD_VALUE", String(120), nullable=False),
                             extend_existing=True)
    t_create_query = CreateTable(table_app_config, if_not_exists=True)
    conn.execute(t_create_query)

    table_api_details = Table("table_api_details", meta,
                              Column("row_id", Integer, primary_key=True, nullable=False, unique=True),
                              Column("field_name", String(), nullable=False, unique=True),
                              Column("value", String(), nullable=False),
                              sqlite_autoincrement=True,
                              extend_existing=True
                              )
    t_create_query = CreateTable(table_api_details, if_not_exists=True)
    conn.execute(t_create_query)

    if flag:
        #           FNAME LNAME  USERNAME   PASSWORD - TO ENCRYPT     EMAIL PHONE
        args_def = (None, None, "def-user", "secret-password", None, None)
        insert_user_data(*args_def)
    return row_count


def insert_user_data(f_name: str, l_name: str, user_name: str, password: str, email_id: str, phone: str):
    """
    insert a row in user_data table in local database
    :return:
    """

    db_engine, meta = create_connection()

    with db_engine.connect() as conn:
        table_user_data: Table = meta.tables['user_data']
        count_stmt = select(func.count(table_user_data.c.user_name))
        rows_count = conn.execute(count_stmt).scalar()

        if rows_count > 1:
            return

        encrypted_passwd = encrypto.encrypt_db_pass(password, email_id)

        # values for local storage
        insert_stmt = table_user_data.insert().values({
            'f_name': f_name,
            'l_name': l_name,
            'user_name': user_name,
            'password': encrypted_passwd,
            'email_id': email_id,
            'phone': phone
        })
        try:
            conn.execute(insert_stmt)
        except IntegrityError:
            # logger.warning('Integrity Error', exc_info=True)
            pass


def get_all_api_uids():
    """
    Get all field_name for table "table_api_details" and return as a list
    :return:
    """
    conn = create_connection("sqlite3")
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT field_name FROM table_api_details order by row_id;")
    rows = cursor.fetchall()
    return [row[0] for row in rows]


def read_api_details(field_name: str):
    """
    Read KiteConnect api details
    :param field_name:
    :return:
    """
    create_tables()

    db_engine, meta = create_connection()
    conn = db_engine.connect()
    if not conn:
        print("Failed to connect to database")
        return
    table_api_details = meta.tables['table_api_details']
    select_query = select(table_api_details.c.value).where(table_api_details.c.field_name == field_name)
    res = conn.execute(select_query)
    data = res.fetchone()
    conn.close()
    db_engine.dispose()
    if not data:
        return
    return data[0]  # should be base64 encoded string


def write_api_details(field_name: str, enc_string: str):
    """
    Write connect api details
    :param field_name:
    :param enc_string:
    :return:
    """
    create_tables()

    conn = create_connection(engine="sqlite3")
    if not conn:
        print("Failed to connect to database")
        return
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO table_api_details (field_name, value)
    VALUES(?, ?)
    ON CONFLICT(field_name) do UPDATE set value=?;
    """
    cursor.execute(insert_query, (field_name, enc_string, enc_string))
    conn.commit()
    conn.close()
    return True


def clear_all_api_details():
    conn = create_connection("sqlite3")
    if not conn:
        print('Failed to connect to database')
    cursor = conn.cursor()
    delete_query = """
    DELETE from table_api_details;
    """
    cursor.execute(delete_query)
    conn.commit()
    conn.close()
    return True


def get_to_fill_data() -> Tuple[int, typing.Dict]:
    """
    Get data to fill in registration form and login panel
    :return: valid data should return 1, tuple
    """
    create_tables()
    conn = create_connection(engine="sqlite3")
    if not conn:
        logger.critical("Failed to connect to local data")
        return -1, {}

    fetch_statement = "select user_name, f_name, l_name, password, email_id, phone from user_data where user_name!='def-user';"
    cursor = conn.cursor()
    res = cursor.execute(fetch_statement)
    data = res.fetchone()  # get default user data
    conn.close()
    if not data or len(data) < 6:
        return -1, {}
    return pack_data(data, decrypt_passwd=True)  # this data should be used to fill user's input fields


# --------------------- UPDATE USER PREFERENCE ----------------
def set_user_preference_table(update_dict: dict):
    """update user preference for application"""
    create_tables()  # create table if not exists
    db_engine, meta = create_connection()
    with db_engine.connect() as conn:
        table_app_config = meta.tables['APP_CONFIG']
        key, value = tuple(update_dict.items())[0]  # get only the first item of update dict
        to_set = {"FIELD_NAME": key, "FIELD_VALUE": value}
        query = Insert(table_app_config).on_conflict_do_update(index_elements=table_app_config.primary_key,
                                                               set_=to_set).values(to_set)
        conn.execute(query)


def get_user_preference_table(preference: str):
    """
    get user preference for the given preference string
    returns None if returned value is an empty tuple
    """
    create_tables()  # create table if not exists
    db_engine, meta = create_connection()
    with db_engine.connect() as conn:
        table_app_config = meta.tables['APP_CONFIG']
        query = select(table_app_config.c.FIELD_VALUE).where(table_app_config.c.FIELD_NAME == preference)
        res = conn.execute(query)
        data = res.fetchone()
    return data[0] if data else None


def set_custom_stylesheet_values():
    tab_padding_main = '8ex' if os.name == 'nt' else '2ex'
    tab_padding_sub = '8ex' if os.name == 'nt' else '2ex'
    min_tab_width_sub = '52ex' if os.name == 'nt' else '30ex'
    tab_min_height_main = '6ex' if os.name == 'nt' else '2.5ex'
    tab_min_height_sub = '5.5ex' if os.name == 'nt' else '2.0ex'
    main_tab_width = "200px" if os.name == 'nt' else '130px'
    min_tab_width_main = "50ex" if os.name == 'nt' else '25ex'

    res = get_user_preference_table("ui_data")
    if res:
        pass
    else:
        set_user_preference_table(
            {"ui_data": json.dumps({"tab_padding_main": tab_padding_main,
                                    "tab_padding_sub": tab_padding_sub,
                                    "min_tab_width_sub": min_tab_width_sub,
                                    "tab_min_height_main": tab_min_height_main,
                                    "tab_min_height_sub": tab_min_height_sub,
                                    "main_tab_width": main_tab_width,
                                    "min_tab_width_main": min_tab_width_main}, indent=2)})


def logout():
    """delete user login records from local database: locorum"""
    delete_query = """delete from user_data where user_name <> 'def-user';"""
    connection = create_connection("sqlite3")
    cursor = connection.cursor()
    cursor.execute(delete_query)
    connection.commit()


if __name__ == '__main__':
    # create_tables()
    # status = check_status()
    # print("Status now:", status)
    # data = get_user_data()
    # print(data[1])
    # print("\nInserting approved user data now...")
    # args = ("Raghav", "Basu", "raghavbasu", "raghav123", "raghav1234@mail.com", "(099)-755-8591", "pending")
    # insert_user_data(*args)
    # replace_with_or_passwd()
    # get_to_fill_data()
    pass
