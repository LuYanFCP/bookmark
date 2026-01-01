"""Base storage interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseStorage(ABC):
    """Abstract base class for storage implementations."""
    
    @abstractmethod
    async def save_message(self, data: Dict[str, Any]) -> str:
        """
        Save a processed message.
        
        Args:
            data: Processed message data
            
        Returns:
            Storage identifier (page ID, file path, etc.)
        """
        pass
    
    @abstractmethod
    async def get_message(self, identifier: str) -> Dict[str, Any]:
        """
        Retrieve a message by identifier.
        
        Args:
            identifier: Storage identifier
            
        Returns:
            Message data
        """
        pass
    
    @abstractmethod
    async def update_message(self, identifier: str, updates: Dict[str, Any]) -> bool:
        """
        Update a stored message.
        
        Args:
            identifier: Storage identifier
            updates: Fields to update
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def delete_message(self, identifier: str) -> bool:
        """
        Delete a stored message.
        
        Args:
            identifier: Storage identifier
            
        Returns:
            Success status
        """
        pass