# Research: Keyword-Driven Research Collector CLI

**Branch**: `001-keyword-research-collector` | **Date**: 2026-03-24
**Phase**: 0 — Resolved unknowns and best-practice decisions

---

## 1. SerpAPI Query Strategy

**Decision**: Issue one query per authority domain using the `site:` operator combined
with the `after:` date filter and an optional `filetype:pdf` modifier for whitepaper
searches. Example query set for keyword "AI in healthcare":

```
site:mckinsey.com "AI in healthcare" after:2023-01-01
site:gartner.com "AI in healthcare" after:2023-01-01
site:forrester.com "AI in healthcare" filetype:pdf after:2023-01-01
site:deloitte.com "AI in healthcare" filetype:pdf after:2023-01-01
site:pwc.com "AI in healthcare" after:2023-01-01
site:statista.com "AI in healthcare" after:2023-01-01
site:hbr.org "AI in healthcare" after:2023-01-01
```

**Rationale**: Per-domain site-restricted queries produce higher-precision results than
a single broad query. The `after:` filter performs pre-filtering at the search engine
level, reducing unnecessary API result processing. `filetype:pdf` targets whitepapers
and reports on domains known to publish PDFs (Deloitte, Forrester, McKinsey).

**Alternatives considered**:
- Single broad query with all domains as `OR` — rejected; lower precision, harder to
  attribute results to specific sources.
- Separate SerpAPI params for date range — SerpAPI's `tbs` param supports this but
  the `after:` query modifier is simpler and equally reliable.

---

## 2. Date Parsing

**Decision**: Use `python-dateutil` (`dateutil.parser.parse`) as the primary date parser.
Fall back to a set of explicit `strptime` patterns for common formats. Any result that
raises a `ValueError` or `ParserError` is excluded with a WARNING log.

**Rationale**: SerpAPI returns dates in varied formats ("Jan 15, 2024", "2024-01-15",
"3 days ago", etc.). `python-dateutil` handles the majority without manual format lists.
Stdlib `datetime.strptime` alone would require maintaining an exhaustive format list.

**Alternatives considered**:
- Regex-only date extraction — rejected; too brittle for the variety of SerpAPI date
  string formats.
- `arrow` library — considered but `python-dateutil` is lighter and already a transitive
  dependency of many packages.

---

## 3. Content Type Classification

**Decision**: Heuristic signal-based classifier using keyword matching on the result
title and snippet. Classification signals:

| Content Type | Signals (title/snippet keywords) |
|---|---|
| Stats / Data Points | "statistic", "percent", "%", "survey says", "according to", "data shows", "report finds", "by 2025", "by 2026", "billion", "million", "growth rate" |
| Survey / Research Report | "survey", "research", "report", "study", "findings", "analysis", "whitepaper", "white paper", "forecast", "market research" |
| Ebook / Whitepaper | "ebook", "e-book", "whitepaper", "white paper", "guide", "handbook", "playbook", "download", "pdf" |

Priority order when signals overlap: Stats > Survey/Report > Ebook/Whitepaper.
Default (no signals matched): "Survey / Research Report".

**Rationale**: ML-based classification is over-engineered for v1 given the narrow domain
and explicit content signals present in authority-source titles and snippets.
Heuristic accuracy is sufficient for research collection use cases.

**Alternatives considered**:
- Rule-based URL pattern matching (e.g., `/ebooks/`) — used as a supplementary signal
  but unreliable across all domains.
- Zero-shot LLM classification — rejected for v1; introduces API cost and latency.

---

## 4. Environment / Configuration Loading

**Decision**: Use `python-dotenv` to load a `.env` file in the working directory before
reading `os.environ["SERPAPI_KEY"]`. This means users can store their key in a `.env`
file (gitignored) without manually exporting env vars in their shell.

**Rationale**: `.env` files are the de-facto standard for local secrets in Python CLI
tools. `python-dotenv` is a tiny, well-maintained library that does exactly this.

**Alternatives considered**:
- Config file (YAML/TOML) — rejected; introduces parsing complexity for a single key.
- Require explicit shell export only — less ergonomic; creates friction for new users.

