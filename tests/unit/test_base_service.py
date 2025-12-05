"""
Unit tests for BaseService

Tests the base service lifecycle, health checks, and metric tracking.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.core.base_service import BaseService, ServiceError


class ConcreteService(BaseService):
    """Concrete implementation of BaseService for testing."""
    
    async def initialize(self):
        """Initialize the service."""
        self._healthy = True
    
    async def start(self):
        """Start the service."""
        self._mark_started()
    
    async def stop(self):
        """Stop the service."""
        self._mark_stopped()


class TestBaseService:
    """Test suite for BaseService class."""
    
    @pytest.fixture
    async def service(self, mock_message_bus):
        """Create a ConcreteService instance for testing."""
        service = ConcreteService("test_service", mock_message_bus)
        yield service
        # Cleanup
        if service._running:
            await service.stop()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialization(self, mock_message_bus):
        """Test service initialization."""
        service = ConcreteService("test_service", mock_message_bus)
        
        assert service.name == "test_service"
        assert service.message_bus == mock_message_bus
        assert not service._running
        assert not service._healthy
        assert service._error_count == 0
        assert service._start_time is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_lifecycle(self, service):
        """Test complete service lifecycle."""
        # Initialize
        await service.initialize()
        assert service._healthy is True
        
        # Start
        await service.start()
        assert service._running is True
        assert service._start_time is not None
        
        # Stop
        await service.stop()
        assert service._running is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_health_check(self, service):
        """Test health check functionality."""
        # Unhealthy initially
        health = await service.health_check()
        assert health is False

        # Healthy after initialization (even without start)
        await service.initialize()
        health = await service.health_check()
        assert health is True
        assert service.is_running() is False  # Not started yet

        # Still healthy after start
        await service.start()
        health = await service.health_check()
        assert health is True
        assert service.is_running() is True
        assert service.is_healthy_and_running() is True

        # Unhealthy if error count exceeds threshold
        for _ in range(11):
            service.increment_error_count()
        health = await service.health_check()
        assert health is False  # Too many errors
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_uptime_tracking(self, service):
        """Test uptime tracking."""
        await service.initialize()
        await service.start()
        
        # Wait a bit
        await asyncio.sleep(0.1)
        
        uptime = service.get_uptime()
        assert uptime > 0
        assert uptime >= 0.1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_counting(self, service):
        """Test error count tracking."""
        assert service.get_error_count() == 0
        
        service.increment_error_count()
        assert service.get_error_count() == 1
        
        service.increment_error_count()
        service.increment_error_count()
        assert service.get_error_count() == 3
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_status_publishing(self, service, mock_message_bus):
        """Test status publishing to message bus."""
        await service.initialize()
        await service.start()
        
        # Publish status
        await service.publish_status("running", {"extra": "data"})
        
        # Verify message bus publish was called
        assert mock_message_bus.publish.called
        
        # Get the call arguments
        call_args = mock_message_bus.publish.call_args
        channel = call_args[0][0]
        data = call_args[0][1]
        
        assert "service.test_service.status" in channel
        assert data["status"] == "running"
        assert data["service"] == "test_service"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_metrics_publishing(self, service, mock_message_bus):
        """Test metrics publishing to message bus."""
        await service.initialize()
        await service.start()

        # Publish metrics
        metrics = {"requests": 100, "latency": 0.5}
        await service.publish_metrics(metrics)

        # Verify message bus publish was called
        assert mock_message_bus.publish.called

        call_args = mock_message_bus.publish.call_args
        channel = call_args[0][0]
        data = call_args[0][1]

        assert "service.test_service.metrics" in channel
        assert data["service"] == "test_service"
        assert "metrics" in data
        assert data["metrics"]["requests"] == 100
        assert data["metrics"]["latency"] == 0.5
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_error_exception(self):
        """Test ServiceError exception."""
        with pytest.raises(ServiceError) as exc_info:
            raise ServiceError("Test error message")
        
        assert "Test error message" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_start_stop(self, service):
        """Test that multiple start/stop calls are handled gracefully."""
        await service.initialize()
        
        # Start multiple times
        await service.start()
        await service.start()  # Should be safe
        assert service._running is True
        
        # Stop multiple times
        await service.stop()
        await service.stop()  # Should be safe
        assert service._running is False
