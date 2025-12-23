"""Tick-based bar generation."""

from typing import Optional
import pandas as pd
import numpy as np


class TickBarGenerator:
    """Generate bars from a fixed number of ticks.
    
    Instead of time-based bars, tick bars form after a fixed number
    of trades/ticks. This provides constant information flow
    regardless of time.
    
    Example:
        generator = TickBarGenerator(ticks_per_bar=100)
        
        # From OHLCV data (each row = 1 tick)
        tick_bars = generator.generate(df_ticks)
        
        # From tick data
        tick_bars = generator.generate_from_ticks(ticks)
    """
    
    def __init__(self, ticks_per_bar: int):
        """Initialize tick bar generator.
        
        Args:
            ticks_per_bar: Number of ticks to form a bar.
        """
        if ticks_per_bar <= 0:
            raise ValueError("ticks_per_bar must be positive")
        
        self.ticks_per_bar = ticks_per_bar
    
    def generate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate tick bars from row data.
        
        Each row in the input DataFrame is treated as one tick.
        
        Args:
            df: DataFrame where each row is a tick.
            
        Returns:
            DataFrame with tick bars.
        """
        if df.empty:
            return df.copy()
        
        bars = []
        tick_count = 0
        bar_open = None
        bar_high = -np.inf
        bar_low = np.inf
        bar_start_time = None
        bar_volume = 0.0
        
        for timestamp, row in df.iterrows():
            # Get price - prefer close, then price column
            price = row.get("close", row.get("price"))
            if price is None:
                continue
            
            volume = row.get("volume", 1)
            
            # Start new bar if first tick
            if bar_open is None:
                bar_open = row.get("open", price)
                bar_start_time = timestamp
            
            # Update bar stats
            bar_high = max(bar_high, row.get("high", price))
            bar_low = min(bar_low, row.get("low", price))
            bar_volume += volume
            tick_count += 1
            
            # Check if we've hit the tick count
            if tick_count >= self.ticks_per_bar:
                bars.append({
                    "timestamp": bar_start_time,
                    "open": bar_open,
                    "high": bar_high,
                    "low": bar_low,
                    "close": price,
                    "volume": bar_volume,
                    "tick_count": tick_count,
                })
                
                # Reset for next bar
                tick_count = 0
                bar_open = None
                bar_high = -np.inf
                bar_low = np.inf
                bar_volume = 0.0
        
        # Add partial bar if there's remaining data
        if bar_open is not None and tick_count > 0:
            bars.append({
                "timestamp": bar_start_time,
                "open": bar_open,
                "high": bar_high if bar_high != -np.inf else bar_open,
                "low": bar_low if bar_low != np.inf else bar_open,
                "close": df.iloc[-1].get("close", df.iloc[-1].get("price")),
                "volume": bar_volume,
                "tick_count": tick_count,
            })
        
        if not bars:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume", "tick_count"])
        
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
        """Generate tick bars from tick data.
        
        Args:
            ticks: List of tick dictionaries.
            price_key: Key for price in tick dict.
            volume_key: Key for volume in tick dict.
            time_key: Key for timestamp in tick dict.
            
        Returns:
            DataFrame with tick bars.
        """
        if not ticks:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume", "tick_count"])
        
        bars = []
        tick_count = 0
        bar_open = None
        bar_high = -np.inf
        bar_low = np.inf
        bar_start_time = None
        bar_volume = 0.0
        
        for tick in ticks:
            price = tick[price_key]
            volume = tick.get(volume_key, 1)
            timestamp = tick[time_key]
            
            if bar_open is None:
                bar_open = price
                bar_start_time = timestamp
            
            bar_high = max(bar_high, price)
            bar_low = min(bar_low, price)
            bar_volume += volume
            tick_count += 1
            
            if tick_count >= self.ticks_per_bar:
                bars.append({
                    "timestamp": bar_start_time,
                    "open": bar_open,
                    "high": bar_high,
                    "low": bar_low,
                    "close": price,
                    "volume": bar_volume,
                    "tick_count": tick_count,
                })
                
                tick_count = 0
                bar_open = None
                bar_high = -np.inf
                bar_low = np.inf
                bar_volume = 0.0
        
        # Add partial bar
        if bar_open is not None and tick_count > 0:
            bars.append({
                "timestamp": bar_start_time,
                "open": bar_open,
                "high": bar_high if bar_high != -np.inf else bar_open,
                "low": bar_low if bar_low != np.inf else bar_open,
                "close": ticks[-1][price_key],
                "volume": bar_volume,
                "tick_count": tick_count,
            })
        
        if not bars:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume", "tick_count"])
        
        result = pd.DataFrame(bars)
        result.set_index("timestamp", inplace=True)
        
        return result
