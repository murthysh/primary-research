# Quickstart: Keyword-Driven Research Collector CLI

**Branch**: `001-keyword-research-collector` | **Date**: 2026-03-24

Use this guide to validate the implementation end-to-end after tasks are complete.

---

## Prerequisites

- Python 3.10 or later
- A SerpAPI account with an API key ([serpapi.com](https://serpapi.com))
- Git (to clone/checkout the branch)

---

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Expected packages: `serpapi` (or `google-search-results`), `pandas`, `openpyxl`,
`requests`, `beautifulsoup4`, `python-dotenv`, `python-dateutil`, `click`.

---

## 2. Configure API Key

Create a `.env` file in the project root:

```bash
echo "SERPAPI_KEY=your_actual_key_here" > .env
```

Verify it is listed in `.gitignore`:

```bash
grep ".env" .gitignore   # should print ".env"
```

---

## 3. Run Basic Collection (User Story 1 — P1 MVP)

```bash
python tool.py --keyword "AI in healthcare"
```

**Expected output:**

```
Querying gartner.com...
Querying mckinsey.com...
...
Collected 12 records → ai-in-healthcare-research-2026-03-24.xlsx
```

**Validate the file:**

1. Open `ai-in-healthcare-research-2026-03-24.xlsx` in Excel or LibreOffice.
2. Confirm columns: Title | Source | URL | Date | Content Type | Keyword Match | Summary.
3. Confirm all rows in Date column are ≥ 2023-01-01.
4. Confirm all rows in Source column match known authority names (McKinsey, Gartner, etc.).
5. Confirm Keyword Match column contains only `TRUE`.

---

## 4. Test Content Type Filter (User Story 2 — P2)

```bash
python tool.py --keyword "AI in healthcare" --type ebook
```

**Expected:** Output file contains only rows where Content Type = "Ebook / Whitepaper".

```bash
python tool.py --keyword "AI in healthcare" --type stats
```

**Expected:** Output file contains only rows where Content Type = "Stats / Data Points".

---

## 5. Test CSV Export (User Story 3 — P3)

```bash
python tool.py --keyword "AI in healthcare" --format csv
```

**Expected:**
- File `ai-in-healthcare-research-2026-03-24.csv` is created.
- Open in a text editor: first line is the header row, encoding is UTF-8 with BOM
  (`EF BB BF` as first three bytes).

```bash
python tool.py --keyword "AI in healthcare" --format excel --format csv
```

**Expected:** Both `.xlsx` and `.csv` files are produced.

---

## 6. Test Error Handling

**Missing API key:**

```bash
unset SERPAPI_KEY   # or remove from .env temporarily
python tool.py --keyword "AI in healthcare"
```

**Expected:** Exit code 1, message: `Error: SERPAPI_KEY environment variable is not set.`

**Invalid content type:**

```bash
python tool.py --keyword "AI in healthcare" --type invalid
```

**Expected:** Exit code 2, message listing valid choices: `stats`, `survey`, `ebook`.

---

## 7. Run Unit Tests

```bash
pytest tests/unit/ -v
```

All tests should pass. Key test modules:
- `tests/unit/test_filter.py` — date filter, domain allowlist, keyword relevance
- `tests/unit/test_classifier.py` — content type heuristic signals
- `tests/unit/test_writer.py` — DataFrame construction, atomic write, column types

---

## 8. Run Integration Tests (requires valid SERPAPI_KEY)

```bash
pytest tests/integration/ -v
```

Integration tests make real SerpAPI calls; results vary by quota and live search index.
Mark expected to pass: at least one result returned for a common keyword like "AI".

---

## Validation Checklist

- [ ] `requirements.txt` installs cleanly in a fresh virtualenv
- [ ] `.env` file loads correctly; `SERPAPI_KEY` absence produces clear error
- [ ] Basic collection produces a non-empty `.xlsx` with correct 7 columns
- [ ] All output dates are ≥ 2023-01-01
- [ ] All output sources are from the authority domain list
- [ ] `--type` flag filters correctly to one content type
- [ ] `--format csv` produces UTF-8-BOM CSV with same data as Excel
- [ ] `--format excel --format csv` produces both files
- [ ] Retry logic handles transient errors (mock test in integration suite)
- [ ] `pytest tests/unit/` passes with zero failures
