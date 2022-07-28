import sys
import logging


def get_logger(
        name,
        log_file=None,
        log_level=logging.INFO,
        log_format = "%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s"
    ):

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    ch.setFormatter(logging.Formatter(log_format))
    logger.addHandler(ch)

    # log to file as well
    if log_file:
        shnd = logging.FileHandler(log_file)
        shnd.setLevel(log_level)
        shnd.setFormatter(logging.Formatter(log_format))
        logger.addHandler(shnd)

    logger.propagate = False
    return logger
