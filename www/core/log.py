import logging
from .param_store import ParamStore

"""
Setup the logger.
"""
logger = logging.getLogger()

if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

logging.basicConfig(level=logging.getLevelName(ParamStore.LOG_LEVEL(default='INFO')))
