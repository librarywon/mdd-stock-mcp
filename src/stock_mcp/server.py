"""FastMCP server with 4 stock MDD analysis tools."""

import math

from fastmcp import FastMCP
from pydantic import ValidationError

from stock_mcp.data import currency_for, fetch_price_data, select_price_column
from stock_mcp.errors import StockMCPError
from stock_mcp.mdd import calculate_max_drawdown as _calc_mdd
from stock_mcp.mdd import compute_drawdown_series
from stock_mcp.models import CompareQuery, StockQuery

mcp = FastMCP(
    "mdd-stock-mcp",
    instructions=(
        "Maximum Drawdown analytics for US stocks, Korean stocks (KOSPI/KOSDAQ), "
        "and cryptocurrencies. Pass ticker + date range + market "
        "(\"us\" default, \"kr\", or \"crypto\"). For Korean stocks, a 6-digit "
        "code like \"005930\" auto-resolves to \"005930.KS\" (KOSPI); use the "
        "explicit \".KQ\" suffix for KOSDAQ. For crypto, \"BTC\" auto-resolves "
        "to \"BTC-USD\"; use \"BTC-KRW\" for a different quote currency. "
        "Returns JSON data for charting."
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
    market: str = "us",
) -> dict:
    """Calculate Maximum Drawdown for a stock or cryptocurrency.

    Returns MDD percentage, peak/trough dates, duration, and recovery info.
    Use this for single-asset drawdown analysis.

    Args:
        ticker: Symbol (e.g. "AAPL", "SPY", "005930" or "005930.KS", "BTC" or "BTC-USD")
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        price: Price basis - "adj_close" (default, dividend-adjusted) or "close"
        market: "us" (default), "kr" (KOSPI/KOSDAQ), or "crypto"
    """
    try:
        q = StockQuery(ticker=ticker, start=start, end=end, price=price, market=market)
        df = fetch_price_data(q.ticker, q.start, q.end)
        series = select_price_column(df, q.price)
        result = _calc_mdd(series, q.ticker)
        payload = result.model_dump(mode="json")
        payload["market"] = q.market
        payload["currency"] = currency_for(q.market, q.ticker)
        return payload
    except ValidationError as e:
        return {"error": True, "error_type": "ValidationError", "message": str(e)}
    except StockMCPError as e:
        return {"error": True, "error_type": type(e).__name__, "message": str(e)}


def get_price_history(
    ticker: str,
    start: str,
    end: str,
    price: str = "adj_close",
    market: str = "us",
) -> dict:
    """Get historical price data for a stock or cryptocurrency.

    Returns OHLCV time series as JSON. Use for charting price history.

    Args:
        ticker: Symbol (US, KR, or crypto)
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        price: Price basis - "adj_close" (default) or "close"
        market: "us" (default), "kr", or "crypto"
    """
    try:
        q = StockQuery(ticker=ticker, start=start, end=end, price=price, market=market)
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
            "market": q.market,
            "currency": currency_for(q.market, q.ticker),
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
    market: str = "us",
) -> dict:
    """Get daily drawdown percentage series for underwater chart.

    Each day's value = current_price / running_peak - 1 (always <= 0).
    Use this to plot an 'underwater chart' showing drawdown depth over time.

    Args:
        ticker: Symbol (US, KR, or crypto)
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        price: Price basis - "adj_close" (default) or "close"
        market: "us" (default), "kr", or "crypto"
    """
    try:
        q = StockQuery(ticker=ticker, start=start, end=end, price=price, market=market)
        df = fetch_price_data(q.ticker, q.start, q.end)
        series = select_price_column(df, q.price)
        data = compute_drawdown_series(series)
        return {
            "ticker": q.ticker,
            "market": q.market,
            "currency": currency_for(q.market, q.ticker),
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
    market: str = "us",
) -> dict:
    """Compare Maximum Drawdown across multiple assets in the same market.

    Returns MDD results for each ticker. Use for side-by-side comparison.
    All tickers must belong to the same market (mixing currencies is meaningless).

    Args:
        tickers: List of symbols (2-20)
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        price: Price basis - "adj_close" (default) or "close"
        market: "us" (default), "kr", or "crypto"
    """
    try:
        q = CompareQuery(tickers=tickers, start=start, end=end, price=price, market=market)
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
        except Exception as e:
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
        "market": q.market,
        "currency": currency_for(q.market, q.tickers[0]) if q.tickers else None,
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
    market: str = "us",
) -> dict:
    """Calculate Maximum Drawdown for a stock or cryptocurrency.

    Returns MDD percentage, peak/trough dates, duration, and recovery info.

    Args:
        ticker: Symbol — US ("AAPL"), KR ("005930" auto-resolves to "005930.KS",
            or explicit "035720.KQ"), or crypto ("BTC" auto-resolves to "BTC-USD")
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        price: Price basis - "adj_close" (default, dividend-adjusted) or "close"
        market: "us" (default), "kr" (KOSPI/KOSDAQ), or "crypto"
    """
    return calculate_mdd(ticker, start, end, price, market)


@mcp.tool("get_price_history")
def _tool_get_price_history(
    ticker: str,
    start: str,
    end: str,
    price: str = "adj_close",
    market: str = "us",
) -> dict:
    """Get historical OHLCV price data for a stock or cryptocurrency.

    Args:
        ticker: Symbol (US, KR, or crypto)
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        price: Price basis - "adj_close" (default) or "close"
        market: "us" (default), "kr", or "crypto"
    """
    return get_price_history(ticker, start, end, price, market)


@mcp.tool("get_drawdown_series")
def _tool_get_drawdown_series(
    ticker: str,
    start: str,
    end: str,
    price: str = "adj_close",
    market: str = "us",
) -> dict:
    """Get daily drawdown percentage series for underwater chart.

    Each day's value = current_price / running_peak - 1 (always <= 0).

    Args:
        ticker: Symbol (US, KR, or crypto)
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        price: Price basis - "adj_close" (default) or "close"
        market: "us" (default), "kr", or "crypto"
    """
    return get_drawdown_series(ticker, start, end, price, market)


@mcp.tool("compare_mdd")
def _tool_compare_mdd(
    tickers: list[str],
    start: str,
    end: str,
    price: str = "adj_close",
    market: str = "us",
) -> dict:
    """Compare Maximum Drawdown across multiple assets (2-20 tickers, same market).

    Args:
        tickers: List of symbols
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        price: Price basis - "adj_close" (default) or "close"
        market: "us" (default), "kr", or "crypto"
    """
    return compare_mdd(tickers, start, end, price, market)


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

    parser = argparse.ArgumentParser(prog="mdd-stock-mcp", description="US stock MDD MCP server")
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
