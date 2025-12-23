"""Tests for the Resampling module."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from market_data.resampling import TimeResampler, VolumeBarGenerator, TickBarGenerator


@pytest.fixture
def sample_minute_data():
    """Create sample 1-minute OHLCV data."""
    np.random.seed(42)
    n = 100
    
    dates = pd.date_range(start="2024-01-01 09:30", periods=n, freq="1min")
    
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n) * 0.2)
    low = close - np.abs(np.random.randn(n) * 0.2)
    open_price = close + np.random.randn(n) * 0.1
    volume = np.random.randint(1000, 10000, n).astype(float)
    
    return pd.DataFrame({
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }, index=dates)


@pytest.fixture
def sample_tick_data():
    """Create sample tick data."""
    np.random.seed(42)
    n = 500
    
    timestamps = pd.date_range(start="2024-01-01 09:30", periods=n, freq="1s")
    prices = 100 + np.cumsum(np.random.randn(n) * 0.1)
    volumes = np.random.randint(10, 100, n).astype(float)
    
    return pd.DataFrame({
        "price": prices,
        "close": prices,
        "high": prices,
        "low": prices,
        "open": prices,
        "volume": volumes,
    }, index=timestamps)


class TestTimeResampler:
    """Tests for TimeResampler class."""
    
    def test_resample_to_5min(self, sample_minute_data):
        """Test resampling to 5-minute bars."""
        resampler = TimeResampler()
        result = resampler.resample(sample_minute_data, "5min")
        
        # 100 minutes should give ~20 5-minute bars
        assert len(result) == 20
        assert "open" in result.columns
        assert "high" in result.columns
        assert "low" in result.columns
        assert "close" in result.columns
        assert "volume" in result.columns
    
    def test_resample_to_15min(self, sample_minute_data):
        """Test resampling to 15-minute bars."""
        resampler = TimeResampler()
        result = resampler.resample(sample_minute_data, "15min")
        
        # 100 minutes should give 7 15-minute bars (6 full + 1 partial)
        assert len(result) == 7
    
    def test_ohlc_aggregation(self, sample_minute_data):
        """Test OHLC aggregation rules."""
        resampler = TimeResampler()
        result = resampler.resample(sample_minute_data, "5min")
        
        # Check first bar
        first_5_rows = sample_minute_data.iloc[:5]
        first_bar = result.iloc[0]
        
        assert first_bar["open"] == first_5_rows["open"].iloc[0]
        assert first_bar["high"] == first_5_rows["high"].max()
        assert first_bar["low"] == first_5_rows["low"].min()
        assert first_bar["close"] == first_5_rows["close"].iloc[-1]
        assert first_bar["volume"] == first_5_rows["volume"].sum()
    
    def test_to_hourly(self, sample_minute_data):
        """Test resampling to hourly."""
        resampler = TimeResampler()
        result = resampler.to_hourly(sample_minute_data)
        
        # 100 minutes starting at 09:30 = 09:00, 10:00, 11:00 hourly buckets
        assert len(result) >= 2
    
    def test_to_daily(self, sample_minute_data):
        """Test resampling to daily."""
        resampler = TimeResampler()
        result = resampler.to_daily(sample_minute_data)
        
        # All data is on same day
        assert len(result) == 1
        assert result["volume"].iloc[0] == sample_minute_data["volume"].sum()
    
    def test_timeframe_aliases(self, sample_minute_data):
        """Test timeframe alias conversion."""
        resampler = TimeResampler()
        
        # Test various aliases
        r1 = resampler.resample(sample_minute_data, "5m")
        r2 = resampler.resample(sample_minute_data, "5min")
        
        assert len(r1) == len(r2)
    
    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        resampler = TimeResampler()
        empty = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        empty.index = pd.DatetimeIndex([])
        
        result = resampler.resample(empty, "5min")
        assert result.empty
    
    def test_preserves_feature_columns(self, sample_minute_data):
        """Test that feature columns are preserved."""
        resampler = TimeResampler()
        
        # Add a feature column
        df = sample_minute_data.copy()
        df["rsi_14"] = 50.0
        
        result = resampler.resample(df, "5min")
        assert "rsi_14" in result.columns
    
    def test_get_available_timeframes(self):
        """Test getting available timeframes."""
        resampler = TimeResampler()
        timeframes = resampler.get_available_timeframes()
        
        assert "1m" in timeframes
        assert "1h" in timeframes
        assert "1D" in timeframes


class TestVolumeBarGenerator:
    """Tests for VolumeBarGenerator class."""
    
    def test_generate_volume_bars(self, sample_tick_data):
        """Test generating volume bars."""
        generator = VolumeBarGenerator(volume_threshold=500)
        result = generator.generate(sample_tick_data)
        
        # Should have created multiple bars
        assert len(result) > 0
        assert "open" in result.columns
        assert "high" in result.columns
        assert "low" in result.columns
        assert "close" in result.columns
        assert "volume" in result.columns
    
    def test_volume_threshold_respected(self, sample_tick_data):
        """Test that volume threshold is respected."""
        threshold = 500
        generator = VolumeBarGenerator(volume_threshold=threshold)
        result = generator.generate(sample_tick_data)
        
        # All complete bars should have volume >= threshold
        # Only last bar (partial) might have less
        for i in range(len(result) - 1):
            assert result.iloc[i]["volume"] >= threshold
    
    def test_ohlc_values(self, sample_tick_data):
        """Test OHLC values are correct."""
        generator = VolumeBarGenerator(volume_threshold=500)
        result = generator.generate(sample_tick_data)
        
        # High should be >= Open, Close
        for _, row in result.iterrows():
            assert row["high"] >= row["open"]
            assert row["high"] >= row["close"]
            assert row["low"] <= row["open"]
            assert row["low"] <= row["close"]
    
    def test_from_ticks(self):
        """Test generating from tick dictionaries."""
        ticks = [
            {"timestamp": datetime(2024, 1, 1, 9, 30), "price": 100.0, "volume": 100},
            {"timestamp": datetime(2024, 1, 1, 9, 31), "price": 101.0, "volume": 200},
            {"timestamp": datetime(2024, 1, 1, 9, 32), "price": 99.0, "volume": 300},
            {"timestamp": datetime(2024, 1, 1, 9, 33), "price": 102.0, "volume": 100},
        ]
        
        generator = VolumeBarGenerator(volume_threshold=500)
        result = generator.generate_from_ticks(ticks)
        
        # 100 + 200 + 300 = 600 >= 500, so first bar complete
        assert len(result) >= 1
    
    def test_invalid_threshold(self):
        """Test that invalid threshold raises error."""
        with pytest.raises(ValueError):
            VolumeBarGenerator(volume_threshold=0)
        
        with pytest.raises(ValueError):
            VolumeBarGenerator(volume_threshold=-100)
    
    def test_empty_data(self):
        """Test with empty data."""
        generator = VolumeBarGenerator(volume_threshold=500)
        empty = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        empty.index = pd.DatetimeIndex([])
        
        result = generator.generate(empty)
        assert result.empty


class TestTickBarGenerator:
    """Tests for TickBarGenerator class."""
    
    def test_generate_tick_bars(self, sample_tick_data):
        """Test generating tick bars."""
        generator = TickBarGenerator(ticks_per_bar=50)
        result = generator.generate(sample_tick_data)
        
        # 500 ticks / 50 per bar = 10 bars
        assert len(result) == 10
        assert "open" in result.columns
        assert "tick_count" in result.columns
    
    def test_tick_count(self, sample_tick_data):
        """Test tick count in bars."""
        ticks_per_bar = 50
        generator = TickBarGenerator(ticks_per_bar=ticks_per_bar)
        result = generator.generate(sample_tick_data)
        
        # All complete bars should have exactly ticks_per_bar ticks
        for i in range(len(result) - 1):
            assert result.iloc[i]["tick_count"] == ticks_per_bar
    
    def test_partial_bar(self):
        """Test partial bar at end."""
        ticks = [
            {"timestamp": datetime(2024, 1, 1, 9, 30) + timedelta(seconds=i), "price": 100.0 + i, "volume": 10}
            for i in range(75)
        ]
        
        generator = TickBarGenerator(ticks_per_bar=50)
        result = generator.generate_from_ticks(ticks)
        
        # 75 ticks / 50 = 1 complete + 1 partial
        assert len(result) == 2
        assert result.iloc[0]["tick_count"] == 50
        assert result.iloc[1]["tick_count"] == 25
    
    def test_ohlc_values(self, sample_tick_data):
        """Test OHLC values are correct."""
        generator = TickBarGenerator(ticks_per_bar=50)
        result = generator.generate(sample_tick_data)
        
        for _, row in result.iterrows():
            assert row["high"] >= row["open"]
            assert row["high"] >= row["close"]
            assert row["low"] <= row["open"]
            assert row["low"] <= row["close"]
    
    def test_from_ticks(self):
        """Test generating from tick dictionaries."""
        ticks = [
            {"timestamp": datetime(2024, 1, 1, 9, 30) + timedelta(seconds=i), "price": 100.0 + i * 0.1, "volume": 10}
            for i in range(100)
        ]
        
        generator = TickBarGenerator(ticks_per_bar=20)
        result = generator.generate_from_ticks(ticks)
        
        assert len(result) == 5
    
    def test_invalid_ticks_per_bar(self):
        """Test that invalid ticks_per_bar raises error."""
        with pytest.raises(ValueError):
            TickBarGenerator(ticks_per_bar=0)
        
        with pytest.raises(ValueError):
            TickBarGenerator(ticks_per_bar=-10)
    
    def test_empty_data(self):
        """Test with empty data."""
        generator = TickBarGenerator(ticks_per_bar=50)
        empty = pd.DataFrame(columns=["close", "volume"])
        empty.index = pd.DatetimeIndex([])
        
        result = generator.generate(empty)
        assert result.empty
