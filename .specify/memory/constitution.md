<!--
  SYNC IMPACT REPORT
  ==================
  Version change: [UNVERSIONED / template] → 1.0.0
  Modified principles: N/A (initial authoring from template)
  Added sections:
    - Core Principles (I–VI)
    - Technology Stack & Dependencies
    - Development Workflow & Quality Gates
    - Governance
  Removed sections: None (all template placeholders replaced)
  Templates reviewed:
    - .specify/templates/plan-template.md     ✅ Constitution Check section aligns
    - .specify/templates/spec-template.md     ✅ Requirements/constraints compatible
    - .specify/templates/tasks-template.md    ✅ Phase structure compatible
  Deferred TODOs: None
-->

# Python CLI Research Collector Constitution

## Core Principles

### I. Library-First (NON-NEGOTIABLE)

The tool MUST rely on well-established, actively maintained Python libraries for all
functionality. Specifically: `requests` for HTTP, `pandas` for data manipulation,
`openpyxl` for Excel output, and `serpapi` (or `google-search-results`) for search
ingestion. No custom re-implementations of functionality already covered by these
libraries are permitted.

**Non-negotiable rules:**
- MUST import and use an existing library before writing any custom logic for the same concern.
- MUST NOT implement custom HTTP retry logic when `requests` + `urllib3` retry adapters exist.
- MUST NOT implement custom Excel writing when `openpyxl` / `pandas.to_excel()` exist.
- Custom code is only acceptable for orchestration, domain logic, and CLI wiring.

**Rationale:** Custom implementations introduce maintenance burden, edge-case bugs, and
divergence from well-tested community solutions. Libraries encode years of battle-testing.

### II. Data Relevance

Every record fetched from an external source MUST be verified as keyword-relevant before
being included in any output artifact. Irrelevant records MUST be filtered out at ingest
time, not post-processing.

**Non-negotiable rules:**
- MUST apply keyword matching (title + abstract/snippet) as a gate before writing any row.
- MUST NOT rely solely on the search engine's relevance ranking — explicit field-level
  keyword checks are required.
- Relevance logic MUST be unit-testable in isolation from network calls.

**Rationale:** Search APIs return noisy results. Downstream consumers depend on precision;
polluted datasets erode trust in the tool's output.

### III. Date Integrity

Date filtering MUST strictly enforce a minimum cutoff of **2023-01-01**. Any record with
a publication or indexing date earlier than this cutoff MUST be excluded, regardless of
keyword relevance.

**Non-negotiable rules:**
- MUST parse and validate dates before inclusion; unparseable dates MUST be treated as
  excluded (log a warning, never silently include).
- MUST NOT allow the cutoff to be overridden to a date earlier than 2023-01-01 via CLI
  flags or configuration.
- Date comparison MUST use ISO 8601 format internally (`YYYY-MM-DD`).

**Rationale:** Research relevance degrades rapidly; pre-2023 data introduces outdated
citations and inflates result counts without adding value to the target use case.

### IV. Output Quality

All output MUST be written as clean, formatted Excel (`.xlsx`) or CSV files using
`pandas` and `openpyxl`. Raw, unstructured, or partial output files are not acceptable
deliverables.

**Non-negotiable rules:**
- MUST produce well-typed columns (strings, dates, integers — never mixed-type columns).
- Excel output MUST include a header row with human-readable column names.
- MUST NOT write partial files on error; use atomic write patterns (write to temp, rename).
- CSV output MUST use UTF-8 encoding with BOM (`utf-8-sig`) for cross-platform Excel
  compatibility.

**Rationale:** Analysts open output directly in Excel. Corrupt or inconsistently typed
files create rework and erode tool adoption.

### V. Resilience

The tool MUST handle rate limiting, transient network errors, and API quota exhaustion
gracefully without crashing. All recoverable errors MUST be retried with exponential
back-off; unrecoverable errors MUST produce a clear, actionable message and a clean exit.

