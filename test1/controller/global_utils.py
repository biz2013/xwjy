import logging
import logging.handlers

LOGGER = None

def setup_logger(logfile, name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(
             logfile, maxBytes=40000000, backupCount=5)
    formatter = logging.Formatter("[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
