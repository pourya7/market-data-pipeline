"""Corporate action adjustments for stock splits and dividends."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional

import pandas as pd
import numpy as np


class AdjustmentType(Enum):
    """Type of corporate action adjustment."""
    SPLIT = "split"
    DIVIDEND = "dividend"


@dataclass
class CorporateAction:
    """Represents a single corporate action event.
    
    Attributes:
        action_type: Type of action (split or dividend).
        ex_date: Ex-dividend or effective date.
        ratio: Split ratio (e.g., 4.0 for 4:1 split) or dividend amount.
        symbol: Optional ticker symbol.
    """
    action_type: AdjustmentType
    ex_date: date | datetime
    ratio: float  # For splits: new/old ratio. For dividends: amount per share.
    symbol: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.ex_date, datetime):
            self.ex_date = self.ex_date.date()


class CorporateActionAdjuster:
    """Adjusts OHLCV data for stock splits and dividends.
    
    Provides backward adjustment (most common for backtesting) where
    historical prices are adjusted to be comparable to current prices.
    
    Example:
        adjuster = CorporateActionAdjuster()
        
        # Apply a 4:1 stock split
        split = CorporateAction(AdjustmentType.SPLIT, date(2024, 1, 15), 4.0)
        adjusted_df = adjuster.apply(df, [split])
    """
    
    def apply(
        self,
        df: pd.DataFrame,
        actions: list[CorporateAction],
        adjust_volume: bool = True,
    ) -> pd.DataFrame:
        """Apply corporate actions to OHLCV data.
        
        Args:
            df: OHLCV DataFrame with DatetimeIndex.
            actions: List of corporate actions to apply.
            adjust_volume: Whether to adjust volume for splits.
            
        Returns:
            Adjusted DataFrame with additional 'adj_close' column.
        """
        result = df.copy()
        
        # Ensure we have a DatetimeIndex
        if not isinstance(result.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")
        
        # Sort actions by date (newest first for backward adjustment)
        sorted_actions = sorted(actions, key=lambda a: a.ex_date, reverse=True)
        
        # Calculate cumulative adjustment factor
        adj_factor = pd.Series(1.0, index=result.index)
        
        for action in sorted_actions:
            if action.action_type == AdjustmentType.SPLIT:
                adj_factor = self._apply_split_factor(adj_factor, action)
            elif action.action_type == AdjustmentType.DIVIDEND:
                # For dividends, calculate adjustment based on close price
                adj_factor = self._apply_dividend_factor(
                    adj_factor, action, result["close"]
                )
        
        # Apply adjustment factors
        result["adj_close"] = result["close"] * adj_factor
        
        # Optionally create fully adjusted OHLCV
        if "adj_open" not in result.columns:
            result["adj_open"] = result["open"] * adj_factor
            result["adj_high"] = result["high"] * adj_factor
            result["adj_low"] = result["low"] * adj_factor
        
        if adjust_volume:
            # Volume is inversely adjusted for splits
            volume_factor = pd.Series(1.0, index=result.index)
            for action in sorted_actions:
                if action.action_type == AdjustmentType.SPLIT:
                    mask = result.index.date < action.ex_date
                    volume_factor[mask] *= action.ratio
            result["adj_volume"] = result["volume"] * volume_factor
        
        # Store adjustment factor for reference
        result["adj_factor"] = adj_factor
        
        return result
    
    def _apply_split_factor(
        self,
        factor: pd.Series,
        action: CorporateAction,
    ) -> pd.Series:
        """Apply split adjustment factor.
        
        For backward adjustment, prices before the split date are divided
        by the split ratio.
        """
        result = factor.copy()
        mask = result.index.date < action.ex_date
        result[mask] /= action.ratio
        return result
    
    def _apply_dividend_factor(
        self,
        factor: pd.Series,
        action: CorporateAction,
        close_prices: pd.Series,
    ) -> pd.Series:
        """Apply dividend adjustment factor.
        
        For backward adjustment, prices before the ex-date are adjusted
        by the dividend yield on that date.
        """
        result = factor.copy()
        mask = result.index.date < action.ex_date
        
        # Find the close price on or just before the ex-date
        pre_ex_prices = close_prices[close_prices.index.date < action.ex_date]
        if len(pre_ex_prices) > 0:
            last_close = pre_ex_prices.iloc[-1]
            # Dividend adjustment factor: (close - dividend) / close
            div_factor = (last_close - action.ratio) / last_close
            result[mask] *= div_factor
        
        return result
    
    def apply_split(
        self,
        df: pd.DataFrame,
        split_date: date | datetime | str,
        ratio: float,
    ) -> pd.DataFrame:
        """Convenience method to apply a single split.
        
        Args:
            df: OHLCV DataFrame.
            split_date: Date of the split.
            ratio: Split ratio (e.g., 4.0 for 4:1 split).
            
        Returns:
            Adjusted DataFrame.
        """
        if isinstance(split_date, str):
            split_date = date.fromisoformat(split_date)
        
        action = CorporateAction(AdjustmentType.SPLIT, split_date, ratio)
        return self.apply(df, [action])
    
    def apply_dividend(
        self,
        df: pd.DataFrame,
        ex_date: date | datetime | str,
        amount: float,
    ) -> pd.DataFrame:
        """Convenience method to apply a single dividend.
        
        Args:
            df: OHLCV DataFrame.
            ex_date: Ex-dividend date.
            amount: Dividend amount per share.
            
        Returns:
            Adjusted DataFrame.
        """
        if isinstance(ex_date, str):
            ex_date = date.fromisoformat(ex_date)
        
        action = CorporateAction(AdjustmentType.DIVIDEND, ex_date, amount)
        return self.apply(df, [action])
    
    @staticmethod
    def compute_adjustment_factors(
        df: pd.DataFrame,
        actions: list[CorporateAction],
    ) -> pd.Series:
        """Compute cumulative adjustment factors without modifying data.
        
        Args:
            df: OHLCV DataFrame for reference dates.
            actions: List of corporate actions.
            
        Returns:
            Series of adjustment factors indexed like df.
        """
        adjuster = CorporateActionAdjuster()
        adjusted = adjuster.apply(df, actions, adjust_volume=False)
        return adjusted["adj_factor"]
