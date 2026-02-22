"""Data models for the Atsu Downloader."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Page:
    """Represents a single page/image in a chapter."""
    id: str
    image: str
    number: int
    width: int = 0
    height: int = 0
    aspect_ratio: float = 0.0

    @property
    def full_url(self) -> str:
        """Get the full image URL."""
        return f"https://atsu.moe{self.image}"



@dataclass
class Chapter:
    """Represents a manga chapter."""
    id: str
    title: str
    number: float
    index: int
    page_count: int
    scanlation_manga_id: str = ""
    pages: List[Page] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Chapter":
        """Create a Chapter from API response dict."""
        number = data.get("number")
        if number is None:
            number = 0.0
            
        return cls(
            id=data["id"],
            title=data["title"],
            number=float(number),
            index=data.get("index", 0),
            page_count=data.get("pageCount", 0),
            scanlation_manga_id=data.get("scanlationMangaId") or data.get("scanId") or ""
        )


@dataclass
class Scanlator:
    """Represents a scanlation group."""
    id: str
    name: str

    @classmethod
    def from_dict(cls, data: dict) -> "Scanlator":
        """Create a Scanlator from API response dict."""
        return cls(
            id=data["id"],
            name=data["name"]
        )


@dataclass
class MangaInfo:
    """Represents manga information and chapters."""
    id: str
    title: str
    manga_type: str
    synopsis: str = ""
    cover_url: str = ""
    genres: List[str] = field(default_factory=list)
    authors: List[str] = field(default_factory=list)
    status: str = "Unknown"
    scanlators: List[Scanlator] = field(default_factory=list)
    chapters: List[Chapter] = field(default_factory=list)


    @classmethod
    def from_dict(cls, data: dict) -> "MangaInfo":
        """Create MangaInfo from API response dict."""
        # Handle cases where data is nested under 'mangaPage'
        manga = data.get("mangaPage") or data
        
        chapters: List[Chapter] = []
        seen_chapter_ids = set()
        seen_chapter_keys = set()

        def normalize_number(value: float) -> str:
            if value == int(value):
                return str(int(value))
            return f"{value:.6f}".rstrip("0").rstrip(".")

        # Process chapters if present
        for ch in manga.get("chapters", []):
            chapter_id = ch.get("id")
            if not chapter_id or chapter_id in seen_chapter_ids:
                continue

            chapter = Chapter.from_dict(ch)
            chapter_key = (
                normalize_number(chapter.number),
                chapter.title.strip().lower(),
            )

            if chapter_key in seen_chapter_keys:
                continue

            seen_chapter_ids.add(chapter_id)
            seen_chapter_keys.add(chapter_key)
            chapters.append(chapter)

        # Parse cover URL if possible
        poster = manga.get("poster") or manga.get("image")
        cover_url = ""
        if isinstance(poster, dict):
            poster = poster.get("image")
        if isinstance(poster, str):
            poster = poster.lstrip("/")
            if poster.startswith("static/"):
                poster = poster[len("static/") :]
            cover_url = f"https://atsu.moe/static/{poster}"

        return cls(
            id=manga["id"],
            title=manga.get("title") or manga.get("englishTitle") or "Unknown",
            manga_type=manga.get("type", "Unknown"),
            synopsis=manga.get("synopsis", ""),
            cover_url=cover_url,
            genres=[g.get("name") for g in manga.get("genres") or [] if g.get("name")] or \
                   [t.get("name") for t in manga.get("tags") or [] if t.get("name")] or [],
            authors=[a.get("name") for a in manga.get("authors") or [] if a.get("name")] or [],
            scanlators=[Scanlator.from_dict(s) for s in manga.get("scanlators") or []],
            status=manga.get("status", "Unknown"),
            chapters=chapters
        )



@dataclass
class DownloadResult:
    """Result of a download operation."""
    success: bool
    chapter: Chapter
    output_path: str
    error: Optional[str] = None
    images_downloaded: int = 0
