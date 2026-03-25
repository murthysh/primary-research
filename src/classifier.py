from __future__ import annotations

from .config import CONTENT_TYPE_SIGNALS
from .models import ContentType


def classify(title: str, snippet: str | None) -> ContentType:
    """Classify a search result by content type using heuristic signal matching.

    Checks title and snippet against CONTENT_TYPE_SIGNALS in priority order:
        STATS > SURVEY > EBOOK

    Returns ContentType.SURVEY as the default when no signals are matched.
    Pure function — no network calls. Testable in isolation.
    """
    text = (title + " " + (snippet or "")).lower()

    for content_type in (ContentType.STATS, ContentType.SURVEY, ContentType.EBOOK):
        signals = CONTENT_TYPE_SIGNALS.get(content_type, [])
        for signal in signals:
            if signal.lower() in text:
                return content_type

    return ContentType.SURVEY
