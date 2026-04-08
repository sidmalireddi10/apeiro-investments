"""
news_ingestion.py – Institutional Data Ingestion with "Sweep" Strategy and Forensic Deduplication.
"""

import sqlite3
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List

import requests
import feedparser

from config import (
    NEWSAPI_KEY,
    NEWSAPI_BASE_URL,
    NEWSAPI_PAGE_SIZE,
    RSS_FEEDS,
    SECTORS,
    DB_PATH,
)

logger = logging.getLogger(__name__)


# ── Database Helpers ──────────────────────────────────────────────────────────

def init_db() -> sqlite3.Connection:
    """Create the articles, sentiment, and trade log tables."""
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Articles Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            url         TEXT    UNIQUE NOT NULL,
            title       TEXT,
            description TEXT,
            source      TEXT,
            sector      TEXT,
            published   TEXT,
            fetched_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    
    # 2. Sentiment History (For Trend Analysis)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT    DEFAULT (date('now')),
            sector      TEXT,
            score       REAL,
            article_count INTEGER,
            narrative_summary TEXT
        )
    """)
    
    # 3. Trade Log (For Accountability)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trade_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    DEFAULT (datetime('now')),
            asset       TEXT,
            type        TEXT,
            view        TEXT,
            thesis      TEXT,
            entry_price REAL    DEFAULT 0,
            status      TEXT    DEFAULT 'PENDING' -- PENDING, WIN, LOSS, CLOSED
        )
    """)
    
    conn.commit()
    return conn


def article_exists(conn: sqlite3.Connection, url: str) -> bool:
    cur = conn.execute("SELECT 1 FROM articles WHERE url = ?", (url,))
    return cur.fetchone() is not None


