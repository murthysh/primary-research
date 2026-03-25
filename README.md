# Research Collector CLI

A Python CLI tool that collects research, stats, and reports from high-authority sources
(Gartner, McKinsey, Deloitte, PwC, Statista, HBR, and more) for a given seed keyword.
Results are exported to clean, typed Excel (`.xlsx`) or CSV files.

## Prerequisites

- Python 3.10 or later
- A [SerpAPI](https://serpapi.com) account and API key
  - **Free tier**: 100 searches/month
  - **Paid plans**: from $50/month for 5,000 searches
  - *No free alternative currently matches SerpAPI's reliability for site-restricted
    Google queries. The tool is designed with a swappable backend interface so a
    free source can be substituted if one becomes available.*

## Installation

```bash
# 1. Clone the repo and enter the project directory
git clone <repo-url>
cd primary-research

# 2. (Recommended) Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root (it is already listed in `.gitignore`):

```bash
cp .env.example .env
# Then edit .env and replace the placeholder with your real key:
# SERPAPI_KEY=your_actual_serpapi_key_here
```

## Usage

### Basic collection

```bash
python tool.py --keyword "AI in healthcare"
```

Produces: `ai-in-healthcare-research-YYYY-MM-DD.xlsx`

### Filter by content type

```bash
python tool.py --keyword "digital transformation" --type ebook
python tool.py --keyword "digital transformation" --type survey
python tool.py --keyword "digital transformation" --type stats
```

Valid values: `stats` · `survey` · `ebook`

### Export to CSV instead of (or in addition to) Excel

```bash
# CSV only
python tool.py --keyword "AI in healthcare" --format csv

# Both Excel and CSV
python tool.py --keyword "AI in healthcare" --format excel --format csv
```

### Custom output path

```bash
python tool.py --keyword "cloud adoption" --output ./reports/cloud-adoption
# Produces: ./reports/cloud-adoption.xlsx
```

### Verbose logging

```bash
python tool.py --keyword "AI in healthcare" --verbose
```

### Full help

```bash
python tool.py --help
```

## Authority Sources

Results are restricted to **48 high-authority domains** across six categories:

### Strategy & Management Consulting
| Source | Domain |
|---|---|
| Gartner | gartner.com |
| Forrester | forrester.com |
| McKinsey & Company | mckinsey.com |
| Deloitte | deloitte.com |
| PwC | pwc.com |
| Accenture | accenture.com |
| BCG | bcg.com |
| Bain & Company | bain.com |
| KPMG | kpmg.com |
| EY | ey.com |
| Capgemini | capgemini.com |
| Oliver Wyman | oliverwyman.com |
| Roland Berger | rolandberger.com |

### Market Research & Data
| Source | Domain |
|---|---|
| Statista | statista.com |
| IDC | idc.com |
| eMarketer | emarketer.com |
| NielsenIQ | nielseniq.com |
| Ipsos | ipsos.com |
| Kantar | kantar.com |
| Mintel | mintel.com |
| Euromonitor | euromonitor.com |
| Grand View Research | grandviewresearch.com |
| MarketsandMarkets | marketsandmarkets.com |
| 451 Research | 451research.com |

### Intergovernmental & Government
| Source | Domain |
|---|---|
| World Economic Forum | weforum.org |
| World Bank | worldbank.org |
| IMF | imf.org |
| OECD | oecd.org |
| United Nations | un.org |
| World Health Organization | who.int |
| U.S. Census Bureau | census.gov |
| U.S. Bureau of Labor Statistics | bls.gov |
| NIH | nih.gov |

### Academic
| Source | Domain |
|---|---|
| Harvard Business Review | hbr.org |
| MIT | mit.edu |
| Harvard University | harvard.edu |
| Stanford University | stanford.edu |
| IEEE | ieee.org |

### Business Media
| Source | Domain |
|---|---|
| Wall Street Journal | wsj.com |
| Financial Times | ft.com |
| The Economist | economist.com |
| Forbes | forbes.com |
| Business Insider | businessinsider.com |
| TechCrunch | techcrunch.com |
| VentureBeat | venturebeat.com |
| CIO | cio.com |

### Professional Associations
| Source | Domain |
|---|---|
| SHRM | shrm.org |
| American Marketing Association | ama.org |

## Output Columns

| Column | Description |
|---|---|
| Title | Article or report title |
| Source | Authority source display name |
| URL | Full URL |
| Date | Publication date (YYYY-MM-DD) |
| Content Type | Stats / Data Points · Survey / Research Report · Ebook / Whitepaper |
| Keyword Match | Always `TRUE` (all exported rows match the keyword) |
| Summary | SerpAPI snippet, max 300 characters |

## Running Tests

```bash
# Unit tests (no API key required)
pytest tests/unit/ -v

# Integration tests (requires SERPAPI_KEY in environment)
pytest tests/integration/ -v

# All tests
pytest -v
```

## Development

```bash
pip install -r requirements-dev.txt

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Web UI (Streamlit)

A password-protected browser interface is available as an alternative to the CLI.

### Run locally

```bash
# 1. Install dependencies (includes streamlit)
pip install -r requirements.txt

# 2. Create secrets file
mkdir -p .streamlit
# Edit .streamlit/secrets.toml and set:
#   APP_PASSWORD = "your_team_password"
#   SERPAPI_KEY  = "your_serpapi_key"

# 3. Start the app
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`. Enter your password to access the UI.

### Deploy to Streamlit Community Cloud

1. Push to GitHub (ensure `.streamlit/secrets.toml` is in `.gitignore` — it already is).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → select repo, branch (`main`), main file: `streamlit_app.py`.
4. Under **Advanced settings → Secrets**, paste:
   ```
   APP_PASSWORD = "your_team_password"
   SERPAPI_KEY  = "your_serpapi_key"
   ```
5. Click **Deploy** and share the generated URL with your team.

See `specs/002-streamlit-web-ui/quickstart.md` for the full validation checklist.

---

## Date Filter

All results are strictly filtered to **2023-01-01 or later**. This cutoff is enforced
both in the SerpAPI query (`after:2023-01-01`) and in post-processing validation.
Records with missing or unparseable dates are excluded with a warning.
