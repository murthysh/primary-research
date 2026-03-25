from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path


class ContentType(str, Enum):
    STATS = "Stats / Data Points"
    SURVEY = "Survey / Research Report"
    EBOOK = "Ebook / Whitepaper"


@dataclass(frozen=True)
class SearchResult:
    """Raw record returned by a single SerpAPI organic result item."""

    title: str
    link: str
    snippet: str | None
    date_raw: str | None
    source_domain: str


@dataclass(frozen=True)
class ResearchRecord:
    """Enriched, validated record ready for output."""

    title: str
    source: str
    url: str
    date: date
    content_type: ContentType
    keyword_match: bool
    summary: str


class CollectionError(Exception):
    """Raised when an unrecoverable error occurs during collection."""


@dataclass
class RunResult:
    """Output of a single Streamlit UI pipeline execution."""

    records_collected: int
    excel_bytes: bytes | None
    csv_bytes: bytes | None
    output_stem: str
    error: str | None
    warning: str | None


@dataclass
class CollectionRun:
    """Metadata about a single CLI execution."""

    keyword: str
    content_type_filter: ContentType | None
    output_format: set[str]
    output_paths: list[Path]
    records_collected: int
    records_excluded: list[tuple[str, str]]
    started_at: datetime
    completed_at: datetime | None = None
