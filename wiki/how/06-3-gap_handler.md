# Cleaning — Gap Handler

Purpose
- Detect missing intervals in time series and apply a policy: fill, mark, or emit gap events so downstream resampling and features handle missing data correctly.

What is a gap
- A gap is a period where expected data is missing. For time bars, gaps happen when no trades occurred in an interval; for higher-level time series, gaps can be caused by market closures, data loss, or delayed feeds.

Detection
- Define expected frequency (e.g., 1-minute). Reindex the series to the expected index and find intervals where rows are missing.
- Detect long gaps vs short gaps using a threshold (e.g., > N consecutive missing intervals).

Policies
- Fill short gaps: forward-fill last price for small gaps that are likely microstructure-related.
- Leave long gaps as NaN: prevents misleading aggregates and features.
- Emit gap events: record gap metadata (start, end, duration) for auditing or special handling by consumers.

Implementation outline
1. Normalize timestamps and set index with expected frequency.
2. Reindex to the full expected range.
3. Identify missing intervals and compute consecutive-missing runs.
4. Apply policy: fill small runs with `ffill()` for prices and `0` for volume (or NaN), insert gap metadata column.

Example (conceptual)

```python
# expected_idx = pd.date_range(start, end, freq='1T', tz='UTC')
# df = df.reindex(expected_idx)
missing = df['close'].isna()
runs = find_consecutive_runs(missing)
for run in runs:
    if run.length <= short_gap_thresh:
        df.loc[run.index,'close'] = df.loc[run.start-1,'close']  # ffill
    else:
        df.loc[run.index,'gap'] = True
```

Notes on markets and holidays
- Recognize market hours and holidays: gaps outside market hours may be expected and should be treated differently.
- Use trading calendars when possible to avoid mis-classifying expected closures as gaps.

Testing
- See `tests/test_gap_handler.py` for examples showing short and long gap behaviors.

Pitfalls
- Blindly filling gaps can introduce false signals; conservative defaults are recommended.
- Reindexing very long ranges for many symbols can be memory-heavy — operate per-symbol and per-range.

See also
- `src/market_data/cleaning/gap_handler.py` for project-specific implementation choices.
