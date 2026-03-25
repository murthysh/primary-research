# CLI Contract: Keyword-Driven Research Collector

**Branch**: `001-keyword-research-collector` | **Date**: 2026-03-24

This document defines the command-line interface contract — all commands, flags,
arguments, exit codes, and output behaviours that implementations MUST honour.

---

## Entry Point

```
python tool.py [OPTIONS]
```

or (after packaging):

```
research-collector [OPTIONS]
```

---

## Commands / Options

### `--keyword TEXT` *(required)*

The seed keyword to search for. Passed as a quoted string.

```
python tool.py --keyword "AI in healthcare"
python tool.py --keyword "digital transformation"
```

- MUST be non-empty; tool exits with code `2` and a usage error if omitted or blank.
- Spaces and special characters are supported; quote accordingly in shell.

---

### `--type [stats|survey|ebook]` *(optional)*

Filter output to a single content type.

| Value | Maps to ContentType |
|---|---|
| `stats` | Stats / Data Points |
| `survey` | Survey / Research Report |
| `ebook` | Ebook / Whitepaper |

- If omitted, all three content types are collected.
- Invalid value → exit code `2`, print valid choices.

---

### `--format [excel|csv]` *(optional, repeatable)*

Output format. May be specified once or twice.

```
python tool.py --keyword "AI in healthcare"                    # Excel only (default)
python tool.py --keyword "AI in healthcare" --format excel     # Excel only
python tool.py --keyword "AI in healthcare" --format csv       # CSV only
python tool.py --keyword "AI in healthcare" --format excel --format csv  # Both
```

- Default: `excel`
- Both formats produce the same data with the same column order.

---

### `--output PATH` *(optional)*

Override the default output file path (without extension — extension is appended per
format).

```
python tool.py --keyword "AI in healthcare" --output ./reports/ai-health
# Produces: ./reports/ai-health.xlsx (and/or .csv)
```

- Default: `./{keyword-slug}-research-{YYYY-MM-DD}` in the current working directory.
- Directory MUST exist; tool exits with code `1` and a clear message if it does not.

---

### `--verbose` / `-v` *(optional)*

Enable verbose logging (INFO level). Without this flag, only WARNING and ERROR messages
are printed to stderr.

---

### `--help`

Print usage and exit with code `0`.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SERPAPI_KEY` | Yes | SerpAPI API key. Loaded from `.env` via python-dotenv, then from shell env. |

If `SERPAPI_KEY` is absent after `.env` load:
- Print to stderr: `Error: SERPAPI_KEY environment variable is not set. Add it to a .env file or export it in your shell.`
- Exit with code `1`.

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success — output file(s) written |
| `1` | Runtime error — missing env var, output directory missing, unrecoverable API failure |
| `2` | Usage error — missing required argument, invalid option value |

---

## Stdout / Stderr Behaviour

| Stream | Content |
|---|---|
| `stdout` | Progress messages in verbose mode: `Querying mckinsey.com...`, `Found 3 results.` |
| `stderr` | WARNING and ERROR messages always; all log output in non-verbose mode |

On success, the tool prints to stdout:
```
Collected N records → output/ai-in-healthcare-research-2026-03-24.xlsx
```

On empty result:
```
Warning: No results matched the filters. Output file contains headers only.
Collected 0 records → output/ai-in-healthcare-research-2026-03-24.xlsx
```

---

## `.env` File Format

```dotenv
SERPAPI_KEY=your_serpapi_key_here
```

File location: working directory from which the tool is invoked.
The `.env` file MUST be added to `.gitignore`.

---

## Example Invocations

```bash
# Basic usage
python tool.py --keyword "AI in healthcare"

# Filter to whitepapers only, output CSV
python tool.py --keyword "digital transformation" --type ebook --format csv

# Both formats, custom output path, verbose
python tool.py --keyword "cloud adoption" --format excel --format csv \
  --output ./research/cloud-adoption -v
```
