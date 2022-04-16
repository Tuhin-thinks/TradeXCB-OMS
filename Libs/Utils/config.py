import os.path
from datetime import datetime
from functools import lru_cache

import pandas as pd
import requests

from Libs.Storage.manage_local import set_user_preference_table
from Libs.globals import exception_handler, settings

logger = exception_handler.getAlgoLogger("algo.config")
instruments_file_loc = os.path.join(settings.DATA_FILES['INSTRUMENTS_CSV'])


def download_instruments_file(_test_load=False, _try_count=0):
    try:
        last_updated = datetime.fromtimestamp(os.stat(instruments_file_loc).st_mtime)
        days_difference = (datetime.today() - last_updated).days
    except (FileExistsError, FileNotFoundError):
        days_difference = 0

    if not os.path.exists(instruments_file_loc) or days_difference > 0:
        response = requests.get("https://api.kite.trade/instruments?api_key=kitefront")
        file_pointer = open(instruments_file_loc, "w")
        file_pointer.write(response.text)
        logger.info("Instruments File updated...")

    # test if download of instruments csv was successful
    if _test_load:
        try:
            return pd.read_csv(instruments_file_loc)['tradingsymbol']
        except KeyError:
            if _try_count < 3:
                _try_count += 1
                logger.info("Instruments File not found, trying again...")
                return download_instruments_file(_test_load=True, _try_count=_try_count)
            else:
                logger.info("Instruments File not found, count exceeded, aborting process...")
                return None


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
            response = requests.get("https://api.kite.trade/instruments?api_key=kitefront")
            with open(instruments_file_loc, "w") as file_pointer:
                file_pointer.write(response.text)
        return pd.read_csv(instruments_file_loc)


def set_quantity_freeze_limits():
    def lot_size_mapper(series):
        symbol_name = series['SYMBOL'].strip()
        vol_frz_qty = series['VOL_FRZ_QTY']
        try:
            return round(vol_frz_qty / instruments_df[instruments_df['name'] == symbol_name]['lot_size'].values[0])
        except IndexError:
            print(f"{symbol_name=}")
            return pd.NA

    freeze_lims_file_loc = settings.DATA_FILES['QTY_FREEZE_LIMIT_CSV']
    if os.path.exists(freeze_lims_file_loc):
        freeze_lim_df = pd.read_csv(freeze_lims_file_loc)
        freeze_lim_df['SYMBOL'] = freeze_lim_df['SYMBOL'].str.strip()
        freeze_lim_df['VOL_FRZ_QTY'] = freeze_lim_df['VOL_FRZ_QTY'].astype(int)
        instruments_df = load_instruments_csv(broker="kite")

        temp_df = freeze_lim_df.copy()
        temp_df['lot_freeze_limit'] = freeze_lim_df[["VOL_FRZ_QTY", 'SYMBOL']].apply(lambda x: lot_size_mapper(x),
                                                                                     axis=1)
        temp_df.to_csv(freeze_lims_file_loc, index=False)

        freeze_limits_json = temp_df[["SYMBOL", "lot_freeze_limit"]].set_index('SYMBOL', drop=True)[
            "lot_freeze_limit"].to_json()

        set_user_preference_table({"freeze_limits": freeze_limits_json})
    else:
        logger.critical("Freeze Limits File not found")


def prepare_files():
    download_instruments_file(_test_load=True)
    # prepare freeze limits
    set_quantity_freeze_limits()
