from datetime import date
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.models import ContentType, ResearchRecord
from src.writer import COLUMNS, build_dataframe, default_output_stem, write_csv, write_excel


def _record() -> ResearchRecord:
    return ResearchRecord(
        title="AI Trends 2024",
        source="Gartner",
        url="https://www.gartner.com/ai-trends",
        date=date(2024, 3, 15),
        content_type=ContentType.SURVEY,
        keyword_match=True,
        summary="AI adoption is accelerating across industries.",
    )


# ---------------------------------------------------------------------------
# build_dataframe
# ---------------------------------------------------------------------------

def test_columns_exact():
    df = build_dataframe([_record()])
    assert list(df.columns) == COLUMNS


def test_column_count():
    assert len(COLUMNS) == 7


def test_keyword_match_dtype():
    df = build_dataframe([_record()])
    assert df["Keyword Match"].dtype == bool


def test_date_iso_string():
    df = build_dataframe([_record()])
    assert df["Date"].iloc[0] == "2024-03-15"


def test_content_type_string_value():
    df = build_dataframe([_record()])
    assert df["Content Type"].iloc[0] == "Survey / Research Report"


def test_empty_records_has_correct_columns():
    df = build_dataframe([])
    assert list(df.columns) == COLUMNS
    assert len(df) == 0


def test_empty_keyword_match_bool():
    df = build_dataframe([])
    assert df["Keyword Match"].dtype == bool


# ---------------------------------------------------------------------------
# write_excel
# ---------------------------------------------------------------------------

def test_write_excel_creates_file(tmp_path: Path):
    df = build_dataframe([_record()])
    out = tmp_path / "test.xlsx"
    write_excel(df, out)
    assert out.exists()


def test_write_excel_no_tmp_remaining(tmp_path: Path):
    df = build_dataframe([_record()])
    out = tmp_path / "output.xlsx"
    write_excel(df, out)
    assert not (tmp_path / "output.xlsx.tmp").exists()


def test_write_excel_readable(tmp_path: Path):
    df = build_dataframe([_record()])
    out = tmp_path / "test.xlsx"
    write_excel(df, out)
    read_back = pd.read_excel(str(out), engine="openpyxl")
    assert list(read_back.columns) == COLUMNS


# ---------------------------------------------------------------------------
# write_csv
# ---------------------------------------------------------------------------

def test_write_csv_creates_file(tmp_path: Path):
    df = build_dataframe([_record()])
    out = tmp_path / "test.csv"
    write_csv(df, out)
    assert out.exists()


def test_write_csv_utf8_bom(tmp_path: Path):
    df = build_dataframe([_record()])
    out = tmp_path / "test.csv"
    write_csv(df, out)
    raw = out.read_bytes()
    assert raw[:3] == b"\xef\xbb\xbf", "CSV must start with UTF-8 BOM"


def test_write_csv_column_order(tmp_path: Path):
    df = build_dataframe([_record()])
    out = tmp_path / "test.csv"
    write_csv(df, out)
    read_back = pd.read_csv(str(out), encoding="utf-8-sig")
    assert list(read_back.columns) == COLUMNS


def test_write_csv_no_tmp_remaining(tmp_path: Path):
    df = build_dataframe([_record()])
    out = tmp_path / "output.csv"
    write_csv(df, out)
    assert not (tmp_path / "output.tmp").exists()


# ---------------------------------------------------------------------------
# default_output_stem
# ---------------------------------------------------------------------------

def test_output_stem_format():
    with patch("src.writer.date") as mock_date:
        mock_date.today.return_value = date(2026, 3, 24)
        stem = default_output_stem("AI in healthcare")
    assert stem == "ai-in-healthcare-research-2026-03-24"


def test_output_stem_special_chars():
    with patch("src.writer.date") as mock_date:
        mock_date.today.return_value = date(2026, 3, 24)
        stem = default_output_stem("AI & ML (2024)")
    assert "research-2026-03-24" in stem
    assert " " not in stem
    assert "&" not in stem
