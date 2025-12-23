"""Tests for Parquet I/O."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from market_data.storage.parquet import ParquetWriter, ParquetReader


@pytest.fixture
def sample_ohlcv_df():
    """Create sample OHLCV DataFrame."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame({
        "open": [100.0 + i for i in range(10)],
        "high": [105.0 + i for i in range(10)],
        "low": [99.0 + i for i in range(10)],
        "close": [104.0 + i for i in range(10)],
        "volume": [1000.0 + i * 100 for i in range(10)],
    }, index=dates)


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path)


class TestParquetWriter:
    """Tests for ParquetWriter."""
    
    def test_write_basic(self, sample_ohlcv_df, temp_dir):
        """Test basic write operation."""
        writer = ParquetWriter()
        path = temp_dir / "test.parquet"
        
        writer.write(sample_ohlcv_df, path)
        
        assert path.exists()
    
    def test_write_creates_directories(self, sample_ohlcv_df, temp_dir):
        """Test that write creates parent directories."""
        writer = ParquetWriter()
        path = temp_dir / "nested" / "dir" / "test.parquet"
        
        writer.write(sample_ohlcv_df, path)
        
        assert path.exists()
    
    def test_write_with_compression(self, sample_ohlcv_df, temp_dir):
        """Test write with different compression."""
        for compression in ["snappy", "gzip", "none"]:
            writer = ParquetWriter(compression=compression)
            path = temp_dir / f"test_{compression}.parquet"
            
            writer.write(sample_ohlcv_df, path)
            
            assert path.exists()
    
    def test_default_compression_is_snappy(self):
        """Test default compression is snappy."""
        writer = ParquetWriter()
        assert writer.compression == "snappy"


class TestParquetReader:
    """Tests for ParquetReader."""
    
    def test_read_basic(self, sample_ohlcv_df, temp_dir):
        """Test basic read operation."""
        writer = ParquetWriter()
        reader = ParquetReader()
        path = temp_dir / "test.parquet"
        
        writer.write(sample_ohlcv_df, path)
        result = reader.read(path)
        
        assert len(result) == len(sample_ohlcv_df)
        assert list(result.columns) == list(sample_ohlcv_df.columns)
    
    def test_read_with_columns(self, sample_ohlcv_df, temp_dir):
        """Test reading specific columns."""
        writer = ParquetWriter()
        reader = ParquetReader()
        path = temp_dir / "test.parquet"
        
        writer.write(sample_ohlcv_df, path)
        result = reader.read(path, columns=["close", "volume"])
        
        assert list(result.columns) == ["close", "volume"]
    
    def test_read_file_not_found(self, temp_dir):
        """Test reading non-existent file raises."""
        reader = ParquetReader()
        
        with pytest.raises(FileNotFoundError):
            reader.read(temp_dir / "nonexistent.parquet")
    
    def test_get_metadata(self, sample_ohlcv_df, temp_dir):
        """Test getting file metadata."""
        writer = ParquetWriter()
        reader = ParquetReader()
        path = temp_dir / "test.parquet"
        
        writer.write(sample_ohlcv_df, path)
        metadata = reader.get_metadata(path)
        
        assert metadata["num_rows"] == 10
        assert "schema" in metadata
    
    def test_get_schema(self, sample_ohlcv_df, temp_dir):
        """Test getting PyArrow schema."""
        writer = ParquetWriter()
        reader = ParquetReader()
        path = temp_dir / "test.parquet"
        
        writer.write(sample_ohlcv_df, path)
        schema = reader.get_schema(path)
        
        field_names = [f.name for f in schema]
        assert "close" in field_names
        assert "volume" in field_names


class TestRoundTrip:
    """Tests for write/read roundtrip."""
    
    def test_data_integrity(self, sample_ohlcv_df, temp_dir):
        """Test data integrity after write/read."""
        writer = ParquetWriter()
        reader = ParquetReader()
        path = temp_dir / "test.parquet"
        
        writer.write(sample_ohlcv_df, path)
        result = reader.read(path)
        
        pd.testing.assert_frame_equal(
            result.reset_index(drop=True),
            sample_ohlcv_df.reset_index(drop=True),
        )
