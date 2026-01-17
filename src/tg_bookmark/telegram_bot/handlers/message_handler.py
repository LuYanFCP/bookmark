"""Text message handler."""
import json
from telegram.constants import ParseMode
import traceback
import html

import logging
from typing import Dict, Any
from telegram import Update, Message
from telegram.ext import ContextTypes

from tg_bookmark.ai_engine import MessageSummarizer, ContentClassifier
from tg_bookmark.content_extractor import ContentExtractionPipeline
from tg_bookmark.utils.logging import debug, info, warning, error

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

        info(logger, event="processing_message", user_id=user.id, username=user.username, message_id=message.message_id)

        try:
            # Start processing notification
            processing_msg = await message.reply_text("🤖 Processing your message...")

            # Extract content from message (including URLs, entities, etc.)
            debug(logger, event="starting_content_extraction", message_id=message.message_id)
            extracted_content = await self.extractor.process_message(message)
            full_text = extracted_content.get("text", "")
            debug(logger, event="content_extraction_complete", message_id=message.message_id, text_length=len(full_text))

            if not full_text.strip():
                await processing_msg.edit_text("❌ No content found in message.")
                return

            # Generate AI processing
            debug(logger, event="starting_ai_processing", message_id=message.message_id)
            summary = await self.summarizer.summarize(full_text, max_length=300)
            category, tags = await self.classifier.classify(full_text)
            embedding = await self.summarizer.generate_embedding(full_text)
            keywords = await self.classifier.extract_keywords(full_text)
            debug(logger, event="ai_processing_complete", message_id=message.message_id, category=category)

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
                    "is_forwarded": bool(getattr(message, 'forward_origin')),
                    "has_document": bool(getattr(message, 'document')),
                    "has_photo": bool(getattr(message, "photo")),
                    "extracted_urls": len(extracted_content.get("urls", [])),
                    "extracted_files": len(extracted_content.get("files", [])),
                    "extracted_images": len(extracted_content.get("images", [])),
                }
            }

            # Add to processing queue if available
            if "queue" in context.bot_data:
                await context.bot_data["queue"].put(processed_data)
                info(logger, event="added_to_queue", message_id=message.message_id)

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
            error(logger, event="message_processing_failed", message_id=message.message_id, user_id=user.id, error=str(e))
            logger.exception("Full traceback:")
            await message.reply_text("❌ Sorry, an error occurred while processing your message.")

    async def handle_help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        info(logger, event="help_command_received", user_id=update.message.from_user.id)
        """Handle /help command."""
        icon_url = "https://r2.whikylucky.top/avatar.png"

        start_message = (
            f"<a href='{icon_url}'>&#8204;</a>"  # 隐藏的图片链接，用于显示图标预览
            "<b>🐈 这里是小卷 Bot</b>\n"
            "<i>您的 书签机器人 </i>\n"
            "\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "<b>✨ 核心功能</b>\n"
            "• <b>总结</b> ➔ 自动提取长文要点\n"
            "• <b>分类</b> ➔ 智能标签与自动归档\n"
            "• <b>提取</b> ➔ 关键词与实体识别\n"
            "• <b>同步</b> ➔ <code>Notion</code> / <code>Obsidian</code>\n"
            "• <b>链接</b> ➔ 网页内容解析提取\n"
            "• <b>文字</b> ➔ 图像 OCR 识别\n"
            "\n"
            "<b>💡 使用方法</b>\n"
            "只需直接发送任何消息给我，我会立即为您处理！\n"
            "\n"
            "<b>🛠 常用指令</b>\n"
            "<code>/help</code>     - 获取详细帮助\n"
            "<code>/settings</code> - 偏好设置\n"
            "<code>/stats</code>    - 统计数据\n"
            "<code>/export</code>   - 导出数据\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "\n"
        )

        await update.message.reply_photo(
            photo=icon_url,
            caption=start_message,
            parse_mode=ParseMode.HTML,
        )

    async def handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""

        icon_url = "https://r2.whikylucky.top/avatar.png"

        # 精简版 HTML 内容
        start_message = (
            "<b>👋 欢迎使用小卷知识助手！</b>\n"
            "\n"
            "我是您的智能 AI 助理，负责帮您整理和存储碎片化信息。只需发送任何消息，我将为您：\n"
            "\n"
            "• <b>智能总结</b> ➔ 提炼核心内容\n"
            "• <b>自动分类</b> ➔ 智能打标归档\n"
            "• <b>提取信息</b> ➔ 捕获关键实体\n"
            "• <b>同步知识库</b> ➔ 永久存储沉淀\n"
            "\n"
            "直接发送消息开始尝试，或输入 <code>/help</code> 查看更多技巧。"
        )

        await update.message.reply_photo(
            photo=icon_url,
            caption=start_message,
            parse_mode=ParseMode.HTML
        )

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
