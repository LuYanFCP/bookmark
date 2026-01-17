"""Content extraction pipeline."""

import logging
from typing import Dict, Any, List

from telegram import Message

from .url_processor import URLProcessor
from .file_processor import FileProcessor
from .ocr import OCRProcessor
from tg_bookmark.utils.logging import debug, info, warning, error

logger = logging.getLogger(__name__)


class ContentExtractionPipeline:
    """Pipeline for extracting content from messages."""

    def __init__(self):
        self.url_processor = URLProcessor()
        self.file_processor = FileProcessor()
        self.ocr = OCRProcessor()

    async def process_message(self, message: Message) -> Dict[str, Any]:
        """
        Extract all content from a Telegram message.

        Args:
            message: Telegram message object

        Returns:
            Dictionary containing extracted content and metadata
        """
        user = message.from_user.username if message.from_user and message.from_user.username else message.from_user.id if message.from_user else 'unknown'
        debug(
            logger,
            event="starting_extraction",
            message_id=message.message_id,
            user=user,
            has_text=bool(message.text or message.caption),
            has_entities=bool(message.entities or message.caption_entities)
        )
        
        extracted = {
            "text": "",
            "urls": [],
            "files": [],
            "images": [],
            "entities": [],
            "metadata": {}
        }

        # Extract base text
        base_text = message.text or message.caption
        if base_text:
            extracted["text"] = base_text
            debug(logger, event="text_extracted", length=len(base_text), type="text" if message.text else "caption")
        else:
            debug(logger, event="no_text_found")

        # Extract entities (URLs, mentions, etc.)
        entity_count = 0
        if message.entities:
            extracted["entities"] = await self._extract_entities(message)
            entity_count += len(extracted["entities"])
        if message.caption_entities:
            caption_entities = await self._extract_entities(message, caption=True)
            extracted["entities"].extend(caption_entities)
            entity_count += len(caption_entities)
        
        if entity_count > 0:
            debug(logger, event="entities_extracted", count=entity_count)

        # Process URLs
        urls = await self._extract_urls(message, extracted["entities"])
        if urls:
            extracted["urls"] = urls
            info(logger, event="urls_found", count=len(urls), urls=urls)
            
            # Fetch content from URLs
            url_contents = []
            for url in urls:
                try:
                    debug(logger, event="fetching_url", url=url)
                    content = await self.url_processor.extract(url)
                    debug(logger, event="url_content_extracted", url=url, length=len(content))
                    url_contents.append(f"\n\n[From URL: {url}]\n{content}")
                except Exception as e:
                    warning(logger, event="url_extraction_failed", url=url, error=str(e))
                    url_contents.append(f"\n\n[From URL: {url}]\nFailed to extract content")

            if url_contents:
                extracted["text"] += "".join(url_contents)
                debug(logger, event="url_content_appended", total_length=len(extracted["text"]))
        else:
            debug(logger, event="no_urls_found")

        # Process documents
        if message.document:
            info(
                logger,
                event="document_found",
                file_name=message.document.file_name,
                mime_type=message.document.mime_type,
                file_size=message.document.file_size
            )
            try:
                file_content = await self.file_processor.extract_document(
                    message.document,
                    context=message.get_bot()
                )
                if file_content:
                    extracted["files"].append({
                        "file_id": message.document.file_id,
                        "file_name": message.document.file_name,
                        "mime_type": message.document.mime_type,
                    })
                    extracted["text"] += f"\n\n[Document Content: {message.document.file_name}]\n{file_content}"
                    debug(logger, event="document_extracted", file_name=message.document.file_name, content_length=len(file_content))
            except Exception as e:
                error(logger, event="document_extraction_failed", file_name=message.document.file_name, error=str(e))
        else:
            debug(logger, event="no_document_found")

        # Process photos with OCR
        if message.photo:
            photo_count = len(message.photo)
            info(logger, event="photo_found", photo_count=photo_count)
            try:
                # Get the largest photo
                photo = message.photo[-1]
                debug(logger, event="processing_photo", photo_id=photo.file_id, dimensions=f"{photo.width}x{photo.height}")
                ocr_text = await self.ocr.extract_from_photo(
                    photo,
                    context=message.get_bot()
                )
                if ocr_text:
                    extracted["images"].append({
                        "file_id": photo.file_id,
                        "width": photo.width,
                        "height": photo.height,
                    })
                    extracted["text"] += f"\n\n[OCR from Image]\n{ocr_text}"
                    debug(logger, event="ocr_completed", photo_id=photo.file_id, text_length=len(ocr_text))
            except Exception as e:
                error(logger, event="ocr_failed", photo_id=photo.file_id, error=str(e))
        else:
            debug(logger, event="no_photo_found")

        # Process voice messages (if supported)
        if message.voice or message.audio:
            # Note: Would need speech-to-text service for this
            info(logger, event="voice_message_received", has_voice=bool(message.voice), has_audio=bool(message.audio))

        # Update metadata
        extracted["metadata"] = {
            "chat_type": message.chat.type,
            "chat_id": message.chat.id,
            "has_entities": bool(message.entities or message.caption_entities),
            "is_forwarded": bool(getattr(message, 'forward_origin', None)),
            "extracted_urls": len(urls),
            "extracted_files": len(extracted["files"]),
            "extracted_images": len(extracted["images"]),
        }
        
        debug(
            logger,
            event="extraction_complete",
            message_id=message.message_id,
            text_length=len(extracted["text"]),
            urls_count=len(urls),
            files_count=len(extracted["files"]),
            images_count=len(extracted["images"])
        )

        return extracted

    async def _extract_entities(self, message: Message, caption: bool = False) -> List[Dict[str, Any]]:
        """Extract entities from message."""
        entities = []
        source_entities = message.caption_entities if caption else message.entities
        text = message.caption if caption else message.text

        for entity in source_entities:
            entity_data = {
                "type": entity.type,
                "offset": entity.offset,
                "length": entity.length,
                "text": text[entity.offset:entity.offset + entity.length]
            }
            entities.append(entity_data)

        return entities

    async def _extract_urls(self, message: Message, entities: List[Dict[str, Any]]) -> List[str]:
        """Extract URLs from message entities."""
        urls = []

        for entity in entities:
            if entity["type"] == "url":
                urls.append(entity["text"])
            elif entity["type"] == "text_link":
                # URL is in the entity URL field
                for raw_entity in (message.entities or message.caption_entities or []):
                    if raw_entity.offset == entity["offset"] and hasattr(raw_entity, "url"):
                        urls.append(raw_entity.url)
                        break

        # Also check for URLs in plain text
        import re
        text = message.text or message.caption or ""
        # Improved pattern to support Unicode characters (Chinese, etc.) and URL encoding
        url_pattern = r'https?://[^\s<>{}|\\^`\[\]]+(?:\?[^\s<>{}|\\^`\[\]]+)?(?:#[^\s<>{}|\\^`\[\]]+)?'
        plain_urls = re.findall(url_pattern, text)
        urls.extend(plain_urls)

        return list(set(urls))  # Remove duplicates
