"""Logging configuration for radiobridge."""

import json
import logging
import sys
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Simple JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Whitelist some common extra fields used across the codebase
        for key in (
            "url",
            "status",
            "content_type",
            "elapsed_s",
            "params",
            "timeout",
            "state_id",
        ):
            if hasattr(record, key):
                try:
                    payload[key] = getattr(record, key)
                except Exception:
                    payload[key] = str(getattr(record, key))
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(
    verbose: bool = False,
    log_file: Optional[str] = None,
    log_format: str = "text",
) -> None:
    """Set up logging configuration for radiobridge.

    Args:
        verbose: If True, set log level to DEBUG, otherwise INFO
        log_file: Optional path to log file. If None, logs only to console
        log_format: 'text' (default) or 'json' for structured logging
    """
    # Determine log level
    log_level = logging.DEBUG if verbose else logging.INFO

    # Choose formatter
    if (log_format or "text").lower() == "json":
        formatter: logging.Formatter = JSONFormatter()
    else:
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
    logger.debug(
        f"Logging configured - Level: {logging.getLevelName(log_level)}; Format: {log_format}"
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the specified module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Logger instance configured for radiobridge
    """
    return logging.getLogger(f'radiobridge.{name.split(".")[-1]}')
