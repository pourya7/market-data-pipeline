"""Tests for OHLCV data models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from market_data.models.ohlcv import OHLCVBar, OHLCVDataset


class TestOHLCVBar:
    """Tests for OHLCVBar model."""
    
    def test_valid_bar_creation(self, sample_ohlcv_data):
        """Test creating a valid OHLCV bar."""
        bar = OHLCVBar(**sample_ohlcv_data)
        
        assert bar.symbol == "AAPL"
        assert bar.open == 100.0
        assert bar.high == 105.0
        assert bar.low == 99.0
        assert bar.close == 104.0
        assert bar.volume == 1000000.0
        assert bar.provider == "yahoo"
    
    def test_bar_immutability(self, sample_ohlcv_data):
        """Test that bars are immutable (frozen)."""
        bar = OHLCVBar(**sample_ohlcv_data)
        
        with pytest.raises(ValidationError):
            bar.close = 200.0
    
    def test_invalid_negative_price(self, sample_ohlcv_data):
        """Test that negative prices are rejected."""
        sample_ohlcv_data["open"] = -10.0
        
        with pytest.raises(ValidationError) as exc_info:
            OHLCVBar(**sample_ohlcv_data)
        
        assert "greater than 0" in str(exc_info.value).lower()
    
    def test_invalid_zero_price(self, sample_ohlcv_data):
        """Test that zero prices are rejected."""
        sample_ohlcv_data["close"] = 0.0
        
        with pytest.raises(ValidationError):
            OHLCVBar(**sample_ohlcv_data)
    
    def test_negative_volume_rejected(self, sample_ohlcv_data):
        """Test that negative volume is rejected."""
        sample_ohlcv_data["volume"] = -100.0
        
        with pytest.raises(ValidationError):
            OHLCVBar(**sample_ohlcv_data)
    
    def test_zero_volume_allowed(self, sample_ohlcv_data):
        """Test that zero volume is allowed."""
        sample_ohlcv_data["volume"] = 0.0
        bar = OHLCVBar(**sample_ohlcv_data)
        
        assert bar.volume == 0.0
    
    def test_empty_symbol_rejected(self, sample_ohlcv_data):
        """Test that empty symbol is rejected."""
        sample_ohlcv_data["symbol"] = ""
        
        with pytest.raises(ValidationError):
            OHLCVBar(**sample_ohlcv_data)
    
    def test_whitespace_stripped(self, sample_ohlcv_data):
        """Test that whitespace is stripped from strings."""
        sample_ohlcv_data["symbol"] = "  AAPL  "
        sample_ohlcv_data["provider"] = " yahoo "
        
        bar = OHLCVBar(**sample_ohlcv_data)
        
        assert bar.symbol == "AAPL"
        assert bar.provider == "yahoo"
    
    def test_high_less_than_low_rejected(self, sample_ohlcv_data):
        """Test that high < low is rejected."""
        sample_ohlcv_data["high"] = 95.0
        sample_ohlcv_data["low"] = 100.0
        
        with pytest.raises(ValidationError):
            OHLCVBar(**sample_ohlcv_data)
    
    def test_high_less_than_open_rejected(self, sample_ohlcv_data):
        """Test that high < open is rejected."""
        sample_ohlcv_data["high"] = 99.0
        sample_ohlcv_data["open"] = 100.0
        
        with pytest.raises(ValidationError):
            OHLCVBar(**sample_ohlcv_data)
    
    def test_high_less_than_close_rejected(self, sample_ohlcv_data):
        """Test that high < close is rejected."""
        # Adjust all values to create invalid scenario: high < close
        sample_ohlcv_data["open"] = 100.0
        sample_ohlcv_data["high"] = 103.0
        sample_ohlcv_data["low"] = 99.0
        sample_ohlcv_data["close"] = 104.0  # close > high - invalid!
        
        with pytest.raises(ValidationError):
            OHLCVBar(**sample_ohlcv_data)
    
    def test_low_greater_than_open_rejected(self, sample_ohlcv_data):
        """Test that low > open is rejected."""
        sample_ohlcv_data["low"] = 101.0
        sample_ohlcv_data["open"] = 100.0
        
        with pytest.raises(ValidationError):
            OHLCVBar(**sample_ohlcv_data)
    
    def test_model_dump(self, sample_ohlcv_data):
        """Test model serialization."""
        bar = OHLCVBar(**sample_ohlcv_data)
        data = bar.model_dump()
        
        assert isinstance(data, dict)
        assert data["symbol"] == "AAPL"
        assert "timestamp" in data


class TestOHLCVDataset:
    """Tests for OHLCVDataset model."""
    
    def test_empty_dataset(self):
        """Test creating an empty dataset."""
        dataset = OHLCVDataset(symbol="AAPL", provider="yahoo")
        
        assert len(dataset) == 0
        assert dataset.symbol == "AAPL"
    
    def test_dataset_with_bars(self, sample_ohlcv_bars):
        """Test creating a dataset with bars."""
        bars = [OHLCVBar(**b) for b in sample_ohlcv_bars]
        dataset = OHLCVDataset(symbol="AAPL", provider="yahoo", bars=bars)
        
        assert len(dataset) == 5
    
    def test_dataset_iteration(self, sample_ohlcv_bars):
        """Test iterating over dataset."""
        bars = [OHLCVBar(**b) for b in sample_ohlcv_bars]
        dataset = OHLCVDataset(symbol="AAPL", provider="yahoo", bars=bars)
        
        count = 0
        for bar in dataset:
            assert isinstance(bar, OHLCVBar)
            count += 1
        
        assert count == 5
    
    def test_to_pandas(self, sample_ohlcv_bars):
        """Test converting to pandas DataFrame."""
        bars = [OHLCVBar(**b) for b in sample_ohlcv_bars]
        dataset = OHLCVDataset(symbol="AAPL", provider="yahoo", bars=bars)
        
        df = dataset.to_pandas()
        
        assert len(df) == 5
        assert "open" in df.columns
        assert "close" in df.columns
        assert df.index.name == "timestamp"
    
    def test_to_polars(self, sample_ohlcv_bars):
        """Test converting to polars DataFrame."""
        bars = [OHLCVBar(**b) for b in sample_ohlcv_bars]
        dataset = OHLCVDataset(symbol="AAPL", provider="yahoo", bars=bars)
        
        df = dataset.to_polars()
        
        assert len(df) == 5
        assert "open" in df.columns
        assert "close" in df.columns
    
    def test_empty_dataset_to_pandas(self):
        """Test converting empty dataset to pandas."""
        dataset = OHLCVDataset(symbol="AAPL", provider="yahoo")
        df = dataset.to_pandas()
        
        assert len(df) == 0
        assert "open" in df.columns
    
    def test_empty_dataset_to_polars(self):
        """Test converting empty dataset to polars."""
        dataset = OHLCVDataset(symbol="AAPL", provider="yahoo")
        df = dataset.to_polars()
        
        assert len(df) == 0
