import requests
import pandas as pd
import enum
import logging
import time
import sys


while True:
    try:
        response = requests.get("https://api.kite.trade/instruments?api_key=kitefront")
        file_pointer = open("instruments.csv", "w")
        file_pointer.write(response.text)
        instruments_df = pd.read_csv('instruments.csv')
        instruments_df['expiry'] = pd.to_datetime(instruments_df['expiry'])
        break
    except:

        print(sys.exc_info())



class Allcols(enum.Enum):
    broker_name = 'Stock Broker Name'
    apikey  = 'apiKey'
    apisecret = 'apiSecret'
    username = 'accountUserName'
    password = 'accountPassword'
    pin = 'securityPin'
    totp_secret = 'totp_secret'
    lots = 'No of Lots'
    consumer_key = 'consumerKey'
    access_token = 'accessToken'
    host = 'host'
    source = 'source'

class Broker:
    order_status = {0: 'pending', 1: 'executed'}
    instrument_df = instruments_df

    def __init__(self, *args, **kwargs):
        self.all_data_kwargs = kwargs
        self.all_data_args = args
        self.broker = None
        self.broker_name = kwargs['Stock Broker Name']
        return


    def do_login(self):
        pass


    def get_order_status(self,order_id):
        pass


    def get_data(self, instrument_name,timeframe):
        pass


    def place_order(self,**kwargs):
        pass


    def cancel_order(self,order_id):
        pass

    def modify_order(self,**kwargs):
        pass

    def close_positions(self,instrument_name):## Check if it is required or not
        pass


    def get_logger(self,name):

        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s  %(levelname)-10s  %(message)s')
        file_handler = logging.FileHandler('logs/{}{}'.format(name,time.strftime('%Y-%m-%d.log')))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

if __name__ == '__main__':
    broker = Broker()