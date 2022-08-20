class StrategiesColumn:

    tradexcb_display_columns = ['transaction_type', 'buy_ltp_percent', 'sell_ltp_percent', 'order_type', 'product_type',
                                'wait_time', 'exchange', 'Symbol Name', 'expiry', 'instrument', 'buy_above',
                                'use_priceba', 'sell_below', 'use_pricesb', 'stoploss_type', 'stoploss',
                                'target_type', 'target', 'timeframe', 'vwap', 'vwap_signal', 'ATRTS',
                                'ATR TS Period', 'ATR TS Multiplier', 'atrts_signal', 'moving_average_period',
                                'moving_average', 'moving_average_signal']
    tradexcb_numeric_columns = {
        'buy_ltp_percent': float, 'sell_ltp_percent': float, 'wait_time': float, 'buy_above': float,
        'sell_below': float, 'stoploss': float, 'target': float, 'timeframe': int,
        'ATR TS Period': int, 'ATR TS Multiplier': float, 'moving_average_period': int}

    strategy_dict = {
        'Default': tradexcb_display_columns,
    }
    strategy__customization_dict = {
        'Default': None
    }
