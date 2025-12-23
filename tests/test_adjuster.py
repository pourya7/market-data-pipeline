"""Tests for corporate action adjuster."""

import pytest
import pandas as pd
import numpy as np
from datetime import date

from market_data.cleaning.adjuster import (
    CorporateActionAdjuster,
    CorporateAction,
    AdjustmentType,
)


@pytest.fixture
def sample_ohlcv_df():
    """Create sample OHLCV DataFrame for testing."""
    dates = pd.bdate_range("2024-01-01", periods=10, freq="B")
    return pd.DataFrame({
        "open": [100.0] * 10,
        "high": [105.0] * 10,
        "low": [95.0] * 10,
        "close": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
        "volume": [1000000.0] * 10,
    }, index=dates)


class TestCorporateAction:
    """Tests for CorporateAction dataclass."""
    
    def test_split_action(self):
        """Test creating a split action."""
        action = CorporateAction(
            action_type=AdjustmentType.SPLIT,
            ex_date=date(2024, 1, 15),
            ratio=4.0,
        )
        
        assert action.action_type == AdjustmentType.SPLIT
        assert action.ratio == 4.0
    
    def test_dividend_action(self):
        """Test creating a dividend action."""
        action = CorporateAction(
            action_type=AdjustmentType.DIVIDEND,
            ex_date=date(2024, 1, 15),
            ratio=0.50,  # $0.50 dividend
        )
        
        assert action.action_type == AdjustmentType.DIVIDEND
        assert action.ratio == 0.50


class TestCorporateActionAdjuster:
    """Tests for CorporateActionAdjuster."""
    
    def test_no_adjustments(self, sample_ohlcv_df):
        """Test that no adjustments returns original data."""
        adjuster = CorporateActionAdjuster()
        result = adjuster.apply(sample_ohlcv_df, [])
        
        assert "adj_close" in result.columns
        assert (result["adj_close"] == result["close"]).all()
    
    def test_split_adjustment(self, sample_ohlcv_df):
        """Test 4:1 stock split adjustment."""
        adjuster = CorporateActionAdjuster()
        
        # Split happens on Jan 8 (5th trading day)
        split_date = sample_ohlcv_df.index[4].date()
        action = CorporateAction(AdjustmentType.SPLIT, split_date, 4.0)
        
        result = adjuster.apply(sample_ohlcv_df, [action])
        
        # Pre-split prices should be divided by 4
        pre_split = result[result.index.date < split_date]
        post_split = result[result.index.date >= split_date]
        
        # Adjustment factor for pre-split should be 0.25 (1/4)
        assert np.allclose(pre_split["adj_factor"].values, 0.25)
        assert np.allclose(post_split["adj_factor"].values, 1.0)
    
    def test_split_volume_adjustment(self, sample_ohlcv_df):
        """Test that volume is adjusted for splits."""
        adjuster = CorporateActionAdjuster()
        
        split_date = sample_ohlcv_df.index[4].date()
        action = CorporateAction(AdjustmentType.SPLIT, split_date, 4.0)
        
        result = adjuster.apply(sample_ohlcv_df, [action], adjust_volume=True)
        
        # Pre-split volume should be multiplied by 4
        pre_split = result[result.index.date < split_date]
        
        assert "adj_volume" in result.columns
        assert (pre_split["adj_volume"] == pre_split["volume"] * 4).all()
    
    def test_dividend_adjustment(self, sample_ohlcv_df):
        """Test dividend adjustment."""
        adjuster = CorporateActionAdjuster()
        
        # Ex-dividend on Jan 8
        ex_date = sample_ohlcv_df.index[4].date()
        dividend_amount = 1.0  # $1 dividend
        action = CorporateAction(AdjustmentType.DIVIDEND, ex_date, dividend_amount)
        
        result = adjuster.apply(sample_ohlcv_df, [action])
        
        # Pre-ex-date prices should be adjusted
        pre_ex = result[result.index.date < ex_date]
        
        # Adjustment factor should be < 1 for pre-ex-date
        assert all(pre_ex["adj_factor"] < 1.0)
    
    def test_multiple_actions(self, sample_ohlcv_df):
        """Test multiple corporate actions."""
        adjuster = CorporateActionAdjuster()
        
        actions = [
            CorporateAction(AdjustmentType.SPLIT, sample_ohlcv_df.index[6].date(), 2.0),
            CorporateAction(AdjustmentType.SPLIT, sample_ohlcv_df.index[3].date(), 2.0),
        ]
        
        result = adjuster.apply(sample_ohlcv_df, actions)
        
        # Very early dates should have both splits applied
        earliest = result.iloc[0]
        # Two 2:1 splits = 4:1 total adjustment
        assert np.isclose(earliest["adj_factor"], 0.25)
    
    def test_apply_split_convenience(self, sample_ohlcv_df):
        """Test apply_split convenience method."""
        adjuster = CorporateActionAdjuster()
        
        result = adjuster.apply_split(
            sample_ohlcv_df,
            split_date="2024-01-08",
            ratio=2.0,
        )
        
        assert "adj_close" in result.columns
    
    def test_apply_dividend_convenience(self, sample_ohlcv_df):
        """Test apply_dividend convenience method."""
        adjuster = CorporateActionAdjuster()
        
        result = adjuster.apply_dividend(
            sample_ohlcv_df,
            ex_date="2024-01-08",
            amount=0.50,
        )
        
        assert "adj_close" in result.columns
    
    def test_requires_datetime_index(self):
        """Test that non-DatetimeIndex raises error."""
        df = pd.DataFrame({
            "open": [100.0],
            "high": [105.0],
            "low": [95.0],
            "close": [102.0],
            "volume": [1000.0],
        })
        
        adjuster = CorporateActionAdjuster()
        
        with pytest.raises(ValueError, match="DatetimeIndex"):
            adjuster.apply(df, [])


