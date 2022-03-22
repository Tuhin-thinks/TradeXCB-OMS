import pandas as pd
import os.path
from datetime import datetime
from functools import lru_cache

import requests

from Libs.globals import exception_handler, settings

logger = exception_handler.getAlgoLogger("algo.config")
instruments_file_loc = os.path.join(settings.DATA_FILES['INSTRUMENTS_CSV'])


def download_instruments_file():
    try:
        last_updated = datetime.fromtimestamp(os.stat(instruments_file_loc).st_mtime)
        days_difference = (datetime.today() - last_updated).days
    except (FileExistsError, FileNotFoundError):
        days_difference = 0

    if not os.path.exists(instruments_file_loc) or days_difference > 0:
        response = requests.get("https://api.kite.trade/instruments?api_key=")
        file_pointer = open(instruments_file_loc, "w")
        file_pointer.write(response.text)
        logger.info("Instruments File updated...")


def load_symbols_mapping_file():
    symbol_mapping_df = pd.read_csv(settings.DATA_FILES['symbols_mapping_csv'])
    return symbol_mapping_df


@lru_cache(maxsize=None)
def load_instruments_csv(broker="kite"):
    if broker.lower() == "kite":
        try:
            last_updated = datetime.fromtimestamp(os.stat(instruments_file_loc).st_mtime)
            days_difference = (datetime.today() - last_updated).days
        except (FileExistsError, FileNotFoundError):
            days_difference = 0

        if not os.path.exists(instruments_file_loc) or days_difference > 0:
            response = requests.get("https://api.kite.trade/instruments?api_key=")
            with open(instruments_file_loc, "w") as file_pointer:
                file_pointer.write(response.text)
                print("Instruments File updated...")
        return pd.read_csv(instruments_file_loc)
