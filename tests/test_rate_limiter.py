"""Tests for rate limiter."""

import asyncio
import time

import pytest

from market_data.core.rate_limiter import RateLimiter


class TestRateLimiter:
    """Tests for RateLimiter class."""
    
    @pytest.mark.asyncio
    async def test_basic_acquire(self):
        """Test basic token acquisition."""
        limiter = RateLimiter(rate=10.0, capacity=10.0)
        
        wait_time = await limiter.acquire()
        
        assert wait_time == 0.0  # Should not wait with full bucket
    
    @pytest.mark.asyncio
    async def test_multiple_acquires_within_capacity(self):
        """Test multiple acquires within capacity."""
        limiter = RateLimiter(rate=100.0, capacity=10.0)
        
        for _ in range(5):
            wait_time = await limiter.acquire()
            assert wait_time == 0.0
    
    @pytest.mark.asyncio
    async def test_acquire_waits_when_exhausted(self):
        """Test that acquire waits when tokens exhausted."""
        # Very slow rate to force waiting
        limiter = RateLimiter(rate=1.0, capacity=1.0)
        
        # First acquire should be instant
        await limiter.acquire()
        
        # Second acquire should wait
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        
        # Should have waited approximately 1 second
        assert elapsed >= 0.9
    
    @pytest.mark.asyncio
    async def test_tokens_refill(self):
        """Test that tokens refill over time."""
        limiter = RateLimiter(rate=100.0, capacity=10.0)
        
        # Exhaust some tokens
        for _ in range(5):
            await limiter.acquire()
        
        initial_tokens = limiter.available_tokens
        
        # Wait for refill
        await asyncio.sleep(0.1)
        
        # Should have more tokens now
        assert limiter.available_tokens > initial_tokens
    
    @pytest.mark.asyncio
    async def test_capacity_limit(self):
        """Test that tokens don't exceed capacity."""
        limiter = RateLimiter(rate=1000.0, capacity=10.0)
        
        # Wait for potential over-refill
        await asyncio.sleep(0.1)
        
        assert limiter.available_tokens <= 10.0
    
    def test_from_requests_per_minute(self):
        """Test creating limiter from RPM."""
        limiter = RateLimiter.from_requests_per_minute(60.0)
        
        assert limiter.rate == 1.0  # 60 rpm = 1 rps
    
    def test_from_requests_per_hour(self):
        """Test creating limiter from RPH."""
        limiter = RateLimiter.from_requests_per_hour(3600.0)
        
        assert limiter.rate == 1.0  # 3600 rph = 1 rps
    
    @pytest.mark.asyncio
    async def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens at once."""
        limiter = RateLimiter(rate=10.0, capacity=10.0)
        
        wait_time = await limiter.acquire(tokens=5.0)
        
        assert wait_time == 0.0
        # Use approximate check due to time-based refill
        assert abs(limiter.available_tokens - 5.0) < 0.1
    
    @pytest.mark.asyncio
    async def test_concurrent_acquires(self):
        """Test concurrent token acquisition."""
        limiter = RateLimiter(rate=100.0, capacity=10.0)
        
        async def acquire_token():
            await limiter.acquire()
            return True
        
        # Run 5 concurrent acquires
        results = await asyncio.gather(*[acquire_token() for _ in range(5)])
        
        assert all(results)
        # Allow small tolerance due to time-based refill
        assert limiter.available_tokens <= 5.5  # Used at least 5 tokens
