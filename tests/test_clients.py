"""Tests for exchange clients with mocked APIs."""

import pytest
from datetime import date, datetime
from unittest.mock import patch, MagicMock
import pandas as pd

from market_data.clients.yahoo import YahooFinanceClient
from market_data.clients.polygon import PolygonClient
from market_data.clients.oanda import OandaClient
from market_data.models.ohlcv import OHLCVBar


class TestYahooFinanceClient:
    """Tests for YahooFinanceClient."""
    
    def test_provider_name(self):
        """Test provider name."""
        client = YahooFinanceClient()
        assert client.get_provider_name() == "yahoo"
    
    def test_supported_intervals(self):
        """Test supported intervals."""
        client = YahooFinanceClient()
        intervals = client.get_supported_intervals()
        
        assert "1d" in intervals
        assert "1h" in intervals
        assert "1m" in intervals
    
    def test_validate_symbol_valid(self):
        """Test valid symbol validation."""
        client = YahooFinanceClient()
        
        assert client.validate_symbol("AAPL")
        assert client.validate_symbol("BRK-B")
        assert client.validate_symbol("^GSPC")  # S&P 500 index
    
    def test_validate_symbol_invalid(self):
        """Test invalid symbol validation."""
        client = YahooFinanceClient()
        
        assert not client.validate_symbol("")
        assert not client.validate_symbol("   ")
    
    @pytest.mark.asyncio
    async def test_fetch_ohlcv_invalid_symbol(self):
        """Test fetch with invalid symbol raises."""
        client = YahooFinanceClient()
        
        with pytest.raises(ValueError, match="Invalid symbol"):
            await client.fetch_ohlcv("", "2024-01-01", "2024-01-05")
    
    @pytest.mark.asyncio
    async def test_fetch_ohlcv_invalid_interval(self):
        """Test fetch with invalid interval raises."""
        client = YahooFinanceClient()
        
        with pytest.raises(ValueError, match="Unsupported interval"):
            await client.fetch_ohlcv("AAPL", "2024-01-01", "2024-01-05", "invalid")
    
    @pytest.mark.asyncio
    async def test_fetch_ohlcv_invalid_date_range(self):
        """Test fetch with start > end raises."""
        client = YahooFinanceClient()
        
        with pytest.raises(ValueError, match="start_date"):
            await client.fetch_ohlcv("AAPL", "2024-01-10", "2024-01-01")
    
    @pytest.mark.asyncio
    async def test_fetch_ohlcv_with_mocked_yfinance(self):
        """Test fetch with mocked yfinance."""
        # Create mock DataFrame
        mock_df = pd.DataFrame({
            "Open": [100.0, 101.0],
            "High": [105.0, 106.0],
            "Low": [99.0, 100.0],
            "Close": [104.0, 105.0],
            "Volume": [1000000, 1100000],
        }, index=pd.to_datetime(["2024-01-02", "2024-01-03"]))
        
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_df
        
        with patch("market_data.clients.yahoo.yf.Ticker", return_value=mock_ticker):
            client = YahooFinanceClient()
            bars = await client.fetch_ohlcv("AAPL", "2024-01-01", "2024-01-05")
        
        assert len(bars) == 2
        assert all(isinstance(b, OHLCVBar) for b in bars)
        assert bars[0].open == 100.0
        assert bars[0].symbol == "AAPL"
        assert bars[0].provider == "yahoo"


class TestPolygonClient:
    """Tests for PolygonClient."""
    
    def test_provider_name(self):
        """Test provider name."""
        client = PolygonClient()
        assert client.get_provider_name() == "polygon"
    
    def test_supported_intervals(self):
        """Test supported intervals."""
        client = PolygonClient()
        intervals = client.get_supported_intervals()
        
        assert "1d" in intervals
        assert "1h" in intervals
    
    @pytest.mark.asyncio
    async def test_fetch_without_api_key_raises(self):
        """Test fetch without API key raises."""
        client = PolygonClient()
        
        with pytest.raises(ValueError, match="API key required"):
            await client.fetch_ohlcv("AAPL", "2024-01-01", "2024-01-05")
    
    @pytest.mark.asyncio
    async def test_fetch_not_implemented(self):
        """Test fetch is not implemented."""
        client = PolygonClient(config={"api_key": "test_key"})
        
        with pytest.raises(NotImplementedError):
            await client.fetch_ohlcv("AAPL", "2024-01-01", "2024-01-05")


class TestOandaClient:
    """Tests for OandaClient."""
    
    def test_provider_name(self):
        """Test provider name."""
        client = OandaClient()
        assert client.get_provider_name() == "oanda"
    
    def test_supported_intervals(self):
        """Test supported intervals."""
        client = OandaClient()
        intervals = client.get_supported_intervals()
        
        assert "1d" in intervals
        assert "1h" in intervals
    
    def test_validate_symbol_valid(self):
        """Test valid forex pair validation."""
        client = OandaClient()
        
        assert client.validate_symbol("EUR_USD")
        assert client.validate_symbol("GBP_JPY")
    
    def test_validate_symbol_invalid(self):
        """Test invalid forex pair validation."""
        client = OandaClient()
        
        assert not client.validate_symbol("EURUSD")  # Missing underscore
        assert not client.validate_symbol("EUR_")
        assert not client.validate_symbol("")
    
    @pytest.mark.asyncio
    async def test_fetch_without_api_key_raises(self):
        """Test fetch without API key raises."""
        client = OandaClient()
        
        with pytest.raises(ValueError, match="API key required"):
            await client.fetch_ohlcv("EUR_USD", "2024-01-01", "2024-01-05")
    
    @pytest.mark.asyncio
    async def test_fetch_without_account_id_raises(self):
        """Test fetch without account ID raises."""
        client = OandaClient(config={"api_key": "test_key"})
        
        with pytest.raises(ValueError, match="account ID required"):
            await client.fetch_ohlcv("EUR_USD", "2024-01-01", "2024-01-05")
    
    @pytest.mark.asyncio
    async def test_fetch_not_implemented(self):
        """Test fetch is not implemented."""
        client = OandaClient(config={
            "api_key": "test_key",
            "account_id": "test_account"
        })
        
        with pytest.raises(NotImplementedError):
            await client.fetch_ohlcv("EUR_USD", "2024-01-01", "2024-01-05")
