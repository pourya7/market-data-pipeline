"""Technical Analysis indicators using pure pandas.

Since pandas-ta doesn't support Python 3.14, we implement common
technical indicators using pandas directly.
"""

from typing import Optional
import pandas as pd
import numpy as np


class TechnicalAnalyzer:
    """Technical Analysis calculator using pure pandas.
    
    Provides a clean interface for adding common technical indicators
    to OHLCV DataFrames without external dependencies.
    
    Example:
        analyzer = TechnicalAnalyzer()
        df = analyzer.add_rsi(df, length=14)
        df = analyzer.add_macd(df)
        df = analyzer.add_defaults(df)
    """
    
    def add_rsi(
        self,
        df: pd.DataFrame,
        length: int = 14,
        column: str = "close",
    ) -> pd.DataFrame:
        """Add Relative Strength Index (RSI).
        
        Args:
            df: OHLCV DataFrame.
            length: RSI period.
            column: Column to calculate RSI from.
            
        Returns:
            DataFrame with RSI column added.
        """
        result = df.copy()
        
        # Calculate price changes
        delta = result[column].diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0.0)
        losses = (-delta).where(delta < 0, 0.0)
        
        # Calculate average gains and losses (Wilder's smoothing)
        avg_gains = gains.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        result[f"rsi_{length}"] = rsi
        return result
    
    def add_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        column: str = "close",
    ) -> pd.DataFrame:
        """Add Moving Average Convergence Divergence (MACD).
        
        Args:
            df: OHLCV DataFrame.
            fast: Fast EMA period.
            slow: Slow EMA period.
            signal: Signal line period.
            column: Column to calculate MACD from.
            
        Returns:
            DataFrame with MACD, MACD signal, and MACD histogram columns.
        """
        result = df.copy()
        
        # Calculate EMAs
        ema_fast = result[column].ewm(span=fast, adjust=False).mean()
        ema_slow = result[column].ewm(span=slow, adjust=False).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        # Histogram
        histogram = macd_line - signal_line
        
        result[f"macd_{fast}_{slow}_{signal}"] = macd_line
        result[f"macd_signal_{fast}_{slow}_{signal}"] = signal_line
        result[f"macd_hist_{fast}_{slow}_{signal}"] = histogram
        
        return result
    
    def add_bbands(
        self,
        df: pd.DataFrame,
        length: int = 20,
        std: float = 2.0,
        column: str = "close",
    ) -> pd.DataFrame:
        """Add Bollinger Bands.
        
        Args:
            df: OHLCV DataFrame.
            length: Moving average period.
            std: Standard deviation multiplier.
            column: Column to calculate bands from.
            
        Returns:
            DataFrame with lower, mid, upper band columns.
        """
        result = df.copy()
        
        # Middle band (SMA)
        middle = result[column].rolling(window=length).mean()
        
        # Standard deviation
        rolling_std = result[column].rolling(window=length).std()
        
        # Upper and lower bands
        upper = middle + (rolling_std * std)
        lower = middle - (rolling_std * std)
        
        # Bandwidth and %B
        bandwidth = (upper - lower) / middle * 100
        percent_b = (result[column] - lower) / (upper - lower)
        
        result[f"bband_lower_{length}"] = lower
        result[f"bband_mid_{length}"] = middle
        result[f"bband_upper_{length}"] = upper
        result[f"bband_bandwidth_{length}"] = bandwidth
        result[f"bband_percent_{length}"] = percent_b
        
        return result
    
    def add_sma(
        self,
        df: pd.DataFrame,
        length: int = 20,
        column: str = "close",
    ) -> pd.DataFrame:
        """Add Simple Moving Average (SMA).
        
        Args:
            df: OHLCV DataFrame.
            length: SMA period.
            column: Column to calculate SMA from.
            
        Returns:
            DataFrame with SMA column added.
        """
        result = df.copy()
        sma = result[column].rolling(window=length).mean()
        result[f"sma_{length}"] = sma
        return result
    
    def add_ema(
        self,
        df: pd.DataFrame,
        length: int = 20,
        column: str = "close",
    ) -> pd.DataFrame:
        """Add Exponential Moving Average (EMA).
        
        Args:
            df: OHLCV DataFrame.
            length: EMA period.
            column: Column to calculate EMA from.
            
        Returns:
            DataFrame with EMA column added.
        """
        result = df.copy()
        ema = result[column].ewm(span=length, adjust=False).mean()
        result[f"ema_{length}"] = ema
        return result
    
    def add_atr(
        self,
        df: pd.DataFrame,
        length: int = 14,
    ) -> pd.DataFrame:
        """Add Average True Range (ATR).
        
        Args:
            df: OHLCV DataFrame with high, low, close columns.
            length: ATR period.
            
        Returns:
            DataFrame with ATR column added.
        """
        result = df.copy()
        
        # True Range components
        high_low = result["high"] - result["low"]
        high_close = (result["high"] - result["close"].shift()).abs()
        low_close = (result["low"] - result["close"].shift()).abs()
        
        # True Range is the max of the three
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # ATR is the EMA of True Range
        atr = true_range.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
        
        result[f"atr_{length}"] = atr
        return result
    
    def add_volume_sma(
        self,
        df: pd.DataFrame,
        length: int = 20,
    ) -> pd.DataFrame:
        """Add Volume Simple Moving Average.
        
        Args:
            df: OHLCV DataFrame with volume column.
            length: SMA period.
            
        Returns:
            DataFrame with volume SMA column added.
        """
        result = df.copy()
        vol_sma = result["volume"].rolling(window=length).mean()
        result[f"volume_sma_{length}"] = vol_sma
        return result
    
    def add_stochastic(
        self,
        df: pd.DataFrame,
        k_length: int = 14,
        d_length: int = 3,
    ) -> pd.DataFrame:
        """Add Stochastic Oscillator.
        
        Args:
            df: OHLCV DataFrame.
            k_length: %K period.
            d_length: %D smoothing period.
            
        Returns:
            DataFrame with %K and %D columns added.
        """
        result = df.copy()
        
        # Highest high and lowest low
        lowest_low = result["low"].rolling(window=k_length).min()
        highest_high = result["high"].rolling(window=k_length).max()
        
        # %K
        stoch_k = 100 * (result["close"] - lowest_low) / (highest_high - lowest_low)
        
        # %D (SMA of %K)
        stoch_d = stoch_k.rolling(window=d_length).mean()
        
        result[f"stoch_k_{k_length}"] = stoch_k
        result[f"stoch_d_{k_length}_{d_length}"] = stoch_d
        
        return result
    
    def add_defaults(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add a default set of commonly used indicators.
        
        Adds: RSI(14), MACD(12,26,9), BBands(20,2), SMA(20,50), EMA(12,26), ATR(14)
        
        Args:
            df: OHLCV DataFrame.
            
        Returns:
            DataFrame with all default indicators added.
        """
        result = df.copy()
        
        # Momentum
        result = self.add_rsi(result, length=14)
        result = self.add_macd(result)
        result = self.add_stochastic(result)
        
        # Volatility
        result = self.add_bbands(result, length=20, std=2.0)
        result = self.add_atr(result, length=14)
        
        # Trend
        result = self.add_sma(result, length=20)
        result = self.add_sma(result, length=50)
        result = self.add_ema(result, length=12)
        result = self.add_ema(result, length=26)
        
        # Volume
        result = self.add_volume_sma(result, length=20)
        
        return result
    
    def apply_indicators(
        self,
        df: pd.DataFrame,
        indicators: list[dict],
    ) -> pd.DataFrame:
        """Apply a list of indicators from configuration.
        
        Args:
            df: OHLCV DataFrame.
            indicators: List of indicator configs with 'name' and 'params' keys.
            
        Returns:
            DataFrame with all specified indicators added.
        """
        result = df.copy()
        
        indicator_methods = {
            "rsi": self.add_rsi,
            "macd": self.add_macd,
            "bbands": self.add_bbands,
            "sma": self.add_sma,
            "ema": self.add_ema,
            "atr": self.add_atr,
            "volume_sma": self.add_volume_sma,
            "stochastic": self.add_stochastic,
        }
        
        for indicator in indicators:
            name = indicator.get("name", "").lower()
            params = indicator.get("params", {})
            
            if name in indicator_methods:
                method = indicator_methods[name]
                result = method(result, **params)
            else:
                raise ValueError(f"Unknown indicator: {name}")
        
        return result
    
    def get_available_indicators(self) -> list[str]:
        """Get list of available indicator names.
        
        Returns:
            List of indicator names that can be used in apply_indicators.
        """
        return [
            "rsi",
            "macd", 
            "bbands",
            "sma",
            "ema",
            "atr",
            "volume_sma",
            "stochastic",
        ]
