"""Logging filter to only show project's own logs."""

import logging


class ProjectLogFilter(logging.Filter):
    """Filter that only shows logs from the tg_bookmark package."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Only allow logs from tg_bookmark package."""
        return record.name.startswith("tg_bookmark")
