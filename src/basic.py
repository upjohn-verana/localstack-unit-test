# from helpers.logger import CwLogger
from loguru import logger
import sys
import os

# logg_thing = CwLogger("debug")


def run(event, context):
    # logg_thing.info("Hello")
    logger.debug(event)
    logger.info(os.environ.get("LOGURU_LEVEL"))
    logger.info(os.environ.get("LOG_THRESHOLD"))
    logger.debug("Check debug")
    logger.info("Useful")
    return "big deal"
