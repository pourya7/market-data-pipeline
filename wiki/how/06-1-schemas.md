# Cleaning — Schemas

Purpose
- Define the canonical data schema and validation rules used by the cleaning pipeline.

Canonical schema (OHLCV bars)
- Columns: `timestamp`, `open`, `high`, `low`, `close`, `volume`.
- Types:
  - `timestamp`: timezone-aware `datetime64[ns, UTC]` (or set as index)
  - `open`, `high`, `low`, `close`: float (numeric)
  - `volume`: numeric (int/float), >= 0

Schema rules and invariants
- Required columns must be present. Missing required columns should either be coerced (if possible) or the row/frame rejected.
- Type coercion first: parse timestamps, convert numeric strings to floats, coerce NaNs where parsing fails.
- Price invariants: `low <= min(open, close)` and `high >= max(open, close)`. Values violating these rules should be validated and either corrected (if clearly due to rounding) or dropped.
- Non-negative volume: negative or missing volume should be flagged.

Timestamp handling
- Convert all timestamps to UTC as early as possible. Prefer timezone-aware datetimes over naive datetimes.
- Decide whether `timestamp` is a column or an index. The codebase prefers normalized `timestamp` column or UTC index consistently — check `src/market_data/models/ohlcv.py` for conventions.
- For tick/trade data, ensure monotonic ordering by `timestamp` before any aggregation.

Validation vs coercion
- Coercion: Parse and convert values (e.g., strings -> datetimes or floats). This step should be forgiving.
- Validation: After coercion, apply strict checks (presence, ranges, invariants). Validation failures should be:
  - Logged with context
  - Either corrected if safe, or
  - Marked/dropped according to cleaning policy in config.

Common implementation approaches
- Lightweight custom validation functions (small projects) — fast, minimal deps.
- Schema libraries (`pandera`, `pydantic`) — provide expressive schemas and automatic validation reporting.

Testing schemas
- Unit tests should include:
  - Good input -> passes
  - Malformed timestamps -> coerced or rejected as expected
  - Invalid invariants -> handled according to policy

See also
- `src/market_data/cleaning/schemas.py` for concrete rules the pipeline uses.
- `tests/test_schemas.py` for expected behavior and edge cases.
