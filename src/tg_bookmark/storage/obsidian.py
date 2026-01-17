"""Obsidian storage implementation."""

import os
import logging
from datetime import datetime
from typing import Any, Dict, Optional
import frontmatter

from .base import BaseStorage
from tg_bookmark.config import get_settings
from tg_bookmark.utils.logging import debug, info, warning, error

logger = logging.getLogger(__name__)


class ObsidianStorage(BaseStorage):
    """Obsidian vault storage implementation."""
    
    def __init__(self, vault_path: Optional[str] = None):
        settings = get_settings()
        self.vault_path = vault_path or settings.storage.obsidian.vault_path
        self.daily_notes = settings.storage.obsidian.daily_notes
        self.folder_structure = settings.storage.obsidian.folder_structure
        
        if not self.vault_path:
            raise ValueError("Obsidian vault path is required")
        
        if not os.path.exists(self.vault_path):
            raise ValueError(f"Obsidian vault not found at: {self.vault_path}")
        
        logger.info(f"Initialized Obsidian storage at: {self.vault_path}")
    
    async def save_message(self, data: Dict[str, Any]) -> str:
        """Save message as Obsidian markdown file."""
        user_id = data.get("user_id")
        message_id = data.get("message_id")
        category = data.get("category", "Unknown")
        
        debug(logger, event="obsidian_save_start", user_id=user_id, message_id=message_id, category=category, vault_path=self.vault_path)
        
        try:
            # Generate file path
            debug(logger, event="generating_file_path", message_id=message_id)
            file_path = self._generate_file_path(data)
            debug(logger, event="file_path_generated", message_id=message_id, file_path=file_path)
            
            # Ensure directory exists
            dir_path = os.path.dirname(file_path)
            debug(logger, event="creating_directory", directory=dir_path)
            os.makedirs(dir_path, exist_ok=True)
            debug(logger, event="directory_ready", directory=dir_path)
            
            # Build frontmatter and content
            debug(logger, event="building_file_content", message_id=message_id)
            file_content = self._build_file_content(data)
            debug(logger, event="file_content_built", message_id=message_id, content_length=len(file_content))
            
            # Write file
            debug(logger, event="writing_file", message_id=message_id, file_path=file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            # Verify file was written
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                info(logger, event="obsidian_save_success", user_id=user_id, message_id=message_id, file_path=file_path, file_size=file_size, category=category)
            else:
                error(logger, event="obsidian_file_not_found_after_write", user_id=user_id, message_id=message_id, file_path=file_path)
                raise FileNotFoundError(f"File not found after writing: {file_path}")
            
            return file_path
            
        except Exception as e:
            error(logger, event="obsidian_save_failed", user_id=user_id, message_id=message_id, error=str(e))
            raise
    
    def _generate_file_path(self, data: Dict[str, Any]) -> str:
        """Generate file path based on configuration."""
        timestamp = datetime.fromisoformat(data["timestamp"])
        
        # Build folder structure
        folder = self.folder_structure.format(
            category=data.get("category", "General"),
            year=timestamp.year,
            month=timestamp.month,
            day=timestamp.day,
            user_id=data["user_id"]
        )
        
        # Clean folder name (remove special characters)
        folder = folder.replace("/", "_").replace("\\", "_")
        
        # Generate filename
        if self.daily_notes:
            # Use daily note format
            filename = f"{timestamp.strftime('%Y-%m-%d')}.md"
            
            # Append message as section to daily note
            folder_path = os.path.join(self.vault_path, folder)
            return os.path.join(folder_path, filename)
        else:
            # Use unique filename for each message
            filename = f"{timestamp.strftime('%Y-%m-%d-%H%M')}-{data['message_id']}.md"
            folder_path = os.path.join(self.vault_path, folder)
            return os.path.join(folder_path, filename)
    
    def _build_file_content(self, data: Dict[str, Any]) -> str:
        """Build markdown file content with frontmatter."""
        
        if self.daily_notes:
            # Append to daily note format
            return self._build_daily_note_append(data)
        else:
            # Standalone file format
            return self._build_standalone_file(data)
    
    def _build_standalone_file(self, data: Dict[str, Any]) -> str:
        """Build standalone markdown file."""
        # Create frontmatter
        post = frontmatter.Post("")
        
        # Add metadata to frontmatter
        post["title"] = data["summary"][:100]
        post["category"] = data.get("category", "General")
        post["tags"] = data.get("tags", [])
        post["keywords"] = data.get("keywords", [])
        post["message_id"] = data["message_id"]
        post["user_id"] = data["user_id"]
        post["user_username"] = data.get("user_username")
        post["created_at"] = data["timestamp"]
        post["ai_summary"] = data["summary"]
        post["has_media"] = data.get("metadata", {}).get("has_media", False)
        post["media_type"] = data.get("metadata", {}).get("media_type")
        
        # Build content
        lines = []
        lines.append("> [!AI Summary] " + data["summary"]
        )
        lines.append("")
        lines.append("## Content")
        lines.append("")
        lines.append(data["content"])
        lines.append("")
        
        # Add metadata section
        lines.append("## Metadata")
        lines.append("")
        metadata = data.get("metadata", {})
        lines.append(f"- **Chat Type:** {metadata.get('chat_type', 'Unknown')}")
        lines.append(f"- **Message ID:** {data['message_id']}")
        lines.append(f"- **Timestamp:** {data['timestamp']}")
        
        if metadata.get("extracted_urls"):
            lines.append(f"- **URLs Extracted:** {metadata['extracted_urls']}")
        if metadata.get("extracted_files"):
            lines.append(f"- **Files Processed:** {metadata['extracted_files']}")
        if metadata.get("extracted_images"):
            lines.append(f"- **Images Processed:** {metadata['extracted_images']}")
        
        post.content = "\n".join(lines)
        
        return frontmatter.dumps(post)
    
    def _build_daily_note_append(self, data: Dict[str, Any]) -> str:
        """Build content to append to daily note."""
        timestamp = datetime.fromisoformat(data["timestamp"])
        time_str = timestamp.strftime('%H:%M')
        
        lines = []
        lines.append("")
        lines.append(f"## Message at {time_str}")
        lines.append("")
        lines.append(f"**Category:** {data.get('category', 'General')}")
        lines.append(f"**Tags:** {', '.join(data.get('tags', []))}")
        lines.append("")
        lines.append("> [!Summary] " + data["summary"]
        )
        lines.append("")
        lines.append("### Content")
        lines.append("")
        lines.append(data["content"])
        lines.append("")
        
        return "\n".join(lines)
    
    async def get_message(self, file_path: str) -> Dict[str, Any]:
        """Read a message from Obsidian file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            post = frontmatter.loads(content)
            
            return {
                "content": post.content,
                "metadata": post.metadata,
                "file_path": file_path
            }
        except Exception as e:
            logger.error(f"Error reading Obsidian file: {e}")
            raise
    
    async def update_message(self, file_path: str, updates: Dict[str, Any]) -> bool:
        """Update an Obsidian file."""
        try:
            # Read existing file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            post = frontmatter.loads(content)
            
            # Update metadata
            post.metadata.update(updates)
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
            
            logger.info(f"Updated Obsidian file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating Obsidian file: {e}")
            return False
    
    async def delete_message(self, file_path: str) -> bool:
        """Delete an Obsidian file."""
        try:
            os.remove(file_path)
            logger.info(f"Deleted Obsidian file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting Obsidian file: {e}")
            return False