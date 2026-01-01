"""Base classes for AI providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate text completion."""
        pass

    @abstractmethod
    async def generate_embedding(self, text: str, **kwargs) -> List[float]:
        """Generate text embedding."""
        pass


class BaseSummarizer(ABC):
    """Abstract base class for summarization."""

    @abstractmethod
    async def summarize(self, text: str, max_length: int = 300) -> str:
        """Summarize the given text."""
        pass


class BaseClassifier(ABC):
    """Abstract base class for classification."""

    @abstractmethod
    async def classify(self, text: str) -> tuple[str, list[str]]:
        """Classify the given text."""
        pass
