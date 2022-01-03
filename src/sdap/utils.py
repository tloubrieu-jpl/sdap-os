import sys
import logging


def get_log(name):
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    return logging.getLogger(name)


