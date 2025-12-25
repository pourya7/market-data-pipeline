# Features & Pipelines

Purpose
- Compute technical indicators and orchestrate per-instrument processing pipelines that combine fetching, cleaning, resampling, feature computation, and storage.

Where the features code lives
- `src/market_data/features`
- Key files: `config.py`, `pipeline.py`, `technical.py`.

Responsibilities
- `config.py`: defines available feature sets, default parameters (SMA windows, RSI periods), and feature-related toggles.
- `pipeline.py`: composes the end-to-end processing steps for an instrument (fetch -> clean -> resample -> features -> store). It accepts configuration for frequency, features to compute, and storage targets.
- `technical.py`: implementations of technical indicators (SMA, EMA, RSI, ATR, etc.) that operate on OHLCV bars and return aligned series or columns that merge into the bar DataFrame.

Typical pipeline flow
1. Fetch raw data via a client (delegated to `clients/`).
2. Clean the raw data using the cleaning pipeline (see `cleaning/pipeline.py`).
3. Resample cleaned data into the desired bar frequency (using `resampling/*`).
4. Compute requested features from `technical.py` and merge them into the bars DataFrame.
5. Optionally drop warm-up periods (where indicators need history) and persist the result via `storage/manager.py`.

Feature function contracts
- Feature functions accept a DataFrame with OHLCV columns and return either:
  - A Series aligned to the input index (single feature), or
  - A DataFrame with multiple columns (multi-feature output).
- Functions should be pure (no side effects) and deterministic for given inputs.

Example usage (conceptual)

```python
from market_data.features.pipeline import FeaturePipeline

pipeline = FeaturePipeline(config)
result = pipeline.run(symbol='AAPL', start='2025-01-01', end='2025-02-01', freq='1T', features=['sma_20','rsi_14'])
# result: DataFrame with OHLCV + columns ['sma_20','rsi_14']
```

Warm-up periods and alignment
- Many indicators require a history window; pipelines typically drop or mark the initial `N` rows as warm-up so consumers know which rows are reliable.
- Ensure features are aligned to the bar close (e.g., SMA at time T uses data up to T).

Performance considerations
- Compute vectorized indicators using pandas/numpy; avoid Python loops per-row.
- Cache intermediate results when computing multiple features that share sub-calculations (e.g., rolling highs/lows).

Testing
- See `tests/test_features.py` for unit tests showing expected indicator values on synthetic data.

Where to read next
- `src/market_data/features/pipeline.py` — orchestration and config wiring.
- `src/market_data/features/technical.py` — concrete implementations of indicators.
- `src/market_data/storage/manager.py` — how the pipeline persists results.

Next: I can write `docs/09-storage.md` documenting storage, manifest, parquet, and partitions. Proceed? 
