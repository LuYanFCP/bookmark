"""Content classification module."""

import json
from typing import Dict, Any, List, Tuple

from .base import BaseClassifier
from .providers import AIProviderFactory


class ContentClassifier(BaseClassifier):
    """AI-powered content classifier."""

    def __init__(self, provider_name: str = "openai"):
        self.provider = AIProviderFactory.create_provider(provider_name)
        self.categories = [
            "Technology/Programming",
            "Learning Notes",
            "Ideas/Inspiration",
            "To-Do Items",
            "Article Summary",
            "Link Collection",
            "Meeting Notes",
            "Project Planning",
            "Personal Journal"
        ]

    async def classify(self, text: str) -> tuple[str, list[str]]:
        """
        Classify text and generate tags.

        Args:
            text: Text to classify

        Returns:
            Tuple of (category, tags_list)
        """
        prompt = f"""
        Analyze the following content and:
        1. Choose the most appropriate category (select from: {', '.join(self.categories)})
        2. Generate 3-5 relevant tags that capture the main topics

        Content: {text}

        Return ONLY a JSON object in this exact format:
        {{"category": "Category Name", "tags": ["tag1", "tag2", "tag3"]}}
        """

        try:
            response = await self.provider.complete(
                prompt,
                max_tokens=200,
                response_format={"type": "json_object"}
            )

            result = json.loads(response)

            # Validate category
            category = result.get("category", "Learning Notes")
            if category not in self.categories:
                # Find most similar category
                category = self._find_best_category(category)

            # Ensure tags is a list
            tags = result.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]

            return category, list(set(tags))  # Remove duplicates

        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to default classification
            return "Learning Notes", ["general"]

    def _find_best_category(self, predicted: str) -> str:
        """Find the closest matching category."""
        # Simple fallback: if predicted category is close to one in our list, use it
        predicted_lower = predicted.lower()

        for category in self.categories:
            if category.lower() in predicted_lower or predicted_lower in category.lower():
                return category

        return "Learning Notes"

    async def extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text: Text to analyze
            top_k: Number of keywords to extract

        Returns:
            List of keywords
        """
        prompt = f"""
        Extract {top_k} key terms or phrases from the following text.
        Focus on important concepts, technologies, topics, or entities.

        Text: {text}

        Return ONLY a JSON object:
        {{"keywords": ["keyword1", "keyword2", "keyword3"]}}
        """

        try:
            response = await self.provider.complete(
                prompt,
                max_tokens=200,
                response_format={"type": "json_object"}
            )

            result = json.loads(response)
            return result.get("keywords", [])[:top_k]

        except (json.JSONDecodeError, KeyError):
            return []
