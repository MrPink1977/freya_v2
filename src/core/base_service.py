"""
Base Service - Abstract base class for all Freya services

All services (Audio, STT, TTS, LLM, etc.) inherit from this class
to ensure consistent lifecycle management and message bus integration.
"""

from abc import ABC, abstractmethod
from typing import Optional
from loguru import logger

from src.core.message_bus import MessageBus


class BaseService(ABC):
    """
    Abstract base class for all Freya services.
    
    Provides common functionality for:
    - Message bus integration
    - Lifecycle management (start/stop)
    - Health checking
    """
    
    def __init__(self, name: str, message_bus: MessageBus):
        self.name = name
        self.message_bus = message_bus
        self._running = False
        self._healthy = False
        
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the service.
        
        This is called once during startup to set up any resources,
        connections, or models needed by the service.
        """
        pass
        
    @abstractmethod
    async def start(self) -> None:
        """
        Start the service.
        
        This is called to begin the service's main processing loop.
        Should subscribe to relevant message bus channels here.
        """
        pass
        
    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the service gracefully.
        
        Clean up resources, close connections, and unsubscribe from
        message bus channels.
        """
        pass
        
    async def health_check(self) -> bool:
        """
        Check if the service is healthy.
        
        Returns:
            True if the service is operational, False otherwise
        """
        return self._healthy
        
    def is_running(self) -> bool:
        """Check if the service is currently running."""
        return self._running
        
    async def publish_status(self, status: str, details: Optional[dict] = None) -> None:
        """
        Publish service status to the message bus.
        
        Args:
            status: Status string (e.g., "started", "stopped", "error")
            details: Optional additional details
        """
        message = {
            "service": self.name,
            "status": status,
            "healthy": self._healthy,
        }
        if details:
            message["details"] = details
            
        await self.message_bus.publish(f"service.{self.name}.status", message)
        logger.info(f"[{self.name}] Status: {status}")
