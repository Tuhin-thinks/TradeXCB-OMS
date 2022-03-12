import base64
import json
import typing

from Libs.Storage import manage_local as localdb, app_data
from Libs.Utils import exception_handler

logger = exception_handler.getFutureLogger("load_data")


def read_user_api_details(unique_identifier: typing.Union[None, str] = None) -> typing.List[typing.Dict]:
    """LOAD user's API details"""
    settings_dict = dict(zip(app_data.API_DETAILS_COLUMNS, [""] * len(app_data.API_DETAILS_COLUMNS)))
    try:
        all_api_details = []
        api_uid_list = localdb.get_all_api_uids()
        for api_uid in api_uid_list:
            api_details_base64_enc = localdb.read_api_details(api_uid)
            dec_string = base64.b64decode(api_details_base64_enc).decode("utf-8")
            settings_dict = json.loads(dec_string)
            all_api_details.append(settings_dict)
        return all_api_details
    except Exception as e:
        logger.error(f"Cannot read user settings/No API details found, {e.__str__()}", exc_info=True)
    return [settings_dict]


def save_user_api_details(unique_identifier: str, details_dict: typing.Dict):
    """SAVE user's API details"""
    try:
        json_string = json.dumps(details_dict, indent=3).encode("utf-8")
        enc_string = base64.b64encode(json_string).decode("utf-8")
        res = localdb.write_api_details(unique_identifier, enc_string)
        if res:
            logger.info("Details saved Successfully")
            return True
    except Exception as e:
        logger.error(f"Cannot save settings/No API details found, {e.__str__()}", exc_info=True)
    return False


def clear_api_details():
    try:
        localdb.clear_all_api_details()
    except Exception:
        logger.error("Cannot delete API details.")
