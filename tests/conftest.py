"""Pytest configuration and fixtures."""

import pytest
from datetime import datetime


@pytest.fixture
def sample_ohlcv_data():
    """Sample OHLCV data for testing."""
    return {
        "timestamp": datetime(2024, 1, 15, 9, 30),
        "open": 100.0,
        "high": 105.0,
        "low": 99.0,
        "close": 104.0,
        "volume": 1000000.0,
        "symbol": "AAPL",
        "provider": "yahoo",
        "interval": "1d",
    }


@pytest.fixture
def sample_ohlcv_bars():
    """Multiple OHLCV bars for testing."""
    base_date = datetime(2024, 1, 15)
    bars = []
    
    for i in range(5):
        bars.append({
            "timestamp": datetime(2024, 1, 15 + i, 9, 30),
            "open": 100.0 + i,
            "high": 105.0 + i,
            "low": 99.0 + i,
            "close": 104.0 + i,
            "volume": 1000000.0 + i * 100000,
            "symbol": "AAPL",
            "provider": "yahoo",
            "interval": "1d",
        })
    
    return bars
