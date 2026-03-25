from __future__ import annotations

import io
import logging
import os
import re
from datetime import date
from pathlib import Path

import pandas as pd

from .models import ResearchRecord

logger = logging.getLogger(__name__)

# Canonical column order — matches spec FR-007
COLUMNS = [
    "Title",
    "Source",
    "URL",
    "Date",
    "Content Type",
    "Keyword Match",
    "Summary",
]


def _make_slug(keyword: str) -> str:
    """Convert keyword to a filesystem-safe lowercase slug."""
    slug = keyword.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def default_output_stem(keyword: str) -> str:
    """Generate the default output file stem (without extension).

    Format: {keyword-slug}-research-{YYYY-MM-DD}
    Example: ai-in-healthcare-research-2026-03-24
    """
    slug = _make_slug(keyword)
    today = date.today().strftime("%Y-%m-%d")
    return f"{slug}-research-{today}"


def build_dataframe(records: list[ResearchRecord]) -> pd.DataFrame:
    """Build a typed DataFrame with the canonical column order.

    Date is stored as ISO 8601 string for cross-platform Excel compatibility.
    Keyword Match column is always bool dtype.
    """
    if not records:
        df = pd.DataFrame(columns=COLUMNS)
        df["Keyword Match"] = df["Keyword Match"].astype(bool)
        return df

    rows = [
        {
            "Title": r.title,
            "Source": r.source,
            "URL": r.url,
            "Date": r.date.strftime("%Y-%m-%d"),
            "Content Type": r.content_type.value,
            "Keyword Match": r.keyword_match,
            "Summary": r.summary,
        }
        for r in records
    ]

    df = pd.DataFrame(rows, columns=COLUMNS)
    df["Keyword Match"] = df["Keyword Match"].astype(bool)
    return df


def write_excel(df: pd.DataFrame, path: Path) -> None:
    """Write DataFrame to .xlsx using openpyxl with atomic write.

    Writes to <path>.tmp then renames to <path> to prevent partial files.
    """
    path = Path(path)
    tmp_path = path.with_name(path.name + ".tmp")
    try:
        buf = io.BytesIO()
        df.to_excel(buf, engine="openpyxl", index=False)
        tmp_path.write_bytes(buf.getvalue())
        os.replace(str(tmp_path), str(path))
        logger.info("Excel written: %s", path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialise DataFrame to Excel bytes in memory (no disk write)."""
    buf = io.BytesIO()
    df.to_excel(buf, engine="openpyxl", index=False)
    return buf.getvalue()


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Serialise DataFrame to UTF-8-BOM CSV bytes in memory (no disk write)."""
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write DataFrame to .csv with UTF-8-BOM encoding and atomic write.

    UTF-8-BOM (utf-8-sig) ensures the file opens correctly in Microsoft Excel
    on all platforms without manual encoding selection.
    """
    path = Path(path)
    tmp_path = path.with_suffix(".tmp")
    try:
        df.to_csv(str(tmp_path), index=False, encoding="utf-8-sig")
        os.replace(str(tmp_path), str(path))
        logger.info("CSV written: %s", path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
