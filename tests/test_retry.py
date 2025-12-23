"""Tests for retry logic."""

import pytest

from market_data.core.retry import (
    with_retry,
    RetryableError,
    RateLimitError,
    TemporaryAPIError,
)


class TestRetryDecorator:
    """Tests for retry decorator."""
    
    @pytest.mark.asyncio
    async def test_no_retry_on_success(self):
        """Test that successful calls don't retry."""
        call_count = 0
        
        @with_retry(max_attempts=3)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await successful_func()
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_retryable_error(self):
        """Test retry on RetryableError."""
        call_count = 0
        
        @with_retry(max_attempts=3, min_wait=0.1, max_wait=0.1)
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableError("temporary failure")
            return "success"
        
        result = await failing_func()
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test that retries are exhausted."""
        call_count = 0
        
        @with_retry(max_attempts=3, min_wait=0.1, max_wait=0.1)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise RetryableError("always fails")
        
        with pytest.raises(RetryableError):
            await always_fails()
        
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable_error(self):
        """Test that non-retryable errors are not retried."""
        call_count = 0
        
        @with_retry(max_attempts=3)
        async def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")
        
        with pytest.raises(ValueError):
            await raises_value_error()
        
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_rate_limit_error(self):
        """Test retry on RateLimitError."""
        call_count = 0
        
        @with_retry(max_attempts=2, min_wait=0.1, max_wait=0.1)
        async def rate_limited_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError("429 Too Many Requests")
            return "success"
        
        result = await rate_limited_func()
        
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_on_temporary_api_error(self):
        """Test retry on TemporaryAPIError."""
        call_count = 0
        
        @with_retry(max_attempts=2, min_wait=0.1, max_wait=0.1)
        async def api_error_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TemporaryAPIError("500 Internal Server Error")
            return "success"
        
        result = await api_error_func()
        
        assert result == "success"
        assert call_count == 2


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""
    
    def test_rate_limit_error_is_retryable(self):
        """Test RateLimitError is a RetryableError."""
        assert issubclass(RateLimitError, RetryableError)
    
    def test_temporary_api_error_is_retryable(self):
        """Test TemporaryAPIError is a RetryableError."""
        assert issubclass(TemporaryAPIError, RetryableError)
