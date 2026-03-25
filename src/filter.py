from __future__ import annotations

import logging
from datetime import date
from urllib.parse import urlparse

from dateutil import parser as dateutil_parser
from dateutil.parser import ParserError

from .config import AUTHORITY_DOMAINS, DATE_CUTOFF
from .models import ContentType, ResearchRecord

logger = logging.getLogger(__name__)


def is_authority_domain(url: str) -> tuple[bool, str]:
    """Check if URL belongs to an authority domain.

    Returns (is_authority, display_name). Pure function — no network calls.
    """
    if not url:
        return False, ""

    try:
        hostname = urlparse(url).hostname or ""
    except Exception:
        return False, ""

    hostname = hostname.lower().removeprefix("www.")

    for domain, display_name in AUTHORITY_DOMAINS.items():
        if hostname == domain or hostname.endswith("." + domain):
            return True, display_name

    return False, ""


def parse_and_validate_date(date_raw: str | None) -> date | None:
    """Parse a raw date string and validate it is >= DATE_CUTOFF.

    Returns a datetime.date if valid, None otherwise.
    Unparseable or absent dates are excluded with a WARNING log.
    """
    if not date_raw:
        logger.warning("Record has no date — excluding")
        return None

    try:
        parsed = dateutil_parser.parse(date_raw, fuzzy=True)
        parsed_date = parsed.date()
    except (ParserError, ValueError, OverflowError, TypeError):
        logger.warning("Could not parse date '%s' — excluding", date_raw)
        return None

    if parsed_date < DATE_CUTOFF:
        logger.debug("Date %s is before cutoff %s — excluding", parsed_date, DATE_CUTOFF)
        return None

    return parsed_date


def is_keyword_relevant(keyword: str, title: str, snippet: str | None) -> bool:
    """Return True if keyword appears in title or snippet (case-insensitive).

    Pure function — no network calls. Testable in isolation.
    """
    keyword_lower = keyword.lower()
    if keyword_lower in title.lower():
        return True
    if snippet and keyword_lower in snippet.lower():
        return True
    return False


def filter_by_type(
    records: list[ResearchRecord],
    content_type_filter: ContentType | None,
) -> list[ResearchRecord]:
    """Filter records to a single content type.

    Returns all records unchanged when content_type_filter is None.
    """
    if content_type_filter is None:
        return records
    return [r for r in records if r.content_type == content_type_filter]
