"""Integration tests for the SerpAPI searcher module.

These tests make real SerpAPI calls and are skipped automatically when
SERPAPI_KEY is not set in the environment.

Run with:
    pytest tests/integration/ -v
"""

import os

import pytest

from src.models import SearchResult
from src.searcher import build_queries, fetch_results

pytestmark = pytest.mark.skipif(
    not os.getenv("SERPAPI_KEY"),
    reason="SERPAPI_KEY not set — skipping live integration tests",
)


def test_build_queries_count():
    queries = build_queries("AI")
    # One query per domain in AUTHORITY_DOMAINS (at least 10)
    assert len(queries) >= 10


def test_build_queries_contain_keyword():
    queries = build_queries("digital transformation")
    for q in queries:
        assert '"digital transformation"' in q


def test_build_queries_contain_date_filter():
    queries = build_queries("AI")
    for q in queries:
        assert "after:2023-01-01" in q


def test_build_queries_pdf_domains():
    queries = build_queries("AI")
    pdf_queries = [q for q in queries if "filetype:pdf" in q]
    # At least the 3 PDF domains should have filetype:pdf
    assert len(pdf_queries) >= 3


def test_fetch_results_returns_list():
    api_key = os.environ["SERPAPI_KEY"]
    # Use a broad query likely to return at least some results
    query = 'site:mckinsey.com "AI" after:2023-01-01'
    results = fetch_results(query, api_key)
    assert isinstance(results, list)


def test_fetch_results_items_are_search_results():
    api_key = os.environ["SERPAPI_KEY"]
    query = 'site:gartner.com "AI" after:2023-01-01'
    results = fetch_results(query, api_key)
    for r in results:
        assert isinstance(r, SearchResult)
        assert r.link.startswith("http")
        assert isinstance(r.title, str)
