import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(name):
    os.makedirs("logs",exist_ok=True)
    #time_now = time.asctime()
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", '
        '"logger": "%(name)s", "message": %(message)s}',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler = RotatingFileHandler(
        f'logs/{name}.log',
        maxBytes=10_000_000,
        backupCount=10
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger    