import pandas as pd
import os.path
from datetime import datetime

import requests

from Libs.globals import exception_handler, settings

logger = exception_handler.getIDeltaLogger("algo.config")


def download_instruments_file():
    try:
        last_updated = datetime.fromtimestamp(os.stat(settings.DATA_FILES['INSTRUMENTS_CSV']).st_mtime)
        days_difference = (datetime.today() - last_updated).days
    except (FileExistsError, FileNotFoundError):
        days_difference = 0

    if not os.path.exists(settings.DATA_FILES['INSTRUMENTS_CSV']) or days_difference > 0:
        response = requests.get("https://api.kite.trade/instruments?api_key=")
        file_pointer = open(settings.DATA_FILES['INSTRUMENTS_CSV'], "w")
        file_pointer.write(response.text)
        logger.info("Instruments File updated...")


def load_symbols_mapping_file():
    symbol_mapping_df = pd.read_csv(settings.DATA_FILES['symbols_mapping_csv'])
    return symbol_mapping_df