---

## 5. CLI Framework

**Decision**: Use `click` for the CLI interface.

**Rationale**: `click` provides clean decorator-based argument/option definition,
automatic `--help` generation, type validation, and multi-value option support with less
boilerplate than `argparse`. The `--type` flag (multi-choice) and `--format` flag benefit
from `click.Choice`.

**Alternatives considered**:
- `argparse` (stdlib) — viable but more verbose for the flags this tool needs.
- `typer` — wraps click with type hints; adds dependency for marginal benefit in a
  single-file CLI.

---

## 6. beautifulsoup4 Scope

**Decision**: Include `beautifulsoup4` as a dependency but limit its use to optional
snippet enrichment. For v1, summaries are populated directly from SerpAPI snippets
(truncated to 300 characters). `bs4` is available for future snippet scraping expansion.

**Rationale**: The spec assumption is that the Summary column is the SerpAPI snippet.
Introducing full-page scraping in v1 would add latency, rate-limit concerns, and
robots.txt compliance considerations. Keeping `bs4` as a listed dependency signals the
intended future direction without forcing it into the v1 data path.

**Alternatives considered**:
- Exclude entirely from requirements — possible for v1 but removes the hook for v2
  snippet enrichment work.

---

## 7. Atomic File Write

**Decision**: Write output to `<filename>.tmp`, then `os.replace(<filename>.tmp, <filename>)`.
`os.replace` is atomic on POSIX and best-effort on Windows (same-volume moves succeed
atomically on NTFS).

**Rationale**: Prevents partial/corrupt files if the process is interrupted during write.
`os.replace` is stdlib; no extra library needed.

---

## 8. Authority Domain Allowlist

**Decision**: Store the domain allowlist as a `dict[str, str]` in `src/config.py`
mapping domain suffix → display name:

```python
AUTHORITY_DOMAINS: dict[str, str] = {
    "gartner.com": "Gartner",
    "forrester.com": "Forrester",
    "mckinsey.com": "McKinsey & Company",
    "deloitte.com": "Deloitte",
    "pwc.com": "PwC",
    "statista.com": "Statista",
    "hbr.org": "Harvard Business Review",
    "accenture.com": "Accenture",
    "bcg.com": "BCG",
    "bain.com": "Bain & Company",
    "idc.com": "IDC",
    "idc-research.net": "IDC",
    "weforum.org": "World Economic Forum",
}
```

The `Source` column in the output uses the display name, not the raw domain.

**Rationale**: Hardcoded in config for v1; no external file required. The dict structure
makes it trivial to extend without touching business logic.

---

## 9. Output File Naming

**Decision**: Default filename: `{keyword-slug}-research-{YYYY-MM-DD}.xlsx`
where keyword-slug = keyword lowercased, spaces → hyphens, non-alphanumeric removed.
Example: `ai-in-healthcare-research-2026-03-24.xlsx`.
Overridable via `--output <path>` CLI flag.

---

## 10. Retry / Back-off Strategy

**Decision**: Wrap the SerpAPI HTTP call in a retry loop with exponential back-off:
- Max 3 retries
- Initial wait: 2 seconds; doubles each retry (2 → 4 → 8)
- Retry on: HTTP 429, HTTP 5xx, `requests.ConnectionError`, `requests.Timeout`
- Log each retry at INFO; log final failure at ERROR; re-raise as `CollectionError`

`requests.adapters.HTTPAdapter` with `urllib3.util.retry.Retry` is used for the
underlying HTTP session. SerpAPI client wraps this session.

---

## All NEEDS CLARIFICATION Items: Resolved

| Item | Resolution |
|---|---|
| Date parsing library | `python-dateutil` |
| CLI framework | `click` |
| `.env` loading | `python-dotenv` |
| Content classification approach | Heuristic keyword signals |
| `bs4` scope | Optional v1 dependency, summaries from SerpAPI snippet |
| Atomic write mechanism | `os.replace` (stdlib) |
| Authority domain storage | `dict` in `config.py` |
