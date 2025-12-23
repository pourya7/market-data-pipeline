"""Token bucket rate limiter for API throttling."""

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class RateLimiter:
    """Token bucket rate limiter for controlling API request rates.
    
    Implements the token bucket algorithm where tokens are added at a fixed
    rate and consumed when requests are made. If no tokens are available,
    the request waits until a token becomes available.
    
    Example:
        limiter = RateLimiter(rate=5.0, capacity=10)  # 5 requests/second, burst of 10
        
        async def make_request():
            await limiter.acquire()
            # Make API call
    """
    
    rate: float = 1.0  # Tokens per second
    capacity: float = 10.0  # Maximum tokens (burst capacity)
    tokens: float = field(default=None, init=False)
    last_update: float = field(default=None, init=False)
    _lock: asyncio.Lock = field(default=None, init=False, repr=False)
    
    def __post_init__(self):
        """Initialize tokens and lock after dataclass creation."""
        self.tokens = self.capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: float = 1.0) -> float:
        """Acquire tokens, waiting if necessary.
        
        Args:
            tokens: Number of tokens to acquire (default 1).
            
        Returns:
            Time waited in seconds (0 if no wait was needed).
        """
        async with self._lock:
            wait_time = await self._acquire_impl(tokens)
        return wait_time
    
    async def _acquire_impl(self, tokens: float) -> float:
        """Internal implementation of token acquisition."""
        self._refill()
        
        wait_time = 0.0
        if self.tokens < tokens:
            # Calculate time needed to get enough tokens
            deficit = tokens - self.tokens
            wait_time = deficit / self.rate
            await asyncio.sleep(wait_time)
            self._refill()
        
        self.tokens -= tokens
        return wait_time
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
    
    @property
    def available_tokens(self) -> float:
        """Return current number of available tokens."""
        self._refill()
        return self.tokens
    
    @classmethod
    def from_requests_per_minute(cls, rpm: float, burst: float | None = None) -> "RateLimiter":
        """Create a rate limiter from requests per minute.
        
        Args:
            rpm: Requests per minute.
            burst: Burst capacity (defaults to rpm/10 or 1, whichever is larger).
            
        Returns:
            Configured RateLimiter instance.
        """
        rate = rpm / 60.0
        capacity = burst if burst is not None else max(rpm / 10, 1.0)
        return cls(rate=rate, capacity=capacity)
    
    @classmethod
    def from_requests_per_hour(cls, rph: float, burst: float | None = None) -> "RateLimiter":
        """Create a rate limiter from requests per hour.
        
        Args:
            rph: Requests per hour.
            burst: Burst capacity (defaults to rph/100 or 1, whichever is larger).
            
        Returns:
            Configured RateLimiter instance.
        """
        rate = rph / 3600.0
        capacity = burst if burst is not None else max(rph / 100, 1.0)
        return cls(rate=rate, capacity=capacity)
