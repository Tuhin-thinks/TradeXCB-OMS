import requests
import pandas as pd
import time

while True:
    try:
        master_file = pd.read_json(requests.get('https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json').text)
        break
    except:
        time.sleep(1)
        continue


def get_symbol_from_token(token,exchange):
    global master_file
    row = master_file[(master_file['token']==str(token))&(master_file['exch_seg']==str(exchange))]
    return row.iloc[-1]['symbol']





if __name__ == '__main__':
    token = '3045'
    exchange = 'NSE'

