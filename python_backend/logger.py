"""
logger.py — Centralized production-grade logging configuration for CogniTree.
"""

import logging
import sys


def setup_logger(name: str = "cognitree") -> logging.Logger:
    """
    Configures and returns a production-grade logger.
    Format: [TIMESTAMP] [LOG_LEVEL] [LOGGER_NAME] Message
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


logger = setup_logger()
