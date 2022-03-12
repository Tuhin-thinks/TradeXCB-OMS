import enum

from Libs.Utils import config, exception_handler


class Allcols(enum.Enum):
    broker_name = 'Stock Broker Name'
    apikey = 'apiKey'
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
    instrument_df = config.load_instruments_csv(broker="kite")

    def __init__(self, *args, **kwargs):
        self.all_data_kwargs = kwargs
        self.all_data_args = args
        self.broker = None
        self.broker_name = kwargs['Stock Broker Name']
        return

    def do_login(self):
        pass

    def get_order_status(self, order_id):
        pass

    def get_data(self, instrument_name, timeframe):
        pass

    def place_order(self, **kwargs):
        pass

    def cancel_order(self, order_id):
        pass

    def modify_order(self, **kwargs):
        pass

    def close_positions(self, instrument_name):  # Check if it is required or not
        pass

    @staticmethod
    def get_logger(name):
        logger = exception_handler.getFutureLogger(name)
        return logger


if __name__ == '__main__':
    broker = Broker()
