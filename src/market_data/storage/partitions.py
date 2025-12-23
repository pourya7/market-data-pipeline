"""Partition management for year/ticker data layout."""

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional


@dataclass
class PartitionInfo:
    """Information about a single partition.
    
    Attributes:
        symbol: Ticker symbol.
        year: Year of the partition.
        path: Full path to the parquet file.
        start_date: First date in partition.
        end_date: Last date in partition.
        rows: Number of rows in partition.
    """
    symbol: str
    year: int
    path: Path
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    rows: int = 0


class PartitionManager:
    """Manages year/ticker partitioned data layout.
    
    Layout: {base_path}/year={YYYY}/{SYMBOL}.parquet
    
    Example:
        pm = PartitionManager(Path("data"))
        path = pm.get_partition_path("AAPL", 2024)
        # Returns: data/year=2024/AAPL.parquet
    """
    
    def __init__(self, base_path: str | Path):
        """Initialize partition manager.
        
        Args:
            base_path: Root directory for data storage.
        """
        self.base_path = Path(base_path)
    
    def get_partition_path(self, symbol: str, year: int) -> Path:
        """Get the path for a specific symbol/year partition.
        
        Args:
            symbol: Ticker symbol.
            year: Year for the partition.
            
        Returns:
            Full path to the parquet file.
        """
        return self.base_path / f"year={year}" / f"{symbol.upper()}.parquet"
    
    def get_year_directory(self, year: int) -> Path:
        """Get the directory for a specific year.
        
        Args:
            year: Year.
            
        Returns:
            Path to year directory.
        """
        return self.base_path / f"year={year}"
    
    def list_partitions(self) -> list[PartitionInfo]:
        """List all existing partitions.
        
        Returns:
            List of PartitionInfo objects for all partitions.
        """
        partitions = []
        
        if not self.base_path.exists():
            return partitions
        
        for year_dir in sorted(self.base_path.glob("year=*")):
            if not year_dir.is_dir():
                continue
            
            try:
                year = int(year_dir.name.split("=")[1])
            except (ValueError, IndexError):
                continue
            
            for parquet_file in sorted(year_dir.glob("*.parquet")):
                symbol = parquet_file.stem
                partitions.append(PartitionInfo(
                    symbol=symbol,
                    year=year,
                    path=parquet_file,
                ))
        
        return partitions
    
    def list_years(self) -> list[int]:
        """List all available years.
        
        Returns:
            Sorted list of years with data.
        """
        years = []
        
        if not self.base_path.exists():
            return years
        
        for year_dir in self.base_path.glob("year=*"):
            if year_dir.is_dir():
                try:
                    year = int(year_dir.name.split("=")[1])
                    years.append(year)
                except (ValueError, IndexError):
                    pass
        
        return sorted(years)
    
    def list_symbols(self, year: Optional[int] = None) -> list[str]:
        """List available symbols.
        
        Args:
            year: If provided, only list symbols for this year.
            
        Returns:
            Sorted list of unique symbols.
        """
        symbols = set()
        
        if year is not None:
            year_dir = self.get_year_directory(year)
            if year_dir.exists():
                for f in year_dir.glob("*.parquet"):
                    symbols.add(f.stem)
        else:
            for partition in self.list_partitions():
                symbols.add(partition.symbol)
        
        return sorted(symbols)
    
    def get_symbols_for_year(self, year: int) -> list[str]:
        """Get all symbols available for a specific year.
        
        Args:
            year: Year to query.
            
        Returns:
            List of symbol names.
        """
        return self.list_symbols(year=year)
    
    def partition_exists(self, symbol: str, year: int) -> bool:
        """Check if a partition exists.
        
        Args:
            symbol: Ticker symbol.
            year: Year.
            
        Returns:
            True if partition file exists.
        """
        return self.get_partition_path(symbol, year).exists()
    
    def get_partitions_for_symbol(self, symbol: str) -> list[PartitionInfo]:
        """Get all partitions for a symbol.
        
        Args:
            symbol: Ticker symbol.
            
        Returns:
            List of partitions for the symbol.
        """
        return [p for p in self.list_partitions() if p.symbol.upper() == symbol.upper()]
    
    def delete_partition(self, symbol: str, year: int) -> bool:
        """Delete a partition file.
        
        Args:
            symbol: Ticker symbol.
            year: Year.
            
        Returns:
            True if deleted, False if not found.
        """
        path = self.get_partition_path(symbol, year)
        if path.exists():
            path.unlink()
            return True
        return False
    
    @staticmethod
    def extract_year_from_timestamp(ts: datetime | date) -> int:
        """Extract year from a timestamp.
        
        Args:
            ts: Datetime or date object.
            
        Returns:
            Year as integer.
        """
        if isinstance(ts, datetime):
            return ts.year
        return ts.year
