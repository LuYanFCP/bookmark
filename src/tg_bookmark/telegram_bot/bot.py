"""Main bot class."""

import asyncio
import logging
from queue import Queue
from typing import Any

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from ..config import get_settings
from .handlers.message_handler import LocalMessageHandler
from .handlers.media_handler import MediaHandler
from .handlers.callback_handler import CallbackHandler

logger = logging.getLogger(__name__)


class KnowledgeBot:
    """Main bot class."""

    def __init__(self):
        self.settings = get_settings()
        self.message_handler = LocalMessageHandler()
        self.media_handler = MediaHandler()
        self.callback_handler = CallbackHandler()
        self.application: Application = None
        self.processing_queue: asyncio.Queue = None

    def create_application(self) -> Application:
        """Create and configure the bot application."""
        # Build application
        app = ApplicationBuilder().token(
            self.settings.telegram.bot_token
        ).post_init(
            self.post_init
        ).build()

        # Add handlers
        self._setup_handlers(app)

        # Store queue in bot_data
        if self.processing_queue:
            app.bot_data["queue"] = self.processing_queue

        return app

    def _setup_handlers(self, app: Application):
        """Setup message and command handlers."""

        # Command handlers
        app.add_handler(CommandHandler("start", self.message_handler.handle_start_command))
        app.add_handler(CommandHandler("help", self.message_handler.handle_help_command))
        app.add_handler(CommandHandler("settings", self.callback_handler.handle_settings))
        app.add_handler(CommandHandler("stats", self.callback_handler.handle_stats))
        app.add_handler(CommandHandler("export", self.callback_handler.handle_export))

        # Message handlers
        # Text messages
        app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.message_handler.handle_text_message
            )
        )

        # Media messages
        app.add_handler(
            MessageHandler(
                filters.Document.ALL | filters.PHOTO | filters.AUDIO | filters.VIDEO,
                self.media_handler.handle_media_message
            )
        )

        # Error handler
        app.add_error_handler(
            self.message_handler.handle_error
        )

    async def post_init(self, app: Application) -> None:
        await self.setup_bot_commands(app)

    async def setup_bot_commands(self, application: Application):
        """Setup bot commands in Telegram."""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show help message"),
            BotCommand("settings", "Configure preferences"),
            BotCommand("stats", "View statistics"),
            BotCommand("export", "Export your data"),
        ]

        await application.bot.set_my_commands(commands)
        logger.info("Bot commands set successfully")

    def run_polling(self):
        """Run the bot in polling mode."""
        logger.info("Starting bot in polling mode...")

        try:
            # Create processing queue
            # self.processing_queue = asyncio.Queue()

            # Create application
            self.application = self.create_application()

            # Start background tasks
            # await self.start_background_tasks()

            logger.info("Bot started successfully. Listening for messages...")

            # Run polling (wait for stop signal)
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)

            logger.info("Bot stopped gracefully")

        except Exception as e:
            logger.critical(f"Fatal error in polling mode: {e}", exc_info=True)
            raise

    async def run_webhook(self, host: str = "0.0.0.0", port: int = 8443):
        raise NotImplementedError()

    async def start_background_tasks(self):
        """Start background processing tasks."""
        if self.processing_queue:
            # Start storage processor task
            asyncio.create_task(self._storage_processor(), name="storage_processor")
            logger.info("Storage processor task started")

    async def _storage_processor(self):
        """Background task to process queue and store data."""
        from ..storage.factory import StorageFactory

        logger.info("Storage processor started")

        # Create storage instances
        primary_storage = StorageFactory.create_storage(self.settings.storage.primary)

        while True:
            try:
                # Wait for data in queue
                data = await self.processing_queue.get()

                logger.debug(f"Processing message {data.get('message_id')} for storage")

                try:
                    # Save to primary storage
                    if primary_storage:
                        result = await primary_storage.save_message(data)
                        logger.info(f"Saved message to primary storage: {result}")

                    # Save to secondary storage if configured
                    if self.settings.storage.obsidian.is_enabled:
                        obsidian_storage = StorageFactory.create_storage("obsidian")
                        if obsidian_storage:
                            result = await obsidian_storage.save_message(data)
                            logger.info(f"Saved message to Obsidian: {result}")

                except Exception as e:
                    logger.error(f"Error storing message: {e}", exc_info=True)

                # Mark task as done
                self.processing_queue.task_done()

            except asyncio.CancelledError:
                logger.info("Storage processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in storage processor: {e}", exc_info=True)
                await asyncio.sleep(1)  # Prevent tight loop on errors

    def run(self, mode: str = "polling", **kwargs):
        """Run the bot."""
        try:
            if mode == "polling":
                self.run_polling()
            elif mode == "webhook":
                self.run_webhook(**kwargs)
            else:
                raise ValueError(f"Unsupported mode: {mode}")
        except Exception as e:
            logger.critical(f"Fatal error running bot in {mode} mode: {e}", exc_info=True)
            raise
