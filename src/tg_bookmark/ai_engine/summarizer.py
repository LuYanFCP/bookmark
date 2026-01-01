"""Message summarization module."""

import json
from typing import Optional

from .base import BaseSummarizer
from .providers import AIProviderFactory


class MessageSummarizer(BaseSummarizer):
    """AI-powered message summarizer."""

    def __init__(self, provider_name: Optional[str] = None):
        self.provider = AIProviderFactory.create_provider(provider_name)

    async def summarize(self, text: str, max_length: int = 300) -> str:
        """
        Summarize the given text.

        Args:
            text: Text to summarize
            max_length: Maximum length of summary in characters

        Returns:
            Summarized text
        """
        if len(text) <= max_length:
            return text

        prompt = f"""
        Please provide a concise summary of the following text.
        The summary should be approximately {max_length} characters or less.
        Focus on the main points and key information.

        Text to summarize:
        {text}

        Provide only the summary without any additional text or formatting.
        """

        summary = await self.provider.complete(prompt, max_tokens=200)
        return summary.strip()

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for the given text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        return await self.provider.generate_embedding(text)
