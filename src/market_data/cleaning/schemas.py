"""Pandera DataFrame schemas for OHLCV data validation."""

from datetime import datetime
from typing import Optional

import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Check, Index


# Define OHLCV schema using class-based approach (more compatible)
OHLCVSchema = DataFrameSchema(
    columns={
        "open": Column(float, Check.gt(0), description="Opening price"),
        "high": Column(float, Check.gt(0), description="High price"),
        "low": Column(float, Check.gt(0), description="Low price"),
        "close": Column(float, Check.gt(0), description="Closing price"),
        "volume": Column(float, Check.ge(0), description="Trading volume"),
        "symbol": Column(str, nullable=True, required=False, description="Ticker symbol"),
        "provider": Column(str, nullable=True, required=False, description="Data provider"),
        "interval": Column(str, nullable=True, required=False, description="Bar interval"),
    },
    index=Index(datetime),  # Allow any datetime index (named or unnamed)
    checks=[
        # Cross-column checks for OHLCV relationships
        Check(
            lambda df: (df["high"] >= df["low"]).all(),
            error="high must be >= low",
        ),
        Check(
            lambda df: (df["high"] >= df["open"]).all(),
            error="high must be >= open",
        ),
        Check(
            lambda df: (df["high"] >= df["close"]).all(),
            error="high must be >= close",
        ),
        Check(
            lambda df: (df["low"] <= df["open"]).all(),
            error="low must be <= open",
        ),
        Check(
            lambda df: (df["low"] <= df["close"]).all(),
            error="low must be <= close",
        ),
    ],
    strict=False,  # Allow extra columns
    coerce=True,   # Attempt type coercion
)


# Schema with adjusted close column
AdjustedOHLCVSchema = OHLCVSchema.add_columns({
    "adj_close": Column(float, Check.gt(0), description="Adjusted closing price"),
})


def validate_ohlcv(
    df: pd.DataFrame,
    raise_on_error: bool = True,
    include_adjusted: bool = False,
) -> tuple[pd.DataFrame, Optional[pa.errors.SchemaErrors]]:
    """Validate an OHLCV DataFrame against the schema.
    
    Args:
        df: DataFrame to validate.
        raise_on_error: If True, raises SchemaError on validation failure.
        include_adjusted: If True, validates for adj_close column.
        
    Returns:
        Tuple of (validated DataFrame, errors or None).
        
    Raises:
        pa.errors.SchemaError: If validation fails and raise_on_error is True.
    """
    schema = AdjustedOHLCVSchema if include_adjusted else OHLCVSchema
    
    try:
        validated_df = schema.validate(df, lazy=True)
        return validated_df, None
    except pa.errors.SchemaErrors as err:
        if raise_on_error:
            raise
        return df, err


def get_validation_errors(df: pd.DataFrame) -> list[dict]:
    """Get detailed validation errors for a DataFrame.
    
    Args:
        df: DataFrame to validate.
        
    Returns:
        List of error dictionaries with column, check, and failure info.
    """
    _, errors = validate_ohlcv(df, raise_on_error=False)
    
    if errors is None:
        return []
    
    error_list = []
    for error in errors.schema_errors:
        error_list.append({
            "column": error.schema.name if error.schema else "dataframe",
            "check": error.check,
            "failure_cases": error.failure_cases.to_dict() if error.failure_cases is not None else None,
            "message": str(error),
        })
    
    return error_list
