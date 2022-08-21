class StrategiesColumn:

    tradexcb_display_columns = ['transaction_type', 'buy_ltp_percent', 'sell_ltp_percent', 'order_type', 'product_type',
                                'wait_time', 'exchange', 'Symbol Name', 'expiry', 'instrument',
                                'stoploss_type', 'stoploss', 'target_type', 'target']
    tradexcb_numeric_columns = {'buy_ltp_percent': float, 'sell_ltp_percent': float, 'wait_time': float,
                                'stoploss': float, 'target': float}

    strategy_dict = {
        'Default': tradexcb_display_columns,
    }
    strategy__customization_dict = {
        'Default': None
    }
