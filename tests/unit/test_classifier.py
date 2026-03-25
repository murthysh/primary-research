from src.classifier import classify
from src.models import ContentType


def test_classify_stats_percent():
    assert classify("AI adoption reaches 45% of enterprises", None) == ContentType.STATS


def test_classify_stats_billion():
    result = classify("Market worth $2.5 billion by 2026", "Global AI market size")
    assert result == ContentType.STATS


def test_classify_stats_growth_rate():
    assert classify("AI growth rate accelerating", "CAGR of 38% forecast") == ContentType.STATS


def test_classify_ebook_whitepaper_title():
    assert classify("The AI in Healthcare Whitepaper", None) == ContentType.EBOOK


def test_classify_ebook_guide():
    assert classify("Complete Guide to Digital Transformation", None) == ContentType.EBOOK


def test_classify_ebook_in_snippet():
    assert classify("McKinsey 2024", "Download the full ebook on AI strategy") == ContentType.EBOOK


def test_classify_survey_report():
    result = classify("Annual Report on AI Adoption 2024", "Findings from the global survey")
    assert result == ContentType.SURVEY


def test_classify_survey_study():
    assert classify("New Study on Enterprise AI", "Analysis of 500 companies") == ContentType.SURVEY


def test_classify_default_no_signals():
    """When no signals match, default to SURVEY."""
    assert classify("Something completely unclassifiable xyz", None) == ContentType.SURVEY


def test_classify_stats_priority_over_survey():
    """STATS should win over SURVEY when both signals present (priority order)."""
    result = classify("Survey finds 60% of companies use AI", "According to the annual survey")
    assert result == ContentType.STATS


def test_classify_snippet_provides_signal():
    result = classify("McKinsey Report 2024", "The market grew by 35 percent year-over-year")
    assert result == ContentType.STATS


def test_classify_case_insensitive():
    assert classify("WHITEPAPER: AI Trends", None) == ContentType.EBOOK
