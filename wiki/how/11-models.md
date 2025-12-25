# Models & Schemas

Purpose
- Define the canonical data models used across the pipeline (OHLCV bars, ticks) and the validation schemas used during cleaning.

Where the models live
- `src/market_data/models` — domain models like `ohlcv.py`.
- `src/market_data/cleaning/schemas.py` — schema definitions and validation helpers.

`models/ohlcv.py`
- Defines the expected structure for bar data and helpful constructors/serializers.
- Typical contents:
  - A dataclass or small helper that documents column names: `['timestamp','open','high','low','close','volume']`.
  - Type hints and optional conversion helpers (to/from DataFrame).

`cleaning/schemas.py`
- Provides validation rules used by the cleaning pipeline:
  - Required columns and their dtypes
  - Timestamp coercion rules (timezone handling)
  - Nullable vs non-nullable fields
  - Value bounds (e.g., non-negative volume)
- Often uses lightweight validation (custom functions) or a schema library (like `pydantic` or `pandera`) depending on project dependencies.

Contracts and invariants
- `timestamp` should be timezone-aware UTC and either an index or a dedicated column consistently used across modules.
- Prices (`open`, `high`, `low`, `close`) are floats; `volume` is numeric and >= 0.
- For bars: `low <= min(open, close)`, `high >= max(open, close)` should hold — cleaning may coerce or drop rows violating invariants.

Validation patterns
- Perform coercion first (convert types, parse timestamps), then validate invariants and either fix (clamp, forward-fill) or drop invalid rows based on config.
- Emit validation logs or counters to help monitor data quality.

Usage examples

from market_data.models.ohlcv import OHLCV
from market_data.cleaning.schemas import validate_frame

# validate a DataFrame
validate_frame(df)
# construct a typed object
ohlcv = OHLCV.from_dataframe(df)

Testing
- See `tests/test_models.py` and `tests/test_schemas.py` for examples of good and bad input and expected outcomes.

Where to read next
- `src/market_data/models/ohlcv.py` — model helpers and conversions.
- `src/market_data/cleaning/schemas.py` — exact validation rules used in the pipeline.

Next: Do you want `docs/12-testing.md` now? 
