"""Tests for Pandera schema validation."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

import pandera as pa

from market_data.cleaning.schemas import (
    OHLCVSchema,
    AdjustedOHLCVSchema,
    validate_ohlcv,
    get_validation_errors,
)


@pytest.fixture
def valid_ohlcv_df():
    """Create a valid OHLCV DataFrame."""
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame({
        "open": [100.0, 101.0, 102.0, 103.0, 104.0],
        "high": [105.0, 106.0, 107.0, 108.0, 109.0],
        "low": [99.0, 100.0, 101.0, 102.0, 103.0],
        "close": [104.0, 105.0, 106.0, 107.0, 108.0],
        "volume": [1000.0, 1100.0, 1200.0, 1300.0, 1400.0],
    }, index=dates)


class TestOHLCVSchema:
    """Tests for OHLCVSchema validation."""
    
    def test_valid_dataframe_passes(self, valid_ohlcv_df):
        """Test that valid data passes validation."""
        validated = OHLCVSchema.validate(valid_ohlcv_df)
        assert len(validated) == 5
    
    def test_missing_column_fails(self, valid_ohlcv_df):
        """Test that missing required column fails."""
        df = valid_ohlcv_df.drop(columns=["close"])
        
        with pytest.raises(pa.errors.SchemaError):
            OHLCVSchema.validate(df)
    
    def test_negative_price_fails(self, valid_ohlcv_df):
        """Test that negative prices fail validation."""
        df = valid_ohlcv_df.copy()
        df.loc[df.index[0], "open"] = -10.0
        
        with pytest.raises(pa.errors.SchemaError):
            OHLCVSchema.validate(df)
    
    def test_zero_price_fails(self, valid_ohlcv_df):
        """Test that zero prices fail validation."""
        df = valid_ohlcv_df.copy()
        df.loc[df.index[0], "close"] = 0.0
        
        with pytest.raises(pa.errors.SchemaError):
            OHLCVSchema.validate(df)
    
    def test_negative_volume_fails(self, valid_ohlcv_df):
        """Test that negative volume fails validation."""
        df = valid_ohlcv_df.copy()
        df.loc[df.index[0], "volume"] = -100.0
        
        with pytest.raises(pa.errors.SchemaError):
            OHLCVSchema.validate(df)
    
    def test_zero_volume_passes(self, valid_ohlcv_df):
        """Test that zero volume passes validation."""
        df = valid_ohlcv_df.copy()
        df.loc[df.index[0], "volume"] = 0.0
        
        validated = OHLCVSchema.validate(df)
        assert validated.loc[validated.index[0], "volume"] == 0.0
    
    def test_high_less_than_low_fails(self, valid_ohlcv_df):
        """Test that high < low fails validation."""
        df = valid_ohlcv_df.copy()
        df.loc[df.index[0], "high"] = 90.0  # Less than low
        
        with pytest.raises(pa.errors.SchemaError):
            OHLCVSchema.validate(df)
    
    def test_high_less_than_close_fails(self, valid_ohlcv_df):
        """Test that high < close fails validation."""
        df = valid_ohlcv_df.copy()
        df.loc[df.index[0], "high"] = 103.0  # Less than close (104)
        
        with pytest.raises(pa.errors.SchemaError):
            OHLCVSchema.validate(df)
    
    def test_extra_columns_allowed(self, valid_ohlcv_df):
        """Test that extra columns are allowed."""
        df = valid_ohlcv_df.copy()
        df["extra_col"] = "test"
        
        validated = OHLCVSchema.validate(df)
        assert "extra_col" in validated.columns


class TestValidateOHLCV:
    """Tests for validate_ohlcv function."""
    
    def test_valid_returns_no_errors(self, valid_ohlcv_df):
        """Test that valid data returns no errors."""
        validated, errors = validate_ohlcv(valid_ohlcv_df, raise_on_error=False)
        
        assert errors is None
        assert len(validated) == 5
    
    def test_invalid_returns_errors(self, valid_ohlcv_df):
        """Test that invalid data returns errors."""
        df = valid_ohlcv_df.copy()
        df.loc[df.index[0], "volume"] = -100.0
        
        validated, errors = validate_ohlcv(df, raise_on_error=False)
        
        assert errors is not None
    
    def test_raise_on_error(self, valid_ohlcv_df):
        """Test that raise_on_error works."""
        df = valid_ohlcv_df.copy()
        df.loc[df.index[0], "volume"] = -100.0
        
        with pytest.raises(pa.errors.SchemaErrors):
            validate_ohlcv(df, raise_on_error=True)


class TestAdjustedOHLCVSchema:
    """Tests for AdjustedOHLCVSchema."""
    
    def test_with_adj_close(self, valid_ohlcv_df):
        """Test validation with adj_close column."""
        df = valid_ohlcv_df.copy()
        df["adj_close"] = df["close"] * 0.95
        
        validated = AdjustedOHLCVSchema.validate(df)
        assert "adj_close" in validated.columns
    
    def test_without_adj_close_fails(self, valid_ohlcv_df):
        """Test that missing adj_close fails."""
        with pytest.raises(pa.errors.SchemaError):
            AdjustedOHLCVSchema.validate(valid_ohlcv_df)


class TestGetValidationErrors:
    """Tests for get_validation_errors function."""
    
    def test_no_errors(self, valid_ohlcv_df):
        """Test that valid data returns empty list."""
        errors = get_validation_errors(valid_ohlcv_df)
        assert errors == []
    
    def test_returns_error_details(self, valid_ohlcv_df):
        """Test that errors contain details."""
        df = valid_ohlcv_df.copy()
        df.loc[df.index[0], "volume"] = -100.0
        
        errors = get_validation_errors(df)
        
        assert len(errors) > 0
        assert "column" in errors[0]
        assert "message" in errors[0]
