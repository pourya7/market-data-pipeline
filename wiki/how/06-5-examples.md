# Cleaning — Examples & Pitfalls

Quick examples

1) Timestamp coercion

```python
# parse strings -> timezone-aware UTC
df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
```

2) Simple split adjuster

```python
# events: DataFrame with ['date','split_ratio']
# prices: DataFrame indexed by timestamp
factors = compute_cumulative_factors(events, prices.index)
for col in ['open','high','low','close']:
    prices[col] = prices[col] * factors
prices['volume'] = prices['volume'] / factors
```

3) Gap detection (1-minute freq)

```python
expected_idx = pd.date_range(df.index.min(), df.index.max(), freq='1T', tz='UTC')
df = df.reindex(expected_idx)
missing_runs = detect_missing_runs(df['close'].isna())
```

Pitfalls checklist
- Timezones: convert early and consistently.
- Adjustment idempotency: apply adjustments only once or track an `is_adjusted` flag.
- Filling policy: default to conservative (mark large gaps, only fill very short gaps).
- Order: adjustments before resampling; validation before adjustments.

Tests to add (suggested)
- Multi-split sequence test: verify cumulative factor correctness.
- Gap classification test: short vs long gap handling.
- Invalid invariant test: rows with high < low should be dropped or corrected per policy.

Where to look in the repo
- `src/market_data/cleaning/adjuster.py`
- `src/market_data/cleaning/gap_handler.py`
- `src/market_data/cleaning/pipeline.py`
- `tests/test_adjuster.py`, `tests/test_gap_handler.py`, `tests/test_pipeline.py`

If you want, I can now open `src/market_data/cleaning/pipeline.py` and annotate the functions line-by-line. Would you like that? 
