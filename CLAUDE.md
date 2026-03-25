# primary-research Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-24

## Active Technologies

- Python 3.10+ + click, serpapi, pandas, openpyxl, requests, python-dotenv, python-dateutil, beautifulsoup4 (001-keyword-research-collector)

## Project Structure

```text
src/
tests/
```

## Commands

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/unit/ -v
pytest tests/integration/ -v   # requires SERPAPI_KEY env var

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Code Style

Python: Follow standard conventions
- Python 3.10+: use `match` statements and `X | Y` union types where idiomatic
- Type hints required on all public functions
- Dataclasses for models (`@dataclass(frozen=True)` for immutable entities)
- `click` decorators for CLI; no raw `sys.argv` parsing
- `os.replace` for atomic file writes (never write directly to final path)
- Log at INFO for progress, WARNING for skipped records, ERROR for failures
- All filter/classifier logic MUST be unit-testable without network calls

## Recent Changes

- 001-keyword-research-collector: Added Python 3.10+ + click, serpapi, pandas, openpyxl, requests

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
