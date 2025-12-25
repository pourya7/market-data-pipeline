# Core Utilities

Purpose
- Central helpers used across the codebase: configuration loading, rate limiting, and retry logic for robust API calls.

Where the core code lives
- `src/market_data/core`
- Key files: `config.py`, `rate_limiter.py`, `retry.py`.

`config.py`
- Responsibility: load project configuration (from YAML, env vars, or defaults) and provide a single source of truth for clients and pipelines.
- Typical usage:

```python
from market_data.core.config import load_config
cfg = load_config()  # returns a simple mapping-like object
api_key = cfg.get("polygon_api_key")
rate = cfg.get("clients.polygon.rate_limit", 5)
```

- Look for tests or fixtures in `tests/conftest.py` showing how the config is mocked.

`rate_limiter.py`
- Responsibility: prevent exceeding provider rate limits by enforcing a maximum number of requests per time unit and optionally supporting burst tokens.
- Typical patterns:
  - Token-bucket or leaky-bucket implementation.
  - Blocking or async-friendly wait before making a request.
  - Shared instance used by client adapters to centralize rate control.

Example (conceptual)

```python
from market_data.core.rate_limiter import RateLimiter
limiter = RateLimiter(rate=5, per=1.0)  # 5 reqs per second
with limiter:
    response = requests.get(url)
```

- Check `tests/test_rate_limiter.py` for detailed behavior (sleeping vs non-blocking tests).

`retry.py`
- Responsibility: retry transient failures (network errors, 5xx responses) with exponential backoff and optional jitter.
- Typical features:
  - max attempts, initial backoff, multiplier, maximum backoff
  - predicate to decide which errors are retriable
  - optional hook/callback on each retry for logging

Example (conceptual)

```python
from market_data.core.retry import retry

@retry(max_attempts=5, backoff_factor=0.5)
def fetch():
    return requests.get(url)

# or usage helper
result = retry.call(fetch)
```

How clients use core utilities
- Clients import `load_config()` to get credentials and rate settings.
- Network calls are wrapped with `RateLimiter` and `retry` helpers so a single client failure doesn't cascade or hammer an API.

Testing core utilities
- See `tests/test_rate_limiter.py` and `tests/test_retry.py` for example behaviors and edge cases. These tests show expected wait times, attempt counts, and behavior under concurrency.

Where to read next
- `src/market_data/core/config.py` — how the project loads settings and defaults.
- `src/market_data/core/rate_limiter.py` — implementation details and concurrency model.
- `src/market_data/core/retry.py` — retry strategy and parameterization.

Next: which section should I expand after Core Utilities? (Cleaning pipeline is already present; I can expand Resampling & Bars next.)
