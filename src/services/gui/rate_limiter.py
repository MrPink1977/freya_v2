"""
Rate Limiting for GUI Service WebSocket Connections

Implements sliding window rate limiting to protect against abuse.

Author: Claude (AI Assistant)
Version: 0.1.0
Date: 2025-12-04
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
import asyncio
from loguru import logger


class RateLimiter:
    """
    Token bucket rate limiter with sliding window.
    
    Provides per-IP and per-session rate limiting for WebSocket connections.
    
    Uses a sliding window algorithm to track requests over time and enforce limits.
    
    Attributes:
        rate: Maximum requests per second
        burst: Maximum burst size (requests allowed in short burst)
        windows: Dict tracking request timestamps per identifier
    """
    
    def __init__(
        self,
        rate: float = 10.0,
        burst: int = 20,
        cleanup_interval: int = 300
    ) -> None:
        """
        Initialize RateLimiter.
        
        Args:
            rate: Maximum requests per second (default: 10)
            burst: Maximum burst size (default: 20)
            cleanup_interval: Seconds between cleanup of old entries (default: 300)
        """
        self.rate = rate
        self.burst = burst
        self.cleanup_interval = cleanup_interval
        
        # Track request timestamps per identifier
        self.windows: Dict[str, deque] = {}
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.debug(
            f"[RateLimiter] Initialized with rate={rate}/s, burst={burst}"
        )
    
    def _get_window(self, identifier: str) -> deque:
        """
        Get or create the request window for an identifier.
        
        Args:
            identifier: Client identifier (IP, session ID, etc.)
        
        Returns:
            Deque of request timestamps
        """
        if identifier not in self.windows:
            self.windows[identifier] = deque()
        return self.windows[identifier]
    
    def _cleanup_window(self, window: deque, cutoff_time: datetime) -> None:
        """
        Remove old timestamps from a window.
        
        Args:
            window: Deque of timestamps
            cutoff_time: Remove timestamps older than this
        """
        while window and window[0] < cutoff_time:
            window.popleft()
    
    def check_rate_limit(
        self,
        identifier: str,
        cost: int = 1
    ) -> bool:
        """
        Check if a request is allowed under rate limits.
        
        Args:
            identifier: Client identifier (IP, session ID, etc.)
            cost: Request cost in tokens (default: 1)
        
        Returns:
            True if request allowed, False if rate limit exceeded
        """
        now = datetime.utcnow()
        window = self._get_window(identifier)
        
        # Calculate window duration based on burst size
        window_duration = self.burst / self.rate
        cutoff_time = now - timedelta(seconds=window_duration)
        
        # Clean old timestamps
        self._cleanup_window(window, cutoff_time)
        
        # Check if adding this request would exceed limits
        current_count = len(window)
        
        if current_count + cost > self.burst:
            logger.warning(
                f"[RateLimiter] Rate limit exceeded for {identifier}: "
                f"{current_count}/{self.burst} requests"
            )
            return False
        
        # Add timestamp(s) for this request
        for _ in range(cost):
            window.append(now)
        
        return True
    
    def get_limit_status(self, identifier: str) -> Dict[str, any]:
        """
        Get current rate limit status for an identifier.
        
        Args:
            identifier: Client identifier
        
        Returns:
            Dict with limit status information
        """
        now = datetime.utcnow()
        window = self._get_window(identifier)
        
        # Clean old timestamps
        window_duration = self.burst / self.rate
        cutoff_time = now - timedelta(seconds=window_duration)
        self._cleanup_window(window, cutoff_time)
        
        current_count = len(window)
        remaining = max(0, self.burst - current_count)
        
        # Calculate estimated reset time
        if window:
            oldest_request = window[0]
            reset_time = oldest_request + timedelta(seconds=window_duration)
            reset_seconds = (reset_time - now).total_seconds()
        else:
            reset_seconds = 0
        
        return {
            "rate": self.rate,
            "burst": self.burst,
            "current": current_count,
            "remaining": remaining,
            "reset_in_seconds": max(0, reset_seconds),
            "limited": remaining == 0
        }
    
    def reset(self, identifier: str) -> bool:
        """
        Reset rate limit for an identifier.
        
        Args:
            identifier: Client identifier
        
        Returns:
            True if identifier existed, False otherwise
        """
        if identifier in self.windows:
            del self.windows[identifier]
            logger.info(f"[RateLimiter] Reset rate limit for {identifier}")
            return True
        return False
    
    def get_tracked_count(self) -> int:
        """
        Get number of tracked identifiers.
        
        Returns:
            Number of identifiers currently tracked
        """
        return len(self.windows)
    
    async def start_cleanup_task(self) -> None:
        """Start background task to cleanup old entries."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("[RateLimiter] Cleanup task started")
    
    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("[RateLimiter] Cleanup task stopped")
    
    async def _cleanup_loop(self) -> None:
        """Background loop to cleanup old rate limit windows."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[RateLimiter] Cleanup error: {e}")
    
    async def _cleanup_old_entries(self) -> None:
        """Remove entries for identifiers with no recent activity."""
        now = datetime.utcnow()
        window_duration = self.burst / self.rate
        cutoff_time = now - timedelta(seconds=window_duration * 2)  # Extra buffer
        
        stale_identifiers = []
        
        for identifier, window in self.windows.items():
            # Clean the window
            self._cleanup_window(window, cutoff_time)
            
            # If window is empty, mark for removal
            if not window:
                stale_identifiers.append(identifier)
        
        # Remove stale entries
        for identifier in stale_identifiers:
            del self.windows[identifier]
        
        if stale_identifiers:
            logger.debug(
                f"[RateLimiter] Cleaned up {len(stale_identifiers)} stale entries"
            )


class PerIPRateLimiter(RateLimiter):
    """Rate limiter that tracks by IP address."""
    
    def __init__(self, rate: float = 10.0, burst: int = 20) -> None:
        """
        Initialize per-IP rate limiter.
        
        Args:
            rate: Maximum requests per second per IP
            burst: Maximum burst size per IP
        """
        super().__init__(rate=rate, burst=burst)
        logger.debug("[PerIPRateLimiter] Initialized")


class PerSessionRateLimiter(RateLimiter):
    """Rate limiter that tracks by session ID."""
    
    def __init__(self, rate: float = 10.0, burst: int = 20) -> None:
        """
        Initialize per-session rate limiter.
        
        Args:
            rate: Maximum requests per second per session
            burst: Maximum burst size per session
        """
        super().__init__(rate=rate, burst=burst)
        logger.debug("[PerSessionRateLimiter] Initialized")


class CompositeRateLimiter:
    """
    Composite rate limiter that applies multiple limits.
    
    Checks both per-IP and per-session limits.
    """
    
    def __init__(
        self,
        ip_rate: float = 20.0,
        ip_burst: int = 40,
        session_rate: float = 10.0,
        session_burst: int = 20
    ) -> None:
        """
        Initialize composite rate limiter.
        
        Args:
            ip_rate: Maximum requests per second per IP
            ip_burst: Maximum burst size per IP
            session_rate: Maximum requests per second per session
            session_burst: Maximum burst size per session
        """
        self.ip_limiter = PerIPRateLimiter(rate=ip_rate, burst=ip_burst)
        self.session_limiter = PerSessionRateLimiter(
            rate=session_rate,
            burst=session_burst
        )
        
        logger.debug("[CompositeRateLimiter] Initialized with IP and session limits")
    
    def check_rate_limit(
        self,
        client_ip: str,
        session_id: str,
        cost: int = 1
    ) -> bool:
        """
        Check if request is allowed under both IP and session limits.
        
        Args:
            client_ip: Client IP address
            session_id: Session identifier
            cost: Request cost in tokens
        
        Returns:
            True if allowed under both limits, False otherwise
        """
        # Must pass both IP and session limits
        ip_ok = self.ip_limiter.check_rate_limit(client_ip, cost)
        session_ok = self.session_limiter.check_rate_limit(session_id, cost)
        
        return ip_ok and session_ok
    
    def get_limit_status(
        self,
        client_ip: str,
        session_id: str
    ) -> Dict[str, any]:
        """
        Get rate limit status for both IP and session.
        
        Args:
            client_ip: Client IP address
            session_id: Session identifier
        
        Returns:
            Dict with status for both limits
        """
        return {
            "ip": self.ip_limiter.get_limit_status(client_ip),
            "session": self.session_limiter.get_limit_status(session_id)
        }
    
    async def start_cleanup_task(self) -> None:
        """Start cleanup tasks for both limiters."""
        await self.ip_limiter.start_cleanup_task()
        await self.session_limiter.start_cleanup_task()
    
    async def stop_cleanup_task(self) -> None:
        """Stop cleanup tasks for both limiters."""
        await self.ip_limiter.stop_cleanup_task()
        await self.session_limiter.stop_cleanup_task()
