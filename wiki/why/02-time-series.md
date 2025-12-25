# Concepts — Time Series Basics

Why time series matter here
- Market data is inherently ordered in time; understanding temporal properties is essential for correct aggregation, modeling, and storage.

Key concepts
- Sampling vs Event Streams: trades are event-driven (irregular). Sampling produces regular intervals (time bars) which many algorithms expect.
- Stationarity: many statistical methods assume or work better on stationary series. Market data is non-stationary; transformations (returns, differencing) are used to stabilize.
- Timestamps and timezone: consistent, timezone-aware timestamps (UTC) avoid misalignment across sources.
- Indexing: using a datetime index enables efficient resampling and rolling-window operations in pandas.

Why it matters for our code
- Resampling requires monotonic, timezone-normalized timestamps to produce correct OHLCV aggregates.
- Storage partitioning often uses time (year/month/day); correct timestamps enable efficient reads.

Pitfalls
- Mixing naive and timezone-aware datetimes leads to subtle bugs and misaligned bars.
- Aggregating before adjustments can produce incorrect historical bars when corporate actions exist.

Simple example
- To compute 1-minute bars from irregular trades: sort by timestamp, set UTC index, then group into 1-minute buckets and compute OHLCV.
