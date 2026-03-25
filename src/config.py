from datetime import date

from .models import ContentType

# Hard minimum — cannot be overridden via CLI
DATE_CUTOFF = date(2023, 1, 1)

# Authority domain allowlist: domain suffix → display name
AUTHORITY_DOMAINS: dict[str, str] = {
    # Strategy & management consulting
    "gartner.com": "Gartner",
    "forrester.com": "Forrester",
    "mckinsey.com": "McKinsey & Company",
    "deloitte.com": "Deloitte",
    "pwc.com": "PwC",
    "accenture.com": "Accenture",
    "bcg.com": "BCG",
    "bain.com": "Bain & Company",
    "kpmg.com": "KPMG",
    "ey.com": "EY",
    "capgemini.com": "Capgemini",
    "oliverwyman.com": "Oliver Wyman",
    "rolandberger.com": "Roland Berger",
    # Market research & data
    "statista.com": "Statista",
    "idc.com": "IDC",
    "emarketer.com": "eMarketer",
    "nielseniq.com": "NielsenIQ",
    "ipsos.com": "Ipsos",
    "kantar.com": "Kantar",
    "mintel.com": "Mintel",
    "euromonitor.com": "Euromonitor",
    "grandviewresearch.com": "Grand View Research",
    "marketsandmarkets.com": "MarketsandMarkets",
    "451research.com": "451 Research",
    # Intergovernmental & government
    "weforum.org": "World Economic Forum",
    "worldbank.org": "World Bank",
    "imf.org": "IMF",
    "oecd.org": "OECD",
    "un.org": "United Nations",
    "who.int": "World Health Organization",
    "census.gov": "U.S. Census Bureau",
    "bls.gov": "U.S. Bureau of Labor Statistics",
    "nih.gov": "NIH",
    # Academic
    "mit.edu": "MIT",
    "harvard.edu": "Harvard University",
    "stanford.edu": "Stanford University",
    "ieee.org": "IEEE",
    # Business media
    "hbr.org": "Harvard Business Review",
    "wsj.com": "Wall Street Journal",
    "ft.com": "Financial Times",
    "economist.com": "The Economist",
    "forbes.com": "Forbes",
    "businessinsider.com": "Business Insider",
    "techcrunch.com": "TechCrunch",
    "venturebeat.com": "VentureBeat",
    "cio.com": "CIO",
    # Professional associations
    "shrm.org": "SHRM",
    "ama.org": "American Marketing Association",
}

# Domains for which filetype:pdf is appended to queries (publish structured reports as PDFs)
PDF_DOMAINS: set[str] = {
    "forrester.com",
    "deloitte.com",
    "mckinsey.com",
    "kpmg.com",
    "ey.com",
    "capgemini.com",
    "oliverwyman.com",
    "rolandberger.com",
    "worldbank.org",
    "imf.org",
    "oecd.org",
    "who.int",
    "ipsos.com",
}

# Heuristic signals per content type (matched case-insensitively)
CONTENT_TYPE_SIGNALS: dict[ContentType, list[str]] = {
    ContentType.STATS: [
        "statistic",
        "percent",
        "%",
        "survey says",
        "according to",
        "data shows",
        "report finds",
        "by 2025",
        "by 2026",
        "by 2027",
        "by 2028",
        "by 2029",
        "by 2030",
        "billion",
        "million",
        "growth rate",
        "market size",
        "cagr",
        "year-over-year",
        "yoy",
    ],
    ContentType.SURVEY: [
        "survey",
        "research",
        "report",
        "study",
        "findings",
        "analysis",
        "forecast",
        "market research",
        "industry report",
        "annual report",
        "global report",
    ],
    ContentType.EBOOK: [
        "ebook",
        "e-book",
        "whitepaper",
        "white paper",
        "guide",
        "handbook",
        "playbook",
        "download",
        "pdf",
    ],
}
