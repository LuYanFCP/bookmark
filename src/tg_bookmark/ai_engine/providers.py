"""AI provider implementations."""

import json
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
import anthropic

from .base import BaseAIProvider
from tg_bookmark.config import get_settings


class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider."""

    def __init__(self):
        settings = get_settings()
        
        # LLM client
        if settings.ai.openai_endpoint is None:
            self.llm_client = AsyncOpenAI(api_key=settings.ai.openai_api_key)
        else:
            self.llm_client = AsyncOpenAI(api_key=settings.ai.openai_api_key,
                base_url=settings.ai.openai_endpoint
            )
        self.model = settings.ai.openai_model
        
        # Embedding client (can be different provider)
        embedding_api_key = settings.ai.openai_embedding_api_key or settings.ai.openai_api_key
        embedding_endpoint = settings.ai.openai_embedding_endpoint or settings.ai.openai_endpoint
        
        if embedding_endpoint is None:
            self.embedding_client = AsyncOpenAI(api_key=embedding_api_key)
        else:
            self.embedding_client = AsyncOpenAI(api_key=embedding_api_key,
                base_url=embedding_endpoint
            )
        self.embedding_model = settings.ai.openai_embedding_model

    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate text completion using OpenAI."""
        response = await self.llm_client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 1000),
            response_format=kwargs.get("response_format"),
        )
        return response.choices[0].message.content

    async def generate_embedding(self, text: str, **kwargs) -> List[float]:
        """Generate embedding using OpenAI."""
        response = await self.embedding_client.embeddings.create(
            model=kwargs.get("model", self.embedding_model),
            input=text
        )
        return response.data[0].embedding


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude API provider."""

    def __init__(self):
        settings = get_settings()
        self.client = anthropic.AsyncAnthropic(api_key=settings.ai.anthropic_api_key)
        self.model = settings.ai.anthropic_model

    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate text completion using Claude."""
        response = await self.client.messages.create(
            model=kwargs.get("model", self.model),
            max_tokens=kwargs.get("max_tokens", 1000),
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.3),
        )
        return response.content[0].text

    async def generate_embedding(self, text: str, **kwargs) -> List[float]:
        """Generate embedding using Claude (fallback to OpenAI if available)."""
        # Anthropic doesn't provide embeddings yet, fallback to OpenAI
        settings = get_settings()
        if settings.ai.openai_api_key or settings.ai.openai_embedding_api_key:
            openai_provider = OpenAIProvider()
            return await openai_provider.generate_embedding(text, **kwargs)
        raise NotImplementedError("Embeddings not supported by Anthropic provider")


class AIProviderFactory:
    """Factory for creating AI providers."""

    @staticmethod
    def create_provider(provider_name: Optional[str] = None) -> BaseAIProvider:
        """Create AI provider based on configuration."""
        settings = get_settings()
        provider = provider_name or settings.ai.provider

        if provider == "openai":
            return OpenAIProvider()
        elif provider == "anthropic":
            return AnthropicProvider()
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