class TestComputeAdjustmentFactors:
    """Tests for compute_adjustment_factors static method."""
    
    def test_factors_only(self, sample_ohlcv_df):
        """Test computing factors without modifying data."""
        split_date = sample_ohlcv_df.index[4].date()
        actions = [CorporateAction(AdjustmentType.SPLIT, split_date, 4.0)]
        
        factors = CorporateActionAdjuster.compute_adjustment_factors(
            sample_ohlcv_df, actions
        )
        
        assert isinstance(factors, pd.Series)
        assert len(factors) == len(sample_ohlcv_df)


class TestEdgeCases:
    """Edge case tests for corporate action adjustments."""
    
    def test_reverse_split(self, sample_ohlcv_df):
        """Test reverse split (consolidation) e.g., 1:10."""
        adjuster = CorporateActionAdjuster()
        
        # 1:10 reverse split - every 10 shares becomes 1
        split_date = sample_ohlcv_df.index[5].date()
        action = CorporateAction(AdjustmentType.SPLIT, split_date, 0.1)
        
        result = adjuster.apply(sample_ohlcv_df, [action])
        
        # Pre-split prices should be multiplied by 10 (factor = 10)
        pre_split = result[result.index.date < split_date]
        post_split = result[result.index.date >= split_date]
        
        assert np.allclose(pre_split["adj_factor"].values, 10.0)
        assert np.allclose(post_split["adj_factor"].values, 1.0)
    
    def test_fractional_split(self, sample_ohlcv_df):
        """Test 3:2 fractional split."""
        adjuster = CorporateActionAdjuster()
        
        split_date = sample_ohlcv_df.index[5].date()
        # 3:2 split means you get 1.5x shares, factor = 1/1.5 = 0.667
        action = CorporateAction(AdjustmentType.SPLIT, split_date, 1.5)
        
        result = adjuster.apply(sample_ohlcv_df, [action])
        
        pre_split = result[result.index.date < split_date]
        
        expected_factor = 1 / 1.5
        assert np.allclose(pre_split["adj_factor"].values, expected_factor)
    
    def test_special_dividend(self, sample_ohlcv_df):
        """Test large special dividend adjustment."""
        adjuster = CorporateActionAdjuster()
        
        ex_date = sample_ohlcv_df.index[5].date()
        # Large special dividend
        special_div = 10.0
        action = CorporateAction(AdjustmentType.DIVIDEND, ex_date, special_div)
        
        result = adjuster.apply(sample_ohlcv_df, [action])
        
        pre_ex = result[result.index.date < ex_date]
        
        # Large dividend should result in smaller factor
        assert all(pre_ex["adj_factor"] < 1.0)
        # Factor = (close - div) / close
        expected_factor = (104.0 - special_div) / 104.0  # close on day before ex-date
        assert np.allclose(pre_ex["adj_factor"].iloc[0], expected_factor, rtol=0.1)
    
    def test_future_dated_action(self, sample_ohlcv_df):
        """Test that future-dated actions result in pre-split adjustment."""
        adjuster = CorporateActionAdjuster()
        
        # Action dated after all data - all data is "pre-split"
        future_date = date(2025, 1, 15)
        action = CorporateAction(AdjustmentType.SPLIT, future_date, 2.0)
        
        result = adjuster.apply(sample_ohlcv_df, [action])
        
        # All data is before the split, so all factors should be 0.5 (1/2)
        assert np.allclose(result["adj_factor"].values, 0.5)
    
    def test_action_before_data(self, sample_ohlcv_df):
        """Test action dated before all data."""
        adjuster = CorporateActionAdjuster()
        
        # Action dated before all data
        past_date = date(2023, 1, 1)
        action = CorporateAction(AdjustmentType.SPLIT, past_date, 2.0)
        
        result = adjuster.apply(sample_ohlcv_df, [action])
        
        # All adjustment factors should be 0.5 (data is all post-split)
        assert np.allclose(result["adj_factor"].values, 1.0)
    
    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        adjuster = CorporateActionAdjuster()
        
        df = pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"],
            index=pd.DatetimeIndex([]),
        )
        
        result = adjuster.apply(df, [])
        
        assert result.empty
        assert "adj_close" in result.columns
    
    def test_single_row(self):
        """Test with single row DataFrame."""
        adjuster = CorporateActionAdjuster()
        
        df = pd.DataFrame({
            "open": [100.0],
            "high": [105.0],
            "low": [95.0],
            "close": [102.0],
            "volume": [1000000.0],
        }, index=pd.DatetimeIndex(["2024-01-15"]))
        
        action = CorporateAction(AdjustmentType.SPLIT, date(2024, 1, 10), 2.0)
        result = adjuster.apply(df, [action])
        
        assert len(result) == 1
        assert "adj_close" in result.columns
    
    def test_multiple_actions_same_day(self):
        """Test multiple actions on the same day."""
        adjuster = CorporateActionAdjuster()
        
        dates = pd.bdate_range("2024-01-01", periods=5)
        df = pd.DataFrame({
            "open": [100.0] * 5,
            "high": [105.0] * 5,
            "low": [95.0] * 5,
            "close": [100.0, 101.0, 102.0, 103.0, 104.0],
            "volume": [1000000.0] * 5,
        }, index=dates)
        
        # Split and dividend on same day
        same_date = df.index[3].date()
        actions = [
            CorporateAction(AdjustmentType.SPLIT, same_date, 2.0),
            CorporateAction(AdjustmentType.DIVIDEND, same_date, 0.5),
        ]
        
        result = adjuster.apply(df, actions)
        
        # Both adjustments should be applied
        pre_action = result[result.index.date < same_date]
        assert all(pre_action["adj_factor"] < 1.0)

