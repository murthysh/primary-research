---

description: "Task list for Streamlit Web UI implementation"
---

# Tasks: Streamlit Web UI

**Input**: Design documents from `specs/002-streamlit-web-ui/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ui-contract.md ✅ | quickstart.md ✅

**Tests**: Unit tests for new writer helpers only; UI tested via manual smoke test.

**Organization**: Tasks grouped by user story; each story independently implementable and testable.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add Streamlit dependency and deployment config files

- [x] T001 Add `streamlit>=1.32.0` to `requirements.txt`
- [x] T002 [P] Create `.streamlit/secrets.toml` with placeholder keys `APP_PASSWORD` and `SERPAPI_KEY`; add `.streamlit/secrets.toml` to `.gitignore`
- [x] T003 [P] Create empty `streamlit_app.py` at repo root with a `# TODO` comment (establishes entry point for Community Cloud)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add in-memory serialisation helpers and `RunResult` model that the UI depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T00X Add `RunResult` dataclass to `src/models.py` with fields: `records_collected: int`, `excel_bytes: bytes | None`, `csv_bytes: bytes | None`, `output_stem: str`, `error: str | None`, `warning: str | None`
- [x] T00X [P] Add `to_excel_bytes(df: pd.DataFrame) -> bytes` to `src/writer.py`: write DataFrame into a `io.BytesIO` buffer using `df.to_excel(engine="openpyxl", index=False)` and return `buf.getvalue()`
- [x] T00X [P] Add `to_csv_bytes(df: pd.DataFrame) -> bytes` to `src/writer.py`: return `df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")`

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Password Gate (Priority: P1) 🎯 MVP

**Goal**: Team members must enter the correct shared password before seeing any app content. Wrong password shows an error; correct password shows the main UI. Auth persists for the browser session.

**Independent Test**: Run `streamlit run streamlit_app.py`, enter wrong password → error shown, no content visible. Enter correct password → main UI appears.

### Implementation for User Story 1

- [x] T007 [US1] Implement password gate in `streamlit_app.py`:
  - Initialise `st.session_state.authenticated = False` and `st.session_state.auth_error = False` if not present
  - Define `_check_password()` callback: compare `st.session_state.password_input` to `st.secrets.get("APP_PASSWORD", "")` and set `authenticated = True` on match, else set `auth_error = True`
  - If not authenticated: render `st.title("Research Collector")`, `st.text_input("Password", type="password", key="password_input", on_change=_check_password)`, `st.error(...)` if `auth_error`, then `st.stop()`

**Checkpoint**: Password gate works — wrong password blocks, correct password proceeds

---

## Phase 4: User Story 2 — Run Collection & Download (Priority: P1) 🎯 MVP

**Goal**: Authenticated user enters keyword, selects filters and formats, clicks Run, sees progress domain-by-domain, and downloads output file(s) when done.

**Independent Test**: Authenticate, enter "AI in healthcare", click Run — progress bar advances, success message shows record count, Download Excel button appears and produces a valid `.xlsx`.

### Implementation for User Story 2

- [x] T008 [US2] Implement main form in `streamlit_app.py` (below the password gate):
  - `st.text_input("Keyword", key="keyword")` — required
  - `st.selectbox("Content type", ["All", "Stats", "Survey", "Ebook"], key="content_type")`
  - `st.multiselect("Output formats", ["Excel", "CSV"], default=["Excel"], key="output_formats")`
  - Run button: `st.button("Run", disabled=(not keyword or not output_formats))`

- [x] T009 [US2] Implement `_run_pipeline(keyword, content_type_str, output_formats) -> RunResult` function in `streamlit_app.py`:
  - Load `SERPAPI_KEY` from `st.secrets`; return `RunResult(error="SERPAPI_KEY not configured …")` if absent
  - Map content type string to `ContentType | None` (reuse `_content_type_from_str` logic from `src/cli.py`)
  - Call `build_queries(keyword)`, iterate queries with `st.progress` bar (0→100%) and `st.empty()` status line showing current domain
  - For each result: apply domain, date, keyword gates; classify; append to records list; catch `CollectionError` and return `RunResult(error=str(exc), ...)`
  - Apply `filter_by_type`; call `build_dataframe`
  - Build `excel_bytes` via `to_excel_bytes` if "Excel" in formats; build `csv_bytes` via `to_csv_bytes` if "CSV" in formats
  - Return `RunResult(records_collected=len(records), excel_bytes=..., csv_bytes=..., output_stem=default_output_stem(keyword), error=None, warning="No results matched filters." if len(records)==0 else None)`

