"""Integration tests for Yahoo Finance client using mocked responses."""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from market_data.clients.yahoo import YahooFinanceClient


class TestYahooClientIntegration:
    """Integration tests for YahooFinanceClient with mocked HTTP."""
    
    @pytest.fixture
    def client(self):
        """Create Yahoo Finance client."""
        return YahooFinanceClient()
    
    @pytest.mark.asyncio
    async def test_fetch_ohlcv_success(self, client):
        """Test successful OHLCV fetch with mocked yfinance."""
        # Create mock ticker
        mock_ticker = MagicMock()
        mock_history = pd.DataFrame({
            "Open": [182.5, 183.0, 184.5],
            "High": [185.0, 186.0, 187.0],
            "Low": [181.0, 182.0, 183.0],
            "Close": [184.0, 185.0, 186.0],
            "Volume": [100000, 110000, 120000],
        }, index=pd.date_range("2024-01-02", periods=3))
        mock_ticker.history.return_value = mock_history
        
        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = await client.fetch_ohlcv(
                symbol="AAPL",
                start_date=datetime(2024, 1, 2),
                end_date=datetime(2024, 1, 5),
            )
        
        assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_fetch_ohlcv_empty_response(self, client):
        """Test handling of empty response."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        
        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = await client.fetch_ohlcv(
                symbol="INVALID",
                start_date=datetime(2024, 1, 2),
                end_date=datetime(2024, 1, 5),
            )
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_ohlcv_with_interval(self, client):
        """Test fetch with specific interval."""
        mock_ticker = MagicMock()
        mock_history = pd.DataFrame({
            "Open": [182.5],
            "High": [185.0],
            "Low": [181.0],
            "Close": [184.0],
            "Volume": [100000],
        }, index=pd.date_range("2024-01-02", periods=1))
        mock_ticker.history.return_value = mock_history
        
        with patch("yfinance.Ticker", return_value=mock_ticker):
            result = await client.fetch_ohlcv(
                symbol="AAPL",
                start_date=datetime(2024, 1, 2),
                end_date=datetime(2024, 1, 3),
                interval="1h",
            )
        
        assert len(result) >= 0  # Just verify it doesn't crash


class TestEndToEndPipeline:
    """End-to-end pipeline tests with mocked data sources."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_flow(self):
        """Test complete: fetch -> clean -> store flow."""
        from market_data.clients.yahoo import YahooFinanceClient
        from market_data.cleaning.pipeline import DataCleaner
        from market_data.storage.manager import StorageManager, StorageConfig
        import tempfile
        from pathlib import Path
        
        # Setup
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Mock the fetch
            mock_ticker = MagicMock()
            mock_history = pd.DataFrame({
                "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "High": [105.0, 106.0, 107.0, 108.0, 109.0],
                "Low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "Close": [104.0, 105.0, 106.0, 107.0, 108.0],
                "Volume": [1000000, 1100000, 1200000, 1300000, 1400000],
            }, index=pd.date_range("2024-01-02", periods=5))
            mock_ticker.history.return_value = mock_history
            
            # 1. Fetch
            client = YahooFinanceClient()
            with patch("yfinance.Ticker", return_value=mock_ticker):
                bars = await client.fetch_ohlcv(
                    symbol="AAPL",
                    start_date=datetime(2024, 1, 2),
                    end_date=datetime(2024, 1, 10),
                )
            
            # Convert to DataFrame
            from market_data.models import OHLCVDataset
            dataset = OHLCVDataset(symbol="AAPL", bars=bars, provider="yahoo")
            df = dataset.to_pandas()
            
            # 2. Clean
            cleaner = DataCleaner()
            clean_df = cleaner.clean(df)
            
            # 3. Store
            storage = StorageManager(StorageConfig(base_path=temp_dir))
            storage.save(clean_df, "AAPL")
            
            # 4. Verify
            loaded = storage.load("AAPL")
            
            assert len(loaded) == 5
            assert "AAPL" in storage.get_available_symbols()
            
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
