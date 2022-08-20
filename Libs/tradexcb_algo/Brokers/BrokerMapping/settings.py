import os
import json

BASE = os.path.dirname(os.path.abspath(__file__))

LOG_FILE_DIR = os.path.join(BASE, "logs")
UTILS_DIR = os.path.join(BASE, "utils")
INSTRUMENTS_FILE = os.path.join(UTILS_DIR, "Instruments.csv")
BROKERS_DIR = os.path.join(BASE, "brokers")
BROKER_CREDENTIALS_FILE = os.path.join(BASE, "credentials.json")
MAIN_BROKER_API_DIR = os.path.join(BASE, "main_borker_api")
MASTER_DIR = os.path.join(BASE, 'master_file')
EDEL_INSTRUMENTS_FILE = os.path.join(MASTER_DIR, "edelweiss_instruments.csv")
ANGEL_INSTRUMENT_FILE = os.path.join(MASTER_DIR, "angel_instruments.csv")

if not os.path.exists(BROKER_CREDENTIALS_FILE):
    d = {
        "ANGEL": {

        },
        "FIVE_PAISA": {
            "STOCK BROKER NAME": "five_paisa",
            "EMAIL": "",
            "WEB_PASSWORD": "",
            "DOB": "",
            "APP_NAME": "",
            "APP_SOURCE": "",
            "USER_ID": "",
            "APP_PASSWORD": "",
            "USER_KEY": "",
            "ENCRYPTION_KEY": ""
        },
        "ZERODHA": {

        },
        "MOTILAL_OSWAL": {

        },
        "KOTAK": {

        },
        "EDELWEISS": {

        }
    }
    file = open(BROKER_CREDENTIALS_FILE, 'w')
    json.dump(d, file, indent=4)