# Data Model: Keyword-Driven Research Collector CLI

**Branch**: `001-keyword-research-collector` | **Date**: 2026-03-24

---

## Entities

### SearchResult

Raw record returned by a single SerpAPI organic result item. Immutable after ingestion.

| Field | Type | Source | Notes |
|---|---|---|---|
| `title` | `str` | `result["title"]` | Raw title string |
| `link` | `str` | `result["link"]` | Full URL |
| `snippet` | `str \| None` | `result.get("snippet")` | May be absent |
| `date_raw` | `str \| None` | `result.get("date")` | Raw date string from SerpAPI |
| `source_domain` | `str` | Parsed from `link` | e.g., `mckinsey.com` |

**Validation rules:**
- `title` MUST be non-empty; records with empty titles are discarded.
- `link` MUST be a valid URL starting with `http://` or `https://`.
- `date_raw` may be `None`; absence is treated as an excluded date (logged as WARNING).

---

### ResearchRecord

Enriched, validated record ready for output. Produced by the filter + classifier pipeline
from a `SearchResult`.

| Field | Type | Output Column | Notes |
|---|---|---|---|
| `title` | `str` | Title | Trimmed, no HTML entities |
| `source` | `str` | Source | Display name from AUTHORITY_DOMAINS dict |
| `url` | `str` | URL | Full link |
| `date` | `datetime.date` | Date | Parsed, validated ≥ 2023-01-01 |
| `content_type` | `ContentType` | Content Type | Enum: STATS, SURVEY, EBOOK |
| `keyword_match` | `bool` | Keyword Match | True if keyword in title or snippet |
| `summary` | `str` | Summary | SerpAPI snippet, max 300 chars, stripped |

**Validation rules:**
- `date` MUST be `≥ date(2023, 1, 1)`.
- `keyword_match` MUST be `True`; records where `False` are discarded before output.
- `source` MUST appear in `AUTHORITY_DOMAINS` values (i.e., domain was on allowlist).
- `content_type` MUST be one of the three defined enum values.
- `summary` is truncated at 300 characters; ellipsis appended if truncated.

---

### ContentType (Enum)

```python
class ContentType(str, Enum):
    STATS = "Stats / Data Points"
    SURVEY = "Survey / Research Report"
    EBOOK = "Ebook / Whitepaper"
```

String values are used verbatim as the "Content Type" column in the output file.

---

### CollectionRun

Metadata about a single CLI execution. Used for logging and summary output; not written
to the Excel/CSV file.

| Field | Type | Notes |
|---|---|---|
| `keyword` | `str` | Seed keyword as provided by user |
| `content_type_filter` | `ContentType \| None` | Value of `--type` flag; `None` = all types |
| `output_format` | `set[str]` | `{"excel"}`, `{"csv"}`, or `{"excel", "csv"}` |
| `output_paths` | `list[Path]` | Absolute paths of files written |
| `records_collected` | `int` | Count of `ResearchRecord` instances written |
| `records_excluded` | `list[tuple[str, str]]` | `(url, reason)` for each excluded result |
| `started_at` | `datetime` | UTC timestamp |
| `completed_at` | `datetime \| None` | UTC timestamp; `None` if run did not complete |

---

## State Transitions

```
SearchResult (raw)
    │
    ▼
[Domain allowlist check] ──✗──▶ excluded (reason: "domain not in allowlist")
    │ ✓
    ▼
[Date parse + validate] ──✗──▶ excluded (reason: "date unparseable" | "date before 2023")
    │ ✓
    ▼
[Keyword relevance check] ──✗──▶ excluded (reason: "keyword not in title or snippet")
    │ ✓
    ▼
[Content type classification]
    │
    ▼
ResearchRecord (valid, typed)
    │
    ▼
[Content type filter if --type set] ──✗──▶ dropped silently (not counted as excluded)
    │ ✓
    ▼
DataFrame row → Excel / CSV output
```

---

## Output Schema (Excel / CSV)

| Column | Pandas dtype | Notes |
|---|---|---|
| Title | `object` (str) | |
| Source | `object` (str) | From AUTHORITY_DOMAINS display name |
| URL | `object` (str) | |
| Date | `object` (str) | ISO 8601: `YYYY-MM-DD` (str, not datetime, for Excel compat) |
| Content Type | `object` (str) | Enum string value |
| Keyword Match | `bool` | Always `True` in output (filtered) |
| Summary | `object` (str) | Max 300 chars |

**Column order** matches the spec: Title → Source → URL → Date → Content Type →
Keyword Match → Summary.

Excel header row uses these exact column names. No index column written.
