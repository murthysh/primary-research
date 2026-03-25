# Research: Streamlit Web UI

**Branch**: `002-streamlit-web-ui` | **Date**: 2026-03-25

---

## 1. Password Gate

**Decision**: `st.session_state` + `st.secrets` with `on_change` callback and `st.stop()`

**Pattern**:
```python
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def _check_password():
    if st.session_state.password_input == st.secrets.get("APP_PASSWORD", ""):
        st.session_state.authenticated = True
    else:
        st.session_state.auth_error = True

if not st.session_state.authenticated:
    st.text_input("Password", type="password", key="password_input", on_change=_check_password)
    if st.session_state.get("auth_error"):
        st.error("Incorrect password.")
    st.stop()
```

**Rationale**: `on_change` fires before rerun so auth state is set before protected content renders. `st.stop()` hard-blocks everything below it.

---

## 2. In-Memory File Downloads

**Decision**: `io.BytesIO` for Excel, UTF-8-BOM bytes for CSV — no disk writes on the server.

**Excel**:
```python
buf = io.BytesIO()
df.to_excel(buf, engine="openpyxl", index=False)
excel_bytes = buf.getvalue()
st.download_button("Download Excel", data=excel_bytes, file_name="results.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
```

**CSV**:
```python
csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
st.download_button("Download CSV", data=csv_bytes, file_name="results.csv", mime="text/csv")
```

**Rationale**: `BytesIO.getvalue()` returns bytes; `st.download_button` accepts bytes directly. No temp files, no disk I/O on the server, safe for cloud hosting.

---

## 3. Progress During Collection

**Decision**: `st.progress()` bar + per-domain `st.write()` status line inside a placeholder.

**Pattern**:
```python
progress = st.progress(0, text="Starting…")
log = st.empty()
for i, query in enumerate(queries):
    log.write(f"Querying {domain}…")
    results = fetch_results(query, api_key)
    progress.progress(int((i + 1) / total * 100), text=f"{i+1}/{total} domains")
progress.empty()
log.empty()
```

**Rationale**: `st.progress` gives precise numeric feedback for the fixed 12-domain loop. `st.empty()` lets us clear the log line and bar after completion.

---

## 4. Writer Adaptation — In-Memory Helpers

**Decision**: Add two pure helper functions to `src/writer.py`:
- `to_excel_bytes(df) -> bytes` — wraps `BytesIO` + `to_excel`
- `to_csv_bytes(df) -> bytes` — wraps `to_csv(encoding="utf-8-sig")`

**Rationale**: Keeps `streamlit_app.py` thin; writer module owns all serialisation logic; existing `write_excel`/`write_csv` disk functions remain unchanged for CLI use.

---

## 5. Deployment — Streamlit Community Cloud

**Required files**:
- `streamlit_app.py` at repo root (entry point)
- `requirements.txt` with `streamlit>=1.32.0` added
- `.streamlit/secrets.toml` for local dev (gitignored)

**Secrets**:
```toml
# .streamlit/secrets.toml  (local only — never commit)
APP_PASSWORD = "your_team_password"
SERPAPI_KEY  = "your_serpapi_key"
```

In Community Cloud dashboard: paste same key=value pairs in the Secrets field when deploying.

**Rationale**: `st.secrets` resolves from `.streamlit/secrets.toml` locally and from the dashboard in production — identical call site, no code changes between environments.

---

## 6. Constitution Compliance Notes

| Principle | Status | Note |
|-----------|--------|------|
| I. Library-First | ✅ | `streamlit`, existing pipeline libs — no custom reimplementations |
| II. Data Relevance | ✅ | No change to pipeline filter logic |
| III. Date Integrity | ✅ | No change to date cutoff logic |
| IV. Output Quality | ✅ (adapted) | In-memory BytesIO replaces `os.replace` atomic write — justified because no file is persisted on server |
| V. Resilience | ✅ | `CollectionError` caught in UI; human-readable message shown |
| VI. Tool Economics | ✅ | `SERPAPI_KEY` loaded from `st.secrets`; missing key shown as error, not traceback |
