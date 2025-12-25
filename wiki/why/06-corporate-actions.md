# Concepts — Corporate Actions & Adjustments

Why adjust prices
- Corporate actions (splits, dividends) change the nominal prices and volumes reported for past data; without adjustment, historical comparisons and indicators are biased.

Common corporate events
- Splits/Consolidations: change share count; require multiplicative adjustments to historical prices and inverse adjustments to volume.
- Dividends: cash payouts that can be reflected in adjusted close if required by consumers.

Adjustment principles
- Apply multiplicative factors backward in time to produce a continuous, post-event basis series.
- Prefer keeping raw values alongside adjusted values for auditability.
- Always align event timestamps precisely (consider ex-date vs record date).

Why before resampling
- Adjusting at trade-level ensures OHLC aggregates reflect the adjusted series; applying adjustments after aggregation can misrepresent historical ranges.

Pitfalls
- Missing event data or timezone misalignment will mis-apply adjustments; source and align event timestamps carefully.
