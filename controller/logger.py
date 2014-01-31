DEFAULT_FORMAT = '[%(asctime)s] %(levelname)s %(message)s'
DEFAULT_LOG_FILENAME="/var/log/connector/connector.log"
DEFAULT_DATE_FORMAT = '%m-%d %H:%M:%S'

import logging

def config_logging(log_name, default_loglevel, foreground=True):
    formatter = logging.Formatter(fmt=DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    # fixme: for now, it goes to stdout regardless of foreground/background
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(log_name)
    logger.addHandler(handler)
    logger.setLevel(default_loglevel)
    
    return logger
