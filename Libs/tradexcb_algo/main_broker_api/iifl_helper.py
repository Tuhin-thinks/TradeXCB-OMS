import pandas as pd

master_file = None

exchange_map = {'NSE': 'NSECM', 'NFO': 'NSEFO', 'CDS': 'NSECD'}
exchange_map_inverse = {'NSECM': 'NSE', 'NSEFO': 'NFO', 'NSECD': 'CDS'}
number_exchange_dict = {2: 'NSEFO', 1: 'NSECM'}
exchange_number_dict = {'NSEFO': 2, 'NSECM': 1}


def download_master_file(xt):
    global master_file
    all_symbols_result = xt.get_master(exchangeSegmentList=['NSECM', 'NSEFO', 'NSECD'])['result']
    all_symbols_result = all_symbols_result.split('\n')
    all_symbols_result = [x.split('|') for x in all_symbols_result]
    final_df = pd.DataFrame(all_symbols_result,
                            columns=['ExchangeSegment', 'ExchangeInstrumentID', 'InstrumentType', 'Name',
                                     'Description', 'Series', ' NameWithSeries', 'InstrumentID', 'PriceBand.High',
                                     'PriceBand.Low', 'FreezeQty', 'TickSize',
                                     ' LotSize', 'Multiplier', 'UnderlyingInstrumentId', 'UnderlyingIndexName',
                                     'ContractExpiration', 'StrikePrice', 'OptionType'])
    master_file = final_df
    master_file.to_csv("iifl.csv")
    return


def get_symbol_from_token(token, exchange):
    global master_file, exchange_map
    exchange = exchange_map[exchange]
    row = master_file[
        (master_file['ExchangeInstrumentID'] == str(token)) & (master_file['ExchangeSegment'] == str(exchange))]
    return row


def get_exchange_number(exchange):
    return exchange_number_dict[exchange_map[exchange]]


if __name__ == '__main__':
    token = '3045'
    exchange = 'NSE'
