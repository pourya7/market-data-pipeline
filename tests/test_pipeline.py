"""Tests for the unified data cleaning pipeline."""

import pytest
import pandas as pd
import numpy as np
from datetime import date

from market_data.cleaning.pipeline import DataCleaner, CleaningConfig
from market_data.cleaning.adjuster import CorporateAction, AdjustmentType
from market_data.cleaning.gap_handler import GapStrategy


@pytest.fixture
def valid_ohlcv_df():
    """Create a valid OHLCV DataFrame."""
    dates = pd.bdate_range("2024-01-02", periods=10, freq="B")
    return pd.DataFrame({
        "open": [100.0 + i for i in range(10)],
        "high": [105.0 + i for i in range(10)],
        "low": [99.0 + i for i in range(10)],
        "close": [104.0 + i for i in range(10)],
        "volume": [1000.0 + i * 100 for i in range(10)],
    }, index=dates)


@pytest.fixture
def ohlcv_with_gaps():
    """Create OHLCV DataFrame with missing dates."""
    dates = pd.to_datetime([
        "2024-01-02", "2024-01-03", "2024-01-04",
        # Gap: Jan 5
        "2024-01-08", "2024-01-09", "2024-01-10",
    ])
    return pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 105.0, 106.0, 107.0],
        "high": [105.0, 106.0, 107.0, 110.0, 111.0, 112.0],
        "low": [99.0, 100.0, 101.0, 104.0, 105.0, 106.0],
        "close": [104.0, 105.0, 106.0, 109.0, 110.0, 111.0],
        "volume": [1000.0, 1100.0, 1200.0, 1500.0, 1600.0, 1700.0],
    }, index=dates)


class TestCleaningConfig:
    """Tests for CleaningConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CleaningConfig()
        
        assert config.validate_input is True
        assert config.validate_output is True
        assert config.gap_strategy == GapStrategy.FORWARD_FILL
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = CleaningConfig(
            validate_input=False,
            gap_strategy=GapStrategy.LINEAR,
            max_gap_size=3,
        )
        
        assert config.validate_input is False
        assert config.gap_strategy == GapStrategy.LINEAR
        assert config.max_gap_size == 3


class TestDataCleaner:
    """Tests for DataCleaner pipeline."""
    
    def test_default_initialization(self):
        """Test default cleaner initialization."""
        cleaner = DataCleaner()
        
        assert cleaner.config is not None
        assert cleaner.adjuster is not None
        assert cleaner.gap_handler is not None
    
    def test_clean_valid_data(self, valid_ohlcv_df):
        """Test cleaning valid data."""
        cleaner = DataCleaner()
        result = cleaner.clean(valid_ohlcv_df)
        
        assert len(result) == len(valid_ohlcv_df)
    
    def test_clean_with_gaps(self, ohlcv_with_gaps):
        """Test cleaning data with gaps."""
        config = CleaningConfig(gap_strategy=GapStrategy.FORWARD_FILL)
        cleaner = DataCleaner(config)
        
        result = cleaner.clean(ohlcv_with_gaps)
        
        # Should have filled gaps
        assert len(result) >= len(ohlcv_with_gaps)
        assert not result["close"].isna().any()
    
    def test_clean_with_corporate_actions(self, valid_ohlcv_df):
        """Test cleaning with corporate action adjustments."""
        cleaner = DataCleaner()
        
        actions = [
            CorporateAction(
                AdjustmentType.SPLIT,
                valid_ohlcv_df.index[5].date(),
                2.0,
            )
        ]
        
        result = cleaner.clean(valid_ohlcv_df, corporate_actions=actions)
        
        assert "adj_close" in result.columns
        assert "adj_factor" in result.columns
    
    def test_clean_skip_validation(self, valid_ohlcv_df):
        """Test cleaning without validation."""
        config = CleaningConfig(
            validate_input=False,
            validate_output=False,
        )
        cleaner = DataCleaner(config)
        
        result = cleaner.clean(valid_ohlcv_df)
        
        assert len(result) == len(valid_ohlcv_df)
    
    def test_validate_only(self, valid_ohlcv_df):
        """Test validation without cleaning."""
        cleaner = DataCleaner()
        is_valid, errors = cleaner.validate_only(valid_ohlcv_df)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_only_invalid(self, valid_ohlcv_df):
        """Test validation catches errors."""
        df = valid_ohlcv_df.copy()
        df.loc[df.index[0], "volume"] = -100.0
        
        cleaner = DataCleaner()
        is_valid, errors = cleaner.validate_only(df)
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_detect_gaps(self, ohlcv_with_gaps):
        """Test gap detection."""
        cleaner = DataCleaner()
        gaps = cleaner.detect_gaps(ohlcv_with_gaps)
        
        assert len(gaps) > 0
    
    def test_gap_stats_recorded(self, ohlcv_with_gaps):
        """Test that gap stats are recorded."""
        cleaner = DataCleaner()
        cleaner.clean(ohlcv_with_gaps)
        
        stats = cleaner.last_gap_stats
        
        assert "total_gaps" in stats
        assert stats["total_gaps"] > 0
    
    def test_cleaning_report(self, ohlcv_with_gaps):
        """Test cleaning report generation."""
        cleaner = DataCleaner()
        cleaner.clean(ohlcv_with_gaps)
        
        report = cleaner.get_cleaning_report()
        
        assert "gap_statistics" in report
        assert "config" in report


class TestPipelineIntegration:
    """Integration tests for the full pipeline."""
    
    def test_full_pipeline(self, ohlcv_with_gaps):
        """Test full pipeline: validate -> adjust -> fill -> validate."""
        config = CleaningConfig(
            validate_input=True,
            validate_output=True,
            gap_strategy=GapStrategy.FORWARD_FILL,
            apply_adjustments=True,
        )
        cleaner = DataCleaner(config)
        
        # Add a corporate action
        actions = [
            CorporateAction(
                AdjustmentType.SPLIT,
                date(2024, 1, 5),
                2.0,
            )
        ]
        
        result = cleaner.clean(ohlcv_with_gaps, corporate_actions=actions)
        
        # Verify output
        assert not result["close"].isna().any()
        assert "adj_close" in result.columns
        assert len(result) >= len(ohlcv_with_gaps)
