"""
Logger configuration for the Talking Drone application.
"""

import logging
import os
import sys


def setup_logger():
    """Configure and return a logger instance."""
    # Create logger
    logger = logging.getLogger("talkingdrone")
    logger.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create console handler for all logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Set console level based on environment
    if os.environ.get("DEBUG", "false").lower() == "true":
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)

    logger.addHandler(console_handler)

    return logger


# Create the singleton logger instance
logger = setup_logger()
