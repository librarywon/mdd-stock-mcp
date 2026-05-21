"""FastMCP server with 4 stock MDD analysis tools."""

import math

from fastmcp import FastMCP
from pydantic import ValidationError

from stock_mcp.data import fetch_price_data, select_price_column
from stock_mcp.errors import StockMCPError
from stock_mcp.mdd import calculate_max_drawdown as _calc_mdd
from stock_mcp.mdd import compute_drawdown_series
from stock_mcp.models import CompareQuery, StockQuery

mcp = FastMCP(
    "stock-mcp",
    instructions=(
        "US stock Maximum Drawdown analytics. "
        "Pass ticker + date range. Returns JSON data for charting."
    ),
)


# ---------------------------------------------------------------------------
# Plain business-logic functions (importable and directly callable in tests)
# ---------------------------------------------------------------------------

def calculate_mdd(
    ticker: str,
    start: str,
    end: str,
    price: str = "adj_close",
) -> dict:
    """Calculate Maximum Drawdown for a US stock.

    Returns MDD percentage, peak/trough dates, duration, and recovery info.
    Use this for single-stock drawdown analysis.

    Args:
        ticker: US stock ticker symbol (e.g. "AAPL", "SPY")
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        price: Price basis - "adj_close" (default, dividend-adjusted) or "close"
    """
    try:
        q = StockQuery(ticker=ticker, start=start, end=end, price=price)
        df = fetch_price_data(q.ticker, q.start, q.end)
        series = select_price_column(df, q.price)
        result = _calc_mdd(series, q.ticker)
        return result.model_dump(mode="json")
    except ValidationError as e:
        return {"error": True, "error_type": "ValidationError", "message": str(e)}
    except StockMCPError as e:
        return {"error": True, "error_type": type(e).__name__, "message": str(e)}


def get_price_history(
    ticker: str,
    start: str,
    end: str,
    price: str = "adj_close",
) -> dict:
    """Get historical price data for a US stock.

    Returns OHLCV time series as JSON. Use for charting price history.

    Args:
        ticker: US stock ticker symbol
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        price: Price basis - "adj_close" (default) or "close"
    """
    try:
        q = StockQuery(ticker=ticker, start=start, end=end, price=price)
        df = fetch_price_data(q.ticker, q.start, q.end)

        col = "Adj Close" if q.price == "adj_close" else "Close"

        rows = []
        for ts, row in df.iterrows():
            date_str = str(ts.date()) if hasattr(ts, "date") else str(ts)
            close_val = row.get(col)
            rows.append(
                {
                    "date": date_str,
                    "open": _safe_float(row.get("Open")),
                    "high": _safe_float(row.get("High")),
                    "low": _safe_float(row.get("Low")),
                    "close": _safe_float(close_val),
                    "volume": _safe_int(row.get("Volume")),
                }
            )

        return {
            "ticker": q.ticker,
            "price_basis": q.price,
            "count": len(rows),
            "data": rows,
        }
    except ValidationError as e:
        return {"error": True, "error_type": "ValidationError", "message": str(e)}
    except StockMCPError as e:
        return {"error": True, "error_type": type(e).__name__, "message": str(e)}


def get_drawdown_series(
    ticker: str,
    start: str,
    end: str,
    price: str = "adj_close",
) -> dict:
    """Get daily drawdown percentage series for underwater chart.

    Each day's value = current_price / running_peak - 1 (always <= 0).
    Use this to plot an 'underwater chart' showing drawdown depth over time.

    Args:
        ticker: US stock ticker symbol
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        price: Price basis - "adj_close" (default) or "close"
    """
    try:
        q = StockQuery(ticker=ticker, start=start, end=end, price=price)
        df = fetch_price_data(q.ticker, q.start, q.end)
        series = select_price_column(df, q.price)
        data = compute_drawdown_series(series)
        return {
            "ticker": q.ticker,
            "price_basis": q.price,
            "count": len(data),
            "data": data,
        }
    except ValidationError as e:
        return {"error": True, "error_type": "ValidationError", "message": str(e)}
    except StockMCPError as e:
        return {"error": True, "error_type": type(e).__name__, "message": str(e)}


