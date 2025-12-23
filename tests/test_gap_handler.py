"""Tests for gap handler."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from market_data.cleaning.gap_handler import GapHandler, GapStrategy


@pytest.fixture
def ohlcv_with_gaps():
    """Create OHLCV DataFrame with missing dates."""
    # Create dates with gaps (missing Jan 3, 4, 8)
    dates = pd.to_datetime([
        "2024-01-02", "2024-01-05",  # Gap: Jan 3, 4 (weekdays)
        "2024-01-09", "2024-01-10", "2024-01-11",
    ])
    return pd.DataFrame({
        "open": [100.0, 102.0, 105.0, 106.0, 107.0],
        "high": [105.0, 107.0, 110.0, 111.0, 112.0],
        "low": [99.0, 101.0, 104.0, 105.0, 106.0],
        "close": [104.0, 106.0, 109.0, 110.0, 111.0],
        "volume": [1000.0, 1100.0, 1200.0, 1300.0, 1400.0],
    }, index=dates)


@pytest.fixture
def complete_ohlcv():
    """Create OHLCV DataFrame without gaps."""
    dates = pd.bdate_range("2024-01-02", periods=5, freq="B")
    return pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, 107.0, 108.0, 109.0],
        "low": [99.0, 100.0, 101.0, 102.0, 103.0],
        "close": [104.0, 105.0, 106.0, 107.0, 108.0],
        "volume": [1000.0, 1100.0, 1200.0, 1300.0, 1400.0],
    }, index=dates)


class TestGapHandler:
    """Tests for GapHandler class."""
    
    def test_default_strategy(self):
        """Test default strategy is forward fill."""
        handler = GapHandler()
        assert handler.strategy == GapStrategy.FORWARD_FILL
    
    def test_custom_strategy(self):
        """Test custom strategy initialization."""
        handler = GapHandler(strategy=GapStrategy.LINEAR)
        assert handler.strategy == GapStrategy.LINEAR


class TestDetectGaps:
    """Tests for gap detection."""
    
    def test_no_gaps(self, complete_ohlcv):
        """Test detection when no gaps exist."""
        handler = GapHandler()
        gaps = handler.detect_gaps(complete_ohlcv, freq="B")
        
        assert len(gaps) == 0
    
    def test_detect_gaps(self, ohlcv_with_gaps):
        """Test gap detection with missing dates."""
        handler = GapHandler()
        gaps = handler.detect_gaps(ohlcv_with_gaps, freq="B")
        
        assert len(gaps) > 0
        assert "gap_size" in gaps.columns
    
    def test_requires_datetime_index(self):
        """Test that non-DatetimeIndex raises error."""
        df = pd.DataFrame({"close": [100, 101, 102]})
        handler = GapHandler()
        
        with pytest.raises(ValueError, match="DatetimeIndex"):
            handler.detect_gaps(df)


class TestFillGaps:
    """Tests for gap filling strategies."""
    
    def test_forward_fill(self, ohlcv_with_gaps):
        """Test forward fill strategy."""
        handler = GapHandler(strategy=GapStrategy.FORWARD_FILL)
        filled = handler.fill_gaps(ohlcv_with_gaps, freq="B")
        
        # Should have more rows now
        assert len(filled) >= len(ohlcv_with_gaps)
        
        # No NaN in close column after fill
        assert not filled["close"].isna().any()
    
    def test_backward_fill(self, ohlcv_with_gaps):
        """Test backward fill strategy."""
        handler = GapHandler(strategy=GapStrategy.BACKWARD_FILL)
        filled = handler.fill_gaps(ohlcv_with_gaps, freq="B")
        
        assert len(filled) >= len(ohlcv_with_gaps)
        assert not filled["close"].isna().any()
    
    def test_linear_interpolation(self, ohlcv_with_gaps):
        """Test linear interpolation strategy."""
        handler = GapHandler(strategy=GapStrategy.LINEAR)
        filled = handler.fill_gaps(ohlcv_with_gaps, freq="B")
        
        assert len(filled) >= len(ohlcv_with_gaps)
        assert not filled["close"].isna().any()
    
    def test_drop_strategy(self, ohlcv_with_gaps):
        """Test drop strategy removes NaN rows."""
        # First add some NaN
        df = ohlcv_with_gaps.copy()
        df.loc[df.index[0], "close"] = np.nan
        
        handler = GapHandler(strategy=GapStrategy.DROP)
        result = handler.fill_gaps(df)
        
        assert not result["close"].isna().any()
        assert len(result) < len(df)
    
    def test_nan_strategy(self, ohlcv_with_gaps):
        """Test NaN strategy keeps gaps marked."""
        handler = GapHandler(strategy=GapStrategy.NAN)
        filled = handler.fill_gaps(ohlcv_with_gaps, freq="B")
        
        # Should have more rows with NaN values
        assert len(filled) >= len(ohlcv_with_gaps)
        assert filled["close"].isna().any()
    
    def test_max_gap_size_limit(self):
        """Test that max_gap_size limits filling."""
        # Create data with large gap
        dates = pd.to_datetime(["2024-01-02", "2024-01-10"])  # 6 day gap
        df = pd.DataFrame({
            "close": [100.0, 110.0],
        }, index=dates)
        
        handler = GapHandler(
            strategy=GapStrategy.FORWARD_FILL,
            max_gap_size=2,
        )
        filled = handler.fill_gaps(df, freq="B")
        
        # Some gaps should still be NaN due to limit
        assert filled["close"].isna().any()
    
    def test_fill_specific_columns(self, ohlcv_with_gaps):
        """Test filling only specific columns."""
        handler = GapHandler(strategy=GapStrategy.FORWARD_FILL)
        filled = handler.fill_gaps(
            ohlcv_with_gaps,
            freq="B",
            columns=["close"],
        )
        
        # Close should be filled
        assert not filled["close"].isna().any()


class TestGapStatistics:
    """Tests for gap statistics."""
    
    def test_no_gaps_stats(self, complete_ohlcv):
        """Test statistics when no gaps."""
        handler = GapHandler()
        stats = handler.get_gap_statistics(complete_ohlcv, freq="B")
        
        assert stats["total_gaps"] == 0
        assert stats["max_gap_size"] == 0
    
    def test_gap_stats(self, ohlcv_with_gaps):
        """Test statistics with gaps."""
        handler = GapHandler()
        stats = handler.get_gap_statistics(ohlcv_with_gaps, freq="B")
        
        assert stats["total_gaps"] > 0
        assert stats["max_gap_size"] > 0
        assert "gap_dates" in stats


class TestEdgeCases:
    """Edge case tests for gap handling."""
    
    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        handler = GapHandler()
        
        df = pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"],
            index=pd.DatetimeIndex([]),
        )
        
        gaps = handler.detect_gaps(df)
        assert len(gaps) == 0
    
    def test_single_row(self):
        """Test with single row DataFrame."""
        handler = GapHandler()
        
        df = pd.DataFrame({
            "close": [100.0],
        }, index=pd.DatetimeIndex(["2024-01-15"]))
        
        gaps = handler.detect_gaps(df)
        assert len(gaps) == 0
    
    def test_weekend_not_counted_as_gap(self):
        """Test that weekends are not counted as gaps when using business days."""
        handler = GapHandler()
        
        # Friday to Monday (no weekend gap expected)
        dates = pd.to_datetime(["2024-01-05", "2024-01-08"])  # Friday & Monday
        df = pd.DataFrame({
            "close": [100.0, 101.0],
        }, index=dates)
        
        gaps = handler.detect_gaps(df, freq="B", trading_days_only=True)
        
        # No gaps expected - this is a normal weekend
        assert len(gaps) == 0
    
    def test_holiday_gap_detected(self):
        """Test that missing trading days (holidays) are detected."""
        handler = GapHandler()
        
        # Monday to Wednesday (missing Tuesday)
        dates = pd.to_datetime(["2024-01-08", "2024-01-10"])  # Mon & Wed
        df = pd.DataFrame({
            "close": [100.0, 102.0],
        }, index=dates)
        
        gaps = handler.detect_gaps(df, freq="B")
        
        # Should detect Tuesday as missing
        assert len(gaps) > 0
    
    def test_all_nan_input(self):
        """Test handling of all-NaN column."""
        handler = GapHandler(strategy=GapStrategy.FORWARD_FILL)
        
        dates = pd.bdate_range("2024-01-02", periods=5)
        df = pd.DataFrame({
            "close": [np.nan] * 5,
        }, index=dates)
        
        result = handler.fill_gaps(df)
        
        # Should still be NaN since no data to forward fill
        assert result["close"].isna().all()
    
    def test_consecutive_weekends(self):
        """Test data spanning multiple weeks."""
        handler = GapHandler()
        
        # Two Fridays (skip weekend in between)
        dates = pd.to_datetime(["2024-01-05", "2024-01-12"])  # Two Fridays
        df = pd.DataFrame({
            "close": [100.0, 105.0],
        }, index=dates)
        
        gaps = handler.detect_gaps(df, freq="B")
        
        # Should detect Mon-Thu as missing (4 business days)
        assert gaps["gap_size"].sum() == 4
    
    def test_very_large_gap(self):
        """Test handling of very large gaps (months)."""
        handler = GapHandler(strategy=GapStrategy.FORWARD_FILL, max_gap_size=5)
        
        dates = pd.to_datetime(["2024-01-02", "2024-03-01"])
        df = pd.DataFrame({
            "close": [100.0, 150.0],
        }, index=dates)
        
        result = handler.fill_gaps(df, freq="B")
        
        # Should have NaN in the middle due to max_gap_size limit
        assert result["close"].isna().any()
    
    def test_duplicate_timestamps(self):
        """Test handling of duplicate timestamps."""
        handler = GapHandler()
        
        dates = pd.to_datetime([
            "2024-01-02", "2024-01-02",  # Duplicate
            "2024-01-03", "2024-01-04",
        ])
        df = pd.DataFrame({
            "close": [100.0, 100.5, 101.0, 102.0],
        }, index=dates)
        
        # Should not crash
        gaps = handler.detect_gaps(df, freq="B")
        assert isinstance(gaps, pd.DataFrame)

