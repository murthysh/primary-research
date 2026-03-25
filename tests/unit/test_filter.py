from datetime import date

from src.filter import (
    filter_by_type,
    is_authority_domain,
    is_keyword_relevant,
    parse_and_validate_date,
)
from src.models import ContentType, ResearchRecord

# ---------------------------------------------------------------------------
# is_authority_domain
# ---------------------------------------------------------------------------

def test_is_authority_domain_known():
    ok, name = is_authority_domain("https://www.mckinsey.com/industries/ai")
    assert ok is True
    assert name == "McKinsey & Company"


def test_is_authority_domain_unknown():
    ok, name = is_authority_domain("https://www.example.com/article")
    assert ok is False
    assert name == ""


def test_is_authority_domain_subdomain():
    ok, name = is_authority_domain("https://insights.gartner.com/report/123")
    assert ok is True
    assert name == "Gartner"


def test_is_authority_domain_hbr():
    ok, name = is_authority_domain("https://hbr.org/2024/01/ai-strategy")
    assert ok is True
    assert name == "Harvard Business Review"


def test_is_authority_domain_empty_url():
    ok, name = is_authority_domain("")
    assert ok is False


# ---------------------------------------------------------------------------
# parse_and_validate_date
# ---------------------------------------------------------------------------

def test_parse_date_valid_2024():
    result = parse_and_validate_date("January 15, 2024")
    assert result == date(2024, 1, 15)


def test_parse_date_iso_format():
    result = parse_and_validate_date("2023-06-30")
    assert result == date(2023, 6, 30)


def test_parse_date_before_cutoff():
    result = parse_and_validate_date("December 31, 2022")
    assert result is None


def test_parse_date_on_cutoff():
    result = parse_and_validate_date("2023-01-01")
    assert result == date(2023, 1, 1)


def test_parse_date_none_input():
    result = parse_and_validate_date(None)
    assert result is None


def test_parse_date_empty_string():
    result = parse_and_validate_date("")
    assert result is None


def test_parse_date_unparseable():
    result = parse_and_validate_date("not-a-date-at-all")
    assert result is None


# ---------------------------------------------------------------------------
# is_keyword_relevant
# ---------------------------------------------------------------------------

def test_keyword_in_title():
    assert is_keyword_relevant("AI in healthcare", "AI in Healthcare Trends 2024", None) is True


def test_keyword_in_snippet():
    assert is_keyword_relevant(
        "AI in healthcare", "Report on Technology", "AI in healthcare is growing"
    ) is True


def test_keyword_case_insensitive():
    assert is_keyword_relevant("AI IN HEALTHCARE", "ai in healthcare report", None) is True


def test_keyword_absent():
    assert is_keyword_relevant(
        "AI in healthcare", "Cloud Computing Report", "Digital transformation trends"
    ) is False


def test_keyword_none_snippet():
    assert is_keyword_relevant("AI", "AI Strategy Guide", None) is True


# ---------------------------------------------------------------------------
# filter_by_type
# ---------------------------------------------------------------------------

def _record(ct: ContentType) -> ResearchRecord:
    return ResearchRecord(
        title="Test",
        source="Gartner",
        url="https://gartner.com/test",
        date=date(2024, 1, 1),
        content_type=ct,
        keyword_match=True,
        summary="summary",
    )


def test_filter_by_type_none_returns_all():
    records = [_record(ContentType.STATS), _record(ContentType.EBOOK)]
    assert len(filter_by_type(records, None)) == 2


def test_filter_by_type_stats():
    records = [_record(ContentType.STATS), _record(ContentType.EBOOK)]
    result = filter_by_type(records, ContentType.STATS)
    assert len(result) == 1
    assert result[0].content_type == ContentType.STATS


def test_filter_by_type_empty_result():
    records = [_record(ContentType.SURVEY)]
    assert filter_by_type(records, ContentType.EBOOK) == []


def test_filter_by_type_empty_list():
    assert filter_by_type([], ContentType.STATS) == []
