# Crash Course Sections

Pick sections in order or jump to one you care about. I'll expand each into its own file when you tell me to proceed.

1. Architecture & Data Flow — overall diagram and module responsibilities. (03-architecture.md)
2. Clients & Data Sources — `yahoo.py`, `polygon.py`, `oanda.py`, auth, rate-limiting, retry. (04-clients.md)
3. Core Utilities — `config.py`, `rate_limiter.py`, `retry.py` and how they are used. (05-core.md)
4. Cleaning Pipeline — `adjuster.py`, `gap_handler.py`, `pipeline.py`, and `schemas.py`. (06-cleaning.md)
5. Resampling & Bars — `time_resampler.py`, `volume_bars.py`, `tick_bars.py`. (07-resampling.md)
6. Features & Pipelines — `features/config.py`, `features/pipeline.py`, `features/technical.py`. (08-features.md)
7. Storage & Manifest — `storage/manager.py`, `parquet.py`, `manifest.py`, `partitions.py`. (09-storage.md)
8. Dashboard & Components — `dashboard/app.py`, `components/charts.py`, pages. (10-dashboard.md)
9. Models & Schemas — `models/ohlcv.py`, `cleaning/schemas.py` and data types. (11-models.md)
10. Testing & CI — how tests are organized and how to run them. (12-testing.md)

Tell me which section to expand first, or say "Start with Architecture" to begin.
