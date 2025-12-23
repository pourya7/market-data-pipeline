"""Volume-based bar generation."""

from typing import Optional
import pandas as pd
import numpy as np


class VolumeBarGenerator:
    """Generate bars based on volume thresholds.
    
    Instead of time-based bars, volume bars form when cumulative
    volume since the last bar exceeds a threshold. This can better
    represent actual market activity.
    
    Example:
        generator = VolumeBarGenerator(volume_threshold=1_000_000)
        
        # From OHLCV data (with volume column)
        volume_bars = generator.generate(df_1m)
        
        # From tick data
        volume_bars = generator.generate_from_ticks(ticks)
    """
    
    def __init__(self, volume_threshold: float):
        """Initialize volume bar generator.
        
        Args:
            volume_threshold: Volume required to form a new bar.
        """
        if volume_threshold <= 0:
            raise ValueError("volume_threshold must be positive")
        
        self.volume_threshold = volume_threshold
    
    def generate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate volume bars from OHLCV data.
        
        Args:
            df: OHLCV DataFrame with volume column.
            
        Returns:
            DataFrame with volume bars.
        """
        if df.empty:
            return df.copy()
        
        if "volume" not in df.columns:
            raise ValueError("DataFrame must have 'volume' column")
        
        bars = []
        cumulative_volume = 0.0
        bar_open = None
        bar_high = -np.inf
        bar_low = np.inf
        bar_start_time = None
        bar_volume = 0.0
        
        for timestamp, row in df.iterrows():
            price = row.get("close", row.get("price"))
            volume = row["volume"]
            
            # Start new bar if first row
            if bar_open is None:
                bar_open = row.get("open", price)
                bar_start_time = timestamp
            
            # Update bar stats
            bar_high = max(bar_high, row.get("high", price))
            bar_low = min(bar_low, row.get("low", price))
            bar_volume += volume
            cumulative_volume += volume
            
            # Check if we've hit the threshold
            if cumulative_volume >= self.volume_threshold:
                bars.append({
                    "timestamp": bar_start_time,
                    "open": bar_open,
                    "high": bar_high,
                    "low": bar_low,
                    "close": price,
                    "volume": bar_volume,
                })
                
                # Reset for next bar
                cumulative_volume = 0.0
                bar_open = None
                bar_high = -np.inf
                bar_low = np.inf
                bar_volume = 0.0
        
        # Add partial bar if there's remaining data
        if bar_open is not None and bar_volume > 0:
            bars.append({
                "timestamp": bar_start_time,
                "open": bar_open,
                "high": bar_high if bar_high != -np.inf else bar_open,
                "low": bar_low if bar_low != np.inf else bar_open,
                "close": df.iloc[-1].get("close", df.iloc[-1].get("price")),
                "volume": bar_volume,
            })
        
        if not bars:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        
        result = pd.DataFrame(bars)
        result.set_index("timestamp", inplace=True)
        result.index.name = df.index.name
        
        return result
    
    def generate_from_ticks(
        self,
        ticks: list[dict],
        price_key: str = "price",
        volume_key: str = "volume",
        time_key: str = "timestamp",
    ) -> pd.DataFrame:
        """Generate volume bars from tick data.
        
        Args:
            ticks: List of tick dictionaries.
            price_key: Key for price in tick dict.
            volume_key: Key for volume in tick dict.
            time_key: Key for timestamp in tick dict.
            
        Returns:
            DataFrame with volume bars.
        """
        if not ticks:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        
        bars = []
        cumulative_volume = 0.0
        bar_open = None
        bar_high = -np.inf
        bar_low = np.inf
        bar_start_time = None
        bar_volume = 0.0
        
        for tick in ticks:
            price = tick[price_key]
            volume = tick.get(volume_key, 1)  # Default to 1 if no volume
            timestamp = tick[time_key]
            
            if bar_open is None:
                bar_open = price
                bar_start_time = timestamp
            
            bar_high = max(bar_high, price)
            bar_low = min(bar_low, price)
            bar_volume += volume
            cumulative_volume += volume
            
            if cumulative_volume >= self.volume_threshold:
                bars.append({
                    "timestamp": bar_start_time,
                    "open": bar_open,
                    "high": bar_high,
                    "low": bar_low,
                    "close": price,
                    "volume": bar_volume,
                })
                
                cumulative_volume = 0.0
                bar_open = None
                bar_high = -np.inf
                bar_low = np.inf
                bar_volume = 0.0
        
        # Add partial bar
        if bar_open is not None and bar_volume > 0:
            bars.append({
                "timestamp": bar_start_time,
                "open": bar_open,
                "high": bar_high if bar_high != -np.inf else bar_open,
                "low": bar_low if bar_low != np.inf else bar_open,
                "close": ticks[-1][price_key],
                "volume": bar_volume,
            })
        
        if not bars:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        
        result = pd.DataFrame(bars)
        result.set_index("timestamp", inplace=True)
        
        return result
