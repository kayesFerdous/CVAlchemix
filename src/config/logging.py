"""
Centralized logging configuration.

Call ``setup_logging()`` once at application startup to configure the root
logger with a consistent format and the level specified in settings.
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger with a console handler.

    Args:
        level: Logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers on repeated calls
    if root_logger.handlers:
        return

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
