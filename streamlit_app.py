from __future__ import annotations

import logging

import streamlit as st

from src.classifier import classify
from src.filter import (
    filter_by_type,
    is_authority_domain,
    is_keyword_relevant,
    parse_and_validate_date,
)
from src.config import AUTHORITY_DOMAINS
from src.models import CollectionError, ContentType, ResearchRecord, RunResult
from src.searcher import build_queries, fetch_results
from src.writer import build_dataframe, default_output_stem, to_csv_bytes, to_excel_bytes

logging.basicConfig(level=logging.WARNING)

# ---------------------------------------------------------------------------
# Password gate (US1)
# ---------------------------------------------------------------------------

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "auth_error" not in st.session_state:
    st.session_state.auth_error = False


def _check_password() -> None:
    expected = st.secrets.get("APP_PASSWORD", "")
    if st.session_state.password_input == expected:
        st.session_state.authenticated = True
        st.session_state.auth_error = False
    else:
        st.session_state.auth_error = True


if not st.session_state.authenticated:
    st.title("Research Collector")
    st.text_input("Password", type="password", key="password_input", on_change=_check_password)
    if st.session_state.auth_error:
        st.error("Incorrect password. Please try again.")
    st.stop()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONTENT_TYPE_MAP: dict[str, ContentType] = {
    "Stats": ContentType.STATS,
    "Survey": ContentType.SURVEY,
    "Ebook": ContentType.EBOOK,
}


def _truncate(text: str, max_len: int = 300) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "\u2026"


def _run_pipeline(
    keyword: str,
    content_type_label: str,
    output_formats: list[str],
    selected_sources: list[str],
) -> RunResult:
    """Run the full collection pipeline and return an in-memory RunResult."""
    api_key: str = st.secrets.get("SERPAPI_KEY", "")
    if not api_key:
        return RunResult(
            records_collected=0,
            excel_bytes=None,
            csv_bytes=None,
            output_stem=default_output_stem(keyword),
            error=(
                "SERPAPI_KEY is not configured. "
                "Add it to .streamlit/secrets.toml (local) or the Community Cloud dashboard."
            ),
            warning=None,
        )

    content_type_filter: ContentType | None = _CONTENT_TYPE_MAP.get(content_type_label)
    # Map display names back to domain keys
    name_to_domain = {v: k for k, v in AUTHORITY_DOMAINS.items()}
    domains = [name_to_domain[name] for name in selected_sources if name in name_to_domain]
    queries = build_queries(keyword, domains=domains if domains else None)
    total = len(queries)
    records = []

    progress = st.progress(0, text="Starting collection...")
    status = st.empty()

    try:
        for idx, query in enumerate(queries):
            domain = query.split("site:")[-1].split(" ")[0] if "site:" in query else query
            status.write(f"Querying {domain}...")

            raw_results = fetch_results(query, api_key)
            for result in raw_results:
                ok_domain, display_name = is_authority_domain(result.link)
                if not ok_domain:
                    continue
                parsed_date = parse_and_validate_date(result.date_raw)
                if parsed_date is None:
                    continue
                if not is_keyword_relevant(keyword, result.title, result.snippet):
                    continue
                records.append(
                    ResearchRecord(
                        title=result.title.strip(),
                        source=display_name,
                        url=result.link,
                        date=parsed_date,
                        content_type=classify(result.title, result.snippet),
                        keyword_match=True,
                        summary=_truncate(result.snippet or result.title),
                    )
                )

            pct = int((idx + 1) / total * 100)
            progress.progress(pct, text=f"Queried {idx + 1}/{total} domains")

    except CollectionError as exc:
        progress.empty()
        status.empty()
        return RunResult(
            records_collected=0,
            excel_bytes=None,
            csv_bytes=None,
            output_stem=default_output_stem(keyword),
            error=str(exc),
            warning=None,
        )
    except Exception as exc:
        progress.empty()
        status.empty()
        return RunResult(
            records_collected=0,
            excel_bytes=None,
            csv_bytes=None,
            output_stem=default_output_stem(keyword),
            error=f"Unexpected error: {exc}",
            warning=None,
        )

    progress.empty()
    status.empty()

    filtered_records = filter_by_type(records, content_type_filter)
    df = build_dataframe(filtered_records)
    stem = default_output_stem(keyword)
    st.session_state.run_df = df

    return RunResult(
        records_collected=len(filtered_records),
        excel_bytes=to_excel_bytes(df) if "Excel" in output_formats else None,
        csv_bytes=to_csv_bytes(df) if "CSV" in output_formats else None,
        output_stem=stem,
        error=None,
        warning="No results matched the filters." if len(filtered_records) == 0 else None,
    )


# ---------------------------------------------------------------------------
# Main UI (US2 + US3)
# ---------------------------------------------------------------------------

st.title("Research Collector")
st.caption("Collect high-authority research by keyword from Gartner, McKinsey, and more.")

_ALL_SOURCES = list(AUTHORITY_DOMAINS.values())

if "select_all" not in st.session_state:
    st.session_state.select_all = False

with st.form("research_form"):
    keyword = st.text_input("Keyword", placeholder="e.g. AI in healthcare")
    content_type_label = st.selectbox(
        "Content type", ["All", "Stats", "Survey", "Ebook"], index=0
    )
    selected_sources = st.multiselect(
        "Sources to query",
        options=_ALL_SOURCES,
        default=_ALL_SOURCES if st.session_state.select_all else [],
        help="Select which authority sources to search, or tick 'Select all' below.",
    )
    select_all = st.checkbox("Select all sources", value=st.session_state.select_all)
    output_formats = st.multiselect(
        "Output formats", ["Excel", "CSV"], default=["Excel"]
    )
    submitted = st.form_submit_button("Run")

if submitted and not keyword.strip():
    st.error("Please enter a keyword.")
elif submitted and not selected_sources:
    st.error("Please select at least one source.")
elif submitted and not output_formats:
    st.error("Please select at least one output format.")
elif submitted:
    with st.spinner("Running collection..."):
        result = _run_pipeline(keyword.strip(), content_type_label, output_formats, selected_sources)
    st.session_state.run_result = result

result: RunResult | None = st.session_state.get("run_result")

if result is not None:
    if result.error:
        st.error(result.error)
    else:
        if result.warning:
            st.warning(result.warning)
        else:
            st.success(f"Collected {result.records_collected} records.")

        # Results table
        df = st.session_state.get("run_df")
        if df is not None and not df.empty:
            st.subheader("Results")
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn("URL"),
                    "Keyword Match": st.column_config.CheckboxColumn("Keyword Match"),
                },
            )

        # Download buttons
        col1, col2 = st.columns(2)
        if result.excel_bytes:
            col1.download_button(
                label="Download Excel",
                data=result.excel_bytes,
                file_name=f"{result.output_stem}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        if result.csv_bytes:
            col2.download_button(
                label="Download CSV",
                data=result.csv_bytes,
                file_name=f"{result.output_stem}.csv",
                mime="text/csv",
            )
