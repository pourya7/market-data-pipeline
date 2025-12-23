"""Feature Pipeline for calculating and storing features."""

from pathlib import Path
from typing import Optional, Union

import pandas as pd

from market_data.features.technical import TechnicalAnalyzer
from market_data.features.config import FeatureConfig, IndicatorConfig
from market_data.storage import StorageManager, StorageConfig


class FeaturePipeline:
    """Orchestrate feature calculation and storage.
    
    Provides a unified interface for calculating technical indicators
    and storing them as extended columns in Parquet files.
    
    Example:
        config = FeatureConfig.default_config()
        storage = StorageManager(StorageConfig(base_path="./data"))
        pipeline = FeaturePipeline(config, storage)
        
        # Calculate and save features
        df_with_features = pipeline.calculate_features(df, asset_class="equity")
        pipeline.save_with_features(df_with_features, "AAPL")
        
        # Load data with features
        df = pipeline.load_with_features("AAPL")
    """
    
    def __init__(
        self,
        config: Optional[FeatureConfig] = None,
        storage: Optional[StorageManager] = None,
    ):
        """Initialize the feature pipeline.
        
        Args:
            config: Feature configuration. Uses defaults if not provided.
            storage: Storage manager. Created with defaults if not provided.
        """
        self.config = config or FeatureConfig.default_config()
        self.storage = storage
        self.analyzer = TechnicalAnalyzer()
        
        self._last_features: list[str] = []
    
    @property
    def last_features(self) -> list[str]:
        """Get list of feature columns from last calculation."""
        return self._last_features
    
    def calculate_features(
        self,
        df: pd.DataFrame,
        asset_class: Optional[str] = None,
        indicators: Optional[list[IndicatorConfig]] = None,
    ) -> pd.DataFrame:
        """Calculate technical indicators for a DataFrame.
        
        Args:
            df: OHLCV DataFrame with columns: open, high, low, close, volume.
            asset_class: Asset class to use for indicator selection.
            indicators: Override indicators (ignores config if provided).
            
        Returns:
            DataFrame with feature columns added.
        """
        # Get original columns
        original_cols = set(df.columns)
        
        # Determine which indicators to apply
        if indicators is not None:
            indicator_list = indicators
        else:
            indicator_list = self.config.get_indicators(asset_class)
        
        # Convert to dict format for analyzer
        indicator_dicts = [
            {"name": ind.name, "params": ind.params}
            for ind in indicator_list
        ]
        
        # Apply indicators
        result = self.analyzer.apply_indicators(df, indicator_dicts)
        
        # Track which columns were added
        new_cols = set(result.columns) - original_cols
        self._last_features = sorted(list(new_cols))
        
        return result
    
    def save_with_features(
        self,
        df: pd.DataFrame,
        symbol: str,
        mode: str = "overwrite",
        asset_class: Optional[str] = None,
        calculate: bool = True,
    ) -> None:
        """Calculate features and save to storage.
        
        Args:
            df: OHLCV DataFrame.
            symbol: Ticker symbol.
            mode: Storage mode ("overwrite" or "append").
            asset_class: Asset class for indicator selection.
            calculate: If True, calculate features before saving.
                       If False, assumes df already has features.
        """
        if self.storage is None:
            raise ValueError("Storage manager not configured")
        
        if calculate:
            df = self.calculate_features(df, asset_class=asset_class)
        
        self.storage.save(df, symbol, mode=mode)
    
    def load_with_features(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        recalculate: bool = False,
        asset_class: Optional[str] = None,
    ) -> pd.DataFrame:
        """Load data with features from storage.
        
        Args:
            symbol: Ticker symbol.
            start_date: Start date filter.
            end_date: End date filter.
            recalculate: If True, recalculate features even if present.
            asset_class: Asset class for indicator selection (if recalculating).
            
        Returns:
            DataFrame with OHLCV data and features.
        """
        if self.storage is None:
            raise ValueError("Storage manager not configured")
        
        df = self.storage.load(symbol, start_date=start_date, end_date=end_date)
        
        if recalculate:
            df = self.calculate_features(df, asset_class=asset_class)
        
        return df
    
    def get_feature_columns(self, df: pd.DataFrame) -> list[str]:
        """Get list of feature columns in a DataFrame.
        
        Args:
            df: DataFrame to inspect.
            
        Returns:
            List of column names that appear to be features.
        """
        ohlcv_cols = {"open", "high", "low", "close", "volume"}
        return [col for col in df.columns if col not in ohlcv_cols]
    
    def has_features(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame has feature columns.
        
        Args:
            df: DataFrame to check.
            
        Returns:
            True if DataFrame has feature columns.
        """
        return len(self.get_feature_columns(df)) > 0
    
    def calculate_defaults(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate default indicators without using config.
        
        This is a convenience method that adds a standard set of
        indicators without needing configuration.
        
        Args:
            df: OHLCV DataFrame.
            
        Returns:
            DataFrame with default indicators added.
        """
        original_cols = set(df.columns)
        result = self.analyzer.add_defaults(df)
        new_cols = set(result.columns) - original_cols
        self._last_features = sorted(list(new_cols))
        return result
