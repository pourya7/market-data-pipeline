# Concepts — Overview (Why)

Purpose
- Explain the fundamental concepts that underpin this project: why we use OHLCV bars, why resample, why adjust prices, why partition storage, and why testing and idempotency matter.

How to use this set
- These documents are educational: read them to build intuition before diving into code. They explain motivations, trade-offs, and common pitfalls.

Planned concept topics
- Time-series basics (sampling, stationarity, timestamps)
- OHLCV semantics and aggregation caveats
- Resampling rationale (time vs volume vs tick bars)
- Market microstructure (trades, quotes, spreads)
- Corporate actions and why we adjust prices
- Rate limiting and retry strategies — why they're essential
- Storage & partitioning: Parquet trade-offs and manifest rationale
- Feature engineering principles: warm-up, alignment, and lookahead bias
- Testing & reproducibility: idempotency and deterministic pipelines

Next: open any concept file to read the full explanation or ask me to expand one into examples and visuals.
