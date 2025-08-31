"""Logging configuration for radiobridge."""

import logging
import sys
from typing import Optional


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """Set up logging configuration for radiobridge.

    Args:
        verbose: If True, set log level to DEBUG, otherwise INFO
        log_file: Optional path to log file. If None, logs only to console
    """
    # Determine log level
    log_level = logging.DEBUG if verbose else logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Get root logger for radiobridge
    logger = logging.getLogger("radiobridge")
    logger.setLevel(log_level)

    # Remove any existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")

    # Set propagate to True to allow test fixtures to capture logs
    logger.propagate = True

    # Log initial setup
    logger.debug(f"Logging configured - Level: {logging.getLevelName(log_level)}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the specified module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Logger instance configured for radiobridge
    """
    return logging.getLogger(f'radiobridge.{name.split(".")[-1]}')
