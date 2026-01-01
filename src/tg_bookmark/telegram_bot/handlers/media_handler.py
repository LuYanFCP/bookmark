"""Media message handler."""

import logging
from typing import Any, Dict

from telegram import Document, Message, PhotoSize, Update
from telegram.ext import ContextTypes

from ...ai_engine import ContentClassifier, MessageSummarizer
from ...content_extractor import ContentExtractionPipeline

logger = logging.getLogger(__name__)


class MediaHandler:
    """Handles media messages (documents, photos, etc.)."""

    def __init__(self):
        self.extractor = ContentExtractionPipeline()
        self.summarizer = MessageSummarizer()
        self.classifier = ContentClassifier()

    async def handle_media_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Process media messages."""
        if not update.message:
            return

        message: Message = update.message
        user = message.from_user

        logger.info(f"Processing media message from user {user.id}")

        try:
            processing_msg = await message.reply_text("📁 Processing your media...")

            # Extract content from media
            extracted_content = await self.extractor.process_message(message)
            full_text = extracted_content.get("text", "")

            if not full_text.strip():
                # No text content extracted, create a basic description
                media_info = self._describe_media(message)
                full_text = f"Media file received: {media_info}"

            # Process with AI
            summary = await self.summarizer.summarize(full_text, max_length=300)
            category, tags = await self.classifier.classify(full_text)
            embedding = await self.summarizer.generate_embedding(full_text)

            # Prepare data
            processed_data: Dict[str, Any] = {
                "user_id": user.id,
                "user_username": user.username,
                "message_id": message.message_id,
                "timestamp": message.date.isoformat(),
                "content": full_text,
                "summary": summary,
                "category": category,
                "tags": tags,
                "embedding": embedding,
                "metadata": {
                    "chat_type": message.chat.type,
                    "chat_id": message.chat.id,
                    "has_media": True,
                    "media_type": self._get_media_type(message),
                    **extracted_content.get("metadata", {}),
                },
            }

            # Add to queue
            if "queue" in context.bot_data:
                await context.bot_data["queue"].put(processed_data)

            # Respond to user
            result_text = (
                f"✅ *Media Processed Successfully!*\n\n"
                f"📁 *Type:* {self._get_media_type(message)}\n"
                f"🏷️ *Category:* {category}\n"
                f"🏷️ *Tags:* {', '.join(tags)}\n\n"
                f"📝 *Summary:*\n_{summary}_"
            )

            await processing_msg.edit_text(result_text, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error processing media message: {e}", exc_info=True)
            await message.reply_text("❌ Error processing your media file.")

    def _get_media_type(self, message: Message) -> str:
        """Get media type from message."""
        if message.document:
            return f"Document ({message.document.mime_type})"
        elif message.photo:
            return "Photo"
        elif message.audio:
            return "Audio"
        elif message.video:
            return "Video"
        elif message.voice:
            return "Voice Message"
        else:
            return "Unknown"

    def _describe_media(self, message: Message) -> str:
        """Create a description of the media."""
        parts = []

        if message.document:
            doc: Document = message.document
            parts.append(f"Document: {doc.file_name}")
            parts.append(f"Size: {doc.file_size} bytes")
            parts.append(f"Type: {doc.mime_type}")
        elif message.photo:
            photo: PhotoSize = message.photo[-1]  # Largest size
            parts.append(f"Photo")
            parts.append(f"Size: {photo.file_size} bytes")
            parts.append(f"Dimensions: {photo.width}x{photo.height}")
        elif message.audio:
            parts.append(f"Audio: {message.audio.file_name}")
            parts.append(f"Duration: {message.audio.duration} seconds")
        elif message.video:
            parts.append(f"Video")
            parts.append(f"Duration: {message.video.duration} seconds")
        elif message.voice:
            parts.append(f"Voice Message")
            parts.append(f"Duration: {message.voice.duration} seconds")

        if message.caption:
            parts.append(f"Caption: {message.caption}")

        return ". ".join(parts)
