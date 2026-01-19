from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    thumbnail: Optional[str] = None


@dataclass(frozen=True)
class Episode:
    title: str
    url: str


@dataclass(frozen=True)
class VideoLink:
    url: str
    quality: Optional[str] = None


@dataclass(frozen=True)
class QualityOption:
    label: str
    url: str
