"""Pydantic input/output models for mdd-stock-mcp."""

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator


_TICKER_RE = re.compile(r"^[A-Z0-9\-\.]{1,15}$")


class StockQuery(BaseModel):
    ticker: str
    start: str
    end: str
    price: Literal["adj_close", "close"] = "adj_close"

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Ticker must not be empty.")
        if not _TICKER_RE.match(v):
            raise ValueError(
                f"Invalid ticker format: '{v}'. Must be 1-15 alphanumeric characters (hyphens/dots allowed)."
            )
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
    def validate_date_range(self) -> "StockQuery":
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

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: list[str]) -> list[str]:
        if len(v) < 2 or len(v) > 20:
            raise ValueError("tickers must have between 2 and 20 items.")
        result = []
        for ticker in v:
            t = ticker.strip().upper()
            if not t:
                raise ValueError("Each ticker must not be empty.")
            if not _TICKER_RE.match(t):
                raise ValueError(
                    f"Invalid ticker format: '{t}'. Must be 1-15 alphanumeric characters."
                )
            result.append(t)
        return result

    @field_validator("start", "end")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid date format: '{v}'. Expected YYYY-MM-DD.")
        return v

    @model_validator(mode="after")
    def validate_date_range(self) -> "CompareQuery":
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
