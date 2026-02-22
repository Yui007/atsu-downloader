"""Manga scraper for Atsu.moe."""

import logging
import re
from typing import Optional
from urllib.parse import urlparse

from api.client import AtsuClient
from models import MangaInfo

logger = logging.getLogger(__name__)


def parse_manga_id(url: str) -> Optional[str]:
    """Extract manga ID from URL.
    
    Supports:
    - https://atsu.moe/manga/OaKBx
    - atsu.moe/manga/OaKBx
    - /manga/OaKBx
    - OaKBx (direct ID)
    """
    url = url.strip()
    
    # If it looks like a direct ID (no slashes, short alphanumeric)
    if re.match(r'^[A-Za-z0-9]{3,10}$', url):
        return url
    
    # Parse as URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    
    # Match /manga/{id} pattern
    match = re.match(r'^manga/([A-Za-z0-9]+)', path)
    if match:
        return match.group(1)
    
    logger.warning(f"Could not parse manga ID from URL: {url}")
    return None


class MangaScraper:
    """High-level manga scraping interface."""

    def __init__(self, client: Optional[AtsuClient] = None):
        self.client = client or AtsuClient()
        self._owns_client = client is None

    def fetch_manga(self, url_or_id: str) -> Optional[MangaInfo]:
        """Fetch manga info from URL or ID.
        
        Args:
            url_or_id: Either a full URL or manga ID
            
        Returns:
            MangaInfo if successful, None otherwise
        """
        manga_id = parse_manga_id(url_or_id)
        if not manga_id:
            logger.error(f"Invalid manga URL or ID: {url_or_id}")
            return None
        
        try:
            logger.info(f"Fetching manga metadata: {manga_id}")
            manga = self.client.get_manga_info(manga_id)
            
            if manga:
                logger.info(f"Fetching all chapters for: {manga_id}")
                all_chapters = self.client.get_all_chapters(manga_id)
                manga.chapters = all_chapters
                logger.info(f"Retrieved {len(all_chapters)} chapters.")
                
            return manga
        except Exception as e:
            logger.error(f"Failed to fetch manga info: {e}")
            return None


    def close(self):
        """Close resources."""
        if self._owns_client:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
