# Concepts — Resampling Rationale

Why resample
- Many analytics and visualizations require regularly spaced data. Resampling converts irregular trade events into fixed-interval bars (time), or into fixed-quantity bars (volume/tick), each with trade-offs.

Time bars vs Volume/Tick bars
- Time bars: aligned to clock intervals (1m, 5m). Good for calendar-time analyses, simpler to index and store.
- Volume bars: created when cumulative traded volume reaches a threshold. They can normalize information flow per-bar and reduce heteroskedasticity due to variable trade frequency.
- Tick bars: created after a fixed number of trades. Useful to normalize event counts per bar.

Trade-offs
- Time bars are easy to reason about and align to calendars, but can have many empty bars in illiquid assets.
- Volume/tick bars adapt to activity but complicate time-based joins and storage partitioning.

Practical guidance
- Use time bars for dashboards and storage partitions by time; use volume/tick bars for specialized analysis where activity-normalized bars improve signal-to-noise.
- Always document the resampling policy (partial-bar handling, timezone, alignment) so consumers know how bars were created.
