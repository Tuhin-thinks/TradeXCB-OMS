import base64
import json
import typing

from Libs.Storage import manage_local as localdb
from Libs.Utils import exception_handler

logger = exception_handler.getFutureLogger("load_data")


def read_user_settings() -> typing.Dict:
    """LOAD user's API details"""
    settings_dict = {"Stock Broker Name": "", "API Key": "", "API Secret": "", "Account User Name": "",
                     "Account Password": "", "Security Pin": "", "TOTP Secret": ""}
    try:
        api_details_base64_enc = localdb.read_api_details()
        dec_string = base64.b64decode(api_details_base64_enc).decode("utf-8")
        settings_dict = json.loads(dec_string)
    except Exception:
        logger.error("Cannot read user settings/No API details found")
    return settings_dict


def save_user_details(details_dict: typing.Dict):
    """SAVE user's API details"""
    try:
        json_string = json.dumps(details_dict, indent=3).encode("utf-8")
        enc_string = base64.b64encode(json_string).decode("utf-8")
        res = localdb.write_api_details(enc_string)
        if res:
            logger.info("Details saved Successfully")
            return True
    except Exception:
        logger.error("Cannot read user settings/No API details found")
    return False
