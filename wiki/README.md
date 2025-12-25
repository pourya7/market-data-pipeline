# Market Data Pipeline — Educational Summary

This repository is both a working market-data pipeline and a structured learning project. The materials in `wiki/how/` and `wiki/why/` are organized so engineers and analysts can learn practical implementation details alongside the trading and data concepts that motivate them.

What we achieved

- **Reproducible pipeline walkthroughs:** step-by-step `how/` guides that explain clients, cleaning, resampling, feature generation, storage, and the dashboard.
- **Conceptual foundations:** `why/` notes covering time-series theory, OHLCV semantics, microstructure effects, and corporate-action adjustments.
- **Practical engineering patterns:** examples of idempotent storage, atomic Parquet writes, manifests, rate-limiting, and retry strategies.
- **Cleaning & quality-first design:** deep-dive materials on schema expectations, gap detection/handling, and corporate-action adjustments to ensure downstream feature correctness.
- **Resampling strategies:** explanations and code for time bars, tick bars, and volume bars plus trade-offs for each approach.
- **Feature engineering guidance:** technical indicator construction, warm-up handling, and how features are organized for model readiness.
- **Testing and reproducibility:** unit and integration tests that show how to validate each step of the pipeline.

Core learning concepts (trading-focused)

- **Time-series fundamentals:** how timestamps, intervals, and market hours affect aggregation and analysis.
- **OHLCV semantics:** what Open/High/Low/Close/Volume represent at different sampling granularities and why correct construction matters for indicators.
- **Market microstructure:** how trade frequency, tick sizes, and orderbook effects influence resampling and indicator behaviour.
- **Resampling trade-offs:** pros/cons of time-based vs tick/volume bars for volatility, latency, and sample efficiency.
- **Corporate actions & adjustments:** why splits/dividends require cumulative-factor adjustments to keep historical prices consistent.
- **Gap handling & data quality:** practical techniques for detecting missing periods and choosing appropriate imputation or exclusion strategies.
- **Idempotency & storage safety:** manifest-driven writes and atomic file operations to make historical data processing safe and repeatable.
- **Operational concerns:** rate limits, retries, and backoff strategies when integrating with external market-data providers.

How to use these materials

- Start with the practical walkthrough: [wiki/how/01-overview.md](how/01-overview.md).
- Read the conceptual introduction: [wiki/why/01-overview.md](why/01-overview.md).
- For hands-on learning, follow the cleaning deep-dive, then step through resampling and feature generation using the `how/` guides.

Suggested next steps for learners

- Annotate `src/market_data/cleaning/pipeline.py` to connect theory to implementation.
- Run the test suite to validate understanding and experiment by adding small dataset examples.
- Try different resampling strategies on a sample ticker to observe microstructure effects.

This document highlights the educational intent: the repo is designed to teach both the engineering and trading concepts needed to build reliable, analysis-ready market data pipelines.
