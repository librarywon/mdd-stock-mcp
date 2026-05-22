"""Pydantic input/output models for mdd-stock-mcp."""

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator


_TICKER_RE = re.compile(r"^[A-Z0-9\-\.]{1,20}$")
_KR_DIGITS_RE = re.compile(r"^\d{6}$")
_KR_SUFFIX_RE = re.compile(r"\.(KS|KQ)$")

Market = Literal["us", "kr", "crypto"]


def _normalize_ticker(ticker: str, market: str) -> str:
    """Normalize a raw ticker to a yfinance-compatible symbol.

    - kr:    "005930" -> "005930.KS" (KOSPI default); ".KS"/".KQ" passthrough.
    - crypto: "BTC" -> "BTC-USD"; "BTC-KRW" passthrough.
    - us:    unchanged.
    """
    t = ticker.strip().upper()
    if not t:
        raise ValueError("Ticker must not be empty.")

    if market == "kr":
        if _KR_DIGITS_RE.match(t):
            t = f"{t}.KS"
    elif market == "crypto":
        if "-" not in t:
            t = f"{t}-USD"

    if not _TICKER_RE.match(t):
        raise ValueError(
            f"Invalid ticker format after normalization: '{t}'. "
            f"Must be 1-20 alphanumeric characters (hyphens/dots allowed)."
        )
    return t


class StockQuery(BaseModel):
    ticker: str
    start: str
    end: str
    price: Literal["adj_close", "close"] = "adj_close"
    market: Market = "us"

    @field_validator("start", "end")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid date format: '{v}'. Expected YYYY-MM-DD.")
        return v

    @model_validator(mode="after")
    def _finalize(self) -> "StockQuery":
        self.ticker = _normalize_ticker(self.ticker, self.market)

        start_date = date.fromisoformat(self.start)
        end_date = date.fromisoformat(self.end)
        today = date.today()

        if start_date >= end_date:
            raise ValueError(
                f"start ({self.start}) must be before end ({self.end})."
            )
        if end_date > today:
            raise ValueError(
                f"end ({self.end}) must not be in the future (today is {today})."
            )
        return self


class CompareQuery(BaseModel):
    tickers: list[str]
    start: str
    end: str
    price: Literal["adj_close", "close"] = "adj_close"
    market: Market = "us"

    @field_validator("tickers")
    @classmethod
    def validate_tickers_size(cls, v: list[str]) -> list[str]:
        if len(v) < 2 or len(v) > 20:
            raise ValueError("tickers must have between 2 and 20 items.")
        return v

    @field_validator("start", "end")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid date format: '{v}'. Expected YYYY-MM-DD.")
        return v

    @model_validator(mode="after")
    def _finalize(self) -> "CompareQuery":
        self.tickers = [_normalize_ticker(t, self.market) for t in self.tickers]

        start_date = date.fromisoformat(self.start)
        end_date = date.fromisoformat(self.end)
        today = date.today()

        if start_date >= end_date:
            raise ValueError(
                f"start ({self.start}) must be before end ({self.end})."
            )
        if end_date > today:
            raise ValueError(
                f"end ({self.end}) must not be in the future (today is {today})."
            )
        return self


class MDDResult(BaseModel):
    ticker: str
    mdd_pct: float
    peak_date: str
    trough_date: str
    drawdown_duration_days: int
    recovered: bool
    recovery_date: str | None