def compare_mdd(
    tickers: list[str],
    start: str,
    end: str,
    price: str = "adj_close",
) -> dict:
    """Compare Maximum Drawdown across multiple US stocks.

    Returns MDD results for each ticker. Use for side-by-side comparison.

    Args:
        tickers: List of US stock ticker symbols (2-20 tickers)
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        price: Price basis - "adj_close" (default) or "close"
    """
    try:
        q = CompareQuery(tickers=tickers, start=start, end=end, price=price)
    except ValidationError as e:
        return {"error": True, "error_type": "ValidationError", "message": str(e)}

    results = []
    for ticker in q.tickers:
        try:
            df = fetch_price_data(ticker, q.start, q.end)
            series = select_price_column(df, q.price)
            mdd_result = _calc_mdd(series, ticker)
            entry = mdd_result.model_dump(mode="json")
            entry["error"] = None
            results.append(entry)
        except (StockMCPError, Exception) as e:
            results.append(
                {
                    "ticker": ticker,
                    "mdd_pct": None,
                    "peak_date": None,
                    "trough_date": None,
                    "drawdown_duration_days": None,
                    "recovered": None,
                    "recovery_date": None,
                    "error": f"{type(e).__name__}: {e}",
                }
            )

    return {
        "price_basis": q.price,
        "start": q.start,
        "end": q.end,
        "results": results,
    }


# ---------------------------------------------------------------------------
# MCP tool registrations — thin wrappers that delegate to the plain functions
# ---------------------------------------------------------------------------

@mcp.tool("calculate_mdd")
def _tool_calculate_mdd(
    ticker: str,
    start: str,
    end: str,
    price: str = "adj_close",
) -> dict:
    """Calculate Maximum Drawdown for a US stock.

    Returns MDD percentage, peak/trough dates, duration, and recovery info.

    Args:
        ticker: US stock ticker symbol (e.g. "AAPL", "SPY")
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        price: Price basis - "adj_close" (default, dividend-adjusted) or "close"
    """
    return calculate_mdd(ticker, start, end, price)


@mcp.tool("get_price_history")
def _tool_get_price_history(
    ticker: str,
    start: str,
    end: str,
    price: str = "adj_close",
) -> dict:
    """Get historical OHLCV price data for a US stock.

    Args:
        ticker: US stock ticker symbol
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        price: Price basis - "adj_close" (default) or "close"
    """
    return get_price_history(ticker, start, end, price)


@mcp.tool("get_drawdown_series")
def _tool_get_drawdown_series(
    ticker: str,
    start: str,
    end: str,
    price: str = "adj_close",
) -> dict:
    """Get daily drawdown percentage series for underwater chart.

    Each day's value = current_price / running_peak - 1 (always <= 0).

    Args:
        ticker: US stock ticker symbol
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        price: Price basis - "adj_close" (default) or "close"
    """
    return get_drawdown_series(ticker, start, end, price)


@mcp.tool("compare_mdd")
def _tool_compare_mdd(
    tickers: list[str],
    start: str,
    end: str,
    price: str = "adj_close",
) -> dict:
    """Compare Maximum Drawdown across multiple US stocks (2-20 tickers).

    Args:
        tickers: List of US stock ticker symbols
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        price: Price basis - "adj_close" (default) or "close"
    """
    return compare_mdd(tickers, start, end, price)


def _safe_float(val) -> float | None:
    """Convert a value to float, returning None for NaN/None."""
    if val is None:
        return None
    try:
        import math
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _safe_int(val) -> int | None:
    """Convert a value to int, returning None for NaN/None."""
    if val is None:
        return None
    try:
        import math
        f = float(val)
        if math.isnan(f):
            return None
        return int(f)
    except (TypeError, ValueError):
        return None


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="stock-mcp", description="US stock MDD MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport: 'stdio' (default, for Claude Desktop) or 'http' (for hosted/Docker)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="HTTP host (only with --transport http)")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (only with --transport http)")
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run()
    else:
        # FastMCP 2.x HTTP transport — "streamable-http" is the correct transport name
        # for FastMCP >= 2.10. The alias "http" also works but "streamable-http" is canonical.
        # Verified against fastmcp 2.14.7 source: server.py Transport literal includes
        # "stdio", "http", "sse", "streamable-http".
        mcp.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
