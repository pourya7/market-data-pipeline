# Concepts — Rate Limiting & Retry Rationale

Why rate limits matter
- External data providers impose rate limits to protect their infrastructure and enforce quotas. Respecting limits prevents service denial and account throttling.

Rate-limiting strategies
- Token-bucket / leaky-bucket: allow bursts while enforcing long-term average rates.
- Centralized limiter: a shared limiter across client instances avoids accidental concurrent spikes.

Retry strategies and why
- Network and transient server errors happen; retries with exponential backoff and jitter reduce collision and improve success without overloading targets.

Design trade-offs
- Aggressive retries can worsen outages; conservative retries with logging and alerts help diagnose persistent failures.
- Synchronous blocking vs async/non-blocking strategies depend on client design and throughput needs.

Why in `core`
- Centralizing rate-limiting and retry logic yields consistent behavior across all clients and simplifies testing and tuning.
