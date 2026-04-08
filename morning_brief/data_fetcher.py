"""
data_fetcher.py – Institutional Data Module (yfinance, FRED, Finnhub).
Fetches market prices, macro indicators, and corporate earnings.
"""

import logging
from datetime import datetime, timedelta
import yfinance as yf
try:
    from fredapi import Fred
except ImportError:
    Fred = None
try:
    import finnhub
except ImportError:
    finnhub = None
import pandas as pd

from config import (
    FRED_API_KEY,
    FINNHUB_API_KEY,
    SECTOR_ETFS,
)

logger = logging.getLogger(__name__)

def fetch_market_dashboard() -> dict:
    """
    Fetch SPY, QQQ, VIX, Oil, and Sector ETFs data.
    """
    tickers = ["SPY", "QQQ", "^VIX", "CL=F"] + list(SECTOR_ETFS.values())
    data = {}
    
    logger.info(f"[Data] Fetching market prices for {tickers}...")
    try:
        # Fetch data for the last 5 days to ensure we have at least 2 close prices
        df = yf.download(tickers, period="5d", interval="1d", progress=False)
        
        if df.empty:
            logger.warning("[Data] yfinance returned no data.")
            return {}

        # Robust column lookup: fallback to 'Close' if 'Adj Close' is missing (common in some yfinance versions)
        if 'Adj Close' in df.columns:
            close_prices = df['Adj Close']
        elif 'Close' in df.columns:
            close_prices = df['Close']
        else:
            logger.warning("[Data] yfinance returned data but 'Adj Close'/'Close' columns are missing.")
            return {}
        
        for ticker in tickers:
            # Handle MultiIndex if necessary (yfinance download can return MultiIndex)
            if isinstance(close_prices, pd.DataFrame) and ticker in close_prices.columns:
                ticker_series = close_prices[ticker].dropna()
            elif isinstance(close_prices, pd.Series):
                ticker_series = close_prices.dropna()
            else:
                ticker_series = [] # Fallback
                
            if len(ticker_series) >= 2:
                current = ticker_series.iloc[-1]
                prev = ticker_series.iloc[-2]
                pct_change = ((current - prev) / prev) * 100
                data[ticker] = {
                    "price": current,
                    "change": pct_change
                }
            else:
                data[ticker] = {"price": 0, "change": 0}
                
    except Exception as exc:
        logger.error(f"[Data] yfinance fetch failed: {exc}")
        
    return data

def fetch_macro_indicators() -> dict:
    """
    Fetch 10Y-2Y Spread and Credit Spreads from FRED.
    """
    if not FRED_API_KEY or not Fred:
        logger.warning("[Data] FRED key missing or library not installed. Skipping macro data.")
        return {}

    logger.info("[Data] Fetching FRED macro indicators...")
    try:
        fred = Fred(api_key=FRED_API_KEY.strip("'\""))
        # T10Y2Y: 10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity
        # BAMLH0A0HYM2: ICE BofA US High Yield Index Option-Adjusted Spread
        ten_two = fred.get_series('T10Y2Y').iloc[-1]
        hy_spread = fred.get_series('BAMLH0A0HYM2').iloc[-1]
        
        return {
            "ten_two_spread": ten_two,
            "hy_spread": hy_spread,
            "recession_signal": "INVERTED" if ten_two < 0 else "NORMAL"
        }
    except Exception as exc:
        logger.error(f"[Data] FRED fetch failed: {exc}")
        return {}

def fetch_earnings_calendar() -> list:
    """
    Fetch earnings for the next 7 days using Finnhub.
    """
    if not FINNHUB_API_KEY or not finnhub:
        logger.warning("[Data] Finnhub key missing or library not installed. Skipping earnings.")
        return []

    logger.info("[Data] Fetching Finnhub earnings calendar...")
    try:
        client = finnhub.Client(api_key=FINNHUB_API_KEY.strip("'\""))
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        earnings = client.earnings_calendar(_from=start_date, to=end_date, symbol="", international=False)
        return earnings.get('earningsCalendar', [])
    except Exception as exc:
        logger.error(f"[Data] Finnhub fetch failed: {exc}")
        return []

def get_institutional_data_package() -> dict:
    """
    Orchestrate full data package for the AI and Report.
    """
    dashboard = fetch_market_dashboard()
    macro = fetch_macro_indicators()
    earnings = fetch_earnings_calendar()
    
    return {
        "dashboard": dashboard,
        "macro": macro,
        "earnings": earnings,
        "timestamp": datetime.now().isoformat()
    }
