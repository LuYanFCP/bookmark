"""Storage factory for creating storage instances."""

from typing import Optional

from .base import BaseStorage
from .notion import NotionStorage
from .obsidian import ObsidianStorage
from tg_bookmark.config import get_settings


class StorageFactory:
    """Factory for creating storage instances."""

    @staticmethod
    def create_storage(storage_type: Optional[str] = None) -> Optional[BaseStorage]:
        """
        Create storage instance based on configuration.

        Args:
            storage_type: Type of storage ("notion", "obsidian")

        Returns:
            Storage instance or None if not configured
        """
        settings = get_settings()
        storage_type = storage_type or settings.storage.primary

        if storage_type == "notion":
            try:
                return NotionStorage()
            except Exception as e:
                print(f"Failed to create Notion storage: {e}")
                return None

        elif storage_type == "obsidian":
            try:
                return ObsidianStorage()
            except Exception as e:
                print(f"Failed to create Obsidian storage: {e}")
                return None

        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")

    @staticmethod
    def get_all_storages() -> list[BaseStorage]:
        """Get all configured storage instances."""
        storages = []
        settings = get_settings()

        # Add primary storage
        primary = StorageFactory.create_storage(settings.storage.primary)
        if primary:
            storages.append(primary)

        # Add Notion if enabled and not already added
        if settings.storage.notion.is_enabled:
            notion = StorageFactory.create_storage("notion")
            if notion and notion not in storages:
                storages.append(notion)

        # Add Obsidian if enabled and not already added
        if settings.storage.obsidian.is_enabled:
            obsidian = StorageFactory.create_storage("obsidian")
            if obsidian and obsidian not in storages:
                storages.append(obsidian)

        return storages
