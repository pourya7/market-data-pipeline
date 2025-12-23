"""Missing data detection and gap filling strategies."""

from enum import Enum
from typing import Optional, Literal

import pandas as pd
import numpy as np


class GapStrategy(Enum):
    """Strategy for handling missing data gaps."""
    FORWARD_FILL = "forward_fill"   # Carry forward last known value
    BACKWARD_FILL = "backward_fill" # Carry backward next known value
    LINEAR = "linear"               # Linear interpolation
    DROP = "drop"                   # Drop rows with gaps
    NAN = "nan"                     # Keep as NaN (explicit marking)


class GapHandler:
    """Detects and fills gaps in OHLCV time-series data.
    
    Provides configurable strategies for handling missing data based
    on asset type and use case.
    
    Example:
        handler = GapHandler(strategy=GapStrategy.FORWARD_FILL)
        
        # Detect gaps
        gaps = handler.detect_gaps(df, freq="1D")
        
        # Fill gaps
        filled = handler.fill_gaps(df, freq="1D")
    """
    
    def __init__(
        self,
        strategy: GapStrategy = GapStrategy.FORWARD_FILL,
        max_gap_size: Optional[int] = None,
    ):
        """Initialize gap handler.
        
        Args:
            strategy: Default gap filling strategy.
            max_gap_size: Maximum consecutive gaps to fill (None = unlimited).
        """
        self.strategy = strategy
        self.max_gap_size = max_gap_size
    
    def detect_gaps(
        self,
        df: pd.DataFrame,
        freq: str = "1D",
        trading_days_only: bool = True,
    ) -> pd.DataFrame:
        """Detect gaps in time-series data.
        
        Args:
            df: OHLCV DataFrame with DatetimeIndex.
            freq: Expected frequency (e.g., "1D", "1h", "5min").
            trading_days_only: If True, only consider business days for daily data.
            
        Returns:
            DataFrame with missing timestamps and gap sizes.
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")
        
        if len(df) < 2:
            return pd.DataFrame(columns=["expected", "gap_size"])
        
        # Generate expected date range
        start = df.index.min()
        end = df.index.max()
        
        if trading_days_only and freq.upper() in ["1D", "D", "1B", "B"]:
            expected_index = pd.bdate_range(start=start, end=end, freq="B")
        else:
            expected_index = pd.date_range(start=start, end=end, freq=freq)
        
        # Normalize both indices to date-only (midnight) for comparison
        # This handles: 1) timezone mismatches, 2) time component differences
        df_dates = df.index.normalize()
        if df_dates.tz is not None:
            df_dates = df_dates.tz_localize(None)
        
        expected_dates = expected_index.normalize()
        if expected_dates.tz is not None:
            expected_dates = expected_dates.tz_localize(None)
        
        # Find missing dates
        missing = expected_dates.difference(df_dates)
        
        if len(missing) == 0:
            return pd.DataFrame(columns=["expected", "gap_size"])
        
        # Calculate gap sizes (consecutive missing dates)
        gap_info = []
        gap_start = None
        gap_count = 0
        
        for i, date in enumerate(expected_index):
            if date in missing:
                if gap_start is None:
                    gap_start = date
                gap_count += 1
            else:
                if gap_start is not None:
                    gap_info.append({
                        "expected": gap_start,
                        "gap_size": gap_count,
                    })
                    gap_start = None
                    gap_count = 0
        
        # Handle trailing gap
        if gap_start is not None:
            gap_info.append({
                "expected": gap_start,
                "gap_size": gap_count,
            })
        
        return pd.DataFrame(gap_info)
    
    def fill_gaps(
        self,
        df: pd.DataFrame,
        freq: str = "1D",
        strategy: Optional[GapStrategy] = None,
        trading_days_only: bool = True,
        columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Fill gaps in time-series data.
        
        Args:
            df: OHLCV DataFrame with DatetimeIndex.
            freq: Expected frequency.
            strategy: Gap filling strategy (uses instance default if None).
            trading_days_only: If True, only consider business days.
            columns: Columns to fill (None = all numeric columns).
            
        Returns:
            DataFrame with gaps filled according to strategy.
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")
        
        strategy = strategy or self.strategy
        
        if strategy == GapStrategy.DROP:
            return df.dropna()
        
        if strategy == GapStrategy.NAN:
            return self._add_missing_rows(df, freq, trading_days_only)
        
        # Reindex to include all expected dates
        result = self._add_missing_rows(df, freq, trading_days_only)
        
        # Determine columns to fill
        if columns is None:
            columns = result.select_dtypes(include=[np.number]).columns.tolist()
        
        # Apply fill strategy
        if strategy == GapStrategy.FORWARD_FILL:
            result = self._forward_fill(result, columns)
        elif strategy == GapStrategy.BACKWARD_FILL:
            result = self._backward_fill(result, columns)
        elif strategy == GapStrategy.LINEAR:
            result = self._linear_interpolate(result, columns)
        
        return result
    
    def _add_missing_rows(
        self,
        df: pd.DataFrame,
        freq: str,
        trading_days_only: bool,
    ) -> pd.DataFrame:
        """Add missing rows to DataFrame."""
        # Normalize index to midnight (removes time component)
        # This is needed because Pandera validation may add time offsets
        df = df.copy()
        original_name = df.index.name
        df.index = df.index.normalize()
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df.index.name = original_name
        
        start = df.index.min()
        end = df.index.max()
        
        if trading_days_only and freq.upper() in ["1D", "D", "1B", "B"]:
            full_index = pd.bdate_range(start=start, end=end, freq="B")
        else:
            full_index = pd.date_range(start=start, end=end, freq=freq)
        
        # Ensure both are tz-naive for reindex
        if full_index.tz is not None:
            full_index = full_index.tz_localize(None)
        
        return df.reindex(full_index)
    
    def _forward_fill(
        self,
        df: pd.DataFrame,
        columns: list[str],
    ) -> pd.DataFrame:
        """Apply forward fill with optional limit."""
        result = df.copy()
        for col in columns:
            if col in result.columns:
                result[col] = result[col].ffill(limit=self.max_gap_size)
        return result
    
    def _backward_fill(
        self,
        df: pd.DataFrame,
        columns: list[str],
    ) -> pd.DataFrame:
        """Apply backward fill with optional limit."""
        result = df.copy()
        for col in columns:
            if col in result.columns:
                result[col] = result[col].bfill(limit=self.max_gap_size)
        return result
    
    def _linear_interpolate(
        self,
        df: pd.DataFrame,
        columns: list[str],
    ) -> pd.DataFrame:
        """Apply linear interpolation with optional limit."""
        result = df.copy()
        for col in columns:
            if col in result.columns:
                result[col] = result[col].interpolate(
                    method="linear",
                    limit=self.max_gap_size,
                    limit_direction="both",
                )
        return result
    
    def get_gap_statistics(
        self,
        df: pd.DataFrame,
        freq: str = "1D",
    ) -> dict:
        """Get statistics about gaps in the data.
        
        Args:
            df: OHLCV DataFrame.
            freq: Expected frequency.
            
        Returns:
            Dictionary with gap statistics.
        """
        gaps = self.detect_gaps(df, freq)
        
        if len(gaps) == 0:
            return {
                "total_gaps": 0,
                "max_gap_size": 0,
                "mean_gap_size": 0,
                "gap_dates": [],
            }
        
        return {
            "total_gaps": len(gaps),
            "total_missing_bars": gaps["gap_size"].sum(),
            "max_gap_size": gaps["gap_size"].max(),
            "mean_gap_size": gaps["gap_size"].mean(),
            "gap_dates": gaps["expected"].tolist(),
        }
