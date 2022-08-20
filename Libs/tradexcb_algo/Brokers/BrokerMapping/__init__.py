import brokers


def create_new_broker_instance(**broker_creds):
    """
    Do the instance creation and return the specific broker's instance
    """
    return brokers.BROKER_MODULES[broker_creds['Stock Broker Name'].lower()](**broker_creds)
