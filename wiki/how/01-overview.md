# Overview

Purpose
- A Python-based market data pipeline that ingests, cleans, resamples, computes features, stores, and serves market time-series data for analysis and dashboarding.

High-level data flow
- Data sources: clients in `src/market_data/clients` fetch raw market data.
- Cleaning: `src/market_data/cleaning` normalizes, adjusts, and fills gaps.
- Resampling & Bars: `src/market_data/resampling` converts ticks to time/volume bars.
- Features & Pipelines: `src/market_data/features` computes technical features and orchestrates processing.
- Storage: `src/market_data/storage` writes Parquet files, manages manifests and partitions.
- App/GUI: `src/market_data/dashboard` provides a small dashboard for charts and downloads.

Key packages and where to look
- `src/market_data/clients` — API clients for Yahoo/Polygon/Oanda.
- `src/market_data/cleaning` — adjuster, gap handling, pipeline orchestration.
- `src/market_data/resampling` — bar creation and resampling logic.
- `src/market_data/storage` — manager, manifest, parquet helpers, partitions.
- `src/market_data/core` — configuration, rate limiting, retry utilities.
- `src/market_data/features` — feature calculations and feature pipelines.
- `src/market_data/dashboard` — simple web dashboard components.

Tests
- Unit and integration tests live in `tests/` and `tests/integration`.

What you'll learn in this crash course
- Project architecture and responsibilities of each module.
- How data moves from source to storage and visualization.
- How rate limits, retries, and tests ensure robustness.

Next: open [Sections](02-sections.md) to pick a section to dive into.
