from __future__ import annotations

import logging
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import AUTHORITY_DOMAINS, PDF_DOMAINS
from .models import CollectionError, SearchResult

logger = logging.getLogger(__name__)


def _build_session() -> requests.Session:
    """Create a requests Session with retry logic for 429 and 5xx responses."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def build_queries(keyword: str) -> list[str]:
    """Build one site-restricted Google query per authority domain.

    Appends filetype:pdf for domains in PDF_DOMAINS.
    All queries include after:2023-01-01 for server-side date pre-filtering.
    """
    queries: list[str] = []
    for domain in AUTHORITY_DOMAINS:
        query = f'site:{domain} "{keyword}" after:2023-01-01'
        if domain in PDF_DOMAINS:
            query += " filetype:pdf"
        queries.append(query)
    return queries


def fetch_results(query: str, api_key: str) -> list[SearchResult]:
    """Fetch organic search results from SerpAPI for a single query.

    Uses exponential back-off retry via requests HTTPAdapter.
    Raises CollectionError on unrecoverable failure.
    """
    try:
        from serpapi import GoogleSearch  # type: ignore[import]
    except ImportError:
        try:
            from serpapi.google_search import GoogleSearch  # type: ignore[import]
        except ImportError:
            raise CollectionError(
                "serpapi package not installed. Run: pip install google-search-results"
            )

    logger.info("Querying SerpAPI: %s", query)

    try:
        params = {
            "q": query,
            "api_key": api_key,
            "num": 10,
            "engine": "google",
        }
        search = GoogleSearch(params)
        results_dict = search.get_dict()

        organic = results_dict.get("organic_results", [])
        logger.info("  → %d raw results", len(organic))

        search_results: list[SearchResult] = []
        for item in organic:
            link = item.get("link", "")
            if not link:
                continue

            hostname = urlparse(link).hostname or ""
            hostname = hostname.lower().removeprefix("www.")

            search_results.append(
                SearchResult(
                    title=item.get("title", ""),
                    link=link,
                    snippet=item.get("snippet"),
                    date_raw=item.get("date"),
                    source_domain=hostname,
                )
            )

        return search_results

    except CollectionError:
        raise
    except Exception as exc:
        logger.error("SerpAPI query failed for query '%s': %s", query, exc)
        raise CollectionError(f"SerpAPI query failed: {exc}") from exc