- [x] T010 [US2] Wire Run button to pipeline and display results in `streamlit_app.py`:
  - On button click: store result in `st.session_state.run_result = _run_pipeline(...)`
  - After run: if `run_result.error` → `st.error(...)`; elif `run_result.warning` → `st.warning(...)` + show download buttons; else `st.success(f"Collected {n} records")` + show download buttons
  - `st.download_button("Download Excel", data=excel_bytes, file_name=f"{stem}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")` if excel_bytes
  - `st.download_button("Download CSV", data=csv_bytes, file_name=f"{stem}.csv", mime="text/csv")` if csv_bytes

**Checkpoint**: Full collection flow works end-to-end

---

## Phase 5: User Story 3 — Clear Error Messages (Priority: P2)

**Goal**: All error conditions (missing API key, API failure, zero results) show plain-English messages. No raw tracebacks are ever visible.

**Independent Test**: Remove `SERPAPI_KEY` from `.streamlit/secrets.toml`, click Run → error message shown, no traceback visible.

### Implementation for User Story 3

- [x] T011 [US3] Ensure `_run_pipeline` in `streamlit_app.py` catches all exception types:
  - Wrap entire pipeline in `try/except Exception as exc`; return `RunResult(error=f"Unexpected error: {exc}", ...)` for any uncaught exception
  - Verify `CollectionError` from `src/models.py` is caught and surfaced as human-readable message
  - Verify missing `SERPAPI_KEY` path returns a clear message (not a `KeyError` traceback)

**Checkpoint**: All three user stories functional

---

## Phase 6: Polish & Deployment

**Purpose**: Deployment config, README update, lint/type check, smoke test

- [x] T012 [P] Update `README.md` with a "Web UI" section: prerequisites (`pip install -r requirements.txt`), local run command (`streamlit run streamlit_app.py`), secrets setup, and link to Community Cloud deploy steps in `quickstart.md`
- [x] T013 [P] Verify `ruff check src/ streamlit_app.py` passes with zero errors; fix any issues
- [x] T014 [P] Verify `mypy src/` passes with zero errors (no need to type-check `streamlit_app.py` — Streamlit's dynamic API makes strict typing impractical)
- [ ] T015 Run quickstart.md validation checklist end-to-end: local secrets configured, `streamlit run streamlit_app.py`, authenticate, run keyword, download Excel, confirm 7 columns and dates ≥ 2023-01-01

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user stories**
- **US1 Password Gate (Phase 3)**: Depends on Phase 2
- **US2 Collection (Phase 4)**: Depends on Phase 3 (password gate must exist to test collection UI)
- **US3 Errors (Phase 5)**: Depends on Phase 4 (pipeline must exist to test error paths)
- **Polish (Phase 6)**: Depends on all user stories complete

### Parallel Opportunities

- T002, T003 — Phase 1, different files
- T005, T006 — foundational writer helpers, different functions
- T012, T013, T014 — polish tasks, all independent

---

## Parallel Example: Foundational Phase

```bash
# These can run simultaneously:
Task: T005 — add to_excel_bytes() to src/writer.py
Task: T006 — add to_csv_bytes() to src/writer.py
```

---

## Implementation Strategy

### MVP (US1 + US2 only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T006)
3. Complete Phase 3: Password Gate (T007)
4. Complete Phase 4: Collection + Downloads (T008–T010)
5. **STOP and VALIDATE**: Run `streamlit run streamlit_app.py`, authenticate, collect, download

### Full Delivery

1. MVP above ✅
2. Phase 5: Error handling polish (T011)
3. Phase 6: Deployment polish (T012–T015)
4. Deploy to Streamlit Community Cloud

---

## Notes

- `[P]` tasks = different files, no incomplete dependencies
- `[USn]` label maps task to user story for traceability
- `streamlit_app.py` imports directly from `src/` — no new abstraction layer
- `.streamlit/secrets.toml` MUST be in `.gitignore` before first commit
- Community Cloud reads secrets from dashboard — identical `st.secrets` call site in all environments
