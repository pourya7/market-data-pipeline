"""Tests for unified storage manager."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date, datetime, timedelta
import tempfile
import shutil

from market_data.storage.manager import StorageManager, StorageConfig


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path)


@pytest.fixture
def sample_ohlcv_df():
    """Create sample OHLCV DataFrame."""
    dates = pd.date_range("2024-01-02", periods=20, freq="B")
    return pd.DataFrame({
        "open": np.random.uniform(100, 110, 20),
        "high": np.random.uniform(110, 120, 20),
        "low": np.random.uniform(90, 100, 20),
        "close": np.random.uniform(100, 110, 20),
        "volume": np.random.uniform(1e6, 2e6, 20),
    }, index=dates)


@pytest.fixture
def multi_year_df():
    """Create DataFrame spanning multiple years."""
    dates_2023 = pd.date_range("2023-12-01", periods=20, freq="B")
    dates_2024 = pd.date_range("2024-01-02", periods=20, freq="B")
    dates = dates_2023.append(dates_2024)
    
    return pd.DataFrame({
        "open": np.random.uniform(100, 110, 40),
        "high": np.random.uniform(110, 120, 40),
        "low": np.random.uniform(90, 100, 40),
        "close": np.random.uniform(100, 110, 40),
        "volume": np.random.uniform(1e6, 2e6, 40),
    }, index=dates)


@pytest.fixture
def storage_manager(temp_dir):
    """Create storage manager with temp directory."""
    config = StorageConfig(base_path=temp_dir)
    return StorageManager(config)


class TestStorageConfig:
    """Tests for StorageConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = StorageConfig()
        
        assert config.compression == "snappy"
        assert config.update_threshold_hours == 24
    
    def test_custom_config(self, temp_dir):
        """Test custom configuration."""
        config = StorageConfig(
            base_path=temp_dir,
            compression="gzip",
            update_threshold_hours=12,
        )
        
        assert config.compression == "gzip"
        assert config.update_threshold_hours == 12


class TestStorageManager:
    """Tests for StorageManager."""
    
    def test_save_basic(self, storage_manager, sample_ohlcv_df):
        """Test basic save operation."""
        storage_manager.save(sample_ohlcv_df, "AAPL")
        
        symbols = storage_manager.get_available_symbols()
        assert "AAPL" in symbols
    
    def test_save_creates_partition(self, storage_manager, sample_ohlcv_df):
        """Test that save creates year partition."""
        storage_manager.save(sample_ohlcv_df, "AAPL")
        
        years = storage_manager.get_available_years("AAPL")
        assert 2024 in years
    
    def test_save_updates_manifest(self, storage_manager, sample_ohlcv_df):
        """Test that save updates manifest."""
        storage_manager.save(sample_ohlcv_df, "AAPL")
        
        last_date = storage_manager.get_last_date("AAPL")
        assert last_date is not None
    
    def test_save_multi_year(self, storage_manager, multi_year_df):
        """Test saving data spanning multiple years."""
        storage_manager.save(multi_year_df, "AAPL")
        
        years = storage_manager.get_available_years("AAPL")
        assert 2023 in years
        assert 2024 in years
    
    def test_load_basic(self, storage_manager, sample_ohlcv_df):
        """Test basic load operation."""
        storage_manager.save(sample_ohlcv_df, "AAPL")
        result = storage_manager.load("AAPL")
        
        assert len(result) == len(sample_ohlcv_df)
    
    def test_load_with_date_filter(self, storage_manager, sample_ohlcv_df):
        """Test loading with date filter."""
        storage_manager.save(sample_ohlcv_df, "AAPL")
        
        result = storage_manager.load(
            "AAPL",
            start_date="2024-01-10",
            end_date="2024-01-20",
        )
        
        assert len(result) < len(sample_ohlcv_df)
        assert all(result.index.date >= date(2024, 1, 10))
    
    def test_load_nonexistent(self, storage_manager):
        """Test loading non-existent symbol."""
        result = storage_manager.load("NONEXISTENT")
        
        assert result.empty
    
    def test_needs_update_new_symbol(self, storage_manager):
        """Test needs_update for new symbol."""
        assert storage_manager.needs_update("AAPL")
    
    def test_needs_update_fresh_data(self, storage_manager, sample_ohlcv_df):
        """Test needs_update for fresh data."""
        storage_manager.save(sample_ohlcv_df, "AAPL")
        
        assert not storage_manager.needs_update("AAPL")
    
    def test_needs_update_stale_data(self, storage_manager, sample_ohlcv_df):
        """Test needs_update for stale data."""
        storage_manager.save(sample_ohlcv_df, "AAPL")
        
        # Check with old reference time
        old_time = datetime.utcnow() + timedelta(hours=48)
        
        assert storage_manager.needs_update("AAPL", as_of=old_time)
    
    def test_delete_symbol(self, storage_manager, sample_ohlcv_df):
        """Test deleting a symbol."""
        storage_manager.save(sample_ohlcv_df, "AAPL")
        
        result = storage_manager.delete("AAPL")
        
        assert result is True
        assert "AAPL" not in storage_manager.get_available_symbols()
    
    def test_delete_nonexistent(self, storage_manager):
        """Test deleting non-existent symbol."""
        result = storage_manager.delete("NONEXISTENT")
        
        assert result is False
    
    def test_get_storage_stats(self, storage_manager, sample_ohlcv_df):
        """Test getting storage statistics."""
        storage_manager.save(sample_ohlcv_df, "AAPL")
        storage_manager.save(sample_ohlcv_df, "MSFT")
        
        stats = storage_manager.get_storage_stats()
        
        assert stats["num_symbols"] == 2
        assert stats["num_partitions"] == 2
        assert stats["total_size_bytes"] > 0
    
    def test_append_mode(self, storage_manager):
        """Test append mode merges data."""
        # First save
        dates1 = pd.date_range("2024-01-02", periods=3, freq="B")
        df1 = pd.DataFrame({
            "open": [100.0] * 3,
            "high": [105.0] * 3,
            "low": [95.0] * 3,
            "close": [102.0] * 3,
            "volume": [1e6] * 3,
        }, index=dates1)
        
        storage_manager.save(df1, "AAPL")
        
        # Append new data with non-overlapping dates
        dates2 = pd.date_range("2024-01-15", periods=3, freq="B")
        df2 = pd.DataFrame({
            "open": [110.0] * 3,
            "high": [115.0] * 3,
            "low": [105.0] * 3,
            "close": [112.0] * 3,
            "volume": [2e6] * 3,
        }, index=dates2)
        
        storage_manager.save(df2, "AAPL", mode="append")
        
        # Load combined data
        result = storage_manager.load("AAPL")
        
        # Should have all 6 rows since no overlap
        assert len(result) == 6

