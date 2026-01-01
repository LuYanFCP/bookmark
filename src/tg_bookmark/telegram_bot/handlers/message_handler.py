"""Text message handler."""
import json
from telegram.constants import ParseMode
import traceback
import html

import logging
from typing import Dict, Any
from telegram import Update, Message
from telegram.ext import ContextTypes

from ...ai_engine import MessageSummarizer, ContentClassifier
from ...content_extractor import ContentExtractionPipeline

logger = logging.getLogger(__name__)


class LocalMessageHandler:
    """Handles incoming text messages."""

    def __init__(self):
        self.summarizer = MessageSummarizer()
        self.classifier = ContentClassifier()
        self.extractor = ContentExtractionPipeline()

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process text messages."""
        if not update.message:
            return

        message: Message = update.message
        user = message.from_user

        logger.info(f"Processing message from user {user.id}")

        try:
            # Start processing notification
            processing_msg = await message.reply_text("🤖 Processing your message...")

            # Extract content from message (including URLs, entities, etc.)
            extracted_content = await self.extractor.process_message(message)
            full_text = extracted_content.get("text", "")

            if not full_text.strip():
                await processing_msg.edit_text("❌ No content found in message.")
                return

            # Generate AI processing
            summary = await self.summarizer.summarize(full_text, max_length=300)
            category, tags = await self.classifier.classify(full_text)
            embedding = await self.summarizer.generate_embedding(full_text)
            keywords = await self.classifier.extract_keywords(full_text)

            # Prepare structured data
            processed_data: Dict[str, Any] = {
                "user_id": user.id,
                "user_username": user.username,
                "message_id": message.message_id,
                "timestamp": message.date.isoformat(),
                "content": full_text,
                "summary": summary,
                "category": category,
                "tags": tags,
                "keywords": keywords,
                "embedding": embedding,
                "metadata": {
                    "chat_type": message.chat.type,
                    "chat_id": message.chat.id,
                    "chat_title": getattr(message.chat, "title", None),
                    "has_entities": bool(message.entities),
                    "is_forwarded": bool(message.forward_from),
                    "has_document": bool(message.document),
                    "has_photo": bool(message.photo),
                    "extracted_urls": len(extracted_content.get("urls", [])),
                    "extracted_files": len(extracted_content.get("files", [])),
                    "extracted_images": len(extracted_content.get("images", [])),
                }
            }

            # Add to processing queue if available
            if "queue" in context.bot_data:
                await context.bot_data["queue"].put(processed_data)
                logger.info(f"Added message {message.message_id} to processing queue")

            # Edit the processing message with results
            result_text = (
                f"✅ *Message Processed Successfully!*\n\n"
                f"🏷️ *Category:* {category}\n"
                f"🏷️ *Tags:* {', '.join(tags)}\n"
                f"🔑 *Keywords:* {', '.join(keywords)}\n\n"
                f"📝 *Summary:*\n_{summary}_\n\n"
                f"📊 *Stats:*\n"
                f"- Length: {len(full_text)} chars\n"
                f"- URLs: {len(extracted_content.get('urls', []))}\n"
                f"- Files: {len(extracted_content.get('files', []))}\n"
                f"- Images: {len(extracted_content.get('images', []))}"
            )

            await processing_msg.edit_text(
                result_text,
                parse_mode="Markdown"
            )

            logger.info(f"Successfully processed message {message.message_id}")

        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {e}", exc_info=True)
            await message.reply_text("❌ Sorry, an error occurred while processing your message.")

    async def handle_help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = (
            "🤖 *Telegram Knowledge Bot*\n\n"
            "I can help you organize and store your messages with AI-powered processing!\n\n"
            "*What I do:*\n"
            "• 🤖 Auto-summarize long messages\n"
            "• 🏷️ Smart categorization and tagging\n"
            "• 🔍 Extract keywords and entities\n"
            "• 💾 Store to Notion/Obsidian\n"
            "• 🔗 Process URLs and extract content\n"
            "• 🖼️ OCR for images\n\n"
            "*How to use:*\n"
            "Simply send me any message, and I'll process it automatically!\n\n"
            "*Commands:*\n"
            "/help - Show this help message\n"
            "/start - Start the bot\n"
            "/settings - Configure your preferences\n"
            "/stats - View your statistics\n"
            "/export - Export your data"
        )

        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        welcome_text = (
            "👋 *Welcome to Telegram Knowledge Bot!*\n\n"
            "I'm your AI-powered assistant for organizing and storing messages.\n\n"
            "Just send me any message and I'll:\n"
            "• Summarize it intelligently\n"
            "• Categorize and tag it\n"
            "• Extract key information\n"
            "• Store it in your knowledge base\n\n"
            "Type /help to learn more about what I can do!"
        )

        await update.message.reply_text(welcome_text, parse_mode="Markdown")

    async def handle_error(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors globally."""
        logger.error(f"Update {update} caused error {context.error}")


        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)

        # Build the message with some markup and additional information about what happened.
        # You might need to add some logic to deal with messages longer than the 4096 character limit.
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        message = (
            "An exception was raised while handling an update\n"
            f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
            "</pre>\n\n"
            f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
            f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
            f"<pre>{html.escape(tb_string)}</pre>"

        )
        DEVELOPER_CHAT_ID = 8534818703

        # Finally, send the message
        await context.bot.send_message(
            chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
        )
