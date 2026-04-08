"""
ai_processing.py – Institutional Analysis with Normalized Scoring and Data Integration.
"""

import json
import logging
import sqlite3
from typing import Dict, List, Any

from openai import OpenAI
from config import (
    GITHUB_TOKEN,
    GITHUB_AI_BASE_URL,
    GITHUB_AI_MODEL,
    DB_PATH,
)

logger = logging.getLogger(__name__)

# ── Institutional Analysis Prompt ─────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a Senior Portfolio Manager at a multi-strategy hedge fund (Apeiro Investments).
Your goal is to transform raw news headlines and hard market data into forensic market intelligence.

GUIDELINES:
1. **Normalized Scoring**: For every article, assign a forensic sentiment score (+1 for Bullish, -1 for Bearish, 0 for Neutral).
2. **Sector Index (0-100)**: Provide an aggregated score for each sector where 0 is Distressed/Bearish, 50 is Neutral, and 100 is Strongly Bullish.
3. **Credit & Equity Focus**: Distinguish between impact on share prices (Equity) and debt/solvency (Credit).
4. **Actionable Trade Ideas**: Provide "High Conviction" ideas with:
   - **Entry Rationale**: Why now specifically?
   - **Invalidation Point**: What data would break your thesis?
   - **Time Horizon**: Tactical (days) vs Strategic (months).
5. **Data Integration**: Use the provided Market Prices and Macro Data (Yields, Spreads) to ground your narrative in reality.

Structure your response as a valid JSON object:
{
  "market_tone": "Summary including specific market figures...",
  "sectors": {
    "SectorName": {
      "score": 75,
      "tone": "Brief sector summary",
      "equity_outlook": "Growth catalysts...",
      "credit_outlook": "Debt/Spread outlook...",
      "article_sentiments": [{"title": "...", "sentiment": 1}],
      "niche_signals": [
        {"signal": "Signal Headline", "description": "Detailed forensic explanation of why this matters..."}
      ]
    }
  },
  "trade_ideas": [
    {"asset": "...", "type": "Equity/Credit", "view": "Long/Short", "rationale": "...", "invalidation": "...", "horizon": "..."}
  ],
  "macro_analysis": "Forensic look at 10Y-2Y spread and Credit Spreads..."
}
"""

def get_recent_history() -> str:
    """Retrieve last 2 valid sentiment scores per sector for historical context."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("""
            SELECT sector, score, date 
            FROM sentiment_history 
            ORDER BY date DESC LIMIT 10
        """)
        rows = cur.fetchall()
        conn.close()
        if not rows: return "No historical data available."
        return str(rows)
    except:
        return ""

def analyse_news(sector_data: Dict[str, List[Dict[str, Any]]], market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform forensic analysis on news and market data.
    """
    if not GITHUB_TOKEN:
        logger.error("[AI] GITHUB_TOKEN missing.")
        return {}

    history = get_recent_history()
    
    # Construct context
    context_parts = []
    context_parts.append(f"### MARKET DATA DASHBOARD: {market_data.get('dashboard', {})}")
    context_parts.append(f"### MACRO INDICATORS: {market_data.get('macro', {})}")
    context_parts.append(f"### HISTORICAL SENTIMENT: {history}")
    
    for sector, articles in sector_data.items():
        context_parts.append(f"### SECTOR: {sector}")
        for art in articles[:8]: # Institutional quality: process top 8 most relevant
            context_parts.append(f"- [{art.get('source')}] {art.get('title')}: {art.get('description', '')[:200]}")

    prompt_body = "\n".join(context_parts)
    
    try:
        client = OpenAI(base_url=GITHUB_AI_BASE_URL, api_key=GITHUB_TOKEN.strip("'\""))

        import time
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=GITHUB_AI_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Analyze this institutional data package:\n\n{prompt_body}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    time.sleep((attempt + 1) * 60)
                else:
                    raise e
    except Exception as exc:
        logger.error(f"[AI] Analysis failed: {exc}")
        return {}
