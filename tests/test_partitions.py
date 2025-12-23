"""Tests for partition management."""

import pytest
from pathlib import Path
import tempfile
import shutil

from market_data.storage.partitions import PartitionManager, PartitionInfo


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path)


@pytest.fixture
def partition_manager(temp_dir):
    """Create partition manager with temp directory."""
    return PartitionManager(temp_dir)


@pytest.fixture
def populated_partitions(temp_dir):
    """Create partition manager with some files."""
    pm = PartitionManager(temp_dir)
    
    # Create some partition files
    for year in [2023, 2024]:
        year_dir = temp_dir / f"year={year}"
        year_dir.mkdir()
        for symbol in ["AAPL", "MSFT"]:
            (year_dir / f"{symbol}.parquet").touch()
    
    return pm


class TestPartitionManager:
    """Tests for PartitionManager."""
    
    def test_get_partition_path(self, partition_manager):
        """Test partition path generation."""
        path = partition_manager.get_partition_path("AAPL", 2024)
        
        assert "year=2024" in str(path)
        assert "AAPL.parquet" in str(path)
    
    def test_get_partition_path_uppercase(self, partition_manager):
        """Test symbol is uppercased."""
        path = partition_manager.get_partition_path("aapl", 2024)
        
        assert "AAPL.parquet" in str(path)
    
    def test_get_year_directory(self, partition_manager):
        """Test year directory path."""
        path = partition_manager.get_year_directory(2024)
        
        assert path.name == "year=2024"
    
    def test_list_partitions_empty(self, partition_manager):
        """Test listing empty partitions."""
        partitions = partition_manager.list_partitions()
        
        assert partitions == []
    
    def test_list_partitions(self, populated_partitions):
        """Test listing existing partitions."""
        partitions = populated_partitions.list_partitions()
        
        assert len(partitions) == 4  # 2 years * 2 symbols
        assert all(isinstance(p, PartitionInfo) for p in partitions)
    
    def test_list_years(self, populated_partitions):
        """Test listing years."""
        years = populated_partitions.list_years()
        
        assert years == [2023, 2024]
    
    def test_list_symbols(self, populated_partitions):
        """Test listing all symbols."""
        symbols = populated_partitions.list_symbols()
        
        assert symbols == ["AAPL", "MSFT"]
    
    def test_list_symbols_for_year(self, populated_partitions):
        """Test listing symbols for specific year."""
        symbols = populated_partitions.list_symbols(year=2024)
        
        assert symbols == ["AAPL", "MSFT"]
    
    def test_partition_exists(self, populated_partitions):
        """Test checking partition existence."""
        assert populated_partitions.partition_exists("AAPL", 2024)
        assert not populated_partitions.partition_exists("GOOG", 2024)
    
    def test_get_partitions_for_symbol(self, populated_partitions):
        """Test getting partitions for a symbol."""
        partitions = populated_partitions.get_partitions_for_symbol("AAPL")
        
        assert len(partitions) == 2  # 2023 and 2024
        assert all(p.symbol == "AAPL" for p in partitions)
    
    def test_delete_partition(self, populated_partitions):
        """Test deleting a partition."""
        assert populated_partitions.partition_exists("AAPL", 2024)
        
        result = populated_partitions.delete_partition("AAPL", 2024)
        
        assert result is True
        assert not populated_partitions.partition_exists("AAPL", 2024)
    
    def test_delete_nonexistent_partition(self, partition_manager):
        """Test deleting non-existent partition."""
        result = partition_manager.delete_partition("AAPL", 2024)
        
        assert result is False
