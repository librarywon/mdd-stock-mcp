"""Offline MDD math tests using synthetic price series."""

import pandas as pd
import pytest

from stock_mcp.errors import NoDataError
from stock_mcp.mdd import calculate_max_drawdown, compute_drawdown_series


def _make_series(prices: list[float], start: str = "2020-01-01") -> pd.Series:
    """Build a pd.Series with a DatetimeIndex from a list of prices."""
    idx = pd.date_range(start=start, periods=len(prices), freq="B")
    return pd.Series(prices, index=idx)


class TestCalculateMaxDrawdown:
    def test_standard_mdd(self):
        """[100, 105, 95, 80, 90, 100, 110] → MDD ≈ -0.2381, peak idx 1, trough idx 3, recovered."""
        prices = _make_series([100.0, 105.0, 95.0, 80.0, 90.0, 100.0, 110.0])
        result = calculate_max_drawdown(prices, "TEST")

        # MDD = (80 - 105) / 105 = -0.238095...
        expected_mdd = (80 - 105) / 105
        assert abs(result.mdd_pct - expected_mdd) < 1e-4, (
            f"Expected MDD ~{expected_mdd:.4f}, got {result.mdd_pct}"
        )

        # Peak should be at index 1 (price=105)
        assert result.peak_date == str(prices.index[1].date()), (
            f"Expected peak at index 1, got {result.peak_date}"
        )

        # Trough should be at index 3 (price=80)
        assert result.trough_date == str(prices.index[3].date()), (
            f"Expected trough at index 3, got {result.trough_date}"
        )

        # Should have recovered (price reaches 105 again at index 5, then 110 at index 6)
        assert result.recovered is True, "Expected recovered=True"
        assert result.recovery_date is not None, "Expected non-null recovery_date"

    def test_length_one_raises_no_data_error(self):
        """Single-element series should raise NoDataError."""
        prices = _make_series([100.0])
        with pytest.raises(NoDataError):
            calculate_max_drawdown(prices, "TEST")

    def test_constant_series(self):
        """Constant series [100, 100, 100] → mdd_pct=0.0, recovered=True."""
        prices = _make_series([100.0, 100.0, 100.0])
        result = calculate_max_drawdown(prices, "TEST")

        assert result.mdd_pct == 0.0, f"Expected 0.0, got {result.mdd_pct}"
        assert result.peak_date == result.trough_date, "peak_date should equal trough_date"
        assert result.recovered is True, "Expected recovered=True for constant series"

    def test_monotonically_increasing(self):
        """Monotonically increasing series → mdd_pct=0.0 (no drawdown)."""
        prices = _make_series([100.0, 101.0, 102.0, 103.0, 104.0])
        result = calculate_max_drawdown(prices, "TEST")

        assert result.mdd_pct == 0.0, f"Expected 0.0 for monotonic increase, got {result.mdd_pct}"


class TestComputeDrawdownSeries:
    def test_returns_correct_length(self):
        """Drawdown series should have one entry per input price point."""
        prices = _make_series([100.0, 105.0, 95.0, 80.0, 90.0])
        series = compute_drawdown_series(prices)
        assert len(series) == 5

    def test_all_values_lte_zero(self):
        """All drawdown_pct values should be <= 0."""
        prices = _make_series([100.0, 105.0, 95.0, 80.0, 90.0, 100.0, 110.0])
        series = compute_drawdown_series(prices)
        for entry in series:
            assert entry["drawdown_pct"] <= 0.0, (
                f"drawdown_pct should be <= 0, got {entry['drawdown_pct']}"
            )

    def test_first_entry_is_zero(self):
        """First entry should always be 0.0 (at the start price equals running max)."""
        prices = _make_series([100.0, 80.0, 90.0])
        series = compute_drawdown_series(prices)
        assert series[0]["drawdown_pct"] == 0.0

    def test_empty_series(self):
        """Empty series should return empty list."""
        prices = pd.Series([], dtype=float)
        series = compute_drawdown_series(prices)
        assert series == []
