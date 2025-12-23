"""Time-based OHLCV resampling."""

from typing import Optional, Union
import pandas as pd


class TimeResampler:
    """Convert OHLCV data to different timeframes.
    
    Properly aggregates OHLCV data using standard rules:
    - open: first value
    - high: maximum value
    - low: minimum value
    - close: last value
    - volume: sum of all values
    
    Example:
        resampler = TimeResampler()
        
        # Convert 1-minute data to 15-minute bars
        df_15m = resampler.resample(df_1m, "15min")
        
        # Convert to hourly
        df_1h = resampler.to_hourly(df_1m)
        
        # Convert to daily
        df_daily = resampler.to_daily(df_1m)
    """
    
    # Standard OHLCV aggregation rules
    OHLC_RULES = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    
    # Timeframe aliases
    TIMEFRAME_MAP = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "12h": "12h",
        "1d": "1D",
        "1D": "1D",
        "1w": "1W",
        "1W": "1W",
        "1M": "1MS",  # Month start
    }
    
    def resample(
        self,
        df: pd.DataFrame,
        timeframe: str,
        label: str = "left",
        closed: str = "left",
    ) -> pd.DataFrame:
        """Resample OHLCV data to a different timeframe.
        
        Args:
            df: OHLCV DataFrame with DatetimeIndex.
            timeframe: Target timeframe (e.g., "5min", "1h", "1D").
            label: Which bin edge to label ('left' or 'right').
            closed: Which side of bin interval is closed ('left' or 'right').
            
        Returns:
            Resampled DataFrame.
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")
        
        if df.empty:
            return df.copy()
        
        # Normalize timeframe
        tf = self.TIMEFRAME_MAP.get(timeframe, timeframe)
        
        # Build aggregation rules for available columns
        agg_rules = {}
        for col, rule in self.OHLC_RULES.items():
            if col in df.columns:
                agg_rules[col] = rule
        
        # Add any additional numeric columns (features) as 'last'
        for col in df.columns:
            if col not in agg_rules and pd.api.types.is_numeric_dtype(df[col]):
                agg_rules[col] = "last"
        
        # Resample
        result = df.resample(tf, label=label, closed=closed).agg(agg_rules)
        
        # Drop rows where all OHLC values are NaN (no data in period)
        ohlc_cols = [c for c in ["open", "high", "low", "close"] if c in result.columns]
        if ohlc_cols:
            result = result.dropna(subset=ohlc_cols, how="all")
        
        return result
    
    def to_minutes(
        self,
        df: pd.DataFrame,
        minutes: int,
    ) -> pd.DataFrame:
        """Resample to N-minute bars.
        
        Args:
            df: OHLCV DataFrame.
            minutes: Number of minutes per bar.
            
        Returns:
            Resampled DataFrame.
        """
        return self.resample(df, f"{minutes}min")
    
    def to_hourly(
        self,
        df: pd.DataFrame,
        hours: int = 1,
    ) -> pd.DataFrame:
        """Resample to hourly bars.
        
        Args:
            df: OHLCV DataFrame.
            hours: Number of hours per bar.
            
        Returns:
            Resampled DataFrame.
        """
        return self.resample(df, f"{hours}h")
    
    def to_daily(self, df: pd.DataFrame) -> pd.DataFrame:
        """Resample to daily bars.
        
        Args:
            df: OHLCV DataFrame.
            
        Returns:
            Resampled DataFrame.
        """
        return self.resample(df, "1D")
    
    def to_weekly(self, df: pd.DataFrame) -> pd.DataFrame:
        """Resample to weekly bars.
        
        Args:
            df: OHLCV DataFrame.
            
        Returns:
            Resampled DataFrame.
        """
        return self.resample(df, "1W")
    
    def to_monthly(self, df: pd.DataFrame) -> pd.DataFrame:
        """Resample to monthly bars.
        
        Args:
            df: OHLCV DataFrame.
            
        Returns:
            Resampled DataFrame.
        """
        return self.resample(df, "1MS")
    
    def get_available_timeframes(self) -> list[str]:
        """Get list of supported timeframe aliases.
        
        Returns:
            List of timeframe strings.
        """
        return list(self.TIMEFRAME_MAP.keys())
