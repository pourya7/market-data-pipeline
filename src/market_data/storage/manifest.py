"""Metadata manifest for tracking ticker updates and partition info."""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Any


@dataclass
class PartitionMetadata:
    """Metadata for a single partition."""
    start_date: str  # ISO format
    end_date: str    # ISO format
    rows: int
    last_modified: str  # ISO datetime
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "PartitionMetadata":
        return cls(**data)


@dataclass
class TickerInfo:
    """Metadata for a single ticker."""
    last_updated: str  # ISO datetime
    partitions: dict[str, PartitionMetadata] = field(default_factory=dict)  # year -> metadata
    
    def to_dict(self) -> dict:
        return {
            "last_updated": self.last_updated,
            "partitions": {
                year: pm.to_dict() for year, pm in self.partitions.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TickerInfo":
        partitions = {
            year: PartitionMetadata.from_dict(pm)
            for year, pm in data.get("partitions", {}).items()
        }
        return cls(
            last_updated=data["last_updated"],
            partitions=partitions,
        )


@dataclass
class Manifest:
    """Root manifest containing all ticker metadata."""
    version: str = "1.0"
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tickers: dict[str, TickerInfo] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "created": self.created,
            "tickers": {
                symbol: info.to_dict() for symbol, info in self.tickers.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Manifest":
        tickers = {
            symbol: TickerInfo.from_dict(info)
            for symbol, info in data.get("tickers", {}).items()
        }
        return cls(
            version=data.get("version", "1.0"),
            created=data.get("created", datetime.utcnow().isoformat()),
            tickers=tickers,
        )


class ManifestManager:
    """Manages the metadata manifest file.
    
    Tracks last_updated timestamps and partition info for each ticker
    to enable incremental updates.
    
    Example:
        mm = ManifestManager(Path("data/manifest.json"))
        manifest = mm.load()
        
        # Update after download
        mm.update_ticker(manifest, "AAPL", year=2024, ...)
        mm.save(manifest)
    """
    
    MANIFEST_FILENAME = "manifest.json"
    
    def __init__(self, path: str | Path):
        """Initialize manifest manager.
        
        Args:
            path: Path to manifest file or directory containing it.
        """
        path = Path(path)
        if path.is_dir():
            self.path = path / self.MANIFEST_FILENAME
        else:
            self.path = path
    
    def load(self) -> Manifest:
        """Load manifest from file.
        
        Returns:
            Manifest object (empty if file doesn't exist).
        """
        if not self.path.exists():
            return Manifest()
        
        with open(self.path, "r") as f:
            data = json.load(f)
        
        return Manifest.from_dict(data)
    
    def save(self, manifest: Manifest) -> None:
        """Save manifest to file.
        
        Args:
            manifest: Manifest to save.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.path, "w") as f:
            json.dump(manifest.to_dict(), f, indent=2)
    
    def update_ticker(
        self,
        manifest: Manifest,
        symbol: str,
        year: int,
        start_date: date | str,
        end_date: date | str,
        rows: int,
    ) -> Manifest:
        """Update ticker metadata in manifest.
        
        Args:
            manifest: Manifest to update.
            symbol: Ticker symbol.
            year: Year of the partition.
            start_date: First date in partition.
            end_date: Last date in partition.
            rows: Number of rows.
            
        Returns:
            Updated manifest.
        """
        symbol = symbol.upper()
        now = datetime.utcnow().isoformat()
        
        # Convert dates to ISO strings
        if isinstance(start_date, date):
            start_date = start_date.isoformat()
        if isinstance(end_date, date):
            end_date = end_date.isoformat()
        
        # Create or update ticker info
        if symbol not in manifest.tickers:
            manifest.tickers[symbol] = TickerInfo(last_updated=now)
        
        manifest.tickers[symbol].last_updated = now
        manifest.tickers[symbol].partitions[str(year)] = PartitionMetadata(
            start_date=start_date,
            end_date=end_date,
            rows=rows,
            last_modified=now,
        )
        
        return manifest
    
    def get_last_updated(
        self,
        manifest: Manifest,
        symbol: str,
    ) -> Optional[datetime]:
        """Get last update time for a ticker.
        
        Args:
            manifest: Manifest to query.
            symbol: Ticker symbol.
            
        Returns:
            Datetime of last update, or None if not found.
        """
        symbol = symbol.upper()
        
        if symbol not in manifest.tickers:
            return None
        
        try:
            return datetime.fromisoformat(manifest.tickers[symbol].last_updated)
        except (ValueError, TypeError):
            return None
    
    def get_last_date(
        self,
        manifest: Manifest,
        symbol: str,
        year: Optional[int] = None,
    ) -> Optional[date]:
        """Get the last data date for a ticker.
        
        Args:
            manifest: Manifest to query.
            symbol: Ticker symbol.
            year: Specific year, or None for latest across all years.
            
        Returns:
            Last date in data, or None if not found.
        """
        symbol = symbol.upper()
        
        if symbol not in manifest.tickers:
            return None
        
        ticker = manifest.tickers[symbol]
        
        if year is not None:
            partition = ticker.partitions.get(str(year))
            if partition:
                try:
                    return date.fromisoformat(partition.end_date)
                except (ValueError, TypeError):
                    return None
            return None
        
        # Find latest across all partitions
        latest = None
        for partition in ticker.partitions.values():
            try:
                end = date.fromisoformat(partition.end_date)
                if latest is None or end > latest:
                    latest = end
            except (ValueError, TypeError):
                continue
        
        return latest
    
    def list_symbols(self, manifest: Manifest) -> list[str]:
        """List all symbols in manifest.
        
        Args:
            manifest: Manifest to query.
            
        Returns:
            Sorted list of symbols.
        """
        return sorted(manifest.tickers.keys())
    
    def remove_ticker(self, manifest: Manifest, symbol: str) -> Manifest:
        """Remove a ticker from manifest.
        
        Args:
            manifest: Manifest to modify.
            symbol: Ticker to remove.
            
        Returns:
            Updated manifest.
        """
        symbol = symbol.upper()
        if symbol in manifest.tickers:
            del manifest.tickers[symbol]
        return manifest
