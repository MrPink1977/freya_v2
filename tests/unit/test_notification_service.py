"""
Unit Tests for Notification Service

Tests notification service functionality, message handling, and channel implementations.

Author: Freya AI
Version: 0.1.0
Date: 2025-12-06
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from src.services.notification import (
    NotificationService,
    NotificationServiceError,
    NotificationRequest,
    NotificationResult,
    SystemAlert,
    NotificationChannel,
    NotificationType,
    NotificationPriority,
)
from src.core.message_bus import MessageBus


@pytest.fixture
def mock_message_bus() -> MessageBus:
    """Create a mock MessageBus instance."""
    bus = MagicMock(spec=MessageBus)
    bus.subscribe = AsyncMock()
    bus.unsubscribe = AsyncMock()
    bus.publish = AsyncMock()
    bus.is_connected = True
    return bus


@pytest.fixture
async def notification_service(mock_message_bus: MessageBus) -> NotificationService:
    """Create a NotificationService instance."""
    service = NotificationService(mock_message_bus)
    return service


# ==================== Initialization Tests ====================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_service_initialization(notification_service: NotificationService) -> None:
    """Test notification service initialization."""
    await notification_service.initialize()

    assert notification_service._healthy is True
    assert notification_service.name == "notification_service"
    assert notification_service.total_sent == 0
    assert notification_service.total_failed == 0
    assert len(notification_service.channel_counts) > 0
    assert len(notification_service.type_counts) > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_service_start(mock_message_bus: MessageBus, notification_service: NotificationService) -> None:
    """Test notification service start."""
    await notification_service.initialize()
    await notification_service.start()

    assert notification_service.is_running() is True
    assert mock_message_bus.subscribe.call_count == 2
    mock_message_bus.subscribe.assert_any_call(
        "notification.send", notification_service._handle_notification_request
    )
    mock_message_bus.subscribe.assert_any_call(
        "system.alert", notification_service._handle_system_alert
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_service_stop(mock_message_bus: MessageBus, notification_service: NotificationService) -> None:
    """Test notification service stop."""
    await notification_service.initialize()
    await notification_service.start()
    await notification_service.stop()

    assert notification_service.is_running() is False
    assert mock_message_bus.unsubscribe.call_count == 2
    mock_message_bus.unsubscribe.assert_any_call("notification.send")
    mock_message_bus.unsubscribe.assert_any_call("system.alert")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_healthy(
    mock_message_bus: MessageBus, notification_service: NotificationService
) -> None:
    """Test health check when service is healthy."""
    await notification_service.initialize()
    await notification_service.start()

    assert await notification_service.health_check() is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_unhealthy_message_bus(
    mock_message_bus: MessageBus, notification_service: NotificationService
) -> None:
    """Test health check when message bus is disconnected."""
    await notification_service.initialize()
    await notification_service.start()

    mock_message_bus.is_connected = False

    assert await notification_service.health_check() is False


# ==================== Notification Request Tests ====================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_notification_request_console(
    mock_message_bus: MessageBus, notification_service: NotificationService
) -> None:
    """Test handling notification request for console channel."""
    await notification_service.initialize()
    await notification_service.start()

    request_data: Dict[str, Any] = {
        "message": "Test notification",
        "type": "info",
        "priority": "normal",
        "channels": ["console"],
    }

    await notification_service._handle_notification_request(request_data)

    assert notification_service.total_sent == 1
    assert notification_service.total_failed == 0
    assert notification_service.channel_counts["console"] == 1
    assert mock_message_bus.publish.call_count >= 1

    # Verify notification.sent was published
    published_channels = [call[0][0] for call in mock_message_bus.publish.call_args_list]
    assert "notification.sent" in published_channels


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_notification_request_multiple_channels(
    mock_message_bus: MessageBus, notification_service: NotificationService
) -> None:
    """Test handling notification request with multiple channels."""
    await notification_service.initialize()
    await notification_service.start()

    request_data: Dict[str, Any] = {
        "message": "Multi-channel notification",
        "type": "info",
        "priority": "normal",
        "channels": ["console", "gui"],
    }

    await notification_service._handle_notification_request(request_data)

    assert notification_service.total_sent == 1
    assert notification_service.channel_counts["console"] == 1
    assert notification_service.channel_counts["gui"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_notification_request_invalid_data(
    mock_message_bus: MessageBus, notification_service: NotificationService
) -> None:
    """Test handling invalid notification request."""
    await notification_service.initialize()
    await notification_service.start()

    # Missing required 'message' field
    request_data: Dict[str, Any] = {
        "type": "info",
        "priority": "normal",
    }

    await notification_service._handle_notification_request(request_data)

    # Should not increment sent count for invalid data
    assert notification_service.total_sent == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_notification_expired(
    mock_message_bus: MessageBus, notification_service: NotificationService
) -> None:
    """Test handling expired notification."""
    await notification_service.initialize()
    await notification_service.start()

    # Create notification with past expiration
    request_data: Dict[str, Any] = {
        "message": "Expired notification",
        "type": "info",
        "priority": "normal",
        "channels": ["console"],
        "expires_at": "2020-01-01T00:00:00Z",
    }

    await notification_service._handle_notification_request(request_data)

    # Should not send expired notification
    assert notification_service.total_sent == 0


# ==================== System Alert Tests ====================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_system_alert(
    mock_message_bus: MessageBus, notification_service: NotificationService
) -> None:
    """Test handling system alert."""
    await notification_service.initialize()
    await notification_service.start()

    alert_data: Dict[str, Any] = {
        "message": "Critical system error",
        "priority": "critical",
        "source": "llm_service",
        "error_details": {"error": "Out of memory"},
    }

    with patch.object(
        notification_service, "_handle_notification_request", new_callable=AsyncMock
    ) as mock_handle:
        await notification_service._handle_system_alert(alert_data)
        assert mock_handle.called


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_invalid_system_alert(
    mock_message_bus: MessageBus, notification_service: NotificationService
) -> None:
    """Test handling invalid system alert."""
    await notification_service.initialize()
    await notification_service.start()

    # Missing required 'message' and 'source' fields
    alert_data: Dict[str, Any] = {
        "priority": "high",
    }

    await notification_service._handle_system_alert(alert_data)

    # Should handle gracefully without crashing
    assert notification_service.total_sent == 0


# ==================== Channel Implementation Tests ====================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_console_success(notification_service: NotificationService) -> None:
    """Test sending console notification."""
    await notification_service.initialize()

    request = NotificationRequest(
        message="Test console message", type=NotificationType.INFO, channels=[NotificationChannel.CONSOLE]
    )

    result = await notification_service._send_console(request)
    assert result is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_console_different_types(notification_service: NotificationService) -> None:
    """Test console notifications with different types."""
    await notification_service.initialize()

    types = [
        NotificationType.INFO,
        NotificationType.SUCCESS,
        NotificationType.WARNING,
        NotificationType.ERROR,
        NotificationType.ALERT,
    ]

    for ntype in types:
        request = NotificationRequest(
            message=f"Test {ntype.value} message", type=ntype, channels=[NotificationChannel.CONSOLE]
        )

        result = await notification_service._send_console(request)
        assert result is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_gui(mock_message_bus: MessageBus, notification_service: NotificationService) -> None:
    """Test sending GUI notification."""
    notification_service.message_bus = mock_message_bus
    await notification_service.initialize()

    request = NotificationRequest(
        message="Test GUI message",
        type=NotificationType.INFO,
        subject="Test Subject",
        channels=[NotificationChannel.GUI],
    )

    result = await notification_service._send_gui(request)
    assert result is True
    mock_message_bus.publish.assert_called_once()

    # Verify published to gui.notification channel
    call_args = mock_message_bus.publish.call_args
    assert call_args[0][0] == "gui.notification"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_email_disabled(notification_service: NotificationService) -> None:
    """Test email sending when disabled in config."""
    await notification_service.initialize()

    request = NotificationRequest(
        message="Test email", type=NotificationType.INFO, channels=[NotificationChannel.EMAIL]
    )

    result = await notification_service._send_email(request)
    # Should return False when disabled
    assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_webhook_disabled(notification_service: NotificationService) -> None:
    """Test webhook sending when disabled in config."""
    await notification_service.initialize()

    request = NotificationRequest(
        message="Test webhook", type=NotificationType.INFO, channels=[NotificationChannel.WEBHOOK]
    )

    result = await notification_service._send_webhook(request)
    assert result is False


# ==================== Metrics Tests ====================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_success_rate(notification_service: NotificationService) -> None:
    """Test success rate calculation."""
    await notification_service.initialize()

    # Test with no notifications
    assert notification_service._calculate_success_rate() == 1.0

    # Test with successful notifications
    notification_service.total_sent = 8
    notification_service.total_failed = 2
    assert notification_service._calculate_success_rate() == 0.8

    # Test with all failures
    notification_service.total_sent = 0
    notification_service.total_failed = 10
    assert notification_service._calculate_success_rate() == 0.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_avg_duration(notification_service: NotificationService) -> None:
    """Test average duration calculation."""
    await notification_service.initialize()

    # Test with no notifications
    assert notification_service._calculate_avg_duration() is None

    # Test with notifications
    notification_service.total_sent = 5
    notification_service.total_duration = 500.0  # 500ms total
    assert notification_service._calculate_avg_duration() == 100.0  # 100ms average


@pytest.mark.unit
@pytest.mark.asyncio
async def test_publish_metrics(mock_message_bus: MessageBus, notification_service: NotificationService) -> None:
    """Test metrics publishing."""
    notification_service.message_bus = mock_message_bus
    await notification_service.initialize()

    notification_service.total_sent = 10
    notification_service.total_failed = 2

    await notification_service._publish_metrics()

    # Should publish metrics
    assert mock_message_bus.publish.called


# ==================== Error Handling Tests ====================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialization_failure() -> None:
    """Test service behavior on initialization failure."""
    mock_bus = MagicMock(spec=MessageBus)
    service = NotificationService(mock_bus)

    with patch.object(service, "_initialize_backends", side_effect=Exception("Backend init failed")):
        with pytest.raises(NotificationServiceError):
            await service.initialize()

        assert service._healthy is False
        assert service.error_count > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_channel_exception_handling(notification_service: NotificationService) -> None:
    """Test exception handling in channel sending."""
    await notification_service.initialize()

    request = NotificationRequest(
        message="Test message", type=NotificationType.INFO, channels=[NotificationChannel.GUI]
    )

    # Simulate exception in GUI channel
    with patch.object(notification_service, "_send_gui", side_effect=Exception("GUI error")):
        success, channel_results, error = await notification_service._send_notification(request)

        assert success is False  # Overall failure
        assert channel_results["gui"] is False
        assert "gui" in error.lower()


# ==================== Pydantic Model Tests ====================


@pytest.mark.unit
def test_notification_request_validation() -> None:
    """Test NotificationRequest model validation."""
    # Valid request
    request = NotificationRequest(
        message="Test notification",
        type=NotificationType.INFO,
        priority=NotificationPriority.NORMAL,
        channels=[NotificationChannel.CONSOLE],
    )

    assert request.message == "Test notification"
    assert request.type == NotificationType.INFO
    assert request.priority == NotificationPriority.NORMAL

    # Test with invalid data
    with pytest.raises(Exception):  # Pydantic validation error
        NotificationRequest(message="")  # Empty message


@pytest.mark.unit
def test_system_alert_validation() -> None:
    """Test SystemAlert model validation."""
    alert = SystemAlert(
        message="Critical error", priority=NotificationPriority.CRITICAL, source="test_service"
    )

    assert alert.message == "Critical error"
    assert alert.source == "test_service"

    # Test with missing required field
    with pytest.raises(Exception):  # Pydantic validation error
        SystemAlert(message="Test")  # Missing 'source'


@pytest.mark.unit
def test_notification_result_model() -> None:
    """Test NotificationResult model."""
    result = NotificationResult(
        success=True,
        message="Test message",
        type=NotificationType.INFO,
        channels=[NotificationChannel.CONSOLE],
        channel_results={"console": True},
        duration_ms=50.5,
    )

    assert result.success is True
    assert result.duration_ms == 50.5
    assert result.channel_results["console"] is True


# ==================== Integration-style Tests ====================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_full_notification_flow(
    mock_message_bus: MessageBus, notification_service: NotificationService
) -> None:
    """Test complete notification flow from request to result."""
    await notification_service.initialize()
    await notification_service.start()

    request_data: Dict[str, Any] = {
        "message": "Complete flow test",
        "type": "success",
        "priority": "high",
        "channels": ["console", "gui"],
        "subject": "Test Success",
    }

    await notification_service._handle_notification_request(request_data)

    # Verify metrics updated
    assert notification_service.total_sent == 1
    assert notification_service.total_failed == 0
    assert notification_service.type_counts["success"] == 1
    assert notification_service.channel_counts["console"] == 1
    assert notification_service.channel_counts["gui"] == 1

    # Verify message bus publish called
    assert mock_message_bus.publish.called

    # Verify notification.sent published
    published_channels = [call[0][0] for call in mock_message_bus.publish.call_args_list]
    assert "notification.sent" in published_channels


@pytest.mark.unit
@pytest.mark.asyncio
async def test_periodic_metrics_publishing(
    mock_message_bus: MessageBus, notification_service: NotificationService
) -> None:
    """Test that metrics are published periodically."""
    await notification_service.initialize()
    await notification_service.start()

    # Send 10 notifications to trigger metrics publishing
    for i in range(10):
        request_data: Dict[str, Any] = {
            "message": f"Notification {i}",
            "type": "info",
            "channels": ["console"],
        }
        await notification_service._handle_notification_request(request_data)

    # Verify metrics were published
    assert notification_service.total_sent == 10

    # Check that metrics publishing was called
    service_metric_calls = [
        call for call in mock_message_bus.publish.call_args_list
        if "metrics" in str(call[0][0])
    ]
    assert len(service_metric_calls) > 0
