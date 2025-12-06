"""
Retry and Resilience Utilities for Freya v2.0

Provides decorators and utilities for handling transient failures
with exponential backoff, jitter, and circuit breaker patterns.

Author: MrPink1977
Version: 0.1.0
Date: 2024-12-06
"""

import asyncio
import functools
import random
from typing import Callable, TypeVar, Any, Optional, Type, Tuple
from loguru import logger

T = TypeVar('T')


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""
    pass


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and blocking requests."""
    pass


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        jitter: Add random jitter to prevent thundering herd
        exceptions: Tuple of exception types to retry on
        on_retry: Optional callback function called on each retry
        
    Example:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        async def call_external_api():
            return await api.get_data()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"[Retry] {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise RetryExhaustedError(
                            f"Failed after {max_retries} retries: {e}"
                        ) from e
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"[Retry] {func.__name__} attempt {attempt + 1}/{max_retries} "
                        f"failed: {e}. Retrying in {delay:.2f}s..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    await asyncio.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def retry_sync(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for retrying synchronous functions with exponential backoff.
    
    Same as retry_with_backoff but for sync functions.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"[Retry] {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise RetryExhaustedError(
                            f"Failed after {max_retries} retries: {e}"
                        ) from e
                    
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"[Retry] {func.__name__} attempt {attempt + 1}/{max_retries} "
                        f"failed: {e}. Retrying in {delay:.2f}s..."
                    )
                    
                    import time
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


async def with_timeout(
    coro: Callable[..., T],
    timeout: float,
    error_message: str = "Operation timed out"
) -> T:
    """
    Execute coroutine with timeout.
    
    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        error_message: Error message if timeout occurs
        
    Returns:
        Result of coroutine
        
    Raises:
        asyncio.TimeoutError: If operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"[Timeout] {error_message} (timeout: {timeout}s)")
        raise asyncio.TimeoutError(error_message)
