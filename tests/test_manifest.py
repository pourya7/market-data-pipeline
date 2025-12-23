"""Tests for metadata manifest."""

import pytest
import json
from pathlib import Path
from datetime import date, datetime
import tempfile
import shutil

from market_data.storage.manifest import (
    ManifestManager,
    Manifest,
    TickerInfo,
    PartitionMetadata,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path)


@pytest.fixture
def manifest_manager(temp_dir):
    """Create manifest manager."""
    return ManifestManager(temp_dir / "manifest.json")


class TestManifest:
    """Tests for Manifest dataclass."""
    
    def test_empty_manifest(self):
        """Test creating empty manifest."""
        manifest = Manifest()
        
        assert manifest.version == "1.0"
        assert manifest.tickers == {}
    
    def test_to_dict(self):
        """Test converting manifest to dict."""
        manifest = Manifest()
        data = manifest.to_dict()
        
        assert data["version"] == "1.0"
        assert "tickers" in data
    
    def test_from_dict(self):
        """Test creating manifest from dict."""
        data = {
            "version": "1.0",
            "created": "2024-01-01T00:00:00",
            "tickers": {}
        }
        manifest = Manifest.from_dict(data)
        
        assert manifest.version == "1.0"


class TestManifestManager:
    """Tests for ManifestManager."""
    
    def test_load_nonexistent(self, manifest_manager):
        """Test loading non-existent manifest returns empty."""
        manifest = manifest_manager.load()
        
        assert isinstance(manifest, Manifest)
        assert manifest.tickers == {}
    
    def test_save_and_load(self, manifest_manager):
        """Test saving and loading manifest."""
        manifest = Manifest()
        manifest.tickers["AAPL"] = TickerInfo(last_updated="2024-01-01T00:00:00")
        
        manifest_manager.save(manifest)
        loaded = manifest_manager.load()
        
        assert "AAPL" in loaded.tickers
    
    def test_update_ticker(self, manifest_manager):
        """Test updating ticker metadata."""
        manifest = Manifest()
        
        manifest_manager.update_ticker(
            manifest,
            symbol="AAPL",
            year=2024,
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 31),
            rows=22,
        )
        
        assert "AAPL" in manifest.tickers
        assert "2024" in manifest.tickers["AAPL"].partitions
        assert manifest.tickers["AAPL"].partitions["2024"].rows == 22
    
    def test_get_last_updated(self, manifest_manager):
        """Test getting last update time."""
        manifest = Manifest()
        now = datetime.utcnow().isoformat()
        manifest.tickers["AAPL"] = TickerInfo(last_updated=now)
        
        result = manifest_manager.get_last_updated(manifest, "AAPL")
        
        assert result is not None
        assert isinstance(result, datetime)
    
    def test_get_last_updated_not_found(self, manifest_manager):
        """Test getting last update for missing symbol."""
        manifest = Manifest()
        
        result = manifest_manager.get_last_updated(manifest, "AAPL")
        
        assert result is None
    
    def test_get_last_date(self, manifest_manager):
        """Test getting last data date."""
        manifest = Manifest()
        manifest_manager.update_ticker(
            manifest,
            symbol="AAPL",
            year=2024,
            start_date="2024-01-02",
            end_date="2024-01-31",
            rows=22,
        )
        
        result = manifest_manager.get_last_date(manifest, "AAPL")
        
        assert result == date(2024, 1, 31)
    
    def test_get_last_date_specific_year(self, manifest_manager):
        """Test getting last date for specific year."""
        manifest = Manifest()
        manifest_manager.update_ticker(manifest, "AAPL", 2023, "2023-01-02", "2023-12-29", 250)
        manifest_manager.update_ticker(manifest, "AAPL", 2024, "2024-01-02", "2024-01-31", 22)
        
        result = manifest_manager.get_last_date(manifest, "AAPL", year=2023)
        
        assert result == date(2023, 12, 29)
    
    def test_list_symbols(self, manifest_manager):
        """Test listing symbols in manifest."""
        manifest = Manifest()
        manifest_manager.update_ticker(manifest, "AAPL", 2024, "2024-01-02", "2024-01-31", 22)
        manifest_manager.update_ticker(manifest, "MSFT", 2024, "2024-01-02", "2024-01-31", 22)
        
        symbols = manifest_manager.list_symbols(manifest)
        
        assert symbols == ["AAPL", "MSFT"]
    
    def test_remove_ticker(self, manifest_manager):
        """Test removing ticker from manifest."""
        manifest = Manifest()
        manifest_manager.update_ticker(manifest, "AAPL", 2024, "2024-01-02", "2024-01-31", 22)
        
        manifest_manager.remove_ticker(manifest, "AAPL")
        
        assert "AAPL" not in manifest.tickers
