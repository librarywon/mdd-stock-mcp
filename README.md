# mdd-stock-mcp

> An MCP server for Maximum Drawdown (MDD) analytics across US stocks, Korean stocks (KOSPI/KOSDAQ), and cryptocurrencies. Plug it into Claude Desktop and ask questions like "What was SPY's worst drawdown during COVID?" or "비트코인 2022년 MDD 알려줘" — Claude will fetch the data and discuss it conversationally.

[![PyPI](https://img.shields.io/pypi/v/mdd-stock-mcp.svg)](https://pypi.org/project/mdd-stock-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python >=3.11](https://img.shields.io/badge/python-%3E%3D3.11-blue.svg)](https://www.python.org/)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io/)

> **Disclaimer**: This project uses [yfinance](https://github.com/ranaroussi/yfinance), an unofficial Yahoo Finance scraper. Not affiliated with Yahoo, not for production trading systems, not for financial advice. Data may be inaccurate, delayed, or unavailable. Use at your own risk.

---

## What it does

- Calculates Maximum Drawdown for any supported asset over a date range
- Returns OHLCV price history for plotting
- Returns a daily drawdown (underwater) series
- Compares MDD across multiple tickers side-by-side

**Supported markets** (via the `market` parameter):

| `market` | Examples | Notes |
|---|---|---|
| `us` (default) | `AAPL`, `SPY`, `QQQ` | NYSE / NASDAQ |
| `kr` | `005930` → `005930.KS` (Samsung), `035720.KQ` (KOSDAQ) | 6-digit codes auto-append `.KS` (KOSPI). Use explicit `.KQ` for KOSDAQ. |
| `crypto` | `BTC` → `BTC-USD`, `ETH-USD`, `BTC-KRW` | Bare symbols auto-append `-USD`. |

---

## Quickstart (Claude Desktop)

**1. Install [uv](https://docs.astral.sh/uv/) (if you don't have it):**

```bash
# macOS
brew install uv
# Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. Add this to `~/Library/Application Support/Claude/claude_desktop_config.json`** (macOS) **or `%APPDATA%\Claude\claude_desktop_config.json`** (Windows):

```json
{
  "mcpServers": {
    "mdd-stock-mcp": {
      "command": "uvx",
      "args": ["mdd-stock-mcp"]
    }
  }
}
```

That's it. `uvx` fetches the package from PyPI on first run and caches it.

**3. Restart Claude Desktop.**

Ask: *"Using mdd-stock-mcp, what was AAPL's MDD between 2020-01-01 and 2020-12-31?"*

---

## Quickstart (Claude Code CLI)

```bash
claude mcp add mdd-stock-mcp -s user -- uvx mdd-stock-mcp
```

Then in a new Claude Code session you'll see the `mcp__mdd-stock-mcp__*` tools.

---

## Install from source (for development)

```bash
git clone https://github.com/librarywon/mdd-stock-mcp.git
cd mdd-stock-mcp
uv pip install -e ".[dev]"
```

Then point Claude Desktop at the local path:

```json
{
  "mcpServers": {
    "mdd-stock-mcp": {
      "command": "uvx",
      "args": ["--from", "/absolute/path/to/mdd-stock-mcp", "mdd-stock-mcp"]
    }
  }
}
```

---

## Tools

| Tool | Description | Example |
|---|---|---|
| `calculate_mdd` | Single-ticker MDD | `calculate_mdd("SPY", "2020-01-01", "2020-12-31")` |
| `get_price_history` | OHLCV time series | `get_price_history("005930", "2024-01-01", "2024-06-30", market="kr")` |
| `get_drawdown_series` | Daily drawdown % series | `get_drawdown_series("BTC", "2022-01-01", "2022-12-31", market="crypto")` |
| `compare_mdd` | Multi-ticker MDD comparison | `compare_mdd(["SPY","QQQ","DIA"], "2020-01-01", "2020-12-31")` |

Each tool accepts:
- `price`: `"adj_close"` (default, dividend/split adjusted) or `"close"` (raw closing price)
- `market`: `"us"` (default), `"kr"`, or `"crypto"` — see the [supported markets table](#what-it-does)

---

## Output schemas

<details>
<summary><code>calculate_mdd</code> — success response</summary>

```json
{
  "ticker": "SPY",
  "mdd_pct": -0.338915,
  "peak_date": "2020-02-19",
  "trough_date": "2020-03-23",
  "drawdown_duration_days": 33,
  "recovered": false,
  "recovery_date": null,
  "market": "us",
  "currency": "USD"
}
```

</details>

<details>
<summary><code>calculate_mdd</code> — error response</summary>

```json
{
  "error": true,
  "error_type": "InvalidTickerError",
  "message": "InvalidTickerError: Ticker 'XYZFAKE' not found or returned no data from Yahoo Finance."
}
```

</details>

<details>
<summary><code>get_price_history</code> — success response</summary>

```json
{
  "ticker": "AAPL",
  "price_basis": "adj_close",
  "count": 62,
  "data": [
    {
      "date": "2020-01-02",
      "open": 296.239990,
      "high": 300.600006,
      "low": 295.190002,
      "close": 298.829956,
      "volume": 33870100
    }
  ]
}
```

</details>

<details>
<summary><code>get_drawdown_series</code> — success response</summary>

```json
{
  "ticker": "SPY",
  "price_basis": "adj_close",
  "count": 125,
  "data": [
    {"date": "2020-01-02", "drawdown_pct": 0.0},
    {"date": "2020-01-03", "drawdown_pct": -0.007054},
    {"date": "2020-03-23", "drawdown_pct": -0.338915}
  ]
}
```

</details>

<details>
<summary><code>compare_mdd</code> — success response (partial failure shown)</summary>

```json
{
  "price_basis": "adj_close",
  "start": "2020-01-01",
  "end": "2020-06-30",
  "results": [
    {
      "ticker": "SPY",
      "mdd_pct": -0.338915,
      "peak_date": "2020-02-19",
      "trough_date": "2020-03-23",
      "drawdown_duration_days": 33,
      "recovered": false,
      "recovery_date": null,
      "error": null
    },
    {
      "ticker": "XYZFAKE",
      "mdd_pct": null,
      "peak_date": null,
      "trough_date": null,
      "drawdown_duration_days": null,
      "recovered": null,
      "recovery_date": null,
      "error": "InvalidTickerError: Ticker 'XYZFAKE' not found or returned no data from Yahoo Finance."
    }
  ]
}
```

</details>

---

## How MDD is calculated

- **Formula**: `drawdown_t = price_t / max(price_{0..t}) - 1`
- **MDD** = `min(drawdown)` over the date range (most negative value)
- **Peak**: argmax of price up to and including the trough date
- **Recovery**: first date after trough where `price >= peak_price`
- **Note**: `recovered=false` means "did not recover *within the queried window*", not "never recovered historically"

All price values use **dividend/split-adjusted close** by default (`price="adj_close"`). Pass `price="close"` for raw unadjusted closing prices.

---

## Example Claude conversation

> **User**: mdd-stock-mcp으로 SPY의 2020년 코로나 폭락 분석해줘
>
> **Claude**: [calls calculate_mdd] SPY는 2020-02-19 최고점에서 2020-03-23 최저점까지 약 -33.9%의 MDD를 기록했습니다. 회복은 2020-08-18에 완료됐어요. 그래프 그려드릴까요?
>
> **User**: 응
>
> **Claude**: [calls get_price_history + get_drawdown_series, draws chart in artifact]

---

## Limitations

- **US stocks, Korean stocks (KOSPI/KOSDAQ), and major cryptocurrencies** — limited to what Yahoo Finance exposes. Other international exchanges (Tokyo, London, etc.) aren't wired up.
- **Daily resolution** — No intraday (1m, 5m, etc.) data.
- **yfinance is unofficial** — Yahoo Finance may rate-limit or change their API without notice. For production use, swap `data.py` for a paid provider like [Polygon.io](https://polygon.io/), [Alpha Vantage](https://www.alphavantage.co/), or [Tiingo](https://www.tiingo.com/).
- **In-memory cache only** — Price data is cached for 5 minutes per process. Cache is lost on server restart.
- **No real-time data** — All data is end-of-day historical prices.

---

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/

# Open MCP inspector (interactive tool tester)
fastmcp dev src/stock_mcp/server.py
```

**Project structure:**

```
src/stock_mcp/
  server.py   — FastMCP app + 4 tool definitions
  data.py     — yfinance wrapper + TTL cache + price-column selector
  mdd.py      — Pure MDD math functions
  models.py   — Pydantic input/output models
  errors.py   — Custom error types
tests/
  test_mdd.py — Offline math tests (no network required)
```

---

## Deployment

### Local (stdio) — default

The default transport is `stdio`, which is what Claude Desktop expects. Use the `uvx` config from the [Quickstart](#quickstart-claude-desktop) section above.

### Docker

```bash
# Build the image
docker build -t mdd-stock-mcp .

# Run with HTTP transport (e.g. for testing or a hosted setup)
docker run -p 8000:8000 mdd-stock-mcp --transport http
```

Replace `8000` with any port you prefer. The `--transport http` flag enables the HTTP/SSE transport mode; omit it for the default stdio mode.

### Smithery / hosted

[Smithery](https://smithery.ai/) can host MCP servers so you don't need to run them locally. Once the `smithery.yaml` configuration is present in the repo root, you can register the server through the Smithery dashboard. See the [Smithery documentation](https://smithery.ai/) for registration instructions.

---

## Roadmap

Planned additions (not yet scheduled — PRs welcome):

- **Sharpe / Sortino / CAGR tools** — additional risk/return metrics as new MCP tools, following the same patterns as the existing four.
- **Optional Polygon.io / Alpha Vantage providers** — drop-in replacements for the yfinance backend in `data.py`, configurable via environment variable.
- **Shorter date ranges / intraday support** — hourly or intraday resolution for ranges under ~7 days, contingent on a stable data provider.

---

## Contributing

This is a small focused project. PRs are welcome — especially for:

- Additional data providers (Polygon, Alpha Vantage, Tiingo) in `data.py`
- Additional metrics (Sharpe ratio, CAGR, Sortino) as new tools
- Better error messages and edge-case handling

Please open an issue first for significant changes.

---

## License

MIT — see [LICENSE](./LICENSE)