**Non-negotiable rules:**
- MUST implement retry with back-off for HTTP 429 and 5xx responses (use `urllib3` Retry
  or equivalent `requests` adapter).
- MUST NOT surface raw stack traces to the user; wrap exceptions with contextual messages.
- MUST log each retry attempt at INFO level and each final failure at ERROR level.
- MUST exit with a non-zero status code on unrecoverable failure.

**Rationale:** Research collection runs are often long and unattended. Silent failures or
crashes that discard partial progress are unacceptable.

### VI. Tool Economics

Free and open data sources MUST be preferred. SerpAPI is acceptable when free sources
are insufficient for reliability, coverage, or quota requirements. API key costs MUST
be documented in the project README.

**Non-negotiable rules:**
- MUST document every external API dependency, its cost tier, and a free alternative (if
  one exists) in the README.
- MUST support swappable source backends so a free source can replace a paid one without
  changing downstream code.
- SerpAPI usage MUST be gated behind an environment variable (`SERPAPI_KEY`); the tool
  MUST degrade gracefully (warning + fallback or clean exit) when the key is absent.

**Rationale:** Research environments frequently lack budget approval for third-party APIs.
Pluggable backends preserve accessibility while allowing reliability upgrades when funded.

## Technology Stack & Dependencies

The canonical technology stack for this project is:

| Concern | Library / Tool | Notes |
|---|---|---|
| HTTP requests | `requests` ≥ 2.28 | Use `HTTPAdapter` + `Retry` for resilience |
| Data wrangling | `pandas` ≥ 2.0 | Standard DataFrame operations |
| Excel output | `openpyxl` ≥ 3.1 | Via `pandas.to_excel(engine="openpyxl")` |
| Search ingestion | `serpapi` / `google-search-results` | Gated on `SERPAPI_KEY` env var |
| CLI interface | `argparse` or `click` | Prefer `click` for subcommands |
| Testing | `pytest` + `pytest-mock` | Unit and integration tests |
| Date parsing | `python-dateutil` or stdlib `datetime` | ISO 8601 internally |

**Python version**: MUST target Python 3.10+ (use `match` statements, `|` union types
where idiomatic).

**Dependency pinning**: MUST maintain a `requirements.txt` with pinned versions AND a
`requirements-dev.txt` for test/dev dependencies.

## Development Workflow & Quality Gates

All changes MUST pass the following gates before merge:

1. **Lint**: `ruff` (or `flake8`) passes with zero errors.
2. **Type check**: `mypy` passes on `src/` with `strict = false` minimum.
3. **Tests**: `pytest` green; MUST include at least one unit test per public function and
   one integration test per data source connector.
4. **Constitution check**: Reviewer confirms no principle violations (use
   `plan.md` Constitution Check section as checklist).
5. **Output validation**: At least one smoke test writes a real `.xlsx` file and
   verifies it opens without error and contains expected columns.

**Branching**: Feature branches from `main`; squash-merge PRs with descriptive messages.

**Complexity justification**: Any deviation from Principle I (introducing custom logic
where a library exists) MUST be documented in the plan's Complexity Tracking table with
an explicit rationale.

## Governance

This constitution supersedes all other project practices. Amendments require:

1. A pull request modifying `.specify/memory/constitution.md`.
2. Version bump per semantic versioning rules (see below).
3. Propagation to affected templates (`.specify/templates/`) within the same PR.
4. A migration note in the PR description if existing features are impacted.

**Versioning policy:**
- **MAJOR**: Removal or redefinition of a core principle; backward-incompatible governance change.
- **MINOR**: New principle or section added; material expansion of existing guidance.
- **PATCH**: Wording clarifications, typo fixes, non-semantic refinements.

**Compliance review**: All PRs must include a Constitution Check (see `plan-template.md`)
confirming adherence to all six principles. Violations MUST be justified in the
Complexity Tracking table or the PR is blocked.

**Version**: 1.0.0 | **Ratified**: 2026-03-24 | **Last Amended**: 2026-03-24
