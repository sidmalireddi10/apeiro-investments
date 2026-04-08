"""
main.py – Institutional Intelligence Orchestrator.
Pipeline:
  1. Fetch News (Sweep Strategy)
  2. Fetch Market Data (Price/Macro/Earnings)
  3. AI Analysis (Stateful/Normalized)
  4. PDF Generation (Dashboad/Dossier)
  5. Email Delivery
"""

import logging
import time
import sqlite3
from datetime import datetime

import schedule
from typing import Optional

from config import REPORT_TIME, DB_PATH
from news_ingestion import fetch_all_news, get_articles_by_sector
from data_fetcher import get_institutional_data_package
from ai_processing import analyse_news
from pdf_generator import generate_pdf
from email_delivery import send_report

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s – %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


# ── Database Persistence ──────────────────────────────────────────────────────

def persist_sentiment(analysis: dict) -> None:
    """Store sector scores in history for trend analysis."""
    try:
        conn = sqlite3.connect(DB_PATH)
        sectors = analysis.get("sectors", {})
        for sector, data in sectors.items():
            score = data.get("score", 50)
            conn.execute(
                "INSERT INTO sentiment_history (sector, score, article_count) VALUES (?, ?, ?)",
                (sector, score, len(data.get("article_sentiments", [])))
            )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.error(f"[Main] Failed to persist sentiment: {exc}")

def persist_trades(analysis: dict) -> None:
    """Log trade ideas for historical accountability."""
    try:
        conn = sqlite3.connect(DB_PATH)
        trades = analysis.get("trade_ideas", [])
        for t in trades:
            conn.execute(
                "INSERT INTO trade_log (asset, type, view, thesis) VALUES (?, ?, ?, ?)",
                (t.get("asset"), t.get("type"), t.get("view"), t.get("rationale"))
            )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.error(f"[Main] Failed to persist trades: {exc}")


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_pipeline() -> None:
    """Execute the Fund Research Protocol."""
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("APEIRO INVESTMENTS — INSTITUTIONAL BRIEF START")
    logger.info("=" * 60)

    # ── Step 1: Data Gathering (News + Market) ────────────────────────────────
    logger.info("STEP 1/5 – Data Gathering")
    new_articles = fetch_all_news()
    market_package = get_institutional_data_package()
    
    # Retrieve news signals
    articles_by_sector = get_articles_by_sector(hours=24)
    total_articles = sum(len(v) for v in articles_by_sector.values())
    logger.info(f"  ✔ Ingested {new_articles} new articles.")
    logger.info(f"  ✔ Total context: {total_articles} articles across {len(articles_by_sector)} sectors.")

    # ── Step 2: AI Institutional Analysis ─────────────────────────────────────
    logger.info("STEP 2/5 – AI Forensic Analysis")
    analysis = analyse_news(articles_by_sector, market_package)
    if not analysis:
        logger.error("  ✘ AI Analysis failed.")
        return

    # ── Step 3: Persistence (Memory & Accountability) ─────────────────────────
    logger.info("STEP 3/5 – Historical Persistence")
    persist_sentiment(analysis)
    persist_trades(analysis)

    # ── Step 4: PDF Generation ────────────────────────────────────────────────
    logger.info("STEP 4/5 – Premium PDF Generation")
    pdf_path = generate_pdf(analysis, market_package)
    logger.info(f"  ✔ PDF saved: {pdf_path}")

    # ── Step 5: Email Delivery ────────────────────────────────────────────────
    logger.info("STEP 5/5 – Email Delivery")
    if pdf_path:
        success = send_report(pdf_path)
        if success: logger.info("  ✔ Report dispatched successfully.")
        else: logger.warning("  ⚠ Dispatch failed.")

    elapsed = (datetime.now() - start).total_seconds()
    logger.info(f"PIPELINE COMPLETE in {elapsed:.1f}s")
    logger.info("=" * 60)


# ── Main Entry ────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("Apeiro Fund Intelligence scheduler active.")
    run_pipeline() # Startup run
    schedule.every().day.at(REPORT_TIME).do(run_pipeline)
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
