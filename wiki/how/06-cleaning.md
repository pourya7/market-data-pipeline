# Cleaning Pipeline

Purpose
- Normalize and validate raw market data returned by clients so downstream resampling and feature calculations are correct and consistent.

Where the cleaning code lives
- `src/market_data/cleaning`
- Key files: `pipeline.py`, `adjuster.py`, `gap_handler.py`, `schemas.py`.

Responsibilities
- `schemas.py`: defines the canonical data schema (expected columns, types, timestamp handling). Use these schemas to validate incoming frames.
- `pipeline.py`: orchestrates cleaning steps — validate schema, apply adjustments, detect and handle gaps, and mark/flag bad rows. It returns a cleaned, canonical DataFrame ready for resampling.
- `adjuster.py`: applies price/volume adjustments (corporate actions, splits, dividends) to produce continuous series when needed.
- `gap_handler.py`: detects missing intervals and applies strategies (forward-fill, insert NaNs, or emit gap events). This ensures resamplers don't silently aggregate across gaps.

Deep-dive subsections
- [Schemas & Validation](06-1-schemas.md)
- [Adjuster (corporate actions)](06-2-adjuster.md)
- [Gap Handler](06-3-gap_handler.md)
- [Pipeline orchestration](06-4-pipeline.md)
- [Examples & Pitfalls](06-5-examples.md)

Typical flow
1. Receive raw DataFrame from a client: columns may include `timestamp`, `open`, `high`, `low`, `close`, `volume` and provider metadata.
2. Convert timestamps to UTC and set as index (or normalized `timestamp` column) per `schemas.py`.
3. Validate column presence and dtypes. Drop or coerce invalid rows depending on policy.
4. Run `adjuster` if the instrument requires corporate adjustments. Adjuster returns corrected prices/volumes.
5. Run `gap_handler` to locate missing time ranges. Depending on configuration, either fill short gaps or mark them for downstream handling.
6. Return cleaned series for resampling.

Example usage (conceptual)

```python
from market_data.cleaning.pipeline import CleaningPipeline

pipeline = CleaningPipeline(config)
raw = client.fetch_ohlcv(...)
cleaned = pipeline.run(raw)
# cleaned: DataFrame with UTC timestamps, numeric OHLCV columns, gap metadata where applicable
```

Configuration and policies
- Cleaning behaviour (fill vs mark gaps, which adjustments to apply) is driven by project config — check `src/market_data/features/config.py` and `src/market_data/core/config.py` for relevant flags.

Testing
- See `tests/test_adjuster.py`, `tests/test_gap_handler.py`, and `tests/test_pipeline.py` for unit tests that show expected inputs and outputs for each component.

Common pitfalls
- Timezones: ensure clients return timezone-aware timestamps or that the pipeline enforces UTC conversion early.
- Adjuster order: apply adjustments before resampling to avoid incorrect aggregated OHLC values.
- Gap semantics: decide whether short gaps should be filled (e.g., market microstructure) or treated as true missing data; this affects feature computations.

Where to read next
- Open `src/market_data/cleaning/pipeline.py` to follow orchestration and function names.
- Inspect `src/market_data/cleaning/adjuster.py` and `src/market_data/cleaning/gap_handler.py` for concrete logic and algorithms used.

Next: would you like me to expand `Core Utilities` (`docs/05-core.md`) or `Resampling & Bars` (`docs/07-resampling.md`)?
