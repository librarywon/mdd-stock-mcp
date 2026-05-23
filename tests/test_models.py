"""Ticker normalization, market, and currency tests (offline)."""

import pytest
from pydantic import ValidationError

from stock_mcp.data import currency_for
from stock_mcp.models import CompareQuery, StockQuery, _normalize_ticker


class TestNormalizeTicker:
    def test_us_passthrough(self):
        assert _normalize_ticker("AAPL", "us") == "AAPL"
        assert _normalize_ticker("spy", "us") == "SPY"

    def test_kr_six_digits_gets_ks_suffix(self):
        assert _normalize_ticker("005930", "kr") == "005930.KS"

    def test_kr_explicit_suffix_preserved(self):
        assert _normalize_ticker("005930.KS", "kr") == "005930.KS"
        assert _normalize_ticker("035720.KQ", "kr") == "035720.KQ"

    def test_crypto_bare_symbol_gets_usd_quote(self):
        assert _normalize_ticker("BTC", "crypto") == "BTC-USD"
        assert _normalize_ticker("eth", "crypto") == "ETH-USD"

    def test_crypto_explicit_quote_preserved(self):
        assert _normalize_ticker("BTC-USD", "crypto") == "BTC-USD"
        assert _normalize_ticker("BTC-KRW", "crypto") == "BTC-KRW"

    def test_empty_ticker_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            _normalize_ticker("   ", "us")


class TestCurrencyFor:
    def test_us(self):
        assert currency_for("us", "SPY") == "USD"

    def test_kr(self):
        assert currency_for("kr", "005930.KS") == "KRW"

    def test_crypto_default_usd(self):
        assert currency_for("crypto", "BTC-USD") == "USD"

    def test_crypto_quote_currency(self):
        assert currency_for("crypto", "BTC-KRW") == "KRW"
        assert currency_for("crypto", "ETH-EUR") == "EUR"


class TestStockQuery:
    def test_default_market_is_us(self):
        q = StockQuery(ticker="SPY", start="2024-01-01", end="2024-06-30")
        assert q.market == "us"
        assert q.ticker == "SPY"

    def test_kr_market_normalizes_ticker(self):
        q = StockQuery(ticker="005930", start="2024-01-01", end="2024-06-30", market="kr")
        assert q.ticker == "005930.KS"

    def test_crypto_market_normalizes_ticker(self):
        q = StockQuery(ticker="BTC", start="2024-01-01", end="2024-06-30", market="crypto")
        assert q.ticker == "BTC-USD"

    def test_invalid_market_rejected(self):
        with pytest.raises(ValidationError):
            StockQuery(ticker="SPY", start="2024-01-01", end="2024-06-30", market="jp")


class TestCompareQuery:
    def test_normalizes_all_tickers(self):
        cq = CompareQuery(
            tickers=["005930", "035720.KQ"],
            start="2024-01-01",
            end="2024-06-30",
            market="kr",
        )
        assert cq.tickers == ["005930.KS", "035720.KQ"]

    def test_crypto_batch_normalization(self):
        cq = CompareQuery(
            tickers=["BTC", "ETH-USD"],
            start="2024-01-01",
            end="2024-06-30",
            market="crypto",
        )
        assert cq.tickers == ["BTC-USD", "ETH-USD"]
