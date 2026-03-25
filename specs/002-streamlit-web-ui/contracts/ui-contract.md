# UI Contract: Streamlit Web UI

**Branch**: `002-streamlit-web-ui` | **Date**: 2026-03-25

---

## Screen States

### State 1: Password Gate
Shown when `st.session_state.authenticated == False`.

| Element | Type | Behaviour |
|---------|------|-----------|
| Title | `st.title` | "Research Collector" |
| Password input | `st.text_input(type="password")` | `on_change` triggers auth check |
| Error message | `st.error` | Shown only after a failed attempt |

`st.stop()` prevents all State 2 content from rendering.

---

### State 2: Main UI
Shown when `st.session_state.authenticated == True`.

#### Inputs

| Element | Widget | Key | Default | Constraint |
|---------|--------|-----|---------|------------|
| Keyword | `st.text_input` | `keyword` | `""` | Required |
| Content type | `st.selectbox` | `content_type` | `"All"` | Options: All / Stats / Survey / Ebook |
| Output formats | `st.multiselect` | `output_formats` | `["Excel"]` | Min 1 selection |
| Run button | `st.button` | — | — | Disabled if keyword empty or formats empty |

#### Progress (visible during run only)

| Element | Widget | Behaviour |
|---------|--------|-----------|
| Progress bar | `st.progress` | 0→100% as domains are queried |
| Status line | `st.empty` | Shows current domain being queried |

#### Results (visible after successful run)

| Element | Widget | Condition |
|---------|--------|-----------|
| Record count | `st.success` | Always shown on completion |
| Warning | `st.warning` | Shown if `records_collected == 0` |
| Excel download | `st.download_button` | Shown if Excel was requested |
| CSV download | `st.download_button` | Shown if CSV was requested |
| Error message | `st.error` | Shown if `run_result.error is not None` |

---

## Download Button Specs

| Format | `file_name` | `mime` |
|--------|-------------|--------|
| Excel | `{output_stem}.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| CSV | `{output_stem}.csv` | `text/csv` |

---

## Secrets Contract

| Key | Source (local) | Source (cloud) |
|-----|----------------|----------------|
| `APP_PASSWORD` | `.streamlit/secrets.toml` | Community Cloud dashboard |
| `SERPAPI_KEY` | `.streamlit/secrets.toml` | Community Cloud dashboard |
