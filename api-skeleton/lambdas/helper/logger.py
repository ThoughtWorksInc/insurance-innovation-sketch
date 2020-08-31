import logging
import os

logging.getLogger().addHandler(logging.StreamHandler())
LOG_LEVEL = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    return logger