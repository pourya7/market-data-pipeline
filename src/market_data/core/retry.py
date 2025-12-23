"""Retry logic with exponential backoff using tenacity."""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryableError(Exception):
    """Base exception for errors that should trigger a retry."""
    pass


class RateLimitError(RetryableError):
    """Raised when rate limit is hit (HTTP 429)."""
    pass


class TemporaryAPIError(RetryableError):
    """Raised for temporary API errors (5xx, timeouts)."""
    pass


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    retry_exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable:
    """Decorator factory for adding retry logic to async functions.
    
    Uses exponential backoff between retries.
    
    Args:
        max_attempts: Maximum number of retry attempts.
        min_wait: Minimum wait time between retries in seconds.
        max_wait: Maximum wait time between retries in seconds.
        retry_exceptions: Tuple of exception types to retry on.
                         Defaults to RetryableError and its subclasses.
    
    Returns:
        Decorator function.
        
    Example:
        @with_retry(max_attempts=5, min_wait=2.0)
        async def fetch_data():
            # API call that might fail
            ...
    """
    if retry_exceptions is None:
        retry_exceptions = (RetryableError,)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(retry_exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def create_retry_decorator(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
) -> Callable:
    """Create a retry decorator with default settings for API calls.
    
    Retries on:
    - RateLimitError (HTTP 429)
    - TemporaryAPIError (5xx errors, timeouts)
    - ConnectionError
    - TimeoutError
    
    Args:
        max_attempts: Maximum number of retry attempts.
        min_wait: Minimum wait time between retries in seconds.
        max_wait: Maximum wait time between retries in seconds.
        
    Returns:
        Configured retry decorator.
    """
    return with_retry(
        max_attempts=max_attempts,
        min_wait=min_wait,
        max_wait=max_wait,
        retry_exceptions=(
            RetryableError,
            ConnectionError,
            TimeoutError,
        ),
    )


# Pre-configured decorator for common API retry patterns
api_retry = create_retry_decorator(max_attempts=3, min_wait=1.0, max_wait=30.0)
