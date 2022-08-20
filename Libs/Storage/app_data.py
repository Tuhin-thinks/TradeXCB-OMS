import json

from Libs.globals import *

BROKER_NAMES = ["Zerodha", "Angel", "IIFL", "Alice Blue"]

STRATEGIES = ["Default"]

strategies_name_to_img_mapper = {
    "Long IronFly": "LONG IRON BUTTERFLY",
    "Short IronFly": "SHORT IRON BUTTERFLY",
    "Long Strangle": "SHORT STRANGLE",
    "Short Straddle": "SHORT STRADDLE",
    "Long Straddle": "LONG STRADDLE",
    "Short Strangle": "SHORT STRANGLE"
}
with open(settings.DEFAULT_DATA_FILE, "r") as default_data:
    DEFAULT_DATA_ALL_FIELDS = json.load(default_data)
LOG_OPTIONS = ["Future Logs"]

OPTION_DETAILS_ANALYSIS = ['name', 'strike', 'days2expire', 'lot_size', 'OI_CE', 'Price_CE', 'Volume_CE', 'Vwap_CE',
                           'OI_PE', 'Price_PE', 'Volume_PE', 'Vwap_PE', 'Crossoverpct', 'crossover_side', 'pcr_oi',
                           'tradingsymbol_CE', 'tradingsymbol_PE', 'OI_PE_EMA_Crossover', 'OI_PE_Crossover_Timestamp',
                           'OI_CE_EMA_Crossover', 'OI_CE_Crossover_Timestamp', 'Future Name', 'Future_Vwap',
                           'Future_Price', 'OI_Crossover', 'OI_Crossover_Timestamp', 'Volume_FUT', 'OI_FUT',
                           'OPT_VWAP_CE_Action', 'OPT_VWAP_PE_Action', 'FUT_VWAP_Action']

OPTION_GREEKS = ['name', 'tradingsymbol_CE', 'tradingsymbol_PE', 'Opening OI_CE', 'Current OI_CE', 'Change in OI_CE',
                 'Opening OI_PE', 'Current OI_PE', 'Change in OI_PE', 'Opening DELTA_CE', 'Current DELTA_CE',
                 'Change in DELTA_CE', 'Opening DELTA_PE', 'Current DELTA_PE', 'Change in DELTA_PE', 'Opening IV_CE',
                 'Current IV_CE', 'Change in IV_CE', 'Opening IV_PE', 'Current IV_PE', 'Change in IV_PE',
                 'Opening Price_CE', 'Current Price_CE', 'Change in Price_CE', 'Opening Price_PE', 'Current Price_PE',
                 'Change in Price_PE', 'Opening THETA_CE', 'Current THETA_CE', 'Change in THETA_CE',
                 'Opening THETA_PE', 'Current THETA_PE', 'Change in THETA_PE']

DELTA_REPORT = ['name', 'tradingsymbol_CE', 'tradingsymbol_PE', 'lot_size', 'DELTA_CE', 'DELTA_PE', 'IV_CE', 'IV_PE',
                'Price_CE', 'Price_PE', 'THETA_CE',
                'THETA_PE', 'DELTA_CROSSOVER', "Time"]

PREMIUM_REPORT = ['name', 'tradingsymbol_CE', 'tradingsymbol_PE', 'lot_size', 'DELTA_CE', 'DELTA_PE', 'IV_CE',
                  'IV_PE', 'Price_CE', 'Price_PE', 'THETA_CE', 'THETA_PE', 'Vwap_CE', 'Vwap_PE', 'Vwap_Crossover_CE',
                  'Vwap_Crossover_PE',
                  "Time"]

CROSSOVER = ['name', 'strike', 'days2expire', 'Crossoverpct', 'crossover_side', 'tradingsymbol_CE', 'tradingsymbol_PE',
             'OI_PE_EMA_Crossover', 'OI_PE_Crossover_Timestamp', 'OI_CE_EMA_Crossover', 'OI_CE_Crossover_Timestamp',
             'Future Name', 'OI_Crossover', 'OI_Crossover_Timestamp', 'OPT_VWAP_CE_Action', 'OPT_VWAP_PE_Action',
             'FUT_VWAP_Action']

MARKET_PROFILE = ['tradingsymbol_CE', 'Price_CE', 'Vwap_CE', 'HIGH_Value_Node_CE',
                  'LOW_Value_Node_CE', 'Value_Area_CE', 'POC_CE', 'tradingsymbol_PE', 'Price_PE', 'Vwap_PE',
                  'HIGH_Value_Node_PE', 'LOW_Value_Node_PE', 'Value_Area_PE', 'POC_PE', 'Future Name', 'Future_Vwap',
                  'Future_Price', 'HIGH_Value_Node_Fut', 'LOW_Value_Node_Fut', 'Value_Area_FUT',
                  'POC_FUT']

SIGNALS = ['tradingsymbol_CE', 'tradingsymbol_PE', 'days2expire',
           'OI_CE_EMA_Crossover', 'Price_CE', 'Vwap_CE', "OPT_VWAP_CE_Action", 'Supertrend_CE',
           'OI_PE_EMA_Crossover', 'Price_PE', 'Vwap_PE', "OPT_VWAP_PE_Action", 'Supertrend_PE',
           'OI_Crossover', 'Future_Price', 'Future_Vwap', "FUT_VWAP_Action", "Supertrend_FUT",
           'Action_CE', 'TimeStamp_CE', 'Action_PE', 'TimeStamp_PE', "Action_FUT",
           "TimeStamp_FUT", 'tradingsymbol_CE', 'tradingsymbol_PE']

numerical_columns = ['price_ce', 'vwap_ce', 'price_pe', 'vwap_pe', 'future_vwap', 'future_price'] + \
                    ['change in oi_ce', 'change in oi_pe', 'change in delta_ce', 'change in delta_pe',
                     'change in iv_ce', 'change in iv_pe', 'change in price_ce', 'change in price_pe',
                     'change in theta_ce', 'change in theta_pe']

POSITIONS_COLUMNS = ['user_id', 'tradingsymbol', 'exchange', 'quantity', 'timeframe', 'entry_price',
                     'entry_time', 'exit_price', 'exit_time', 'target_price', 'sl_price', 'Row_Type', 'profit', 'ltp',
                     'Trend']

API_DETAILS_COLUMNS = ['Name', 'Stock Broker Name', 'apiKey', 'apiSecret', 'accountUserName', 'accountPassword',
                       'securityPin', 'totp_secret', 'No of Lots', 'consumerKey', 'accessToken', 'host', 'source',
                       'market_appkey', 'market_secretkey']

OMS_TABLE_COLUMNS = ["Instrument", "Entry Price", "Entry Time", "Exit Price", "Exit Time", "Order Type", "Quantity",
                     "Product Type", "Stoploss", "Target", "Order Status", "instrument_df_key", "Close Position?"]

broker_api_fields = {
    "zerodha": ["apiKey", "apiSecret", "accountUserName", "accountPassword", "totp_secret"],
    "angel": ["apiKey", "accountUserName", "accountPassword"],
    "iifl": ["apiKey", "apiSecret", "source", "host", "market_appkey", "market_secretkey"],
    "alice blue": ["accountUserName", "accountPassword", "securityPin", "apiSecret", "apiKey"],
    "common_fields": ["Stock Broker Name", "No of Lots", "Slices", "Name"]
}
