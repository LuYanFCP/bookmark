"""Notion storage implementation."""

import logging
from typing import Any, Dict, Optional
from notion_client import AsyncClient
from notion_client.errors import APIResponseError

from .base import BaseStorage
from tg_bookmark.config import get_settings
from tg_bookmark.utils.logging import debug, info, warning, error

logger = logging.getLogger(__name__)


class NotionStorage(BaseStorage):
    """Notion database storage implementation."""
    
    def __init__(self, api_key: Optional[str] = None, database_id: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.storage.notion.api_key
        self.database_id = database_id or settings.storage.notion.database_id
        
        if not self.api_key or not self.database_id:
            raise ValueError("Notion API key and database ID are required")
        
        self.client = AsyncClient(auth=self.api_key)
    
    async def save_message(self, data: Dict[str, Any]) -> str:
        """Save message to Notion database."""
        user_id = data.get("user_id")
        message_id = data.get("message_id")
        category = data.get("category", "Unknown")
        
        debug(logger, event="notion_save_start", user_id=user_id, message_id=message_id, category=category)
        
        try:
            # Build properties for Notion page
            debug(logger, event="building_notion_properties", message_id=message_id)
            properties = self._build_properties(data)
            
            # Build content for the page (children blocks)
            debug(logger, event="building_notion_blocks", message_id=message_id)
            children = self._build_content_blocks(data)
            
            # Create page in database
            debug(logger, event="creating_notion_page", message_id=message_id, block_count=len(children))
            page = await self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children
            )
            
            page_id = page["id"]
            info(logger, event="notion_save_success", user_id=user_id, message_id=message_id, page_id=page_id, category=category)
            return page_id
            
        except APIResponseError as e:
            error(logger, event="notion_api_error", user_id=user_id, message_id=message_id, error=str(e), status=e.status)
            raise
        except Exception as e:
            error(logger, event="notion_save_failed", user_id=user_id, message_id=message_id, error=str(e))
            raise
    
    def _build_properties(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion page properties."""
        properties = {}
        
        # Title (summary)
        properties["Title"] = {
            "title": [{"text": {"content": data["summary"][:100]}}]
        }
        
        # Category
        category = data.get("category", "Learning Notes")
        properties["Category"] = {
            "select": {"name": category}
        }
        
        # Tags
        tags = data.get("tags", [])
        if tags:
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in tags[:20]]  # Notion limit
            }
        
        # User ID
        properties["User ID"] = {
            "number": data["user_id"]
        }
        
        # Message ID
        properties["Message ID"] = {
            "number": data["message_id"]
        }
        
        # Date
        properties["Date"] = {
            "date": {"start": data["timestamp"]}
        }
        
        # Keywords
        keywords = data.get("keywords", [])
        if keywords:
            properties["Keywords"] = {
                "multi_select": [{"name": kw[:100]} for kw in keywords[:20]]
            }
        
        return properties
    
    def _build_content_blocks(self, data: Dict[str, Any]) -> list[Dict[str, Any]]:
        """Build Notion page content blocks."""
        blocks = []
        
        # Summary section
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Summary"}}]
            }
        })
        
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": data["summary"]}}]
            }
        })
        
        # Full content section
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Full Content"}}]
            }
        })
        
        # Split content into chunks (Notion has a block limit)
        content = data["content"]
        if len(content) > 2000:
            # Split into multiple paragraphs
            for i in range(0, len(content), 1900):
                chunk = content[i:i+1900]
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                }
            })
        
        # Metadata section
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Metadata"}}]
            }
        })
        
        metadata = data.get("metadata", {})
        metadata_text = f"""
        User: {data.get('user_username', data['user_id'])}
        Message ID: {data['message_id']}
        Timestamp: {data['timestamp']}
        Chat Type: {metadata.get('chat_type', 'Unknown')}
        Has Media: {metadata.get('has_media', False)}
        URLs Extracted: {metadata.get('extracted_urls', 0)}
        Files Processed: {metadata.get('extracted_files', 0)}
        """
        
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": metadata_text}}]
            }
        })
        
        return blocks
    
    async def get_message(self, page_id: str) -> Dict[str, Any]:
        """Retrieve a page from Notion."""
        try:
            page = await self.client.pages.retrieve(page_id=page_id)
            return dict(page)
        except APIResponseError as e:
            logger.error(f"Notion API error: {e}")
            raise
    
    async def update_message(self, page_id: str, updates: Dict[str, Any]) -> bool:
        """Update a Notion page."""
        try:
            properties = self._build_properties(updates)
            await self.client.pages.update(page_id=page_id, properties=properties)
            logger.info(f"Updated Notion page: {page_id}")
            return True
        except APIResponseError as e:
            logger.error(f"Notion API error: {e}")
            return False
    
    async def delete_message(self, page_id: str) -> bool:
        """Archive (soft delete) a Notion page."""
        try:
            await self.client.pages.update(page_id=page_id, archived=True)
            logger.info(f"Archived Notion page: {page_id}")
            return True
        except APIResponseError as e:
            logger.error(f"Notion API error: {e}")
            return False