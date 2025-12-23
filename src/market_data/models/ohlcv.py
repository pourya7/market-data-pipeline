"""OHLCV data models with Pydantic validation."""

from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class OHLCVBar(BaseModel):
    """Single OHLCV bar with strict validation.
    
    Represents one candlestick/bar of price data with open, high, low, close, volume.
    """
    
    timestamp: datetime = Field(..., description="Bar timestamp (start of period)")
    open: float = Field(..., gt=0, description="Opening price")
    high: float = Field(..., gt=0, description="High price")
    low: float = Field(..., gt=0, description="Low price")
    close: float = Field(..., gt=0, description="Closing price")
    volume: float = Field(..., ge=0, description="Trading volume")
    symbol: str = Field(..., min_length=1, description="Ticker symbol")
    provider: str = Field(..., min_length=1, description="Data provider name")
    interval: str = Field(default="1d", description="Bar interval (1m, 5m, 1h, 1d, etc.)")
    
    model_config = {
        "frozen": True,  # Immutable after creation
        "str_strip_whitespace": True,
    }
    
    @model_validator(mode="after")
    def validate_ohlcv_relationships(self) -> Self:
        """Validate OHLCV price relationships.
        
        Ensures:
        - high >= low
        - high >= open
        - high >= close
        - low <= open
        - low <= close
        """
        if self.high < self.low:
            raise ValueError("high must be >= low")
        if self.high < self.open:
            raise ValueError("high must be >= open")
        if self.high < self.close:
            raise ValueError("high must be >= close")
        if self.low > self.open:
            raise ValueError("low must be <= open")
        if self.low > self.close:
            raise ValueError("low must be <= close")
        return self


class OHLCVDataset(BaseModel):
    """Collection of OHLCV bars for a single symbol.
    
    Provides utilities for converting to/from pandas/polars DataFrames.
    """
    
    symbol: str = Field(..., min_length=1)
    provider: str = Field(..., min_length=1)
    interval: str = Field(default="1d")
    bars: list[OHLCVBar] = Field(default_factory=list)
    
    model_config = {
        "str_strip_whitespace": True,
    }
    
    def to_pandas(self):
        """Convert to pandas DataFrame."""
        import pandas as pd
        
        if not self.bars:
            return pd.DataFrame(columns=[
                "timestamp", "open", "high", "low", "close", "volume",
                "symbol", "provider", "interval"
            ])
        
        data = [bar.model_dump() for bar in self.bars]
        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df
    
    def to_polars(self):
        """Convert to polars DataFrame."""
        import polars as pl
        
        if not self.bars:
            return pl.DataFrame(schema={
                "timestamp": pl.Datetime,
                "open": pl.Float64,
                "high": pl.Float64,
                "low": pl.Float64,
                "close": pl.Float64,
                "volume": pl.Float64,
                "symbol": pl.Utf8,
                "provider": pl.Utf8,
                "interval": pl.Utf8,
            })
        
        data = [bar.model_dump() for bar in self.bars]
        return pl.DataFrame(data)
    
    def __len__(self) -> int:
        return len(self.bars)
    
    def __iter__(self):
        return iter(self.bars)
