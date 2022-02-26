import logging
import random
import os

APP_ID = 3  # iDelta+
APP_NAME = "iDelta+"
EXTENSION = "-BETA"
App_VERSION = "0.1.4"
SITE_LINK = "https://www.trendmyfriend.co.in"
LOGGING_LEVEL = logging.INFO
adjust_minutes = 2.5  # adjustments on time-frame check delay (check interval = 2.5 minutes less than time-frame)
LOG_FILE_DIR = os.path.realpath(os.path.join("Libs", "Logs"))
LOG_EXPIRY_DURATION = 1  # in days
TABLE_FONT_SIZE = 8
HEADER_VIEW_FONT = TABLE_FONT_SIZE
LOG_MATCHER_REGEX = r"(?P<timestamp>.*) \*\*\* (?P<log>.*) \*\*\* (?P<message>.*) \*\*\* (?P<source>.*)"
USER_SETTINGS_JSON = os.path.realpath("user_details.json")
DEFAULT_DATA_FILE = os.path.realpath(os.path.join("Libs", "Storage", "DEFAULT_VALUES.json"))
ORDER_BOOK_LOG_DICT_PATTERN = r"\{.*\}"
DATETIME_FMT_STRING = "%Y-%m-%d %H:%M:%S"
DATA_FILES_DIR = os.path.realpath(os.path.join("Libs", "Files", "DataFiles"))
TB_DATA_FOLDER = os.path.realpath(os.path.join("Libs", "TimeBasedStrategy", "TB_DataFiles"))
MIN_HEIGHT = 550 if os.name == "posix" else 450
INSTRUMENTS_EXPIRY_THRESHOLD = 60  # in days
DATA_FILES = {
    "Delta_plus_Algo_File": os.path.join(DATA_FILES_DIR, "time_based_renamed.xlsx"),
    "POSITIONS_FILE_NAME": os.path.join(DATA_FILES_DIR, "TIME_BASED_PNL.csv"),
    "INSTRUMENTS_CSV": os.path.join(DATA_FILES_DIR, "Instruments.csv"),
    "get_user_session_pickle": os.path.join(TB_DATA_FOLDER, "token.pickle"),
    "symbols_mapping_csv": os.path.join(TB_DATA_FOLDER, "SYMBOL_MAPPING.csv")
}
TRADING_NAME_INDEX_MAPPING = {
    "Real Live Trading": 0,
    "Real Paper Trading": 1,
    "Backtesting": 2
}
AVAILABLE_LOGOS_RCS = [
    "iDelta-icon-full.jpeg"
]
CURRENT_APP_LOGO = random.choice(AVAILABLE_LOGOS_RCS)
APP_LOGO_img_only = "iDelta-icon-logo.jpeg"
THEME_NAME_MAPPING = {
    "Dark.xml": ":/icons/app_logo_white.png"

}
if not os.path.exists(TB_DATA_FOLDER):
    os.mkdir(TB_DATA_FOLDER)
days2_expire = 60
