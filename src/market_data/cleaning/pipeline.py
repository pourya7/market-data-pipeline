"""Unified data cleaning pipeline."""

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from market_data.cleaning.schemas import validate_ohlcv, OHLCVSchema
from market_data.cleaning.adjuster import CorporateActionAdjuster, CorporateAction
from market_data.cleaning.gap_handler import GapHandler, GapStrategy


@dataclass
class CleaningConfig:
    """Configuration for the data cleaning pipeline.
    
    Attributes:
        validate_input: Whether to validate input data.
        validate_output: Whether to validate output data.
        gap_strategy: Strategy for handling missing data.
        max_gap_size: Maximum consecutive gaps to fill.
        freq: Expected data frequency.
        trading_days_only: Whether to only consider trading days.
        apply_adjustments: Whether to apply corporate actions.
    """
    
    validate_input: bool = True
    validate_output: bool = True
    gap_strategy: GapStrategy = GapStrategy.FORWARD_FILL
    max_gap_size: Optional[int] = 5
    freq: str = "1D"
    trading_days_only: bool = True
    apply_adjustments: bool = True
    raise_on_validation_error: bool = True


class DataCleaner:
    """Unified pipeline for cleaning OHLCV data.
    
    Orchestrates:
    1. Input validation (schema check)
    2. Corporate action adjustments (splits/dividends)
    3. Gap detection and filling
    4. Output validation
    
    Example:
        cleaner = DataCleaner()
        clean_df = cleaner.clean(raw_df)
        
        # With corporate actions
        from market_data.cleaning import CorporateAction, AdjustmentType
        actions = [CorporateAction(AdjustmentType.SPLIT, "2024-01-15", 4.0)]
        clean_df = cleaner.clean(raw_df, corporate_actions=actions)
    """
    
    def __init__(self, config: Optional[CleaningConfig] = None):
        """Initialize the cleaner with configuration.
        
        Args:
            config: Cleaning configuration (uses defaults if None).
        """
        self.config = config or CleaningConfig()
        self.adjuster = CorporateActionAdjuster()
        self.gap_handler = GapHandler(
            strategy=self.config.gap_strategy,
            max_gap_size=self.config.max_gap_size,
        )
        self._last_validation_errors = None
        self._last_gap_stats = None
    
    def clean(
        self,
        df: pd.DataFrame,
        corporate_actions: Optional[list[CorporateAction]] = None,
    ) -> pd.DataFrame:
        """Clean OHLCV data through the full pipeline.
        
        Args:
            df: Raw OHLCV DataFrame with DatetimeIndex.
            corporate_actions: Optional list of corporate actions to apply.
            
        Returns:
            Cleaned DataFrame.
            
        Raises:
            pandera.errors.SchemaErrors: If validation fails.
            ValueError: If data format is invalid.
        """
        result = df.copy()
        
        # Step 1: Input validation
        if self.config.validate_input:
            result, errors = validate_ohlcv(
                result,
                raise_on_error=self.config.raise_on_validation_error,
            )
            self._last_validation_errors = errors
        
        # Step 2: Corporate action adjustments
        if self.config.apply_adjustments and corporate_actions:
            result = self.adjuster.apply(result, corporate_actions)
        
        # Step 3: Gap handling
        self._last_gap_stats = self.gap_handler.get_gap_statistics(
            result, freq=self.config.freq
        )
        
        if self._last_gap_stats["total_gaps"] > 0:
            result = self.gap_handler.fill_gaps(
                result,
                freq=self.config.freq,
                trading_days_only=self.config.trading_days_only,
            )
        
        # Step 4: Output validation
        if self.config.validate_output:
            # Check for adj_close if adjustments were applied
            include_adjusted = (
                self.config.apply_adjustments and 
                corporate_actions is not None and 
                "adj_close" in result.columns
            )
            result, _ = validate_ohlcv(
                result,
                raise_on_error=self.config.raise_on_validation_error,
                include_adjusted=include_adjusted,
            )
        
        return result
    
    def validate_only(self, df: pd.DataFrame) -> tuple[bool, list[dict]]:
        """Validate data without cleaning.
        
        Args:
            df: DataFrame to validate.
            
        Returns:
            Tuple of (is_valid, list of error dicts).
        """
        from market_data.cleaning.schemas import get_validation_errors
        
        errors = get_validation_errors(df)
        return len(errors) == 0, errors
    
    def detect_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect gaps without filling.
        
        Args:
            df: DataFrame to check for gaps.
            
        Returns:
            DataFrame of detected gaps.
        """
        return self.gap_handler.detect_gaps(
            df,
            freq=self.config.freq,
            trading_days_only=self.config.trading_days_only,
        )
    
    @property
    def last_validation_errors(self):
        """Get errors from the last validation."""
        return self._last_validation_errors
    
    @property
    def last_gap_stats(self) -> dict:
        """Get gap statistics from the last clean operation."""
        return self._last_gap_stats or {}
    
    def get_cleaning_report(self) -> dict:
        """Get a summary report of the last cleaning operation.
        
        Returns:
            Dictionary with validation and gap-filling details.
        """
        return {
            "validation_errors": self._last_validation_errors,
            "gap_statistics": self._last_gap_stats,
            "config": {
                "gap_strategy": self.config.gap_strategy.value,
                "max_gap_size": self.config.max_gap_size,
                "freq": self.config.freq,
            }
        }
