"""
Circuit Breaker Pattern for Freya v2.0

Prevents cascading failures by temporarily blocking requests to failing services.

Author: MrPink1977
Version: 0.1.0
Date: 2024-12-06
"""

import asyncio
import time
from enum import Enum
from typing import Callable, TypeVar, Optional
from loguru import logger

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, block all requests
    - HALF_OPEN: Testing if service recovered
    
    Example:
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30.0,
            expected_exception=ConnectionError
        )
        
        @breaker.protect
        async def call_external_service():
            return await service.call()
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: type = Exception,
        name: str = "CircuitBreaker"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type that triggers circuit breaker
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._success_count = 0
        
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self._state == CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return False
        return time.time() - self._last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful request."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= 2:  # Require 2 successes to close
                logger.success(f"[{self.name}] Circuit closed - service recovered")
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0  # Reset failure count on success
    
    def _on_failure(self, exception: Exception):
        """Handle failed request."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        self._success_count = 0
        
        if self._state == CircuitState.HALF_OPEN:
            logger.warning(f"[{self.name}] Circuit reopened - service still failing")
            self._state = CircuitState.OPEN
        elif self._failure_count >= self.failure_threshold:
            logger.error(
                f"[{self.name}] Circuit opened after {self._failure_count} failures. "
                f"Will retry in {self.recovery_timeout}s"
            )
            self._state = CircuitState.OPEN
    
    def protect(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator to protect async function with circuit breaker.
        
        Example:
            @breaker.protect
            async def risky_operation():
                return await external_service()
        """
        async def wrapper(*args, **kwargs) -> T:
            # Check if circuit is open
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"[{self.name}] Attempting recovery (half-open)")
                    self._state = CircuitState.HALF_OPEN
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is open. "
                        f"Service unavailable for {self.recovery_timeout}s"
                    )
            
            # Attempt request
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure(e)
                raise
        
        return wrapper
    
    def reset(self):
        """Manually reset circuit breaker to closed state."""
        logger.info(f"[{self.name}] Circuit manually reset")
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "is_available": self._state != CircuitState.OPEN
        }
