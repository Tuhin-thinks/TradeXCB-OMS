import typing
import pandas as pd
import re

import numpy as np


def get_strikes(kite, _df, nfo_symbol, nse_symbol, atm_string: str, ce_pe_filter: str, expiry_date: str, exchange: str):
    """
    :param nse_symbol: nse_code
    :param nfo_symbol: nfo_code
    :param exchange: exchange entered in excel
    :param kite: authenticated kite instance
    :param _df: instruments.csv
    :param atm_string: ATM, ATM+1, ATM-1 etc...
    :param ce_pe_filter: "CE" or "PE"
    :param expiry_date: example: "2022-01-27"
    :return:
    """
    # instr_file[(instr_file.name == symbol) & (instr_file.days2expire < 30) & (instr_file.days2expire >= 0)]['expiry'].unique().tolist()
    name__ts = ""
    if not is_atm_string_eq_atm_format(atm_string):
        return atm_string
    spt_prc = kite.ltp(nse_symbol)[nse_symbol]['last_price']
    # exchange = symbol.split(":")[0].split()[0]  # to get exchange from symbol name
    if exchange == 'MCX' or exchange == 'CDS':
        name__ts = _df[(_df.tradingsymbol == nfo_symbol)].name.values[0]
        strike_arr = _df[(_df.name == name__ts) & (_df.segment == f"{exchange}-OPT")]
    else:
        strike_arr = _df[(_df.name == nfo_symbol)]
    strike_arr = np.array(sorted(list(set(strike_arr.strike.values[::2]))))
    absprc = np.abs(strike_arr - spt_prc)
    atm_index = np.where(absprc == absprc.min())[0][0]
    # max_strikes = 1
    adjustment = parse_ATM_adjustment(atm_string)
    required_index = atm_index + adjustment
    adjusted_atm = strike_arr[required_index]
    if exchange == 'MCX' or exchange == 'CDS':
        trading_symbol_name = _df[(_df.name == name__ts) &
                                  (_df.segment == f"{exchange}-OPT") &
                                  (_df.expiry == expiry_date) &
                                  (_df.strike == adjusted_atm) &
                                  (_df.instrument_type == ce_pe_filter)]['tradingsymbol'].values.tolist()[0]
    else:
        trading_symbol_name = _df[(_df.name == nfo_symbol) &
                                  (_df.expiry == expiry_date) &
                                  (_df.strike == adjusted_atm) &
                                  (_df.instrument_type == ce_pe_filter)]['tradingsymbol'].values.tolist()[0]
    print(f"{atm_string} =", adjusted_atm)
    return trading_symbol_name


def parse_ATM_adjustment(atm_string: str) -> int:
    atm_string_pattern = "ATM(?P<adjustment>.+)"
    match_obj = re.search(atm_string_pattern, atm_string)
    if match_obj:
        match_dict = match_obj.groupdict()
        adjustment = eval(match_dict['adjustment'])
        return adjustment
    else:
        return 0


def is_atm_string_eq_atm_format(atm_string: str):
    atm_string_pattern = "ATM(?P<adjustment>.+)"
    match_obj = re.search(atm_string_pattern, atm_string)
    if match_obj:
        return True
    else:
        if atm_string == "ATM":
            return True
        return False


def get_quote(kite, instrument_token_list: typing.List[str]):
    return kite.quote(instrument_token_list)


def create_symbols_mapping(filename: str):
    symbol_file = pd.read_excel(filename, sheet_name="Symbol_Mapping")
    df_symbols = symbol_file[['NFO_CODE', 'NSE_CODE']]
    nfo_symbols_array = df_symbols['NFO_CODE'].values
    nfo_nse_map = df_symbols.set_index('NFO_CODE').to_dict()['NSE_CODE']
    return nfo_symbols_array, nfo_nse_map


if __name__ == '__main__':
    _atm_index = parse_ATM_adjustment("ATM" + input("ATM"))
    print("atm index:", _atm_index)
