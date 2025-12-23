# Market Data Pipeline

A production-grade Python library for downloading, cleaning, and storing financial time-series data.

## Features

| Module | Capability |
|--------|------------|
| **Ingestion** | Yahoo Finance, Polygon, Oanda clients with rate limiting & retries |
| **Cleaning** | Pandera validation, split/dividend adjustments, gap filling |
| **Storage** | Parquet with Snappy compression, year/ticker partitioning |

## Installation

```bash
# Clone repository
git clone https://github.com/youruser/market-data-pipeline.git
cd market-data-pipeline

# Install with pip (recommended)
pip install -e ".[dev]"

# Or use make
make install
```

## Quick Start

```python
import asyncio
from market_data.clients import YahooFinanceClient
from market_data.cleaning import DataCleaner
from market_data.storage import StorageManager

async def main():
    # 1. Fetch data
    client = YahooFinanceClient()
    dataset = await client.fetch_ohlcv("AAPL", start="2024-01-01", end="2024-06-30")
    df = dataset.to_pandas()
    
    # 2. Clean data
    cleaner = DataCleaner()
    clean_df = cleaner.clean(df)
    
    # 3. Store data
    storage = StorageManager()
    storage.save(clean_df, "AAPL")
    
    # 4. Load data
    loaded = storage.load("AAPL", start_date="2024-01-01")
    print(loaded)

asyncio.run(main())
```

## Configuration

Create `config.yaml`:

```yaml
providers:
  yahoo:
    requests_per_second: 2
  polygon:
    api_key: ${POLYGON_API_KEY}
    requests_per_second: 5

storage:
  base_path: ./data
  compression: snappy
```

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific module
pytest tests/test_adjuster.py -v
```

## Project Structure

```
src/market_data/
├── clients/        # Exchange clients (Yahoo, Polygon, Oanda)
├── cleaning/       # Data cleaning (validation, adjustments, gaps)
├── core/           # Rate limiting, retry, config
├── models/         # Pydantic OHLCV models
└── storage/        # Parquet persistence
```

## Development

```bash
# Format code
make format

# Lint code
make lint

# Type check
make typecheck
```

## License

MIT
