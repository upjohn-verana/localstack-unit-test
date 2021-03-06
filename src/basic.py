# from loguru import logger
import logging
import os

logger = logging


def run(event, context):
    logger.debug(event)
    logger.info(os.environ.get("LOGURU_LEVEL"))
    logger.info(os.environ.get("LOG_THRESHOLD"))
    logger.debug("Check debug")
    logger.info("Useful")
    return {"what": "big deal"}
