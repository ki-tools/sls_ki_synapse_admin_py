import logging
from . import WWWEnv

"""
Setup the logger.
"""
logger = logging.getLogger()

if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

logging.basicConfig(level=logging.getLevelName(WWWEnv.LOG_LEVEL(default='INFO')))
