# Cleaning — Adjuster

Purpose
- Apply corporate-action adjustments (splits, dividends) to raw price/volume series so the resulting series is continuous and comparable across history.

Why adjust
- Corporate events (stock splits, dividends) change reported prices and volumes. Adjusting creates a continuous series where features and backtests aren't biased by these events.

Common adjustments
- Split adjustment: when a 2-for-1 split occurs, historical prices before the split should be halved to be comparable with post-split prices; volumes should be multiplied accordingly.
- Dividend adjustment: some pipelines distribute dividends into adjusted close; policies vary whether to apply cash dividend adjustments to historical prices.

Adjustment methods
- Cumulative factor method:
  1. Build a series of multiplicative adjustment factors per event (e.g., split factor = post/pre).
  2. Compute the cumulative product of factors going backward in time.
  3. Multiply historical prices by the cumulative factor so pre-event prices reflect post-event basis.
- Volume handling: apply inverse factor to volume when prices are scaled (e.g., after a 2-for-1 split, historical volumes double).

Where adjustments come from
- Adjustments may be fetched from provider metadata (some APIs provide split/dividend events) or from a corporate actions database.

Implementation notes
- Apply adjustments before resampling/aggregation to avoid incorrect OHLC aggregation.
- Keep both adjusted and raw columns if consumers need raw values (e.g., `close` and `adj_close`).
- Floating rounding: be careful with dtype (use float64) and consider rounding policy when writing to Parquet.

Example (conceptual)

```python
# assume events is a DataFrame with ['timestamp','split_ratio'] sorted ascending
prices['adj_factor'] = compute_cumulative_factor(events, prices.index)
prices[['open','high','low','close']] *= prices['adj_factor']
prices['volume'] /= prices['adj_factor']
```

Testing
- See `tests/test_adjuster.py` for unit tests that show expected scaling for single and multiple events.

Pitfalls
- Missing event dates or timezone mismatches can mis-align adjustments.
- Applying adjustments after aggregation loses precision — always adjust raw tick-trade-level data if possible.

See also
- `src/market_data/cleaning/adjuster.py` for concrete implementation in the codebase.
