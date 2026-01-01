"""Content extraction pipeline."""

import logging
from typing import Dict, Any, List

from telegram import Message

from .url_processor import URLProcessor
from .file_processor import FileProcessor
from .ocr import OCRProcessor

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
        extracted = {
            "text": "",
            "urls": [],
            "files": [],
            "images": [],
            "entities": [],
            "metadata": {}
        }
        
        # Extract base text
        if message.text:
            extracted["text"] = message.text
        elif message.caption:
            extracted["text"] = message.caption
        
        # Extract entities (URLs, mentions, etc.)
        if message.entities:
            extracted["entities"] = await self._extract_entities(message)
        
        if message.caption_entities:
            extracted["entities"].extend(await self._extract_entities(message, caption=True))
        
        # Process URLs
        urls = await self._extract_urls(message, extracted["entities"])
        if urls:
            extracted["urls"] = urls
            # Fetch content from URLs
            url_contents = []
            for url in urls:
                try:
                    content = await self.url_processor.extract(url)
                    url_contents.append(f"\n\n[From URL: {url}]\n{content}")
                except Exception as e:
                    logger.warning(f"Failed to extract content from {url}: {e}")
                    url_contents.append(f"\n\n[From URL: {url}]\nFailed to extract content")
            
            if url_contents:
                extracted["text"] += "".join(url_contents)
        
        # Process documents
        if message.document:
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
            except Exception as e:
                logger.error(f"Failed to process document: {e}")
        
        # Process photos with OCR
        if message.photo:
            try:
                # Get the largest photo
                photo = message.photo[-1]
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
            except Exception as e:
                logger.error(f"Failed to process photo: {e}")
        
        # Process voice messages (if supported)
        if message.voice or message.audio:
            # Note: Would need speech-to-text service for this
            logger.info("Voice/audio message received - transcription not implemented")
        
        # Update metadata
        extracted["metadata"] = {
            "chat_type": message.chat.type,
            "chat_id": message.chat.id,
            "has_entities": bool(message.entities or message.caption_entities),
            "is_forwarded": bool(message.forward_from or message.forward_from_chat),
            "extracted_urls": len(urls),
            "extracted_files": len(extracted["files"]),
            "extracted_images": len(extracted["images"]),
        }
        
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
        url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.]+))?)?(?:#[\w\-]+)?'
        plain_urls = re.findall(url_pattern, text)
        urls.extend(plain_urls)
        
        return list(set(urls))  # Remove duplicates