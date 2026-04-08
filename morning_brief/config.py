"""
config.py – Institutional Credit & Equity Intelligence System Configuration.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Secrets & Credentials ───────────────────────────────────────────────────
# You MUST add FRED_API_KEY and FINNHUB_API_KEY to your .env for full data coverage.
NEWSAPI_KEY: str = os.getenv("NEWSAPI_KEY", "")
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
GMAIL_ADDRESS: str = os.getenv("GMAIL_ADDRESS", "")
REPORT_TIME: str = os.getenv("REPORT_TIME", "06:30")

# Institutional-grade data keys
FRED_API_KEY: str = os.getenv("FRED_API_KEY", "")
FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")

# ── Recipients (Institutional Distribution List) ────────────────────────────
RECIPIENTS: list = [
    "sidmalireddi10@gmail.com",
]

# ── AI Backend (OpenAI SDK → GitHub Copilot inference via Azure) ────────────────
GITHUB_AI_BASE_URL: str = "https://models.inference.ai.azure.com"
GITHUB_AI_MODEL: str = "gpt-4o"

# ── Database & Paths ─────────────────────────────────────────────────────────
DB_PATH: str = os.path.join(os.path.dirname(__file__), "news.db")
OUTPUT_DIR: str = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Institutional Industry Sectors & Sector ETFs ────────────────────────────
# Mapping industries to their corresponding "State Street Global Advisors" SPDR ETFs.
SECTOR_ETFS: dict[str, str] = {
    "Tech": "XLK",
    "Energy": "XLE",
    "Healthcare": "XLV",
    "Financials": "XLF",
    "Consumer": "XLY", # Consumer Discretionary
}

SECTORS: dict[str, list[str]] = {
    "Tech": [
        "NVIDIA", "HBM", "High Bandwidth Memory", "semiconductor", "ASIC", 
        "Edge AI", "SaaS churn", "hyperscaler", "cloud", "LLM training",
        "cybersecurity insurance", "fabless", "Microsoft", "Apple", "Google",
        "Meta", "chip", "multi-cloud", "enterprise spend",
    ],
    "Energy": [
        "WTI", "Brent", "refining margin", "rig count", "LNG export",
        "shale efficiency", "upstream", "downstream", "OPEC+", "Exxon",
        "crude oil", "natural gas", "energy infrastructure", "CAPEX",
        "pipeline", "renewables", "carbon credits",
    ],
    "Healthcare": [
        "GLP-1", "patent cliff", "Phase III", "clinical trial", "FDA",
        "biotech", "Pharma", "Medicare reimbursement", "orphan drug",
        "CRO", "MedTech", "CDMO", "biosimilar", "Pfizer", "Moderna",
        "Eli Lilly", "Novo Nordisk", "drug pricing",
    ],
    "Financials": [
        "Net Interest Margin", "NIM", "yield curve", "credit spread",
        "Federal Reserve", "interest rates", "Basel III", "CRE exposure",
        "private credit", "M&A backlog", "CET1", "liquidity coverage",
        "JPMorgan", "Fed", "Treasury", "inflation", "CPI", "bank earnings",
    ],
    "Consumer": [
        "same-store sales", "inventory destocking", "trading down",
        "credit card delinquency", "omni-channel", "ad spend", "retail",
        "luxury resilience", "DTC", "Amazon", "Walmart", "consumer spending",
        "discretionary", "Target", "Nike", "consumer confidence",
    ],
}

# ── Global Institutional RSS Feeds ──────────────────────────────────────────
RSS_FEEDS: list[str] = [
    "http://feeds.marketwatch.com/marketwatch/topstories/",
    "https://fortune.com/feed/",
    "https://www.investing.com/rss/news_301.rss",
    "http://rss.cnn.com/rss/money_topstories.rss",
    "https://www.cnbc.com/id/10001147/device/rss/rss.html",
    "https://www.cnbc.com/id/15839135/device/rss/rss.html",
]

# ── NewsAPI Settings ──────────────────────────────────────────────────────────
NEWSAPI_BASE_URL: str = "https://newsapi.org/v2/everything"
NEWSAPI_PAGE_SIZE: int = 100
