# Market Data Pipeline

Robust ETL for Quantitative Research - Multi-source financial data ingestion.

## Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from market_data.factory import ClientFactory
import asyncio

async def main():
    client = ClientFactory.create("yahoo")
    bars = await client.fetch_ohlcv("AAPL", "2024-01-01", "2024-01-05")
    print(f"Fetched {len(bars)} bars")

asyncio.run(main())
```

## Testing

```bash
pytest tests/ -v
```
