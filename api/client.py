"""HTTP client with retry logic for Atsu API."""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import requests

from config import get_config
from models import MangaInfo, Chapter, Page

logger = logging.getLogger(__name__)

BASE_URL = "https://atsu.moe"


def retry_with_backoff(func: Callable) -> Callable:
    """Decorator for retry with exponential backoff."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        config = get_config()
        max_retries = config.max_retries
        base_delay = config.retry_delay
        
        last_exception: Optional[requests.RequestException] = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except requests.RequestException as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Request failed after {max_retries} attempts: {e}")
        
        if last_exception is not None:
            raise last_exception
        raise requests.RequestException("Max retries exceeded")
    return wrapper


class AtsuClient:
    """HTTP client for Atsu.moe API."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": BASE_URL,
        })

    @retry_with_backoff
    def get_manga_info(self, manga_id: str) -> MangaInfo:
        """Fetch manga information (metadata)."""
        url = f"{BASE_URL}/api/manga/page"
        params = {"id": manga_id}
        
        logger.info(f"Fetching manga page info for: {manga_id}")
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return MangaInfo.from_dict(data)

    @retry_with_backoff
    def get_all_chapters(self, manga_id: str) -> List[Chapter]:
        """Fetch all chapters for a manga using the dedicated endpoint."""
        url = f"{BASE_URL}/api/manga/allChapters"
        params = {"mangaId": manga_id}
        
        logger.info(f"Fetching all chapters for: {manga_id}")
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        chapters_data = data.get("chapters", [])
        
        return [Chapter.from_dict(ch) for ch in chapters_data]

    @retry_with_backoff
    def get_chapter_pages(self, manga_id: str, chapter_id: str) -> List[Page]:
        """Fetch chapter pages/images."""
        url = f"{BASE_URL}/api/read/chapter"
        params = {"mangaId": manga_id, "chapterId": chapter_id}
        
        logger.info(f"Fetching chapter pages: {chapter_id}")
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        read_chapter = data.get("readChapter", {})
        pages_data = read_chapter.get("pages", [])
        
        pages = []
        for p in pages_data:
            pages.append(Page(
                id=p["id"],
                image=p["image"],
                number=p["number"],
                width=p.get("width", 0),
                height=p.get("height", 0),
                aspect_ratio=p.get("aspectRatio", 0.0)
            ))
        
        return pages


    @retry_with_backoff
    def download_image(self, image_path: str) -> bytes:
        """Download a single image and return bytes."""
        url = f"{BASE_URL}{image_path}"
        
        logger.debug(f"Downloading image: {url}")
        response = self.session.get(url, timeout=60)
        response.raise_for_status()
        
        return response.content

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
