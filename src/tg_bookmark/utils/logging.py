"""Structured logging utilities for logfmt format."""

import logging
from typing import Any, Dict, Optional


def log_struct(logger: logging.Logger, level: int, event: str, **kwargs: Any) -> None:
    """
    Log structured data in logfmt format.

    Args:
        logger: Logger instance
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        event: Event name for the log
        **kwargs: Key-value pairs to log
    """
    # Format key=value pairs
    parts = [f'event="{event}"']

    for key, value in kwargs.items():
        if value is None:
            continue

        # Convert value to string and escape quotes
        str_value = str(value)
        if isinstance(value, bool):
            str_value = str(value).lower()
        elif isinstance(value, (int, float)):
            str_value = str(value)
        else:
            # String values need quotes and escaping
            str_value = f'"{str(value).replace(chr(92), r"\\").replace(chr(34), r"\"")}"'

        parts.append(f"{key}={str_value}")

    logger.log(level, " ".join(parts))


def debug(logger: logging.Logger, event: str, **kwargs: Any) -> None:
    """Log debug level structured message."""
    log_struct(logger, logging.DEBUG, event, **kwargs)


def info(logger: logging.Logger, event: str, **kwargs: Any) -> None:
    """Log info level structured message."""
    log_struct(logger, logging.INFO, event, **kwargs)


def warning(logger: logging.Logger, event: str, **kwargs: Any) -> None:
    """Log warning level structured message."""
    log_struct(logger, logging.WARNING, event, **kwargs)


def error(logger: logging.Logger, event: str, **kwargs: Any) -> None:
    """Log error level structured message."""
    log_struct(logger, logging.ERROR, event, **kwargs)
