"""URL content extraction."""

import logging
from typing import Optional
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class URLProcessor:
    """Extract content from URLs."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def extract(self, url: str) -> str:
        """
        Extract text content from a URL.

        Args:
            url: URL to extract content from

        Returns:
            Extracted text content
        """
        try:
            # Check if it's a YouTube URL
            if self._is_youtube_url(url):
                return await self._extract_youtube_content(url)

            # Regular web page
            return await self._extract_web_content(url)

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return f"Failed to extract content from {url}: {str(e)}"

    def _is_youtube_url(self, url: str) -> bool:
        """Check if URL is a YouTube video."""
        youtube_domains = [
            'youtube.com',
            'youtu.be',
            'www.youtube.com',
            'm.youtube.com'
        ]

        return any(domain in url for domain in youtube_domains)

    async def _extract_youtube_content(self, url: str) -> str:
        """Extract YouTube video information."""
        try:
            # Try to get transcript
            from youtube_transcript_api import YouTubeTranscriptApi

            # Extract video ID from URL
            video_id = self._extract_youtube_id(url)
            if not video_id:
                return "Could not extract YouTube video ID"

            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            if transcript:
                text = " ".join([entry["text"] for entry in transcript[:50]])  # First 50 entries
                return f"YouTube Video Transcript:\n{text[:2000]}..."  # Limit length
            else:
                return "YouTube video found but no transcript available"

        except Exception as e:
            logger.warning(f"Could not extract YouTube transcript: {e}")
            return f"YouTube video: {url} (transcript not available)"

    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        import re

        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11})',
            r'(?:embed/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be/)([0-9A-Za-z_-]{11})'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    async def _extract_web_content(self, url: str) -> str:
        """Extract content from a regular web page."""
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()

                # Get title
                title = soup.find('title')
                title_text = title.get_text() if title else "No title"

                # Get meta description
                description = ""
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    description = meta_desc.get('content', '')

                # Get main content
                # Try common content containers
                content = ""
                for selector in ['main', 'article', '.content', '.post', '.entry']:
                    element = soup.select_one(selector)
                    if element:
                        content = element.get_text(separator=' ', strip=True)
                        break

                # Fallback: get all text
                if not content:
                    content = soup.get_text(separator=' ', strip=True)

                # Limit content length
                if len(content) > 2000:
                    content = content[:2000] + "..."

                return f"Title: {title_text}\n\nDescription: {description}\n\nContent: {content}"

            except Exception as e:
                logger.error(f"Failed to fetch URL {url}: {e}")
                return f"Failed to fetch content from {url}: {str(e)}"
