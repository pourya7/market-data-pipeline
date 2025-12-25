# Concepts — OHLCV Semantics

Why OHLCV
- OHLCV (Open, High, Low, Close, Volume) is a compact summary of market activity within a bucket. It preserves price range and traded quantity useful for many analytics.

Semantics and edge cases
- Open: first trade price in the bucket. If no trade in the bucket, open may be undefined or forward-filled depending on policy.
- High/Low: extremes of trade prices in the bucket. Mistakes in ordering or timezone can change these values.
- Close: last trade price in the bucket — often used for feature alignment.
- Volume: sum of traded quantities — must be non-negative and aggregated correctly even across split-adjusted data.

Aggregation caveats
- Order matters: compute open/close from first/last in time order, high/low from max/min across trades.
- Partial buckets: when a bucket has only partial data (e.g., at start/end), decide whether to emit or drop partial bars.
- Adjustments: apply corporate adjustments before aggregation to ensure OHLC semantics remain correct historically.

Why this helps downstream
- Many indicators assume OHLCV inputs; preserving correct semantics avoids lookahead and alignment bugs.
