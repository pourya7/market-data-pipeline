# Clients & Data Sources

Purpose
- Explain how the pipeline fetches market data from external providers and how clients are organized, configured, and hardened (rate limiting + retry).

Where the client code lives
- Directory: [src/market_data/clients](src/market_data/clients)
- Key files: [src/market_data/clients/base.py](src/market_data/clients/base.py), [src/market_data/clients/yahoo.py](src/market_data/clients/yahoo.py), [src/market_data/clients/polygon.py](src/market_data/clients/polygon.py), [src/market_data/clients/oanda.py](src/market_data/clients/oanda.py)

Design overview
- `base.py` defines a common adapter interface and shared helpers (request shaping, response normalization hooks).
- Each concrete client implements provider-specific API calls and maps responses into the project's canonical OHLCV/tick schema.
- Clients are intentionally thin: they do not perform cleaning or resampling — they return raw frames which the cleaning pipeline will normalize further.

Authentication & configuration
- API keys/secrets are read from the central config in [src/market_data/core/config.py](src/market_data/core/config.py) (or environment variables). Check the `tests/conftest.py` and `pyproject.toml` for test fixtures that mock keys.

Rate limiting and retry
- Calls to external APIs are wrapped with utilities from [src/market_data/core/rate_limiter.py](src/market_data/core/rate_limiter.py) and [src/market_data/core/retry.py](src/market_data/core/retry.py).
- `rate_limiter` enforces a maximum request rate (requests/sec or burst limits) to avoid hitting provider quotas.
- `retry` handles transient network/HTTP errors with exponential backoff and optional jitter. Clients call these helpers around network I/O.

Return format
- Each client converts provider-specific responses into a Pandas-friendly `DataFrame` (or typed record) with consistent columns (timestamp, open, high, low, close, volume, maybe exchange-specific fields).
- Timestamps are normalized to UTC and indexed/typed consistently so cleaning/resampling works predictably.

How to use a client (example)

```python
from market_data.clients.yahoo import YahooClient
from market_data.core.config import load_config

cfg = load_config()
client = YahooClient(api_key=cfg.get("yahoo_api_key"))
df = client.fetch_ohlcv(symbol="AAPL", start="2025-01-01", end="2025-01-31")
# df is a DataFrame with normalized timestamps and columns: ['open','high','low','close','volume']
```

Testing clients
- Unit tests for client behaviour live in `tests/test_clients.py` and integration tests in `tests/integration/test_yahoo_client.py`.
- Tests mock network calls and verify rate-limiter and retry wrappers operate as expected.

Common pitfalls and tips
- Watch timezones: provider timestamps may be local — ensure clients convert to UTC.
- Page/limit handling: Polygon and some providers paginate historical ticks — client implementations handle paging and stitch results before returning.
- Respect quotas: when running large backfills, run with conservative `rate_limiter` settings and consider request batching.

Where to read next
- Inspect the client implementations: [src/market_data/clients/base.py](src/market_data/clients/base.py) then each provider file.
- Read `src/market_data/core/rate_limiter.py` and `src/market_data/core/retry.py` to see how calls are guarded.

Next step
- Tell me to expand `Core Utilities` (recommended) or `Cleaning Pipeline` next; I will add `docs/core.md` or `docs/cleaning.md` accordingly.
