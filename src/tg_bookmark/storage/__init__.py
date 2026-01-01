"""Storage module for persisting processed messages."""

from .base import BaseStorage
from .notion import NotionStorage
from .obsidian import ObsidianStorage
from .factory import StorageFactory

__all__ = ["BaseStorage", "NotionStorage", "ObsidianStorage", "StorageFactory"]