# Contributing to stock-mcp

Thanks for your interest in contributing. This is a small, focused project — contributions that stay within scope are most likely to be merged quickly.

---

## Setting up the dev environment

Requires Python 3.11+ and [`uv`](https://github.com/astral-sh/uv).

```bash
git clone https://github.com/librarywon/stock-mcp.git
cd stock-mcp
uv pip install -e ".[dev]"
```

This installs the package in editable mode along with test and lint dependencies.

---

## Running tests

```bash
pytest tests/
```

The test suite is offline (no network required). All tests in `tests/` should pass before you open a PR.

---

## Code style

We use [black](https://github.com/psf/black) for formatting and [ruff](https://github.com/astral-sh/ruff) for linting, both with their default configurations. There is no pre-commit hook yet, but please run them before submitting:

```bash
black src/ tests/
ruff check src/ tests/
```

No style enforcement is automated in CI right now — that will be added in a future release.

---

## Proposing changes

- **Bug fixes and small improvements**: open a PR directly with a clear description.
- **New features or non-trivial changes**: open an issue first to discuss the approach before writing code. This avoids wasted effort if the direction doesn't align with the project's goals.

---

## Commit message conventions

- Use **imperative mood** for the first line: "Add Polygon provider", not "Added Polygon provider".
- Keep the **first line under ~60 characters**.
- Leave a blank line before any extended description.
- Reference relevant issue numbers with `Fixes #N` or `Related to #N` in the body when applicable.

Examples:

```
Add Polygon.io data provider option

Implements the DataProvider protocol in data.py using Polygon's
REST API. Requires POLYGON_API_KEY env var. Falls back to yfinance
if the key is absent.

Fixes #12
```

```
Fix edge case when trough equals start date
```

---

## What's in scope

- **Additional data providers** — Polygon.io, Alpha Vantage, Tiingo, or any well-supported provider. Should implement the same interface as the existing yfinance wrapper in `data.py`.
- **Additional metrics as new MCP tools** — Sharpe ratio, Sortino ratio, CAGR, Calmar ratio, etc. Add them to `server.py` following the existing pattern.
- **Better error handling and edge cases** — Clearer error messages, more robust date validation, etc.
- **Documentation improvements** — Clarifying existing docs, adding examples.

## What's out of scope

- **Non-US tickers** — International stocks, crypto, forex, futures. Keep it simple.
- **Intraday data** — This project is daily-resolution only. No 1m/5m/hourly data.
- **UI or visualization layers** — The server returns data; rendering is the client's job.
- **Breaking changes to existing tool output schemas** — Claude Desktop configs and existing integrations depend on stable schemas.

---

## Pull request checklist

- [ ] `pytest tests/` passes
- [ ] `black` and `ruff` have been run (no new violations)
- [ ] New behavior is covered by tests where practical
- [ ] The PR description explains *why*, not just *what*
