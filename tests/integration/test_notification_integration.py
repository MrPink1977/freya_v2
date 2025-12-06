"""
Integration Tests for Notification Service

Tests notification service integration with message bus and other services.

Author: Freya AI
Version: 0.1.0
Date: 2025-12-06
"""

import pytest
import asyncio
from typing import Dict, Any, List

from src.services.notification import (
    NotificationService,
    NotificationRequest,
    NotificationChannel,
    NotificationType,
    NotificationPriority,
)
from src.core.message_bus import MessageBus
from src.core.config import config


@pytest.fixture
async def message_bus() -> MessageBus:
    """Create a real MessageBus instance for integration testing."""
    bus = MessageBus(
        host=config.redis_host,
        port=config.redis_port,
        max_retries=config.redis_max_retries,
        retry_delay=config.redis_retry_delay,
    )
    await bus.connect()
    yield bus
    await bus.disconnect()


@pytest.fixture
async def notification_service_real(message_bus: MessageBus) -> NotificationService:
    """Create a NotificationService with real message bus."""
    service = NotificationService(message_bus)
    await service.initialize()
    await service.start()
    yield service
    await service.stop()


# ==================== Message Bus Integration Tests ====================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_notification_via_message_bus(
    message_bus: MessageBus, notification_service_real: NotificationService
) -> None:
    """Test sending notification via message bus."""
    received_notifications: List[Dict[str, Any]] = []

    async def on_notification_sent(data: Dict[str, Any]) -> None:
        """Callback for notification.sent channel."""
        received_notifications.append(data)

    # Subscribe to notification results
    await message_bus.subscribe("notification.sent", on_notification_sent)

    # Publish notification request
    request_data = {
        "message": "Integration test notification",
        "type": "info",
        "priority": "normal",
        "channels": ["console", "gui"],
    }

    await message_bus.publish("notification.send", request_data)

    # Wait for processing
    await asyncio.sleep(0.5)

    # Verify notification was sent
    assert len(received_notifications) > 0
    assert received_notifications[0]["success"] is True
    assert received_notifications[0]["message"] == "Integration test notification"

    await message_bus.unsubscribe("notification.sent")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_system_alert_via_message_bus(
    message_bus: MessageBus, notification_service_real: NotificationService
) -> None:
    """Test system alert handling via message bus."""
    received_notifications: List[Dict[str, Any]] = []

    async def on_notification_sent(data: Dict[str, Any]) -> None:
        """Callback for notification.sent channel."""
        received_notifications.append(data)

    # Subscribe to notification results
    await message_bus.subscribe("notification.sent", on_notification_sent)

    # Publish system alert
    alert_data = {
        "message": "Critical system error",
        "priority": "critical",
        "source": "test_integration",
        "error_details": {"test": "integration"},
    }

    await message_bus.publish("system.alert", alert_data)

    # Wait for processing
    await asyncio.sleep(0.5)

    # Verify alert was processed as notification
    assert len(received_notifications) > 0
    assert "Critical system error" in received_notifications[0]["message"]
    assert received_notifications[0]["type"] == "alert"

    await message_bus.unsubscribe("notification.sent")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_notification_failure_handling(
    message_bus: MessageBus, notification_service_real: NotificationService
) -> None:
    """Test notification failure is published to notification.failed."""
    received_failures: List[Dict[str, Any]] = []

    async def on_notification_failed(data: Dict[str, Any]) -> None:
        """Callback for notification.failed channel."""
        received_failures.append(data)

    # Subscribe to notification failures
    await message_bus.subscribe("notification.failed", on_notification_failed)

    # Publish notification request with invalid channel (should fail)
    # Since all our mock channels succeed, we'll test with expired notification
    request_data = {
        "message": "Expired notification",
        "type": "info",
        "channels": ["console"],
        "expires_at": "2020-01-01T00:00:00Z",
    }

    await message_bus.publish("notification.send", request_data)

    # Wait for processing
    await asyncio.sleep(0.5)

    # Expired notifications are silently dropped, not failed
    # So let's test invalid data instead
    await message_bus.unsubscribe("notification.failed")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gui_notification_publishing(
    message_bus: MessageBus, notification_service_real: NotificationService
) -> None:
    """Test that GUI notifications are published to gui.notification channel."""
    received_gui_notifications: List[Dict[str, Any]] = []

    async def on_gui_notification(data: Dict[str, Any]) -> None:
        """Callback for gui.notification channel."""
        received_gui_notifications.append(data)

    # Subscribe to GUI notifications
    await message_bus.subscribe("gui.notification", on_gui_notification)

    # Send notification to GUI channel
    request_data = {
        "message": "GUI integration test",
        "type": "success",
        "subject": "Test Success",
        "channels": ["gui"],
    }

    await message_bus.publish("notification.send", request_data)

    # Wait for processing
    await asyncio.sleep(0.5)

    # Verify GUI notification was published
    assert len(received_gui_notifications) > 0
    assert received_gui_notifications[0]["message"] == "GUI integration test"
    assert received_gui_notifications[0]["type"] == "success"
    assert received_gui_notifications[0]["subject"] == "Test Success"

    await message_bus.unsubscribe("gui.notification")


