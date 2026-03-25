---

description: "Task list template for feature implementation"
---

# Tasks: Keyword-Driven Research Collector CLI

**Input**: Design documents from `specs/001-keyword-research-collector/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/cli-contract.md ✅ | quickstart.md ✅

**Tests**: Unit tests included (test_filter, test_classifier, test_writer). Integration test included (live SerpAPI, skipped without key).

**Organization**: Tasks grouped by user story; each story is independently implementable and testable.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in every task description

## Path Conventions

Single project layout: `src/` and `tests/` at repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, and dependency files

- [x] T001 Create directory structure: `src/`, `tests/unit/`, `tests/integration/`, `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`
- [x] T002 Create `requirements.txt` with pinned versions: `google-search-results>=2.4.2`, `pandas>=2.0.0`, `openpyxl>=3.1.0`, `requests>=2.28.0`, `beautifulsoup4>=4.12.0`, `python-dotenv>=1.0.0`, `python-dateutil>=2.8.2`, `click>=8.1.0`
- [x] T003 [P] Create `requirements-dev.txt` with: `pytest>=7.4.0`, `pytest-mock>=3.11.0`, `ruff>=0.1.0`, `mypy>=1.5.0`
- [x] T004 [P] Create `.env.example` with `SERPAPI_KEY=your_serpapi_key_here`; create `.gitignore` including `.env`, `__pycache__/`, `*.pyc`, `*.xlsx`, `*.csv`, `.mypy_cache/`, `.ruff_cache/`
- [x] T005 [P] Create `tool.py` at repo root: imports and delegates to `src/cli.py` main entrypoint; add `if __name__ == "__main__": main()` guard

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared models and configuration that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create `src/__init__.py` (empty package marker) and `src/models.py` with: `ContentType(str, Enum)` with values `STATS="Stats / Data Points"`, `SURVEY="Survey / Research Report"`, `EBOOK="Ebook / Whitepaper"`; `SearchResult` frozen dataclass with fields `title: str`, `link: str`, `snippet: str | None`, `date_raw: str | None`, `source_domain: str`; `ResearchRecord` frozen dataclass with fields `title: str`, `source: str`, `url: str`, `date: datetime.date`, `content_type: ContentType`, `keyword_match: bool`, `summary: str`
- [x] T007 [P] Create `src/config.py` with: `DATE_CUTOFF = date(2023, 1, 1)`; `AUTHORITY_DOMAINS: dict[str, str]` mapping domain → display name (gartner.com, forrester.com, mckinsey.com, deloitte.com, pwc.com, statista.com, hbr.org, accenture.com, bcg.com, bain.com, idc.com, weforum.org); `CONTENT_TYPE_SIGNALS: dict[ContentType, list[str]]` with signal keywords per type per research.md section 3; `PDF_DOMAINS: set[str]` — domains for which `filetype:pdf` is appended to queries (forrester, deloitte, mckinsey)
- [x] T008 [P] Create `src/models.py` `CollectionRun` dataclass with fields: `keyword: str`, `content_type_filter: ContentType | None`, `output_format: set[str]`, `output_paths: list[Path]`, `records_collected: int`, `records_excluded: list[tuple[str, str]]`, `started_at: datetime`, `completed_at: datetime | None`

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Collect Research by Keyword (Priority: P1) 🎯 MVP

**Goal**: User runs `python tool.py --keyword "AI in healthcare"` and receives a populated
`.xlsx` file containing only records from authority domains dated ≥ 2023-01-01, with all
7 required columns, keyword-matched.

**Independent Test**: `python tool.py --keyword "AI in healthcare"` → non-empty `.xlsx` with
correct columns, all dates ≥ 2023-01-01, all sources in authority list.

### Unit Tests for User Story 1

> **Write these tests FIRST; confirm they FAIL before implementing the source modules**

- [x] T009 [P] [US1] Create `tests/unit/test_filter.py`: test `is_authority_domain()` rejects unknown domains and accepts known ones; test `parse_and_validate_date()` returns `None` for pre-2023 dates, `None` for unparseable strings, valid `date` for 2023+ strings; test `is_keyword_relevant()` returns `True` when keyword in title, `True` when in snippet, `False` when absent from both
- [x] T010 [P] [US1] Create `tests/unit/test_classifier.py`: test `classify()` returns `STATS` for snippets containing "percent", "billion"; returns `EBOOK` for titles containing "whitepaper"; returns `SURVEY` for "report"; returns `SURVEY` (default) when no signals matched
- [x] T011 [P] [US1] Create `tests/unit/test_writer.py`: test `build_dataframe()` produces DataFrame with exactly 7 columns in correct order; test column dtypes (all `object`/str except `keyword_match` bool); test `write_excel()` atomic write creates `.xlsx` and does not leave `.tmp` file; test empty records list produces headers-only DataFrame

### Implementation for User Story 1

- [x] T012 [P] [US1] Implement `src/filter.py` with three pure functions (no network calls): `is_authority_domain(url: str) -> tuple[bool, str]` using `AUTHORITY_DOMAINS` from config; `parse_and_validate_date(date_raw: str | None) -> datetime.date | None` using `python-dateutil` + cutoff check; `is_keyword_relevant(keyword: str, title: str, snippet: str | None) -> bool` (case-insensitive substring check)
- [x] T013 [P] [US1] Implement `src/classifier.py` with `classify(title: str, snippet: str | None) -> ContentType` using `CONTENT_TYPE_SIGNALS` from config; priority order: STATS > SURVEY > EBOOK; default to SURVEY when no signals matched
- [x] T014 [US1] Implement `src/searcher.py`: `build_queries(keyword: str) -> list[str]` generating one `site:<domain> "<keyword>" after:2023-01-01` query per domain in AUTHORITY_DOMAINS (with `filetype:pdf` appended for PDF_DOMAINS); `fetch_results(query: str, api_key: str) -> list[SearchResult]` using `serpapi.GoogleSearch` with retry via `requests.HTTPAdapter` + `urllib3.Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503])`; log each retry at INFO, final failure at ERROR; raise `CollectionError` on unrecoverable failure (depends on T006, T007)
- [x] T015 [US1] Implement `src/writer.py`: `build_dataframe(records: list[ResearchRecord]) -> pd.DataFrame` with columns Title/Source/URL/Date/Content Type/Keyword Match/Summary in order; `write_excel(df: pd.DataFrame, path: Path) -> None` using `df.to_excel(engine="openpyxl", index=False)` with atomic write (`path.with_suffix(".tmp")` → `os.replace`); default output filename logic `{slug}-research-{YYYY-MM-DD}.xlsx` (depends on T006)
- [x] T016 [US1] Implement `src/cli.py`: `click` command with required `--keyword TEXT` option and `--verbose / -v` flag; load `.env` via `python-dotenv` at startup; validate `SERPAPI_KEY` present (exit code 1 with message if absent); wire pipeline: `build_queries` → `fetch_results` per query → filter each `SearchResult` (domain + date + keyword) → classify → append to records list → `build_dataframe` → `write_excel`; print `Collected N records → <path>` on success; warn and write headers-only file if N=0 (depends on T012, T013, T014, T015)
- [x] T017 [US1] Add `CollectionError` custom exception class to `src/models.py`; ensure `src/cli.py` catches it, prints user-friendly message to stderr, and exits with code 1 (no raw tracebacks)

**Checkpoint**: User Story 1 fully functional — `python tool.py --keyword "AI in healthcare"` produces correct `.xlsx`

---

## Phase 4: User Story 2 — Filter by Content Type (Priority: P2)

**Goal**: `--type [stats|survey|ebook]` flag filters output to a single content type.

**Independent Test**: `python tool.py --keyword "AI in healthcare" --type ebook` → output
contains only rows where Content Type = "Ebook / Whitepaper".

### Implementation for User Story 2

- [x] T018 [US2] Add `--type` option to `src/cli.py` using `click.Choice(["stats", "survey", "ebook"], case_sensitive=False)`; map choice string to `ContentType` enum value; pass `content_type_filter: ContentType | None` through pipeline (depends on T016)
- [x] T019 [US2] Implement content type gate in pipeline (either in `src/cli.py` or as `filter_by_type(records, ct_filter)` in `src/filter.py`): if `content_type_filter` is set, drop records whose `content_type != content_type_filter` after classification (before writing); dropped records are NOT counted as excluded (depends on T018)
- [x] T020 [P] [US2] Add test in `tests/unit/test_filter.py` for `filter_by_type()`: returns all records when filter is None; returns only matching records when filter is set; returns empty list when no records match

**Checkpoint**: User Stories 1 AND 2 independently functional

---

## Phase 5: User Story 3 — Export to CSV (Priority: P3)

**Goal**: `--format csv` produces a UTF-8-BOM `.csv` file; `--format excel --format csv` produces both.

**Independent Test**: `python tool.py --keyword "AI in healthcare" --format csv` →
`.csv` file exists, UTF-8-BOM encoded, same 7 columns as Excel output.

### Implementation for User Story 3

- [x] T021 [US3] Add `--format` option to `src/cli.py` using `click.option("--format", "output_formats", multiple=True, type=click.Choice(["excel", "csv"]), default=["excel"])`; pass `output_formats: tuple[str, ...]` to writer (depends on T016)
- [x] T022 [US3] Implement `write_csv(df: pd.DataFrame, path: Path) -> None` in `src/writer.py`: `df.to_csv(encoding="utf-8-sig", index=False)` with atomic write pattern; file extension `.csv` (depends on T015)
- [x] T023 [P] [US3] Add `--output PATH` option to `src/cli.py` for custom output base path override (no extension; tool appends `.xlsx` / `.csv` per format); validate parent directory exists, exit code 1 if not (depends on T016)
- [x] T024 [P] [US3] Add tests in `tests/unit/test_writer.py` for `write_csv()`: output file uses `.csv` extension; first bytes are UTF-8 BOM (`\xef\xbb\xbf`); column order matches Excel output

**Checkpoint**: All three user stories independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, quality gates, and final validation

- [x] T025 [P] Create `README.md` documenting: prerequisites, installation (`pip install -r requirements.txt`), `.env` setup, all CLI flags with examples (matching `contracts/cli-contract.md`), SerpAPI cost tier (free tier: 100 searches/month; paid plans available), note that no free drop-in alternative currently matches SerpAPI's reliability for site-restricted Google queries
- [x] T026 [P] Create `pyproject.toml` with `[tool.ruff]` config (`line-length = 100`, `select = ["E", "F", "I"]`) and `[tool.mypy]` config (`python_version = "3.10"`, `ignore_missing_imports = true`)
- [x] T027 [P] Create `tests/integration/test_searcher.py`: test that `fetch_results()` returns a non-empty list for keyword "AI" against at least one domain; skip entire module with `pytest.mark.skipif(not os.getenv("SERPAPI_KEY"), reason="SERPAPI_KEY not set")`
- [ ] T028 Run quickstart.md validation checklist end-to-end: install deps in fresh venv, configure `.env`, run `python tool.py --keyword "AI in healthcare"`, verify output, run `pytest tests/unit/ -v`, confirm all pass
- [ ] T029 [P] Verify `ruff check src/ tests/` passes with zero errors; verify `mypy src/` passes with zero type errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion
- **User Story 2 (Phase 4)**: Depends on Phase 3 completion (adds `--type` to existing CLI)
- **User Story 3 (Phase 5)**: Depends on Phase 3 completion (adds `--format` to existing CLI)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — no dependency on US2 or US3
- **US2 (P2)**: Extends US1's CLI; can start after US1's T016 (cli.py) is complete
- **US3 (P3)**: Extends US1's CLI and writer; can start after US1's T015+T016 are complete
- US2 and US3 can proceed in **parallel** once US1 is complete

### Within Each User Story

- Unit tests (T009–T011) MUST be written FIRST and confirmed to FAIL before implementation
- Models (T006) before all others
- Config (T007) before searcher and classifier
- filter.py + classifier.py before cli.py
- searcher.py before cli.py
- writer.py before cli.py
- cli.py last (wires everything together)

### Parallel Opportunities

- T003, T004, T005 — all Phase 1, different files
- T007, T008 — foundational, different files
- T009, T010, T011 — unit test stubs, all different files
- T012, T013 — filter.py and classifier.py have no dependency on each other
- T025, T026, T027, T029 — polish tasks, all independent

---

## Parallel Example: User Story 1

```bash
# Launch unit test stubs in parallel (write all first, confirm they fail):
Task: T009 — tests/unit/test_filter.py
Task: T010 — tests/unit/test_classifier.py
Task: T011 — tests/unit/test_writer.py

