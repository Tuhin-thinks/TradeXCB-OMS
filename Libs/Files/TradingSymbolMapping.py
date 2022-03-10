class StrategiesColumn:
    tradexcb_columns = ['transaction_type', 'buy_ltp_percent', 'sell_ltp_percent', 'order_type', 'product_type',
                        'wait_time', 'instrument', 'exchange', 'buy_above', 'use_priceba', 'sell_below', 'use_pricesb',
                        'stoploss_type', 'stoploss', 'tsl_type', 'tsl', 'target_type', 'target', 'timeframe', 'vwap',
                        'vwap_signal', 'ATRTS', 'ATR TS Period', 'ATR TS Multiplier', 'atrts_signal',
                        'moving_average_period', 'moving_average', 'moving_average_signal']

    tradexcb_display_columns = ['transaction_type', 'buy_ltp_percent', 'sell_ltp_percent', 'order_type', 'product_type',
                                'wait_time', 'exchange', 'Symbol Name', 'expiry', 'atm_strike', 'buy_above', 'use_priceba',
                                'sell_below', 'use_pricesb', 'stoploss_type', 'stoploss', 'tsl_type', 'tsl',
                                'target_type', 'target', 'timeframe', 'vwap',
                                'vwap_signal', 'ATRTS', 'ATR TS Period', 'ATR TS Multiplier', 'atrts_signal',
                                'moving_average_period', 'moving_average', 'moving_average_signal']

    strategy_dict = {
        'Default': tradexcb_display_columns,
    }
    strategy__customization_dict = {
        'Default': None
    }