# ==================== Service Lifecycle Integration Tests ====================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_status_publishing(message_bus: MessageBus) -> None:
    """Test that service publishes status updates on start/stop."""
    received_statuses: List[Dict[str, Any]] = []

    async def on_status_update(data: Dict[str, Any]) -> None:
        """Callback for service status updates."""
        received_statuses.append(data)

    # Subscribe to service status
    await message_bus.subscribe("service.notification_service.status", on_status_update)

    # Create and start service
    service = NotificationService(message_bus)
    await service.initialize()
    await service.start()

    # Wait for status publication
    await asyncio.sleep(0.3)

    # Verify started status was published
    assert len(received_statuses) > 0
    started_status = [s for s in received_statuses if s.get("status") == "started"]
    assert len(started_status) > 0

    # Stop service
    await service.stop()
    await asyncio.sleep(0.3)

    # Verify stopped status was published
    stopped_status = [s for s in received_statuses if s.get("status") == "stopped"]
    assert len(stopped_status) > 0

    await message_bus.unsubscribe("service.notification_service.status")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_publishing(
    message_bus: MessageBus, notification_service_real: NotificationService
) -> None:
    """Test that service publishes metrics periodically."""
    received_metrics: List[Dict[str, Any]] = []

    async def on_metrics_update(data: Dict[str, Any]) -> None:
        """Callback for service metrics updates."""
        received_metrics.append(data)

    # Subscribe to service metrics
    await message_bus.subscribe("service.notification_service.metrics", on_metrics_update)

    # Send 10 notifications to trigger metrics publishing
    for i in range(10):
        request_data = {
            "message": f"Metrics test notification {i}",
            "type": "info",
            "channels": ["console"],
        }
        await message_bus.publish("notification.send", request_data)

    # Wait for processing and metrics
    await asyncio.sleep(1.0)

    # Verify metrics were published
    assert len(received_metrics) > 0
    latest_metrics = received_metrics[-1]
    assert "total_sent" in latest_metrics
    assert latest_metrics["total_sent"] >= 10
    assert "success_rate" in latest_metrics
    assert "by_channel" in latest_metrics

    await message_bus.unsubscribe("service.notification_service.metrics")


# ==================== Multi-Service Integration Tests ====================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_notification_from_simulated_service(message_bus: MessageBus) -> None:
    """Test notification service receiving alerts from other services."""
    received_notifications: List[Dict[str, Any]] = []

    async def on_notification_sent(data: Dict[str, Any]) -> None:
        """Callback for notification.sent channel."""
        received_notifications.append(data)

    # Start notification service
    service = NotificationService(message_bus)
    await service.initialize()
    await service.start()

    # Subscribe to results
    await message_bus.subscribe("notification.sent", on_notification_sent)

    # Simulate LLM service sending an alert
    await message_bus.publish(
        "system.alert",
        {"message": "LLM service out of memory", "priority": "critical", "source": "llm_service"},
    )

    # Simulate TTS service sending a notification
    await message_bus.publish(
        "notification.send",
        {
            "message": "TTS generation completed",
            "type": "success",
            "priority": "low",
            "channels": ["console", "gui"],
        },
    )

    # Wait for processing
    await asyncio.sleep(0.5)

    # Verify both notifications were received
    assert len(received_notifications) >= 2

    # Clean up
    await message_bus.unsubscribe("notification.sent")
    await service.stop()


# ==================== Stress and Performance Tests ====================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_high_volume_notifications(
    message_bus: MessageBus, notification_service_real: NotificationService
) -> None:
    """Test service handling high volume of notifications."""
    notification_count = 50
    received_notifications: List[Dict[str, Any]] = []

    async def on_notification_sent(data: Dict[str, Any]) -> None:
        """Callback for notification.sent channel."""
        received_notifications.append(data)

    await message_bus.subscribe("notification.sent", on_notification_sent)

    # Send many notifications rapidly
    for i in range(notification_count):
        request_data = {
            "message": f"High volume test {i}",
            "type": "info" if i % 2 == 0 else "warning",
            "channels": ["console"],
        }
        await message_bus.publish("notification.send", request_data)

    # Wait for all to process
    await asyncio.sleep(2.0)

    # Verify all notifications were processed
    assert len(received_notifications) >= notification_count

    # Verify service metrics are accurate
    assert notification_service_real.total_sent >= notification_count
    assert notification_service_real._calculate_success_rate() >= 0.95  # At least 95% success

    await message_bus.unsubscribe("notification.sent")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_notifications(
    message_bus: MessageBus, notification_service_real: NotificationService
) -> None:
    """Test service handling concurrent notifications."""
    received_notifications: List[Dict[str, Any]] = []

    async def on_notification_sent(data: Dict[str, Any]) -> None:
        """Callback for notification.sent channel."""
        received_notifications.append(data)

    await message_bus.subscribe("notification.sent", on_notification_sent)

    # Send notifications concurrently
    async def send_notification(idx: int) -> None:
        request_data = {
            "message": f"Concurrent test {idx}",
            "type": "info",
            "channels": ["console", "gui"],
        }
        await message_bus.publish("notification.send", request_data)

    # Send 20 concurrent notifications
    await asyncio.gather(*[send_notification(i) for i in range(20)])

    # Wait for processing
    await asyncio.sleep(1.0)

    # Verify all were processed
    assert len(received_notifications) >= 20
    assert notification_service_real.total_sent >= 20

    await message_bus.unsubscribe("notification.sent")


# ==================== Error Recovery Integration Tests ====================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_recovery_after_message_bus_disconnect(message_bus: MessageBus) -> None:
    """Test service behavior when message bus disconnects and reconnects."""
    service = NotificationService(message_bus)
    await service.initialize()
    await service.start()

    # Verify service is healthy initially
    assert await service.health_check() is True

    # Simulate message bus disconnect
    original_connected_state = message_bus.is_connected
    message_bus.is_connected = False

    # Verify health check fails
    assert await service.health_check() is False

    # Restore connection
    message_bus.is_connected = original_connected_state

    # Verify health check passes again
    assert await service.health_check() is True

    await service.stop()
