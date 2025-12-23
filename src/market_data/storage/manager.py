"""Unified storage manager for OHLCV data."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

from market_data.storage.parquet import ParquetWriter, ParquetReader
from market_data.storage.partitions import PartitionManager
from market_data.storage.manifest import ManifestManager, Manifest


@dataclass
class StorageConfig:
    """Configuration for the storage manager.
    
    Attributes:
        base_path: Root directory for data storage.
        compression: Parquet compression codec.
        manifest_filename: Name of the manifest file.
        update_threshold_hours: Hours before data is considered stale.
    """
    base_path: str | Path = "./data"
    compression: str = "snappy"
    manifest_filename: str = "manifest.json"
    update_threshold_hours: int = 24


class StorageManager:
    """Unified API for storing and retrieving OHLCV data.
    
    Manages Parquet files with year/ticker partitioning and tracks
    metadata for incremental updates.
    
    Example:
        storage = StorageManager(StorageConfig(base_path="./data"))
        
        # Save data
        storage.save(df, "AAPL")
        
        # Load data
        df = storage.load("AAPL", start_date="2024-01-01")
        
        # Check if update needed
        if storage.needs_update("AAPL"):
            new_data = fetch_new_data(...)
            storage.save(new_data, "AAPL")
    """
    
    def __init__(self, config: Optional[StorageConfig] = None):
        """Initialize storage manager.
        
        Args:
            config: Storage configuration.
        """
        self.config = config or StorageConfig()
        self.base_path = Path(self.config.base_path)
        
        self.writer = ParquetWriter(compression=self.config.compression)
        self.reader = ParquetReader()
        self.partitions = PartitionManager(self.base_path)
        self.manifest_manager = ManifestManager(
            self.base_path / self.config.manifest_filename
        )
        
        self._manifest: Optional[Manifest] = None
    
    @property
    def manifest(self) -> Manifest:
        """Get manifest, loading from disk if not cached."""
        if self._manifest is None:
            self._manifest = self.manifest_manager.load()
        return self._manifest
    
    def reload_manifest(self) -> Manifest:
        """Force reload manifest from disk and update cache."""
        self._manifest = self.manifest_manager.load()
        return self._manifest
    
    def clear_manifest_cache(self) -> None:
        """Clear the manifest cache to force reload on next access."""
        self._manifest = None
    
    def save(
        self,
        df: pd.DataFrame,
        symbol: str,
        mode: str = "overwrite",
    ) -> None:
        """Save OHLCV data to storage.
        
        Data is partitioned by year and saved to separate files.
        Manifest is updated with metadata.
        
        Args:
            df: DataFrame with DatetimeIndex.
            symbol: Ticker symbol.
            mode: "overwrite" (replace) or "append" (merge with existing).
        """
        if df.empty:
            return
        
        symbol = symbol.upper()
        
        # Ensure DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")
        
        # Group by year
        df = df.sort_index()
        df["_year"] = df.index.year
        
        for year, year_df in df.groupby("_year"):
            year_df = year_df.drop(columns=["_year"])
            partition_path = self.partitions.get_partition_path(symbol, year)
            
            if mode == "append" and partition_path.exists():
                # Merge with existing data
                existing = self.reader.read(partition_path)
                combined = pd.concat([existing, year_df])
                combined = combined[~combined.index.duplicated(keep="last")]
                combined = combined.sort_index()
                self.writer.write(combined, partition_path)
                rows = len(combined)
            else:
                self.writer.write(year_df, partition_path)
                rows = len(year_df)
            
            # Update manifest
            start_date = year_df.index.min().date()
            end_date = year_df.index.max().date()
            
            self.manifest_manager.update_ticker(
                self.manifest,
                symbol,
                year=year,
                start_date=start_date,
                end_date=end_date,
                rows=rows,
            )
        
        # Save updated manifest
        self.manifest_manager.save(self.manifest)
    
    def load(
        self,
        symbol: str,
        start_date: Optional[date | str] = None,
        end_date: Optional[date | str] = None,
        columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Load OHLCV data from storage.
        
        Args:
            symbol: Ticker symbol.
            start_date: Filter data from this date.
            end_date: Filter data until this date.
            columns: Columns to load (None = all).
            
        Returns:
            DataFrame with requested data.
        """
        symbol = symbol.upper()
        
        # Parse dates
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        
        # Determine which years to load
        partitions = self.partitions.get_partitions_for_symbol(symbol)
        
        if not partitions:
            return pd.DataFrame()
        
        # Filter by year range if dates provided
        if start_date:
            partitions = [p for p in partitions if p.year >= start_date.year]
        if end_date:
            partitions = [p for p in partitions if p.year <= end_date.year]
        
        if not partitions:
            return pd.DataFrame()
        
        # Load and combine
        dfs = []
        for partition in partitions:
            df = self.reader.read(partition.path, columns=columns)
            dfs.append(df)
        
        result = pd.concat(dfs) if len(dfs) > 1 else dfs[0]
        result = result.sort_index()
        
        # Apply date filters
        if start_date:
            result = result[result.index.date >= start_date]
        if end_date:
            result = result[result.index.date <= end_date]
        
        return result
    
    def needs_update(
        self,
        symbol: str,
        as_of: Optional[datetime] = None,
    ) -> bool:
        """Check if a symbol needs updating.
        
        Args:
            symbol: Ticker symbol.
            as_of: Reference time (default: now).
            
        Returns:
            True if data is stale or doesn't exist.
        """
        symbol = symbol.upper()
        as_of = as_of or datetime.utcnow()
        
        last_updated = self.manifest_manager.get_last_updated(self.manifest, symbol)
        
        if last_updated is None:
            return True
        
        threshold = timedelta(hours=self.config.update_threshold_hours)
        return (as_of - last_updated) > threshold
    
    def get_last_date(self, symbol: str) -> Optional[date]:
        """Get the last available date for a symbol.
        
        Args:
            symbol: Ticker symbol.
            
        Returns:
            Last date in storage, or None.
        """
        return self.manifest_manager.get_last_date(self.manifest, symbol)
    
    def get_available_symbols(self) -> list[str]:
        """Get list of all stored symbols.
        
        Returns:
            Sorted list of symbols.
        """
        return self.partitions.list_symbols()
    
    def get_available_years(self, symbol: Optional[str] = None) -> list[int]:
        """Get list of available years.
        
        Args:
            symbol: Filter to a specific symbol.
            
        Returns:
            Sorted list of years.
        """
        if symbol:
            partitions = self.partitions.get_partitions_for_symbol(symbol)
            return sorted(set(p.year for p in partitions))
        return self.partitions.list_years()
    
    def delete(self, symbol: str, year: Optional[int] = None) -> bool:
        """Delete stored data for a symbol.
        
        Args:
            symbol: Ticker symbol.
            year: Specific year to delete (None = all years).
            
        Returns:
            True if any data was deleted.
        """
        symbol = symbol.upper()
        deleted = False
        
        if year is not None:
            deleted = self.partitions.delete_partition(symbol, year)
        else:
            for partition in self.partitions.get_partitions_for_symbol(symbol):
                self.partitions.delete_partition(symbol, partition.year)
                deleted = True
            self.manifest_manager.remove_ticker(self.manifest, symbol)
        
        if deleted:
            self.manifest_manager.save(self.manifest)
        
        return deleted
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics.
        
        Returns:
            Dictionary with storage info.
        """
        partitions = self.partitions.list_partitions()
        total_size = sum(p.path.stat().st_size for p in partitions if p.path.exists())
        
        return {
            "base_path": str(self.base_path),
            "num_symbols": len(set(p.symbol for p in partitions)),
            "num_partitions": len(partitions),
            "num_years": len(self.partitions.list_years()),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
    
    def refresh_manifest(self) -> None:
        """Reload manifest from disk."""
        self._manifest = self.manifest_manager.load()
