"""Pure MDD math functions. No network calls, no MCP awareness."""

import pandas as pd

from stock_mcp.errors import NoDataError
from stock_mcp.models import MDDResult


def calculate_max_drawdown(prices: pd.Series, ticker: str) -> MDDResult:
    """Calculate Maximum Drawdown for a price series.

    Args:
        prices: pd.Series with DatetimeIndex and float price values.
        ticker: Ticker symbol string (for inclusion in the result).

    Returns:
        MDDResult with mdd_pct, peak_date, trough_date, duration, recovery info.

    Raises:
        NoDataError: If there are fewer than 2 valid price points.
    """
    # Drop NaNs first
    prices = prices.dropna()

    # Edge case: not enough data
    if len(prices) < 2:
        raise NoDataError(
            ticker=ticker,
            message=f"Need at least 2 valid price points for MDD (got {len(prices)}).",
        )

    # Edge case: constant series
    if prices.nunique() == 1:
        peak_date = prices.index[0]
        return MDDResult(
            ticker=ticker,
            mdd_pct=0.0,
            peak_date=str(peak_date.date()) if hasattr(peak_date, "date") else str(peak_date),
            trough_date=str(peak_date.date()) if hasattr(peak_date, "date") else str(peak_date),
            drawdown_duration_days=0,
            recovered=True,
            recovery_date=None,
        )

    # Main MDD algorithm
    running_max = prices.cummax()
    drawdown = prices / running_max - 1  # always <= 0

    mdd_value = float(drawdown.min())
    trough_date = drawdown.idxmin()

    # Peak is argmax of prices up to and including trough date
    peak_date = prices.loc[:trough_date].idxmax()

    # Degenerate guard: peak == trough means no observable drawdown
    if peak_date == trough_date:
        return MDDResult(
            ticker=ticker,
            mdd_pct=0.0,
            peak_date=_fmt_date(peak_date),
            trough_date=_fmt_date(trough_date),
            drawdown_duration_days=0,
            recovered=True,
            recovery_date=None,
        )

    # Recovery: first date at or after trough where price >= peak price
    peak_price = float(prices.loc[peak_date])
    post_trough = prices.loc[trough_date:]
    recovered_dates = post_trough[post_trough >= peak_price]

    if len(recovered_dates) > 0:
        recovery_date = recovered_dates.index[0]
        # If recovery_date == trough_date it means price never actually fell below peak
        # (shouldn't happen given mdd_value < 0, but guard anyway)
        recovered = True
        recovery_date_str = _fmt_date(recovery_date)
    else:
        recovered = False
        recovery_date_str = None

    duration_days = (trough_date - peak_date).days

    return MDDResult(
        ticker=ticker,
        mdd_pct=round(mdd_value, 6),
        peak_date=_fmt_date(peak_date),
        trough_date=_fmt_date(trough_date),
        drawdown_duration_days=duration_days,
        recovered=recovered,
        recovery_date=recovery_date_str,
    )


def compute_drawdown_series(prices: pd.Series) -> list[dict]:
    """Compute daily drawdown percentage series for an underwater chart.

    Args:
        prices: pd.Series with DatetimeIndex, NaNs already dropped.

    Returns:
        List of {"date": "YYYY-MM-DD", "drawdown_pct": float} dicts.
        All drawdown_pct values are <= 0.
    """
    prices = prices.dropna()
    if prices.empty:
        return []

    running_max = prices.cummax()
    drawdown = prices / running_max - 1

    result = []
    for ts, val in drawdown.items():
        date_str = str(ts.date()) if hasattr(ts, "date") else str(ts)
        result.append({"date": date_str, "drawdown_pct": round(float(val), 6)})

    return result


def _fmt_date(ts) -> str:
    """Format a pandas Timestamp or date-like to YYYY-MM-DD string."""
    if hasattr(ts, "date"):
        return str(ts.date())
    return str(ts)
