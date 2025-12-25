# Resampling & Bars

Purpose
- Convert tick/irregular trade data into regular OHLCV bars (time bars, volume bars, tick bars) used by analytics and dashboards.

Where the resampling code lives
- `src/market_data/resampling`
- Key files: `time_resampler.py`, `volume_bars.py`, `tick_bars.py`.

Concepts
- OHLCV aggregation: when grouping many trades into one bar, compute:
  - Open: first price in interval
  - High: max price
  - Low: min price
  - Close: last price
  - Volume: sum of volumes
- Time bars: fixed-duration intervals (1m, 5m, 1h) aligned to clock time.
- Volume bars: create a bar each time a cumulative traded volume threshold is reached.
- Tick bars: create a bar after a fixed count of trades.

`time_resampler.py`
- Implements resampling of timestamp-indexed trades/trade-aggregates into fixed time buckets.
- Typical flow:
  1. Ensure `timestamp` is UTC and set as index.
  2. Use pandas `resample()` or a custom window to group by frequency.
  3. Aggregate OHLCV with appropriate functions (first, max, min, last, sum).
  4. Emit empty bars as NaNs or fill short gaps according to the cleaning policy.

Example (conceptual)

```python
from market_data.resampling.time_resampler import TimeResampler

resampler = TimeResampler(freq='1T')  # 1-minute bars
bars = resampler.resample(trades_df)
```

`volume_bars.py`
- Produces bars when cumulative volume reaches a target `V`.
- Algorithm outline:
  1. Iterate trades in time order, accumulating volume.
  2. When accumulated volume >= target, create an OHLCV bar from the trades in the bucket and reset accumulator.
  3. Handle leftover partial buckets at the end (emit as partial bar or drop based on config).

`tick_bars.py`
- Similar to volume bars but triggers on trade count `N` instead of volume.

Practical notes
- Maintain order: ensure trade data is strictly time-ordered before resampling.
- Timezones: timestamps must be normalized (UTC) to avoid misaligned bars.
- Gaps: short gaps may be filled before resampling; long gaps often should remain NaN to avoid misleading aggregates.
- Partial bars: choose a consistent policy (emit partial bar vs drop) and document it in pipeline config.

Performance
- For large tick datasets, avoid repeatedly copying DataFrames. Use vectorized pandas operations where possible.
- Volume/tick bar algorithms are often implemented as single-pass loops and can be optimized in Cython/Numba if needed.

Testing
- See `tests/test_resampling.py` for unit tests that show expected bar outputs for small synthetic trade sequences.

Where to read next
- `src/market_data/resampling/time_resampler.py` — exact implementation details.
- `src/market_data/cleaning/pipeline.py` — how cleaned data is prepared before resampling.
- `tests/test_resampling.py` — examples of expected behavior.
