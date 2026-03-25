# Data Model: Streamlit Web UI

**Branch**: `002-streamlit-web-ui` | **Date**: 2026-03-25

All state is in-memory within a single browser session. No database or disk persistence.

---

## Session State Keys

| Key | Type | Initial Value | Description |
|-----|------|---------------|-------------|
| `authenticated` | `bool` | `False` | Whether the user has passed the password gate |
| `auth_error` | `bool` | `False` | Whether the last password attempt failed |
| `run_result` | `RunResult \| None` | `None` | Output of the last pipeline run |

---

## RunResult (dataclass)

Holds the complete output of one pipeline execution. Stored in `st.session_state.run_result`.

```python
@dataclass
class RunResult:
    records_collected: int
    excel_bytes: bytes | None        # None if Excel not requested
    csv_bytes: bytes | None          # None if CSV not requested
    output_stem: str                 # e.g. "ai-in-healthcare-research-2026-03-25"
    error: str | None                # Human-readable error, or None on success
    warning: str | None              # e.g. "No results matched filters", or None
```

---

## Form Inputs (not persisted — read per-run)

| Widget | Type | Default | Validation |
|--------|------|---------|------------|
| Keyword | `str` | `""` | Required; Run button disabled if empty |
| Content type | `str` | `"All"` | One of: All, Stats, Survey, Ebook |
| Output formats | `list[str]` | `["Excel"]` | At least one of: Excel, CSV |
