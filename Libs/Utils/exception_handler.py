import datetime
import os
import re
import logging
from Libs.Utils import settings

f_future_logger = os.path.join(settings.LOG_FILE_DIR, "FutureLogs.log")
f_trash_logger = os.path.join(settings.LOG_FILE_DIR, "DevTrash.log")
f_kitedata_logger = os.path.join(settings.LOG_FILE_DIR, "KiteData.log")
f_algo_logger = os.path.join(settings.LOG_FILE_DIR, "Algo.log")
if not os.path.exists(settings.LOG_FILE_DIR):
    os.mkdir(settings.LOG_FILE_DIR)
    for file in (f_future_logger, f_kitedata_logger, f_algo_logger, f_trash_logger):
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
    logger.setLevel(settings.LOGGING_LEVEL)
    fh = logging.FileHandler(f_trash_logger)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger = logging.LoggerAdapter(logger, {"source": logger_name})

    return logger


def getFutureLogger(logger_name):
    _format = '%(asctime)s *** %(levelname)s *** %(message)s *** %(source)s'
    formatter = logging.Formatter(_format, datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(logger_name)
    logger.setLevel(settings.LOGGING_LEVEL)
    fh = logging.FileHandler(f_future_logger)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger = logging.LoggerAdapter(logger, {"source": logger_name})

    return logger


def getAlgoLogger(logger_name):
    _format = '%(asctime)s *** %(levelname)s *** %(message)s *** %(source)s'
    formatter = logging.Formatter(_format, datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(logger_name)
    logger.setLevel(settings.LOGGING_LEVEL)
    fh = logging.FileHandler(f_algo_logger)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger = logging.LoggerAdapter(logger, {"source": logger_name})

    return logger


def getKiteDataLogs(logger_name):
    _format = '%(asctime)s *** %(levelname)s *** %(message)s'
    formatter = logging.Formatter(_format, datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(logger_name)
    logger.setLevel(settings.LOGGING_LEVEL)
    fh = logging.FileHandler(f_kitedata_logger)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def deleteLogs():
    """AUTO DELETE EXPIRED LOGS"""
    logs = []
    try:
        log_finder_re = re.compile(settings.LOG_MATCHER_REGEX, re.DOTALL)
        with open(f_future_logger, "r") as log_reader:
            for line in log_reader:
                log_data = line.strip()
                try:
                    log_dict = log_finder_re.search(log_data).groupdict()
                    logs.append((log_dict, log_data))
                except AttributeError:
                    logs.append(log_data)
    except FileNotFoundError:
        pass

    with open(f_future_logger, "w") as log_writer:
        write_error_logs = False
        for log_tuple in logs:
            try:
                log_dict, log_str = log_tuple
                datetime_obj = datetime.datetime.strptime(log_dict["timestamp"], '%Y-%m-%d %H:%M:%S')
                days_elapsed = (datetime.datetime.now() - datetime_obj).days
                if days_elapsed < settings.LOG_EXPIRY_DURATION:  # only keep logs for days elapsed == -1
                    log_writer.write(log_str + "\n")
                    write_error_logs = True
            except ValueError:
                if write_error_logs:
                    log_writer.write(log_tuple + "\n")
    del logs

    # ================= IDeltaLogger ===========================
    logs = []
    log_finder_re = re.compile(settings.LOG_MATCHER_REGEX, re.DOTALL)
    try:
        with open(f_algo_logger, "r") as log_reader:
            for line in log_reader:
                log_data = line.strip()
                try:
                    log_dict = log_finder_re.search(log_data).groupdict()
                    logs.append((log_dict, log_data))
                except AttributeError:
                    logs.append(log_data)
    except FileNotFoundError:
        pass

    with open(f_algo_logger, "w") as log_writer:
        write_error_logs = False
        for log_tuple in logs:
            try:
                log_dict, log_str = log_tuple
                datetime_obj = datetime.datetime.strptime(log_dict["timestamp"], '%Y-%m-%d %H:%M:%S')
                days_elapsed = (datetime.datetime.now() - datetime_obj).days
                if days_elapsed < settings.LOG_EXPIRY_DURATION:  # only keep logs for days elapsed == -1
                    log_writer.write(log_str + "\n")
                    write_error_logs = True
            except ValueError:
                if write_error_logs:
                    log_writer.write(log_tuple + "\n")
    del logs

    # ================= Dev Logs ===============================
    with open(f_trash_logger, 'w') as log_writer:
        log_writer.write("")  # clear dev log everytime app opens

    # ================= Kite Logs ===============================
    with open(f_kitedata_logger, 'w') as log_writer:
        log_writer.write("")  # clear KiteData log everytime app opens


if __name__ == '__main__':
    deleteLogs()
