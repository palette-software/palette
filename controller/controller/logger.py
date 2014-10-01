LOGGING_FORMAT = '[%(asctime)s] %(levelname)s %(message)s'
LOGGING_DATEFMT = '%m-%d %H:%M:%S'

import logging

def make_logger(name, config):

    if name == 'logger':
        section = name
        name = 'root'
    elif not name.startswith('logger:'):
        section = 'logger:'+name
    else:
        section = name
        _, name = section.split(':', 1)

    level = getattr(logging, config.get(section, 'level', default='INFO'))
    filename = config.get(section, 'filename', default=None)

    if filename and filename.lower() == 'stderr':
        filename = None

    fmt = config.get(section, 'format', raw=True, default=LOGGING_FORMAT)
    datefmt = config.get(section, 'datefmt', raw=True, default=LOGGING_DATEFMT)

    if name == 'root':
        logger = logging.getLogger()
    else:
        logger = logging.getLogger(name)

    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    if filename:
        from logging.handlers import RotatingFileHandler
        max_bytes = config.getint(section, 'max_bytes', default=20*1024*1024)
        backup_count = config.getint(section, 'backup_count', default=5)
        handler = RotatingFileHandler(filename, "a", max_bytes, backup_count)
    else:
        handler = logging.StreamHandler()

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)

def make_loggers(config):
    for section in config.sections():
        if section == 'logger' or section.startswith('logger:'):
            make_logger(section, config)

def get(name=None):
    return logging.getLogger(name)
