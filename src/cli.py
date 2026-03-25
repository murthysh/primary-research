from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv

from .classifier import classify
from .filter import (
    filter_by_type,
    is_authority_domain,
    is_keyword_relevant,
    parse_and_validate_date,
)
from .models import CollectionError, CollectionRun, ContentType, ResearchRecord, SearchResult
from .searcher import build_queries, fetch_results
from .writer import build_dataframe, default_output_stem, write_csv, write_excel


def _setup_logging(verbose: bool) -> None:
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        stream=sys.stderr,
        level=level,
        format="%(levelname)s: %(message)s",
    )


def _content_type_from_str(value: str | None) -> ContentType | None:
    mapping: dict[str, ContentType] = {
        "stats": ContentType.STATS,
        "survey": ContentType.SURVEY,
        "ebook": ContentType.EBOOK,
    }
    if value is None:
        return None
    return mapping.get(value.lower())


def _truncate(text: str, max_len: int = 300) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "\u2026"


def _write_output(
    records: list[ResearchRecord],
    formats: set[str],
    keyword: str,
    output_base: str | None,
    run: CollectionRun,
) -> None:
    df = build_dataframe(records)
    run.records_collected = len(records)
    stem = output_base if output_base else default_output_stem(keyword)

    if "excel" in formats:
        path = Path(f"{stem}.xlsx")
        write_excel(df, path)
        run.output_paths.append(path)

    if "csv" in formats:
        path = Path(f"{stem}.csv")
        write_csv(df, path)
        run.output_paths.append(path)


@click.command()
@click.option("--keyword", required=True, help="Seed keyword to search for.")
@click.option(
    "--type",
    "content_type_str",
    type=click.Choice(["stats", "survey", "ebook"], case_sensitive=False),
    default=None,
    help="Filter results to a specific content type.",
)
@click.option(
    "--format",
    "output_formats",
    multiple=True,
    type=click.Choice(["excel", "csv"], case_sensitive=False),
    default=["excel"],
    show_default=True,
    help="Output format(s). May be specified multiple times for both.",
)
@click.option(
    "--output",
    "output_base",
    default=None,
    help=(
        "Output file base path without extension. "
        "Defaults to <keyword>-research-<YYYY-MM-DD> in the current directory."
    ),
)
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable verbose logging.")
def main(
    keyword: str,
    content_type_str: str | None,
    output_formats: tuple[str, ...],
    output_base: str | None,
    verbose: bool,
) -> None:
    """Collect research from high-authority sources for a given keyword.

    Example:
        python tool.py --keyword "AI in healthcare"
        python tool.py --keyword "digital transformation" --type ebook --format csv
    """
    load_dotenv()
    _setup_logging(verbose)

    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        click.echo(
            "Error: SERPAPI_KEY environment variable is not set. "
            "Add it to a .env file or export it in your shell.",
            err=True,
        )
        sys.exit(1)

    # Validate output base path directory if custom path provided
    if output_base:
        parent = Path(output_base).parent
        if not parent.exists():
            click.echo(
                f"Error: Output directory '{parent}' does not exist. Create it first.",
                err=True,
            )
            sys.exit(1)

    formats: set[str] = set(output_formats) if output_formats else {"excel"}
    content_type_filter = _content_type_from_str(content_type_str)

    run = CollectionRun(
        keyword=keyword,
        content_type_filter=content_type_filter,
        output_format=formats,
        output_paths=[],
        records_collected=0,
        records_excluded=[],
        started_at=datetime.utcnow(),
    )

    records: list[ResearchRecord] = []
    queries = build_queries(keyword)

    try:
        for query in queries:
            raw_results: list[SearchResult] = fetch_results(query, api_key)

            for result in raw_results:
                # Gate 1: Domain allowlist
                ok_domain, display_name = is_authority_domain(result.link)
                if not ok_domain:
                    run.records_excluded.append((result.link, "domain not in allowlist"))
                    continue

                # Gate 2: Date parse + validate (>= 2023-01-01)
                parsed_date = parse_and_validate_date(result.date_raw)
                if parsed_date is None:
                    reason = (
                        "date missing" if not result.date_raw else "date unparseable or pre-2023"
                    )
                    run.records_excluded.append((result.link, reason))
                    continue

                # Gate 3: Keyword relevance
                if not is_keyword_relevant(keyword, result.title, result.snippet):
                    run.records_excluded.append(
                        (result.link, "keyword not in title or snippet")
                    )
                    continue

                content_type = classify(result.title, result.snippet)
                summary = _truncate(result.snippet or result.title)

                records.append(
                    ResearchRecord(
                        title=result.title.strip(),
                        source=display_name,
                        url=result.link,
                        date=parsed_date,
                        content_type=content_type,
                        keyword_match=True,
                        summary=summary,
                    )
                )

    except CollectionError as exc:
        click.echo(f"Error: {exc}", err=True)
        # Write whatever was collected before the error (prevent data loss)
        if records:
            filtered = filter_by_type(records, content_type_filter)
            _write_output(filtered, formats, keyword, output_base, run)
            for path in run.output_paths:
                click.echo(
                    f"Partial results written ({run.records_collected} records) → {path}"
                )
        sys.exit(1)

    # Apply content type filter (--type flag) — drops silently, not counted as excluded
    records = filter_by_type(records, content_type_filter)

    _write_output(records, formats, keyword, output_base, run)
    run.completed_at = datetime.utcnow()

    if run.records_collected == 0:
        click.echo(
            "Warning: No results matched the filters. Output file contains headers only.",
            err=True,
        )

    for path in run.output_paths:
        click.echo(f"Collected {run.records_collected} records -> {path}")
