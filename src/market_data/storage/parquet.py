"""Parquet I/O with PyArrow for efficient OHLCV storage."""

from pathlib import Path
from typing import Optional, Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


class ParquetWriter:
    """Write DataFrames to Parquet format with compression.
    
    Uses PyArrow for high-performance Parquet writing with
    configurable compression.
    
    Example:
        writer = ParquetWriter()
        writer.write(df, "data/AAPL.parquet")
    """
    
    DEFAULT_COMPRESSION = "snappy"
    
    def __init__(self, compression: str = DEFAULT_COMPRESSION):
        """Initialize writer with compression settings.
        
        Args:
            compression: Compression codec (snappy, gzip, zstd, none).
        """
        self.compression = compression
    
    def write(
        self,
        df: pd.DataFrame,
        path: str | Path,
        compression: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Write DataFrame to Parquet file.
        
        Args:
            df: DataFrame to write.
            path: Output file path.
            compression: Override default compression.
            **kwargs: Additional PyArrow write options.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        compression = compression or self.compression
        
        # Convert to PyArrow Table
        table = pa.Table.from_pandas(df)
        
        # Write with compression
        pq.write_table(
            table,
            path,
            compression=compression,
            **kwargs,
        )
    
    def write_partitioned(
        self,
        df: pd.DataFrame,
        base_path: str | Path,
        partition_cols: list[str],
        compression: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Write DataFrame with Hive-style partitioning.
        
        Args:
            df: DataFrame to write.
            base_path: Base directory for partitioned data.
            partition_cols: Columns to partition by.
            compression: Override default compression.
            **kwargs: Additional PyArrow write options.
        """
        base_path = Path(base_path)
        base_path.mkdir(parents=True, exist_ok=True)
        
        compression = compression or self.compression
        table = pa.Table.from_pandas(df)
        
        pq.write_to_dataset(
            table,
            root_path=str(base_path),
            partition_cols=partition_cols,
            compression=compression,
            **kwargs,
        )


class ParquetReader:
    """Read Parquet files with optional filtering and column selection.
    
    Supports predicate pushdown for efficient data loading.
    
    Example:
        reader = ParquetReader()
        df = reader.read("data/AAPL.parquet", columns=["close", "volume"])
    """
    
    def read(
        self,
        path: str | Path,
        columns: Optional[list[str]] = None,
        filters: Optional[list[tuple]] = None,
    ) -> pd.DataFrame:
        """Read Parquet file to DataFrame.
        
        Args:
            path: Path to Parquet file.
            columns: Columns to load (None = all).
            filters: PyArrow filter expressions for predicate pushdown.
                     Example: [("year", "=", 2024), ("volume", ">", 1000000)]
            
        Returns:
            DataFrame with requested data.
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Parquet file not found: {path}")
        
        # Use ParquetFile directly to avoid dataset auto-detection issues
        # when reading single files from a partitioned directory structure
        parquet_file = pq.ParquetFile(path)
        table = parquet_file.read(columns=columns)
        
        df = table.to_pandas()
        
        # Apply filters manually if provided (since we're not using dataset)
        if filters:
            for col, op, val in filters:
                if col in df.columns:
                    if op == "=":
                        df = df[df[col] == val]
                    elif op == "==":
                        df = df[df[col] == val]
                    elif op == ">":
                        df = df[df[col] > val]
                    elif op == ">=":
                        df = df[df[col] >= val]
                    elif op == "<":
                        df = df[df[col] < val]
                    elif op == "<=":
                        df = df[df[col] <= val]
        
        return df
    
    def read_partitioned(
        self,
        base_path: str | Path,
        columns: Optional[list[str]] = None,
        filters: Optional[list[tuple]] = None,
    ) -> pd.DataFrame:
        """Read partitioned Parquet dataset.
        
        Args:
            base_path: Base directory of partitioned dataset.
            columns: Columns to load.
            filters: Filter expressions.
            
        Returns:
            Combined DataFrame from all matching partitions.
        """
        base_path = Path(base_path)
        
        if not base_path.exists():
            raise FileNotFoundError(f"Dataset path not found: {base_path}")
        
        dataset = pq.ParquetDataset(
            base_path,
            filters=filters,
        )
        
        table = dataset.read(columns=columns)
        return table.to_pandas()
    
    def get_metadata(self, path: str | Path) -> dict:
        """Get Parquet file metadata.
        
        Args:
            path: Path to Parquet file.
            
        Returns:
            Dictionary with schema, row count, and file info.
        """
        path = Path(path)
        parquet_file = pq.ParquetFile(path)
        metadata = parquet_file.metadata
        
        return {
            "num_rows": metadata.num_rows,
            "num_columns": metadata.num_columns,
            "num_row_groups": metadata.num_row_groups,
            "created_by": metadata.created_by,
            "schema": [
                {"name": field.name, "type": str(field.type)}
                for field in parquet_file.schema_arrow
            ],
        }
    
    def get_schema(self, path: str | Path) -> pa.Schema:
        """Get PyArrow schema from Parquet file.
        
        Args:
            path: Path to Parquet file.
            
        Returns:
            PyArrow Schema object.
        """
        path = Path(path)
        parquet_file = pq.ParquetFile(path)
        return parquet_file.schema_arrow