def insert_article(
    conn: sqlite3.Connection,
    url: str,
    title: str,
    description: str,
    source: str,
    sector: str,
    published: str,
) -> None:
    try:
        conn.execute(
            """
            INSERT INTO articles (url, title, description, source, sector, published)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (url, title[:500], description[:1000], source[:100], sector, published),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass


# ── Sector Tagger ─────────────────────────────────────────────────────────────

def tag_sector(title: str, description: str) -> str:
    """Return the best-matching sector name, or 'General' if none match."""
    combined = f"{title} {description}".lower()
    scores: dict[str, int] = {sector: 0 for sector in SECTORS}
    for sector, keywords in SECTORS.items():
        for kw in keywords:
            if kw.lower() in combined:
                scores[sector] += 1
    best = max(scores, key=lambda s: scores[s])
    return best if scores[best] > 0 else "General"


# ── NewsAPI Fetcher (Platinum Sweep Strategy) ────────────────────────────────

def fetch_newsapi(conn: sqlite3.Connection) -> int:
    """
    Fetch articles from NewsAPI using the Multi-Sweep strategy.
    Breaks keywords into chunks to maximize NewsAPI free-tier coverage.
    """
    if not NEWSAPI_KEY:
        logger.warning("NEWSAPI_KEY not set – skipping NewsAPI fetch.")
        return 0

    since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    total_new = 0

    for sector, keywords in SECTORS.items():
        # Split keywords into chunks of 5 for optimal NewsAPI balance
        keyword_chunks: List[List[str]] = [keywords[i:i + 5] for i in range(0, len(keywords), 5)]
        
        for i, chunk in enumerate(keyword_chunks):
            query = " OR ".join(f'"{kw}"' if " " in kw else kw for kw in chunk)
            api_key = NEWSAPI_KEY.strip("'\"")
            params = {
                "q": query,
                "from": since,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 20, # Fetch top 20 for EACH sweep chunk
                "apiKey": api_key,
            }
            try:
                resp = requests.get(NEWSAPI_BASE_URL, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                articles = data.get("articles", [])
                
                chunk_new = 0
                for art in articles:
                    url = art.get("url", "")
                    if not url or article_exists(conn, url):
                        continue
                    
                    title = art.get("title") or ""
                    description = art.get("description") or ""
                    source = art.get("source", {}).get("name", "NewsAPI")
                    published = art.get("publishedAt", "")
                    insert_article(conn, url, title, description, source, sector, published)
                    chunk_new += 1
                    total_new += 1
                
                logger.info(f"[NewsAPI] Sweep {i+1} for {sector}: Found {chunk_new} new articles.")
                time.sleep(1.0) # Polite to API rate limits
                
            except Exception as exc:
                logger.error(f"[NewsAPI] Sweep {i+1} failed for {sector}: {exc}")

    logger.info(f"[NewsAPI] Platinum Sweep complete. Total new: {total_new}")
    return total_new


def fetch_top_headlines(conn: sqlite3.Connection) -> int:
    """
    Fetch the absolute latest global business news from top-tier sources.
    This ensures 'Ever-Fresh' news regardless of niche keyword performance.
    """
    if not NEWSAPI_KEY:
        return 0

    total_new = 0
    params = {
        "category": "business",
        "language": "en",
        "pageSize": 40,
        "apiKey": NEWSAPI_KEY.strip("'\""),
    }
    try:
        url = "https://newsapi.org/v2/top-headlines"
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        
        for art in articles:
            url_val = art.get("url", "")
            if not url_val or article_exists(conn, url_val):
                continue
            
            title = art.get("title") or ""
            description = art.get("description") or ""
            source = art.get("source", {}).get("name", "Global News")
            published = art.get("publishedAt", "")
            
            # Tag sector based on content for these general headlines
            sector = tag_sector(title, description)
            insert_article(conn, url_val, title, description, source, sector, published)
            total_new += 1
            
        logger.info(f"[NewsAPI] Global Headlines: Found {total_new} fresh articles.")
    except Exception as exc:
        logger.error(f"[NewsAPI] Global Headlines fetch failed: {exc}")

    return total_new


# ── RSS Fetcher ───────────────────────────────────────────────────────────────

def fetch_rss(conn: sqlite3.Connection) -> int:
    """Fetch articles from all configured RSS feeds."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    total_new = 0

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            source_name = feed.feed.get("title", feed_url)
            logger.info(f"[RSS] Parsing '{source_name}': {len(feed.entries)} entries.")
            for entry in feed.entries:
                url = entry.get("link", "")
                if not url or article_exists(conn, url):
                    continue
                
                title = entry.get("title", "")
                description = entry.get("summary", entry.get("description", ""))
                
                published_parsed = entry.get("published_parsed")
                if published_parsed:
                    published_dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                    if published_dt < cutoff:
                        continue
                    published_str = published_dt.isoformat()
                else:
                    published_str = datetime.now(timezone.utc).isoformat()

                sector = tag_sector(title, description)
                insert_article(conn, url, title, description, source_name, sector, published_str)
                total_new += 1
        except Exception as exc:
            logger.error(f"[RSS] Error fetching {feed_url}: {exc}")

    logger.info(f"[RSS] Total new articles stored: {total_new}")
    return total_new


# ── Public Interface ──────────────────────────────────────────────────────────

def fetch_all_news() -> int:
    """Ingest new articles into the expanded fund database."""
    logger.info("=== Starting Institutional Ingestion (Platinum + Global Sweep) ===")
    conn = init_db()
    total = 0
    total += fetch_newsapi(conn)
    total += fetch_top_headlines(conn)
    total += fetch_rss(conn)
    conn.close()
    logger.info(f"=== Ingestion complete. {total} new signals stored. ===")
    return total


def get_articles_by_sector(hours: int = 24) -> dict[str, list[dict]]:
    """Retrieve recently stored articles grouped by sector."""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    conn = init_db()
    cur = conn.execute(
        """
        SELECT sector, title, description, source, url, published
        FROM articles
        WHERE published >= ?
        ORDER BY sector, published DESC
        """,
        (since,),
    )
    rows = cur.fetchall()
    conn.close()

    result: dict[str, list[dict]] = {}
    for sector, title, description, source, url, published in rows:
        result.setdefault(sector, []).append({
            "title": title, "description": description, "source": source,
            "url": url, "published": published
        })
    return result
