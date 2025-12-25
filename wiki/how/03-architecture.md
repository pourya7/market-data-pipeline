# Architecture & Data Flow

Goal
- Explain how data flows from external sources through processing and into storage and the dashboard.

High-level components
- Clients: `src/market_data/clients` — adapters for external APIs (Yahoo, Polygon, Oanda). They fetch raw OHLCV/tick data and return normalized frames.
- Core utilities: `src/market_data/core` — configuration loader, `rate_limiter.py` and `retry.py` helpers used by clients to respect API limits and handle transient failures.
- Cleaning pipeline: `src/market_data/cleaning` — normalization, adjustments, gap handling, and validation. Key modules: `adjuster.py`, `gap_handler.py`, `pipeline.py`, and `schemas.py`.
- Resampling & bars: `src/market_data/resampling` — convert tick data into time/volume/tick bars using `time_resampler.py`, `volume_bars.py`, and `tick_bars.py`.
- Features & processing: `src/market_data/features` — compute technical indicators and orchestrate per-instrument pipelines.
- Storage: `src/market_data/storage` — write Parquet files, manage manifests and partitioning (`manager.py`, `parquet.py`, `manifest.py`, `partitions.py`).
- Dashboard: `src/market_data/dashboard` — small app and components to visualize stored data.

Data flow (step-by-step)
1. Request: the pipeline is triggered (CLI, scheduler, or dashboard request) to fetch data for one or many instruments and a time-range.
2. Fetch: a client adapter in `clients/` calls the external API. Calls go through `core/rate_limiter.py` and `core/retry.py` to avoid hitting quotas and to retry on transient errors.
3. Normalize: raw responses are normalized into a consistent schema defined in `cleaning/schemas.py`. Timestamps are converted to UTC and types validated.
4. Clean: `cleaning/pipeline.py` applies adjustments (`adjuster.py`) and fills or marks gaps (`gap_handler.py`) so later resampling is correct.
5. Resample: cleaned tick-level or irregular data is converted into bars via `resampling/*` (time bars, volume bars, tick bars). Aggregation follows OHLCV semantics.
6. Feature compute: `features/pipeline.py` computes indicators (SMA, RSI, etc.) and attaches them to the series if requested.
7. Store: `storage/manager.py` writes results to Parquet using `storage/parquet.py`, updates manifests via `storage/manifest.py`, and organizes files using `storage/partitions.py`.
8. Serve/Visualize: the dashboard or downstream consumers read Parquet files or consult the manifest to load data for charts or downloads.

Design notes and trade-offs
- Separation of concerns: API clients only fetch and return raw frames; cleaning and resampling live in separate modules to keep each responsibility small and testable.
- Idempotency: storage operations and manifests are designed to allow reprocessing without duplicating data (manifest tracks written partitions).
- Robustness: rate limiting and retry logic are centralized under `core` so all clients can share consistent policies.
- Testability: modules are small, pure (where possible), and covered by tests under `tests/` and `tests/integration`.

Key files to inspect next
- [src/market_data/clients](src/market_data/clients) — the client implementations.
- [src/market_data/cleaning/pipeline.py](src/market_data/cleaning/pipeline.py) — the cleaning orchestration.
- [src/market_data/resampling/time_resampler.py](src/market_data/resampling/time_resampler.py) — time-based resampling logic.
- [src/market_data/storage/manager.py](src/market_data/storage/manager.py) — how processed data is written and tracked.

Next steps
- Pick a section to expand from the crash-course list. I recommend `Clients & Data Sources` next so you can follow the data from its origin.
