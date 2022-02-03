from loguru import logger
import sys
import os


def compile_message(log_level, msg, meta_dict):
    """Compiles json version of message, merging in optional metadata"""
    message = meta_dict
    message["log_level"] = log_level.lower()

    if "ENV_NAME" in os.environ:
        message["log_env"] = os.environ["ENV_NAME"]
    if "PRODUCT" in os.environ:
        message["log_product"] = os.environ["PRODUCT"]
    if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
        message["lambda_function"] = os.environ["AWS_LAMBDA_FUNCTION_NAME"]

    message["log_message"] = msg

    return message


# class CwLogger:
#     """The wrapper class for python logging"""

#     def __init__(self, threshold, logger_name=__name__):
#         self.threshold = threshold.upper()
#         self.logger = logger
#         self.logger.remove()
#         self.logger.add(sys.stderr, level=self.threshold)

#         # Avoid duplicate messages when adding handlers on every instantiation
#         # if not self.logger.handlers:
#         #     self.logger.setLevel(threshold.upper())
#         #     handler = logging.StreamHandler()
#         #     handler.setLevel(threshold.upper())
#         #     self.logger.addHandler(handler)

#     def log(self, log_level, msg, meta_dict):
#         """Compile dict from message and metadata and then log it"""
#         # Copy the meta_dict so we don't change it
#         meta_dict_copy = meta_dict.copy() if meta_dict else {}
#         message_dict = compile_message(log_level, msg, meta_dict_copy)
#         levels = {"CRITICAL": 50, "ERROR": 40,
#                   "WARNING": 30, "INFO": 20, "DEBUG": 10}
#         self.logger.log(levels[log_level], message_dict)

#     def critical(self, msg, meta_dict=None):
#         """Log criticals"""
#         self.log("CRITICAL", msg, meta_dict)

#     def error(self, msg, meta_dict=None):
#         """Log errors"""
#         self.log("ERROR", msg, meta_dict)

#     def warning(self, msg, meta_dict=None):
#         """Log warnings"""
#         self.log("WARNING", msg, meta_dict)

#     def info(self, msg, meta_dict=None):
#         """Log infos"""
#         self.log("INFO", msg, meta_dict)

#     def debug(self, msg, meta_dict=None):
#         """Log debugs"""
#         self.log("DEBUG", msg, meta_dict)
