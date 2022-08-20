import logging
import random
import os

APP_ID = 4  # TradeXCB
APP_NAME = "TradeXCB"
EXTENSION = "-BETA"
App_VERSION = "0.1.10"
SITE_LINK = "https://www.trendmyfriend.co.in"
LOGGING_LEVEL = logging.DEBUG
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
MIN_HEIGHT = 550 if os.name == "posix" else 450
INSTRUMENTS_EXPIRY_THRESHOLD = 60  # in days
DATA_FILES = {
    "tradexcb_excel_file": os.path.join(DATA_FILES_DIR, "tradexcb_strategy.xlsx"),
    "POSITIONS_FILE_PATH": os.path.join(DATA_FILES_DIR, "PNLATRTS_All_User.csv"),
    "INSTRUMENTS_CSV": os.path.join(DATA_FILES_DIR, "Instruments.csv"),
    "symbols_mapping_csv": os.path.join(DATA_FILES_DIR, "SYMBOL_MAPPING.csv")
}
TRADING_NAME_INDEX_MAPPING = {
    "Real Live Trading": 0,
    "Real Paper Trading": 1,
    "Backtesting": 2
}
AVAILABLE_LOGOS_RCS = [
    "tradexcb_logo.png"
]
APP_ICON = "TradeXCB - icon.png"
CURRENT_APP_LOGO = random.choice(AVAILABLE_LOGOS_RCS)
APP_LOGO_img_only = "tradexcb_logo.png"
THEME_NAME_MAPPING = {
    "Dark.xml": ":/icons/app_logo_white.png"

}
days2_expire = 60
