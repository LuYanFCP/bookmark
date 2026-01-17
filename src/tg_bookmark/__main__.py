"""Main entry point for the bot."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from telegram_bot import KnowledgeBot
from config import get_settings
from utils.logging_filter import ProjectLogFilter


class LogfmtFormatter(logging.Formatter):
    """Log formatter that outputs logs in logfmt format."""

    def __init__(self):
        super().__init__(datefmt='%Y-%m-%dT%H:%M:%S%z')

    def format(self, record: logging.LogRecord) -> str:
        """Format log record in logfmt style."""
        # Build the base parts
        parts = [
            f'time={self.formatTime(record)}',
            f'level={record.levelname.lower()}',
            f'logger={record.name}',
            f'msg="{str(record.msg).replace("\"", "\\\"")}"' if record.msg else 'msg=""',
            f'filename={record.filename}',
            f'line={record.lineno}',
        ]

        # Add exception info if present
        if record.exc_info:
            import traceback
            exc_text = traceback.format_exception(*record.exc_info)
            exc_escaped = repr(''.join(exc_text))
            parts.append(f'error={exc_escaped}')

        return ' '.join(parts)


def setup_logging():
    """Setup application logging with logfmt format to console only."""
    settings = get_settings()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.logging.level.upper()))

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler with LogfmtFormatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(LogfmtFormatter())
    
    # Add filter to only show our project's logs
    console_handler.addFilter(ProjectLogFilter())
    
    root_logger.addHandler(console_handler)

    # Log initialization using standard logging to ensure it's recorded
    # After this point, structured logging can be used
    root_logger.info(f'event="logging_initialized" level="{settings.logging.level}" handler="console" filter="tg_bookmark_only"')


def main():
    """Main application entry point."""
    # Load settings
    settings = get_settings()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Telegram Knowledge Bot")
    logger.info(f"AI Provider: {settings.ai.provider}")
    logger.info(f"Primary Storage: {settings.storage.primary}")
    logger.info(f"Notion Enabled: {settings.storage.notion.is_enabled}")
    logger.info(f"Obsidian Enabled: {settings.storage.obsidian.is_enabled}")

    # Validate configuration
    if not settings.telegram.bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        sys.exit(1)

    if not settings.ai.openai_api_key and not settings.ai.anthropic_api_key:
        logger.error("No AI API key is set (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        sys.exit(1)

    # Create and run bot
    bot = KnowledgeBot()

    try:
        # Run in polling mode (default)
        bot.run(mode="polling")
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
