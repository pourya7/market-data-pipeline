# Storage, Manifest & Partitions

Purpose
- Persist processed OHLCV bars and feature-enriched datasets to durable storage (Parquet), track what's been written with a manifest, and organize files via partitions for efficient access.

Where storage code lives
- `src/market_data/storage`
- Key files: `manager.py`, `parquet.py`, `manifest.py`, `partitions.py`.

`manager.py`
- Orchestrates writing pipeline outputs to storage and updating the manifest.
- Typical responsibilities:
  - Receive processed DataFrame (OHLCV + features) and metadata (symbol, freq, date-range).
  - Compute partition keys (e.g., `year=YYYY`, `month=MM`, `symbol=SYMBOL`).
  - Write Parquet files via `parquet.py` into the correct partition path.
  - Update the manifest so the system knows which partitions/files exist and their ranges.
- Idempotency: `manager` consults the manifest before writing to avoid duplicate writes and to enable safe reprocessing.

`parquet.py`
- Contains Parquet writing helpers and conventions used across the codebase.
- Typical features:
  - Standardized schema and dtype casting before write.
  - Compression settings (e.g., `snappy`) and row-group tuning.
  - Atomic write pattern: write to a temp file then rename to final path to avoid partial files.

Example (conceptual)

```python
from market_data.storage.manager import StorageManager

sm = StorageManager(base_path="data/")
sm.write(df, symbol="AAPL", freq="1T", start="2025-01-01", end="2025-01-31")
```

`manifest.py`
- Tracks what data exists in storage and metadata about each partition/file.
- Manifest responsibilities:
  - Record entries with keys like `(symbol, freq, partition_key)` and metadata (start, end timestamps, file path, checksum).
  - Support queries: "Which partitions cover symbol X between dates Y and Z?"
  - Allow marking partitions as written, failed, or in-progress to support robust backfills.
- Implementation notes: manifest may be a small JSON/Parquet index on disk or an in-memory structure persisted to a manifest file.

`partitions.py`
- Encodes the partitioning strategy used by the project for efficient storage and query.
- Common partitioning strategies:
  - Date-based: `year=YYYY/month=MM/day=DD` (good for time-range queries)
  - Symbol-based: `symbol=AAPL` (good for per-instrument reads)
  - Hybrid: combine symbol and date (`symbol=AAPL/year=2025/month=01`)
- Partition functions compute the path and keys given metadata and ensure consistent layout across writes.

Reading data
- Consumers (dashboard, analytics) use the manifest to locate relevant Parquet files and then read the needed partitions. This avoids scanning large directories.

Best practices
- Use atomic writes and manifest updates so readers never see partial state.
- Keep partition granularity balanced: too fine (many small files) hurts performance; too coarse requires scanning large files for small queries.
- Store checksums and file sizes in the manifest to detect silent corruption.

Testing
- See `tests/test_parquet.py`, `tests/test_manifest.py`, and `tests/test_storage_manager.py` for examples of expected write/read behavior and manifest updates.

Where to read next
- `src/market_data/storage/manager.py` — orchestration and idempotency logic.
- `src/market_data/storage/parquet.py` — Parquet write helpers and atomic-write patterns.
- `src/market_data/storage/manifest.py` — manifest schema and update methods.
- `src/market_data/storage/partitions.py` — partition key and path functions.

Next: I can write `docs/10-dashboard.md` (dashboard & components) or `docs/11-models.md` (models & schemas). Which should I do next?
