"""
Base Service - Abstract base class for all Freya services

All services (Audio, STT, TTS, LLM, etc.) inherit from this class
to ensure consistent lifecycle management and message bus integration.

Author: MrPink1977
Version: 0.1.0
Date: 2025-12-03
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime

from src.core.message_bus import MessageBus


class ServiceError(Exception):
    """Base exception for service errors."""
    pass


class BaseService(ABC):
    """
    Abstract base class for all Freya services.
    
    Provides common functionality for:
    - Message bus integration
    - Lifecycle management (initialize/start/stop)
    - Health checking
    - Status reporting
    
    Attributes:
        name (str): Service name for identification
        message_bus (MessageBus): Shared message bus instance
        _running (bool): Whether service is currently running
        _healthy (bool): Whether service is healthy
        _start_time (Optional[datetime]): Service start timestamp
        _error_count (int): Number of errors encountered
        
    Example:
        >>> class MyService(BaseService):
        ...     async def initialize(self) -> None:
        ...         # Setup code
        ...         self._healthy = True
        ...     async def start(self) -> None:
        ...         self._running = True
        ...         await self.message_bus.subscribe("my.channel", self._handler)
        ...     async def stop(self) -> None:
        ...         self._running = False
    """
    
    def __init__(self, name: str, message_bus: MessageBus) -> None:
        """
        Initialize the base service.
        
        Args:
            name: Service name (e.g., "llm_engine", "audio_manager")
            message_bus: Shared MessageBus instance for communication
            
        Raises:
            ValueError: If name is empty or message_bus is None
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"Invalid service name: {name}")
            
        if not message_bus:
            raise ValueError("MessageBus instance is required")
            
        self.name = name
        self.message_bus = message_bus
        self._running = False
        self._healthy = False
        self._start_time: Optional[datetime] = None
        self._error_count = 0
        
        logger.debug(f"[{self.name}] Service instance created")
        
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the service.
        
        This is called once during startup to set up any resources,
        connections, or models needed by the service.
        
        Implementations should:
        - Load configuration
        - Initialize external connections
        - Load models/resources
        - Set self._healthy = True on success
        
        Raises:
            ServiceError: If initialization fails
        """
        pass
        
    @abstractmethod
    async def start(self) -> None:
        """
        Start the service.
        
        This is called to begin the service's main processing loop.
        Should subscribe to relevant message bus channels here.
        
        Implementations should:
        - Set self._running = True
        - Subscribe to message bus channels
        - Start background tasks if needed
        - Call await self.publish_status("started")
        
        Raises:
            ServiceError: If service fails to start
        """
        pass
        
    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the service gracefully.
        
        Clean up resources, close connections, and unsubscribe from
        message bus channels.
        
        Implementations should:
        - Set self._running = False
        - Unsubscribe from message bus channels
        - Clean up resources
        - Call await self.publish_status("stopped")
        
        Raises:
            ServiceError: If service fails to stop cleanly
        """
        pass
        
    async def health_check(self) -> bool:
        """
        Check if the service is healthy.
        
        Override this method to implement custom health checks.
        
        Returns:
            True if the service is operational, False otherwise
            
        Example:
            >>> async def health_check(self) -> bool:
            ...     if not await super().health_check():
            ...         return False
            ...     # Custom checks
            ...     return self.model_loaded and self.connection_active
        """
        return self._healthy and self._running
        
    def is_running(self) -> bool:
        """
        Check if the service is currently running.
        
        Returns:
            True if running, False otherwise
        """
        return self._running
        
    def is_healthy(self) -> bool:
        """
        Check if the service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        return self._healthy
        
    def get_uptime(self) -> Optional[float]:
        """
        Get service uptime in seconds.
        
        Returns:
            Uptime in seconds, or None if not started
        """
        if self._start_time:
            return (datetime.now() - self._start_time).total_seconds()
        return None
        
    def get_error_count(self) -> int:
        """
        Get the number of errors encountered.
        
        Returns:
            Error count
        """
        return self._error_count
        
    def increment_error_count(self) -> None:
        """Increment the error counter."""
        self._error_count += 1
        logger.warning(f"[{self.name}] Error count increased to {self._error_count}")
        
    def reset_error_count(self) -> None:
        """Reset the error counter."""
        self._error_count = 0
        logger.debug(f"[{self.name}] Error count reset")
        
    async def publish_status(
        self, 
        status: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Publish service status to the message bus.
        
        Args:
            status: Status string (e.g., "started", "stopped", "error", "healthy")
            details: Optional additional details about the status
            
        Example:
            >>> await self.publish_status("error", {
            ...     "error_type": "ConnectionError",
            ...     "message": "Failed to connect to API"
            ... })
        """
        try:
            message: Dict[str, Any] = {
                "service": self.name,
                "status": status,
                "healthy": self._healthy,
                "running": self._running,
                "timestamp": datetime.now().isoformat(),
            }
            
            if self._start_time:
                message["uptime_seconds"] = self.get_uptime()
                
            if self._error_count > 0:
                message["error_count"] = self._error_count
                
            if details:
                message["details"] = details
                
            await self.message_bus.publish(f"service.{self.name}.status", message)
            
            # Use appropriate log level based on status
            if status == "error":
                logger.error(f"[{self.name}] Status: {status} - {details}")
            elif status in ("started", "stopped"):
                logger.info(f"[{self.name}] Status: {status}")
            else:
                logger.debug(f"[{self.name}] Status: {status}")
                
        except Exception as e:
            logger.error(f"[{self.name}] Failed to publish status: {e}")
            # Don't raise - status publishing should not break the service
            
    async def publish_metric(
        self, 
        metric_name: str, 
        value: Any, 
        unit: Optional[str] = None
    ) -> None:
        """
        Publish a service metric to the message bus.
        
        Args:
            metric_name: Name of the metric (e.g., "response_time", "requests_processed")
            value: Metric value
            unit: Optional unit (e.g., "ms", "count", "bytes")
            
        Example:
            >>> await self.publish_metric("inference_time", 1.23, "seconds")
        """
        try:
            message = {
                "service": self.name,
                "metric": metric_name,
                "value": value,
                "timestamp": datetime.now().isoformat(),
            }
            
            if unit:
                message["unit"] = unit
                
            await self.message_bus.publish(f"service.{self.name}.metrics", message)
            logger.debug(f"[{self.name}] Metric: {metric_name}={value}{unit or ''}")
            
        except Exception as e:
            logger.error(f"[{self.name}] Failed to publish metric: {e}")
            
    def _mark_started(self) -> None:
        """Mark the service as started (internal use)."""
        self._running = True
        self._start_time = datetime.now()
        logger.info(f"[{self.name}] ✓ Service started at {self._start_time.isoformat()}")
        
    def _mark_stopped(self) -> None:
        """Mark the service as stopped (internal use)."""
        uptime = self.get_uptime()
        self._running = False
        self._start_time = None
        logger.info(
            f"[{self.name}] ✓ Service stopped "
            f"(uptime: {uptime:.2f}s)" if uptime else ""
        )
