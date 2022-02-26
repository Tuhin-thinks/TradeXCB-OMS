import pandas as pd


class StrategiesColumn:
    all_columns = ['Transaction_Type', 'Entry_Time', 'Exit_Time', 'Buy_Ltp_Percent', 'Sell_Ltp_Percent',
                               'Wait_Time', 'Symbol Name', 'Expiry Date', 'CE_Instrument', 'PE_Instrument', 'Exchange',
                               'No. of lots', 'stoploss_type', 'CE_Stoploss', 'tsl_type', 'CE_TSL', 'target_type',
                               'CE_target', 'PE_Stoploss', 'PE_TSL', 'PE_target']

    default_strategy_column = [
        'Trading Symbol',
        'Exchange',
        'Quantity',
        'Time Frame',
        'Buy LTP',
        'Sell LTP',
        'Target',
        'ATR Period',
        'Buy Flag',
        'Sell Flag',
        'Order Wait Time',
        'Stop Loss Type',
        'Stop Loss ATR',
        'Stop Loss Value',
        'Exit Criteria']

    vwap_column = ['VWAP Signal', 'VWAP']
    rsi_column = ['USE RSI', 'RSI', 'OverBought', 'OverSold', 'RSI MA Period', 'RSI Signal']
    open_interest_column = ['USE Open Interest', 'OI MA Period', 'OI Signal']
    volume_column = ['USE Volume', 'Volume MA', 'Volume Mulitples']
    donchain_channel_column = ['Donchain High', 'Donchain Low', 'Donchain Line', 'Donchain Channel',
                               'DC Signal']
    atrts_column = ['ATR TS Period', 'ATR TS Multiplier', 'ATRTS', 'ATRTS Signal']

    vwap_columns = ['vwap_signal', 'vwap']
    rsi_columns = ['use_rsi', 'RSI', 'overbought', 'oversold', 'rsi_ma_period', 'rsi_signal']
    open_interest_columns = ['use_oi', 'oi_ma_period', 'oi_signal']
    volume_columns = ['use_vol', 'volume_ma_tp', 'volume_ma_mulitple']
    donchain_channel_columns = ['dc_high', 'dc_low', 'dc_line', 'dc', 'dc_signal']
    atrts_columns = ['ATR TS Period', 'ATR TS Multiplier', 'ATRTS', 'atrts_signal']

    delta_plus_algo_columns = ['Transaction_Type', 'Entry_Time', 'Exit_Time', 'Buy_Ltp_Percent', 'Sell_Ltp_Percent',
                               'Wait_Time', 'Symbol Name', 'Expiry Date', 'CE_Instrument', 'PE_Instrument', 'Exchange',
                               'No. of lots', 'stoploss_type', 'CE_Stoploss', 'tsl_type', 'CE_TSL', 'target_type',
                               'CE_target', 'PE_Stoploss', 'PE_TSL', 'PE_target']

    strategy_dict = {
        'Long IronFly': delta_plus_algo_columns,
        'Short IronFly': delta_plus_algo_columns,
        'Long Strangle': delta_plus_algo_columns,
        'Short Strangle': delta_plus_algo_columns,
        'Short Straddle': delta_plus_algo_columns,
        'Long Straddle': delta_plus_algo_columns,
        'Delta Based Strategy': delta_plus_algo_columns,
        'Premium Based Strategy': delta_plus_algo_columns,
        'Short Far OTM': delta_plus_algo_columns,
        "Pyramiding Strategy": delta_plus_algo_columns
    }
    #     "NF 1 min Pymid 50 Lacs-SStraddl": delta_plus_algo_columns,
    #     "BNF 1 min Pymid 50 Lacs-SStradl": delta_plus_algo_columns,
    #     "NF 5 min Pymid 50 Lacs-SStraddl": delta_plus_algo_columns,
    #     "BNF 5 min Pymid 50 Lacs-SStradl": delta_plus_algo_columns
    # }

    # default rows customizations
    strategy__customization_dict = {
        'Long IronFly': [
            [('Transaction_Type', 'Sell'), ('CE_Instrument', 'ATM'), ('PE_Instrument', 'ATM')],
            [('Transaction_Type', 'Buy'), ('CE_Instrument', 'ATM+2'), ('PE_Instrument', 'ATM-2')],
        ],
        'Short IronFly': [
            [('Transaction_Type', 'Buy'), ('CE_Instrument', 'ATM'), ('PE_Instrument', 'ATM')],
            [('Transaction_Type', 'Sell'), ('CE_Instrument', 'ATM+2'), ('PE_Instrument', 'ATM-2')]
        ],
        'Long Strangle': [
            [('Transaction_Type', 'Buy'), ('CE_Instrument', 'ATM+2'), ('PE_Instrument', 'ATM-2')]
        ],
        'Short Strangle': [
            [('Transaction_Type', 'Sell'), ('CE_Instrument', 'ATM+2'), ('PE_Instrument', 'ATM-2')]
        ],
        'Short Straddle': [
            [('Transaction_Type', 'Buy'), ('CE_Instrument', 'ATM'), ('PE_Instrument', 'ATM')]
        ],
        'Long Straddle': [
            [('Transaction_Type', 'Buy'), ('CE_Instrument', 'ATM'), ('PE_Instrument', 'ATM')]
        ],
        'Delta Based Strategy': None,
        'Premium Based Strategy': None,
        'Short Far OTM': [
            [('Transaction_Type', 'Sell'), ('CE_Instrument', 'ATM+5'), ('PE_Instrument', 'ATM-5')],
            [('Transaction_Type', 'Sell'), ('CE_Instrument', 'ATM+6'), ('PE_Instrument', 'ATM-6')],
            [('Transaction_Type', 'Sell'), ('CE_Instrument', 'ATM+7'), ('PE_Instrument', 'ATM-7')],
            [('Transaction_Type', 'Sell'), ('CE_Instrument', 'ATM+8'), ('PE_Instrument', 'ATM-8')],
            [('Transaction_Type', 'Sell'), ('CE_Instrument', 'ATM+9'), ('PE_Instrument', 'ATM-9')],
            [('Transaction_Type', 'Sell'), ('CE_Instrument', 'ATM+10'), ('PE_Instrument', 'ATM-10')]
        ]
    }

    # --------------- NF 1 min Pymid 50 Lacs-SStraddl ----------------
    # default_row = [('Transaction_Type', 'Sell'),
    #                ('Exit_Time', '15.30.00'),
    #                ("Symbol Name", "NIFTY"),
    #                ('CE_Instrument', 'ATM'),
    #                ('PE_Instrument', 'ATM'),
    #                ("Buy_Ltp_Percent", 0.5),
    #                ("Sell_Ltp_Percent", 0.5),
    #                ("Wait_Time", 30),
    #                ("No. of lots", 1),
    #                ("CE_target", 80),
    #                ("PE_target", 80),
    #                ("CE_Stoploss", 60),
    #                ("PE_Stoploss", 60),
    #                ("CE_TSL", 50),
    #                ("PE_TSL", 50),
    #                ("stoploss_type", "Percentage"),
    #                ("target_type", "Percentage")]
    # row_collection = []
    # date_range = pd.date_range(start="09:25:00", end="10:15:00", freq="T")
    # entry_times = [x.strftime("%H.%M.%S") for x in date_range]
    # for entry_time in entry_times:
    #     row_collection.append(
    #         default_row + [("Entry_Time", entry_time)]
    #     )
    # strategy__customization_dict["NF 1 min Pymid 50 Lacs-SStraddl"] = row_collection
    #
    # # --------------- BNF 1 min Pymid 50 Lacs-SStradl ----------------
    # default_row = [('Transaction_Type', 'Sell'),
    #                ('Exit_Time', '15.30.00'),
    #                ("Symbol Name", "BANKNIFTY"),
    #                ('CE_Instrument', 'ATM'),
    #                ('PE_Instrument', 'ATM'),
    #                ("Buy_Ltp_Percent", 0.5),
    #                ("Sell_Ltp_Percent", 0.5),
    #                ("Wait_Time", 30),
    #                ("No. of lots", 1),
    #                ("CE_target", 80),
    #                ("PE_target", 80),
    #                ("CE_Stoploss", 60),
    #                ("PE_Stoploss", 60),
    #                ("CE_TSL", 50),
    #                ("PE_TSL", 50),
    #                ("stoploss_type", "Percentage"),
    #                ("target_type", "Percentage")]
    # row_collection = []
    # date_range = pd.date_range(start="09:25:00", end="10:15:00", freq="T")
    # entry_times = [x.strftime("%H.%M.%S") for x in date_range]
    # for entry_time in entry_times:
    #     row_collection.append(
    #         default_row + [("Entry_Time", entry_time)]
    #     )
    # strategy__customization_dict["BNF 1 min Pymid 50 Lacs-SStradl"] = row_collection
    #
    # # --------------- NF 5 min Pymid 50 Lacs-SStraddl ----------------
    # default_row = [('Transaction_Type', 'Sell'),
    #                ('Exit_Time', '15.30.00'),
    #                ("Symbol Name", "NIFTY"),
    #                ('CE_Instrument', 'ATM'),
    #                ('PE_Instrument', 'ATM'),
    #                ("Buy_Ltp_Percent", 0.5),
    #                ("Sell_Ltp_Percent", 0.5),
    #                ("Wait_Time", 30),
    #                ("No. of lots", 1),
    #                ("CE_target", 80),
    #                ("PE_target", 80),
    #                ("CE_Stoploss", 80),
    #                ("PE_Stoploss", 80),
    #                ("CE_TSL", 50),
    #                ("PE_TSL", 80),
    #                ("stoploss_type", "Percentage"),
    #                ("target_type", "Percentage")]
    # row_collection = []
    # date_range = pd.date_range(start="09:15:00", end="10:30:00", freq="5T")
    # entry_times = [x.strftime("%H.%M.%S") for x in date_range]
    # for entry_time in entry_times:
    #     row_collection.append(
    #         default_row + [("Entry_Time", entry_time)]
    #     )
    # strategy__customization_dict["NF 5 min Pymid 50 Lacs-SStraddl"] = row_collection
    #
    # # --------------- BNF 5 min Pymid 50 Lacs-SStradl ----------------
    # default_row = [('Transaction_Type', 'Sell'),
    #                ('Exit_Time', '15.30.00'),
    #                ("Symbol Name", "BANKNIFTY"),
    #                ('CE_Instrument', 'ATM'),
    #                ('PE_Instrument', 'ATM'),
    #                ("Buy_Ltp_Percent", 0.5),
    #                ("Sell_Ltp_Percent", 0.5),
    #                ("Wait_Time", 30),
    #                ("No. of lots", 1),
    #                ("CE_target", 80),
    #                ("PE_target", 80),
    #                ("CE_Stoploss", 80),
    #                ("PE_Stoploss", 80),
    #                ("CE_TSL", 50),
    #                ("PE_TSL", 80),
    #                ("stoploss_type", "Percentage"),
    #                ("target_type", "Percentage")]
    # row_collection = []
    # date_range = pd.date_range(start="09:15:00", end="10:15:00", freq="5T")
    # entry_times = [x.strftime("%H.%M.%S") for x in date_range]
    # for entry_time in entry_times:
    #     row_collection.append(
    #         default_row + [("Entry_Time", entry_time)]
    #     )
    # strategy__customization_dict["BNF 5 min Pymid 50 Lacs-SStradl"] = row_collection
