"""
Logger configuration for the Talking Drone application.
"""

import logging
import os
import sys
import traceback
from typing import Any, Dict, Optional


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


def log_endpoint_error(
    error: Exception, endpoint: str, detail: Optional[Dict[str, Any]] = None
):
    """
    Log detailed error information from endpoint failures.

    Args:
        error: The exception that occurred
        endpoint: Name of the endpoint where the error occurred
        detail: Additional context about the error
    """
    error_type = type(error).__name__
    error_message = str(error)
    stack_trace = traceback.format_exc()

    # Create a detailed error message
    log_message = f"\n--- ENDPOINT ERROR: {endpoint} ---\n"
    log_message += f"Error type: {error_type}\n"
    log_message += f"Error message: {error_message}\n"

    if detail:
        log_message += f"Details: {detail}\n"

    log_message += f"Stack trace:\n{stack_trace}\n"
    log_message += "-----------------------------------"

    logger.error(log_message)
