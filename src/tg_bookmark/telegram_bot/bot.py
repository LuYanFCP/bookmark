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

from tg_bookmark.config import get_settings
from tg_bookmark.telegram_bot.handlers.message_handler import LocalMessageHandler
from tg_bookmark.telegram_bot.handlers.media_handler import MediaHandler
from tg_bookmark.telegram_bot.handlers.callback_handler import CallbackHandler
from tg_bookmark.utils.logging import debug, info, warning, error

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
        info(logger, event="starting_polling_mode")

        try:
            # Create processing queue
            self.processing_queue = asyncio.Queue()
            debug(logger, event="queue_created", max_size=self.processing_queue.maxsize)

            # Create application
            self.application = self.create_application()
            info(logger, event="application_created")

            # Start background tasks
            asyncio.run(self.start_background_tasks())
            info(logger, event="background_tasks_started")

            info(logger, event="bot_started", listening=True)

            # Run polling (wait for stop signal)
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)

            info(logger, event="bot_stopped_gracefully")

        except Exception as e:
            error(logger, event="fatal_error_polling", error=str(e))
            logger.exception("Full traceback:")
            raise

    async def run_webhook(self, host: str = "0.0.0.0", port: int = 8443):
        raise NotImplementedError()

    async def start_background_tasks(self):
        """Start background processing tasks."""
        if self.processing_queue:
            # Start storage processor task
            asyncio.create_task(self._storage_processor(), name="storage_processor")
            info(logger, event="storage_processor_started")

    async def _storage_processor(self):
        """Background task to process queue and store data."""
        from tg_bookmark.storage.factory import StorageFactory

        info(logger, event="storage_processor_initialized")

        # Create storage instances
        primary_storage = StorageFactory.create_storage(self.settings.storage.primary)
        if primary_storage:
            info(logger, event="primary_storage_created", storage_type=self.settings.storage.primary)
        else:
            warning(logger, event="primary_storage_creation_failed", storage_type=self.settings.storage.primary)

        secondary_storage = None
        if self.settings.storage.obsidian.is_enabled:
            secondary_storage = StorageFactory.create_storage("obsidian")
            if secondary_storage:
                info(logger, event="secondary_storage_created", storage_type="obsidian")
            else:
                warning(logger, event="secondary_storage_creation_failed", storage_type="obsidian")

        while True:
            try:
                # Wait for data in queue
                data = await self.processing_queue.get()
                message_id = data.get('message_id')
                user_id = data.get('user_id')
                category = data.get('category', 'Unknown')

                debug(logger, event="queue_item_received", message_id=message_id, queue_size=self.processing_queue.qsize())

                try:
                    # Save to primary storage
                    if primary_storage:
                        info(logger, event="saving_to_primary", message_id=message_id, storage_type=self.settings.storage.primary)
                        result = await primary_storage.save_message(data)
                        info(logger, event="saved_to_primary", message_id=message_id, storage_type=self.settings.storage.primary, result=result)
                    else:
                        error(logger, event="no_primary_storage", message_id=message_id)

                    # Save to secondary storage if configured
                    if secondary_storage:
                        info(logger, event="saving_to_secondary", message_id=message_id, storage_type="obsidian")
                        result = await secondary_storage.save_message(data)
                        info(logger, event="saved_to_secondary", message_id=message_id, storage_type="obsidian", result=result)

                except Exception as e:
                    error(logger, event="storage_error", message_id=message_id, user_id=user_id, category=category, error=str(e))
                    logger.exception("Full traceback:")

                # Mark task as done
                self.processing_queue.task_done()
                debug(logger, event="queue_item_completed", message_id=message_id)

            except asyncio.CancelledError:
                info(logger, event="storage_processor_cancelled")
                break
            except Exception as e:
                error(logger, event="storage_processor_error", error=str(e))
                logger.exception("Full traceback:")
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
