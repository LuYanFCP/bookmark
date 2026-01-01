"""Main entry point for the bot."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from telegram_bot import KnowledgeBot
from config import get_settings


def setup_logging():
    """Setup application logging."""
    settings = get_settings()
    
    # Configure structlog if available
    try:
        import structlog
        
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer() if settings.logging.format == "json" 
                else structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    except ImportError:
        # Fallback to standard logging
        logging.basicConfig(
            level=getattr(logging, settings.logging.level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Configure Sentry if available
    if settings.logging.sentry_dsn:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.logging.sentry_dsn,
                traces_sample_rate=1.0
            )
        except ImportError:
            logging.warning("Sentry SDK not installed")
        except Exception as e:
            logging.error(f"Failed to initialize Sentry: {e}")


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