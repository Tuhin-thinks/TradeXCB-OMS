import datetime
import os
import re
import logging
import settings


logging_level = logging.DEBUG
if logging_level == logging.DEBUG:
    logging.basicConfig()
f_future_logger = os.path.join(settings.LOG_FILE_DIR, "FutureLogs.log")
f_trash_logger = os.path.join(settings.LOG_FILE_DIR, "DevTrash.log")
f_orderbook_logger = os.path.join(settings.LOG_FILE_DIR, "OrderBook.log")
if not os.path.exists(settings.LOG_FILE_DIR):
    os.mkdir(settings.LOG_FILE_DIR)
    for file in (f_future_logger, f_orderbook_logger):
        with open(file, 'w') as writer:
            writer.write("")


def getTrashLogger(logger_name):
    """
    This logging should be used for developing purpose only and logs to be written in separate file.

    Args:
        logger_name: Name of the logger, mostly the file __name__

    """
    _format = '%(asctime)s *** %(levelname)s *** %(message)s *** %(source)s'
    formatter = logging.Formatter(_format, datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging_level)
    fh = logging.FileHandler(f_trash_logger)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger = logging.LoggerAdapter(logger, {"source": logger_name})

    return logger


def getFutureLogger(logger_name):
    _format = '%(asctime)s *** %(levelname)s *** %(message)s *** %(source)s'
    formatter = logging.Formatter(_format, datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging_level)
    fh = logging.FileHandler(f_future_logger)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger = logging.LoggerAdapter(logger, {"source": logger_name})

    return logger


def getOrderBookLogger(logger_name):
    _format = '%(asctime)s *** %(levelname)s *** %(message)s'
    formatter = logging.Formatter(_format, datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging_level)
    fh = logging.FileHandler(f_orderbook_logger)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def deleteLogs() -> None:
    """Function to auto-delete expired logs
    :rtype: None
    """

    def clear_logs(date_mather_regex: 're.Pattern', logger_file: str, preserve_exc_errors: bool = False) -> None:
        """
        Inner function to clear logs for different loggers used

        Args:
            date_mather_regex: Pattern: regex to match lines to get datetime from logs
            logger_file: str: file to write and read logs from
            preserve_exc_errors: bool: whether to preserve exceptions in logs (within date range)
        """

        logs_lines_list = []
        # current_day_flag turns to True, when first logs for current day is received (before that all logs are cleared)
        current_day_flag = False
        with open(logger_file, "r") as log_reader:
            for line in log_reader:
                log_data = line.strip()
                try:
                    log_dict = date_mather_regex.search(log_data).groupdict()
                    logs_lines_list.append((log_dict, log_data))
                    current_day_flag = True
                except AttributeError:  # there'll be attribute error for lines with no formats
                    if current_day_flag and preserve_exc_errors:
                        logs_lines_list.append((log_dict, log_data))  # preserve exc_log information here

        with open(logger_file, "w") as writer_:
            for log_dict, log_str in logs_lines_list:
                datetime_obj = datetime.datetime.strptime(log_dict["timestamp"], '%Y-%m-%d %H:%M:%S')
                days_elapsed = (datetime.datetime.now() - datetime_obj).days
                if days_elapsed < settings.LOG_EXPIRY_DURATION:  # only keep logs for days elapsed == -1
                    writer_.write(log_str + "\n")

    # ----------------- clear outdated logs for all required loggers ---------------------
    future__log_matcher_regex = re.compile(settings.LOG_MATCHER_REGEX, re.DOTALL)
    clear_logs(future__log_matcher_regex, f_future_logger, preserve_exc_errors=True)

    ordr_book__log_matcher_regex = re.compile(settings.ORDERBOOK_LOG_MATCHER_REGEX, re.DOTALL)
    clear_logs(ordr_book__log_matcher_regex, f_orderbook_logger, preserve_exc_errors=True)

    # ================= Dev Logs ===============================
    with open(f_trash_logger, 'w') as log_writer:
        log_writer.write("")  # clear dev log everytime app opens
