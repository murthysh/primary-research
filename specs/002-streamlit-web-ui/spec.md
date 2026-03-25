# Feature Specification: Streamlit Web UI

**Feature Branch**: `002-streamlit-web-ui`
**Created**: 2026-03-25
**Status**: Draft
**Input**: User description: "Web UI for the keyword research collector CLI using Streamlit. Single-page app with: password gate (single shared password stored in st.secrets or .env), keyword text input, optional content type dropdown (All / Stats / Survey / Ebook), output format checkboxes (Excel, CSV), Run button that triggers the existing pipeline (build_queries → fetch_results → filter → classify → write), progress indicator during collection, download button(s) for output files after collection, error messages for missing API key or failed runs. Deploy to Streamlit Community Cloud. Feature ID: 002-streamlit-web-ui."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Access the App with a Password (Priority: P1)

A team member visits the hosted app URL and is presented with a password input field. They enter the shared team password and gain access to the research tool. Without the correct password, they cannot proceed.

**Why this priority**: Without authentication, the app is open to anyone with the URL and exposes the team's SerpAPI quota. This must be the first thing working.

**Independent Test**: Navigate to the app, enter the correct password — the main UI appears. Enter a wrong password — access is denied with a clear message.

**Acceptance Scenarios**:

1. **Given** a user visits the app URL, **When** they enter the correct password, **Then** the main research UI is shown.
2. **Given** a user visits the app URL, **When** they enter an incorrect password, **Then** they see an error message and the UI remains locked.
3. **Given** a user has already authenticated, **When** they refresh the page, **Then** they do not need to re-enter the password within the same session.

---

### User Story 2 - Run a Keyword Research Collection (Priority: P1)

An authenticated team member enters a keyword, optionally selects a content type filter and output format(s), then clicks Run. A progress indicator shows while the pipeline runs. When complete, one or two download buttons appear for the output file(s).

**Why this priority**: This is the core value of the app — turning keyword input into downloadable research files.

**Independent Test**: Enter "AI in healthcare", leave defaults, click Run — a `.xlsx` download button appears with 1+ records.

**Acceptance Scenarios**:

1. **Given** the user is authenticated, **When** they enter a keyword and click Run, **Then** a progress indicator is shown while collection runs.
2. **Given** collection completes successfully, **When** results are ready, **Then** a download button appears for each selected format.
3. **Given** collection returns zero results, **When** the run finishes, **Then** the user sees a warning that no results were found and a headers-only file is available to download.
4. **Given** the user selects both Excel and CSV formats, **When** collection completes, **Then** two separate download buttons appear.

---

### User Story 3 - See Clear Error Messages (Priority: P2)

If the SerpAPI key is missing or the API returns an unrecoverable error, the user sees a plain-English error message in the UI rather than a raw traceback.

**Why this priority**: Without this, configuration problems are invisible to non-technical team members.

**Independent Test**: Remove the API key from secrets, click Run — a clear error message appears, no traceback visible.

**Acceptance Scenarios**:

1. **Given** the SerpAPI key is not configured, **When** the user clicks Run, **Then** an error message explains the key is missing and no download button is shown.
2. **Given** the API returns an unrecoverable error mid-run, **When** the error occurs, **Then** the user sees a human-readable error and any partial results collected so far are offered for download.

---

### Edge Cases

- What happens when the keyword field is empty and the user clicks Run? → Run button is disabled or an inline validation message appears.
- What happens if the browser tab is closed mid-run? → The run is abandoned; no partial file is persisted on the server.
- What happens when the SerpAPI free-tier quota is exhausted? → The error propagates as a human-readable message in the UI.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST require a correct password before showing any research functionality.
- **FR-002**: The password MUST be stored in a secrets/environment configuration file, not hardcoded in source code.
- **FR-003**: Users MUST be able to enter a free-text keyword (required field).
- **FR-004**: Users MUST be able to optionally filter results by content type: All (no filter), Stats / Data Points, Survey / Research Report, Ebook / Whitepaper.
- **FR-005**: Users MUST be able to select one or both output formats: Excel (.xlsx) and CSV (.csv). At least one format must be selected.
- **FR-006**: The app MUST display a progress indicator while the collection pipeline is running.
- **FR-007**: After a successful run, the app MUST provide a download button for each selected output format.
- **FR-008**: The app MUST display a human-readable error message (no raw tracebacks) when the SerpAPI key is missing or an API error occurs.
- **FR-009**: The app MUST display a warning when collection completes with zero matching records.
- **FR-010**: The Run button MUST be disabled or blocked when the keyword field is empty.
- **FR-011**: The app MUST be deployable to Streamlit Community Cloud without modification.

### Key Entities

- **Session**: A single authenticated browser session; holds password state and run results in memory.
- **RunResult**: The output of one pipeline execution — collected records count, output file bytes (Excel and/or CSV), and any error or warning messages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An authenticated user can go from entering a keyword to clicking a download button in under 3 minutes for a typical run (12 authority domains queried).
- **SC-002**: 100% of error conditions (missing key, API failure, zero results) surface a readable message — zero raw tracebacks visible to users.
- **SC-003**: The app is accessible via a public URL shared with the team within one deploy cycle.
- **SC-004**: A team member with no CLI knowledge can successfully run a collection and download results on their first attempt.

## Assumptions

- The shared password is a single static string; per-user accounts are out of scope.
- The SerpAPI key is stored alongside the app password in the deployment secrets configuration.
- Output files are generated in memory and served as download bytes; no files are written to disk on the server.
- Mobile browser support is out of scope; the app targets desktop browsers.
- The existing pipeline modules (`src/`) are imported directly; no API layer is introduced between the UI and the pipeline.
- Streamlit Community Cloud is the deployment target; containerisation (Docker) is out of scope for v1.
