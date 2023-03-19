import os
import logging


def setup_logger(logger_name, log_file, level=logging.DEBUG):
    if not os.path.exists('logs'):
        os.makedirs('logs')
    _logger = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(message)s')
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    _logger.setLevel(level)
    _logger.addHandler(fileHandler)
    _logger.addHandler(streamHandler)
