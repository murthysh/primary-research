# Feature Specification: Keyword-Driven Research Collector CLI

**Feature Branch**: `001-keyword-research-collector`
**Created**: 2026-03-24
**Status**: Draft
**Input**: User description: "Build a Python CLI tool that collects external research and stats from high-authority sources when given a seed keyword."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Collect Research by Keyword (Priority: P1)

A researcher enters a seed keyword such as "AI in healthcare" and the tool automatically
queries Google via SerpAPI, filters results to high-authority domains published from
January 2023 onwards, and saves a clean Excel file containing all matching records.

**Why this priority**: This is the core value of the entire tool. All other stories are
enhancements on top of this single workflow.

**Independent Test**: Can be fully tested by running `python cli.py collect "AI in healthcare"`
and verifying that a non-empty `.xlsx` file is produced containing only records from
approved authority domains dated 2023-01-01 or later.

**Acceptance Scenarios**:

1. **Given** a seed keyword "AI in healthcare", **When** the user runs the collect command,
   **Then** the tool returns records only from Gartner, Forrester, McKinsey, Deloitte,
   PwC, Statista, HBR, or equivalent authority domains.
2. **Given** a seed keyword, **When** the tool processes results, **Then** every record in
   the output has a publication date of 2023-01-01 or later; records with earlier dates or
   unparseable dates are silently excluded (warning logged).
3. **Given** a seed keyword, **When** the tool writes output, **Then** an `.xlsx` file is
   created with columns: Title, Source, URL, Date, Content Type, Keyword Match, Summary.
4. **Given** the SerpAPI key is missing from the environment, **When** the user runs
   the collect command, **Then** the tool exits with a non-zero code and a clear message
   explaining the missing `SERPAPI_KEY` environment variable.

---

### User Story 2 - Filter by Content Type (Priority: P2)

A researcher wants to narrow the collection to a specific content type — for example,
only "whitepapers" or only "surveys" — rather than collecting all types at once.

**Why this priority**: Improves precision for researchers who already know what format they
need, reducing noise in the output.

**Independent Test**: Run `python cli.py collect "AI in healthcare" --type whitepaper` and
verify that only records classified as whitepapers appear in the output.

**Acceptance Scenarios**:

1. **Given** a content type flag `--type stats`, **When** the tool runs, **Then** only
   records classified as "Stats and data points" are included in the output.
2. **Given** no `--type` flag, **When** the tool runs, **Then** all three content types
   (stats, surveys, whitepapers/ebooks) are collected.
3. **Given** an unrecognised content type value, **When** the user runs the command,
   **Then** the tool prints the list of valid content types and exits with a non-zero code.

---

### User Story 3 - Export to CSV in Addition to Excel (Priority: P3)

A researcher needs a CSV version of the output for import into another tool or script.

**Why this priority**: Broadens compatibility at low implementation cost; Excel is the
primary deliverable.

**Independent Test**: Run `python cli.py collect "AI in healthcare" --format csv` and
verify a UTF-8-BOM `.csv` file is produced with the same columns as the Excel output.

**Acceptance Scenarios**:

1. **Given** a `--format csv` flag, **When** the tool runs, **Then** a `.csv` file is
   produced with UTF-8-BOM encoding, correct headers, and the same data as the Excel output.
2. **Given** `--format excel` (default), **When** the tool runs, **Then** an `.xlsx` file
   is produced.
3. **Given** both `--format excel` and `--format csv` flags together, **When** the tool
   runs, **Then** both files are produced.

---

### Edge Cases

- What happens when SerpAPI returns zero results for the keyword?
  → Tool produces an empty output file with headers only and logs a warning.
- What happens when all results are filtered out (wrong domain or pre-2023 date)?
  → Same as zero results; empty file with headers, warning to user.
- What happens when the SerpAPI quota is exhausted mid-collection?
  → Tool retries with exponential back-off; if quota remains exhausted after retries,
  writes whatever was collected so far, logs the quota error, and exits non-zero.
- What happens when an output file with the same name already exists?
  → Tool overwrites it (atomic write pattern: write to temp, then rename).
- What happens when the keyword contains special characters or spaces?
  → Keyword is passed as a quoted CLI argument; no transformation required beyond
  standard URL-encoding handled by SerpAPI client.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST accept a seed keyword as a required CLI argument.
- **FR-002**: The tool MUST query Google via SerpAPI using the provided seed keyword.
- **FR-003**: The tool MUST restrict results to an approved list of high-authority domains
  including at minimum: gartner.com, forrester.com, mckinsey.com, deloitte.com, pwc.com,
  statista.com, hbr.org. Additional peer-authority domains are acceptable.
- **FR-004**: The tool MUST exclude any record with a publication date earlier than
  2023-01-01. Records with unparseable dates MUST also be excluded.
- **FR-005**: The tool MUST classify each result into one of three content types:
  "Stats / Data Points", "Survey / Research Report", or "Ebook / Whitepaper".
- **FR-006**: The tool MUST verify that each collected record is keyword-relevant by
  checking that the keyword appears in the record's title or snippet before inclusion.
- **FR-007**: The tool MUST write output to an `.xlsx` file by default, with columns:
  Title, Source, URL, Date, Content Type, Keyword Match, Summary.
- **FR-008**: The tool MUST support an optional `--type` flag to filter results to a
  single content type.
- **FR-009**: The tool MUST support an optional `--format` flag accepting `excel`
  (default) and `csv`.
- **FR-010**: The tool MUST handle HTTP rate limiting (429) and transient errors (5xx)
  with automatic retry and exponential back-off.
- **FR-011**: The tool MUST read the SerpAPI key from the `SERPAPI_KEY` environment
  variable and exit with a clear error if the variable is absent.
- **FR-012**: The tool MUST write output files atomically (write to temporary file, then
  rename) to prevent corrupt partial files.

### Key Entities

- **SearchResult**: A single record returned by SerpAPI — raw title, link, snippet, date.
- **ResearchRecord**: A validated, enriched result — title, source domain, URL, parsed
  date, classified content type, keyword match flag, summary (truncated snippet).
- **CollectionRun**: A single execution — seed keyword, content type filter, output format,
  output file path, records collected, records excluded (with reasons).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A researcher can run the tool with a seed keyword and receive a populated
  output file within 60 seconds for a standard collection (up to 100 results).
- **SC-002**: 100% of records in the output belong to approved authority domains and are
  dated 2023-01-01 or later — zero non-compliant records.
- **SC-003**: The output file opens without error in Microsoft Excel and contains
  well-typed, readable columns on first open (no manual formatting required).
- **SC-004**: The tool recovers automatically from transient API errors without user
  intervention, completing the collection without data loss.
- **SC-005**: A researcher unfamiliar with the tool can run their first successful
  collection using only the README instructions, without additional support.

## Assumptions

- Users have a valid SerpAPI account and API key available as an environment variable.
- "High-authority domains" are treated as a configurable allowlist; the initial list is
  hardcoded but the design should allow easy extension without code changes (e.g., via a
  config file or CLI flag in a future iteration).
- Content type classification is heuristic (keyword/pattern matching on title and snippet)
  rather than ML-based; occasional misclassification is acceptable for v1.
- The "Summary" column is populated from the SerpAPI result snippet (truncated to a
  reasonable length), not from full-page content scraping.
- Output file naming defaults to `<keyword>-research-<date>.xlsx` (spaces replaced with
  hyphens, lowercased); an optional `--output` flag may override this.
- The tool is single-user CLI; no concurrency, authentication, or multi-user concerns.
- Internet connectivity is assumed to be available during execution.
