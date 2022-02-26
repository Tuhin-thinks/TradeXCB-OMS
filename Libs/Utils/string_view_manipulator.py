import re


def humanize_string(string_data: str):
    """Remove all non-word characters including underscore `_` from string and return string in all uppercase"""
    if string_data.isdigit():
        if string_data == "1":
            return "YES"
        elif string_data == "0":
            return "NO"
    else:
        return re.sub("[^a-zA-Z0-9]", " ", string_data, re.I).upper()


def is_match_decimal(string_data: str, round_upto: int = 2):
    pattern = r"(^(?:-\d+|\d+)\.\d+$)"
    if re.match(pattern, string_data):
        return str(round(float(string_data), round_upto))
    else:
        return string_data


def map_shorts(header_string):
    item_shorts_map = {"CHANGE": "CHG", "CURRENT": "CURR", "OPENING": "OPG"}
    for org_string, to_map_string in item_shorts_map.items():
        header_string = header_string.replace(org_string, to_map_string)
    return header_string