# Then implement filter + classifier in parallel (no interdependency):
Task: T012 — src/filter.py
Task: T013 — src/classifier.py

# Then implement searcher + writer in parallel:
Task: T014 — src/searcher.py
Task: T015 — src/writer.py

# Finally wire CLI (depends on all above):
Task: T016 — src/cli.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T005)
2. Complete Phase 2: Foundational (T006–T008) — **CRITICAL, blocks all stories**
3. Complete Phase 3: User Story 1 (T009–T017)
4. **STOP and VALIDATE**: Run `python tool.py --keyword "AI in healthcare"`, confirm output
5. Run `pytest tests/unit/ -v` — all green

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. User Story 1 → MVP: keyword → Excel output ✅
3. User Story 2 → Add `--type` content filter ✅
4. User Story 3 → Add `--format csv` export ✅
5. Polish → README, lint, integration test, quickstart validation ✅

### Parallel Team Strategy

With two developers after Foundational phase:
- Dev A: User Story 1 (core pipeline)
- Dev B: Pre-write US2 and US3 unit tests (T020, T024) while Dev A finishes US1

---

## Notes

- `[P]` tasks = different files, no incomplete dependencies
- `[USn]` label maps task to user story for traceability
- Unit tests MUST be written before implementation and confirmed FAIL first
- Each story is completable and testable independently
- Commit after each checkpoint (end of each phase)
- `os.replace` for all file writes — never write directly to final path
- `SERPAPI_KEY` absence must ALWAYS produce exit code 1 with clear message — never a traceback
