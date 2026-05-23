"""yfinance wrapper with TTL cache and price-column selector."""

import re

import pandas as pd
import yfinance as yf
from cachetools import TTLCache

from stock_mcp.errors import InvalidTickerError, NoDataError

_PRICE_CACHE: TTLCache = TTLCache(maxsize=128, ttl=300)

_CRYPTO_QUOTE_RE = re.compile(r"-([A-Z]{3,5})$")


def currency_for(market: str, ticker: str) -> str:
    """Best-effort currency code for a (market, ticker) pair."""
    if market == "kr":
        return "KRW"
    if market == "crypto":
        m = _CRYPTO_QUOTE_RE.search(ticker)
        return m.group(1) if m else "USD"
    return "USD"


def fetch_price_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Fetch OHLCV price data from Yahoo Finance with 5-minute TTL cache.

    Args:
        ticker: Uppercase ticker symbol (already validated).
        start: Start date string YYYY-MM-DD.
        end: End date string YYYY-MM-DD.

    Returns:
        DataFrame with flat columns: Open, High, Low, Close, Adj Close, Volume.
        Index is DatetimeIndex (Date).

    Raises:
        InvalidTickerError: If yfinance returns empty data.
    """
    key = (ticker, start, end)
    if key in _PRICE_CACHE:
        return _PRICE_CACHE[key].copy()

    df = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)

    # yfinance 0.2.x returns MultiIndex columns even for a single ticker
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(1, axis=1)

    if df.empty:
        raise InvalidTickerError(ticker)

    _PRICE_CACHE[key] = df
    return df.copy()


def select_price_column(df: pd.DataFrame, price: str) -> pd.Series:
    """Select the relevant price column from a fetched DataFrame.

    Args:
        df: DataFrame returned by fetch_price_data (flat columns).
        price: "adj_close" or "close".

    Returns:
        A pd.Series indexed by date with NaNs dropped.

    Raises:
        NoDataError: If the requested column is missing.
    """
    col = "Adj Close" if price == "adj_close" else "Close"
    if col not in df.columns:
        raise NoDataError(
            message=f"Column {col!r} not found in price data. Available: {list(df.columns)}"
        )
    series = df[col].dropna()
    return series
