"""
Notification Service - Send notifications through multiple channels

This service manages sending notifications to users through various channels
including console, email, webhooks, push notifications, and GUI.

Author: Freya AI
Version: 0.1.0
Date: 2025-12-06
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger
import asyncio
import time

from src.core.base_service import BaseService, ServiceError
from src.core.message_bus import MessageBus
from src.core.config import config
from src.services.notification.models import (
    NotificationRequest,
    NotificationResult,
    SystemAlert,
    NotificationMetrics,
    NotificationChannel,
    NotificationType,
    NotificationPriority,
)


class NotificationServiceError(ServiceError):
    """Exception raised for Notification Service specific errors."""

    pass


class NotificationService(BaseService):
    """
    Notification Service for sending alerts and notifications through multiple channels.

    Subscribes to:
        - notification.send: Notification send requests
        - system.alert: System-wide alerts requiring immediate notification

    Publishes to:
        - notification.sent: Successfully sent notifications
        - notification.failed: Failed notification attempts
        - notification.delivered: Delivery confirmations (for channels that support it)
        - service.notification_service.status: Service status updates
        - service.notification_service.metrics: Performance metrics

    Message Bus Channels:
        Input:
            - notification.send (NotificationRequest)
            - system.alert (SystemAlert)

        Output:
            - notification.sent (NotificationResult)
            - notification.failed (NotificationResult)
            - gui.notification (for GUI channel)

    Attributes:
        total_sent: Total count of successfully sent notifications
        total_failed: Total count of failed notifications
        channel_counts: Count of notifications per channel
        type_counts: Count of notifications per type
        total_duration: Cumulative duration of all notification sends
    """

    def __init__(self, message_bus: MessageBus) -> None:
        """
        Initialize the Notification Service.

        Args:
            message_bus: Shared MessageBus instance for pub/sub communication
        """
        super().__init__("notification_service", message_bus)

        # Metrics tracking
        self.total_sent: int = 0
        self.total_failed: int = 0
        self.channel_counts: Dict[str, int] = {}
        self.type_counts: Dict[str, int] = {}
        self.total_duration: float = 0.0

        # Channel backends (initialized in initialize())
        self._email_backend: Optional[Any] = None
        self._webhook_backend: Optional[Any] = None
        self._push_backend: Optional[Any] = None
        self._sms_backend: Optional[Any] = None

        logger.debug(f"[{self.name}] 📨 Notification Service instance created")

    async def initialize(self) -> None:
        """
        Initialize the Notification Service and its backends.

        Raises:
            NotificationServiceError: If initialization fails
        """
        try:
            logger.info(f"[{self.name}] Initializing Notification Service...")

            # Initialize notification channel backends
            await self._initialize_backends()

            # Initialize metrics
            for channel in NotificationChannel:
                self.channel_counts[channel.value] = 0

            for ntype in NotificationType:
                self.type_counts[ntype.value] = 0

            self._healthy = True
            logger.success(f"[{self.name}] ✅ Notification Service initialized successfully")

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Initialization failed: {e}")
            self._healthy = False
            self.increment_error_count()
            raise NotificationServiceError(f"Initialization failed: {e}") from e

    async def start(self) -> None:
        """
        Start the Notification Service and subscribe to message bus channels.

        Raises:
            NotificationServiceError: If service fails to start
        """
        try:
            logger.info(f"[{self.name}] Starting Notification Service...")

            # Subscribe to notification channels
            await self.message_bus.subscribe(
                "notification.send", self._handle_notification_request
            )

            await self.message_bus.subscribe("system.alert", self._handle_system_alert)

            self._mark_started()
            await self.publish_status("started", {"channels_available": list(self.channel_counts.keys())})

            logger.success(f"[{self.name}] ✅ Notification Service started and listening")

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Failed to start service: {e}")
            self.increment_error_count()
            raise NotificationServiceError(f"Service start failed: {e}") from e

    async def stop(self) -> None:
        """
        Stop the Notification Service gracefully and cleanup resources.

        Raises:
            NotificationServiceError: If shutdown encounters errors
        """
        try:
            logger.info(f"[{self.name}] Stopping Notification Service...")

            # Unsubscribe from message bus channels
            await self.message_bus.unsubscribe("notification.send")
            await self.message_bus.unsubscribe("system.alert")

            # Cleanup backends
            await self._cleanup_backends()

            self._mark_stopped()
            await self.publish_status(
                "stopped",
                {
                    "total_sent": self.total_sent,
                    "total_failed": self.total_failed,
                    "success_rate": self._calculate_success_rate(),
                },
            )

            logger.success(
                f"[{self.name}] ✅ Notification Service stopped "
                f"(sent: {self.total_sent}, failed: {self.total_failed})"
            )

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Error during shutdown: {e}")
            self.increment_error_count()
            raise NotificationServiceError(f"Service stop failed: {e}") from e

    async def health_check(self) -> bool:
        """
        Check if the Notification Service is healthy.

        Performs checks on:
            - Base service health
            - Message bus connectivity
            - Backend availability

        Returns:
            True if service is operational, False otherwise
        """
        if not await super().health_check():
            return False

        # Check message bus connection
        if not self.message_bus or not self.message_bus.is_connected:
            logger.warning(f"[{self.name}] ⚠️ Message bus not connected")
            return False

        # All health checks passed
        return True

    # Message Bus Handlers

    async def _handle_notification_request(self, data: Dict[str, Any]) -> None:
        """
        Handle incoming notification send requests.

        Args:
            data: Dictionary containing notification request data

        Message Format (NotificationRequest):
            {
                "message": str,
                "type": NotificationType,
                "priority": NotificationPriority,
                "channels": List[NotificationChannel],
                "recipient": Optional[str],
                "subject": Optional[str],
                "metadata": Dict[str, Any],
                "expires_at": Optional[str],
                "timestamp": str
            }
        """
        try:
            # Validate and parse request
            try:
                request = NotificationRequest(**data)
            except Exception as e:
                logger.error(f"[{self.name}] ❌ Invalid notification request: {e}")
                return

            # Check if notification has expired
            if request.expires_at:
                try:
                    expires = datetime.fromisoformat(request.expires_at.replace("Z", "+00:00"))
                    if datetime.now(expires.tzinfo) > expires:
                        logger.warning(
                            f"[{self.name}] ⚠️ Notification expired, skipping: {request.message[:50]}"
                        )
                        return
                except ValueError:
                    logger.warning(f"[{self.name}] Invalid expiration timestamp, proceeding anyway")

            logger.info(
                f"[{self.name}] 📨 Sending {request.type.value} notification "
                f"via {[ch.value for ch in request.channels]}: {request.message[:50]}..."
            )

            # Send notification
            start_time = time.time()
            success, channel_results, error = await self._send_notification(request)
            duration_ms = (time.time() - start_time) * 1000

            # Build result
            result = NotificationResult(
                success=success,
                message=request.message,
                type=request.type,
                channels=request.channels,
                channel_results=channel_results,
                error=error,
                duration_ms=duration_ms,
            )

            # Update metrics and publish results
            if success:
                self.total_sent += 1
                self.total_duration += duration_ms
                self.type_counts[request.type.value] = self.type_counts.get(request.type.value, 0) + 1

                await self.message_bus.publish("notification.sent", result.model_dump())
                logger.success(
                    f"[{self.name}] ✅ Notification sent successfully in {duration_ms:.2f}ms"
                )
            else:
                self.total_failed += 1
                await self.message_bus.publish("notification.failed", result.model_dump())
                logger.error(f"[{self.name}] ❌ Notification failed: {error}")

            # Publish metrics periodically (every 10 notifications)
            if (self.total_sent + self.total_failed) % 10 == 0:
                await self._publish_metrics()

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Error handling notification request: {e}")
            self.increment_error_count()

    async def _handle_system_alert(self, data: Dict[str, Any]) -> None:
        """
        Handle system-wide alerts requiring immediate notification.

        Args:
            data: Dictionary containing system alert data

        Message Format (SystemAlert):
            {
                "message": str,
                "priority": NotificationPriority,
                "source": str,
                "error_details": Optional[Dict[str, Any]],
                "timestamp": str
            }
        """
        try:
            # Validate and parse alert
            try:
                alert = SystemAlert(**data)
            except Exception as e:
                logger.error(f"[{self.name}] ❌ Invalid system alert: {e}")
                return

            logger.warning(
                f"[{self.name}] ⚠️ System alert from {alert.source} "
                f"({alert.priority.value}): {alert.message}"
            )

            # Convert to notification request with high priority
            notification = NotificationRequest(
                message=f"[{alert.source.upper()}] {alert.message}",
                type=NotificationType.ALERT,
                priority=alert.priority,
                channels=[NotificationChannel.CONSOLE, NotificationChannel.GUI],
                subject=f"System Alert: {alert.source}",
                metadata={"source": alert.source, "error_details": alert.error_details or {}},
            )

            # Send through notification handler
            await self._handle_notification_request(notification.model_dump())

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Error handling system alert: {e}")
            self.increment_error_count()

    # Notification Sending Logic

    async def _send_notification(
        self, request: NotificationRequest
    ) -> tuple[bool, Dict[str, bool], Optional[str]]:
        """
        Send notification through all requested channels.

        Args:
            request: Validated notification request

        Returns:
            Tuple of (overall_success, channel_results, error_message)
        """
        channel_results: Dict[str, bool] = {}
        errors: List[str] = []

        # Send to each requested channel
        for channel in request.channels:
            try:
                success = await self._send_to_channel(channel, request)
                channel_results[channel.value] = success

                if success:
                    self.channel_counts[channel.value] = self.channel_counts.get(channel.value, 0) + 1
                else:
                    errors.append(f"{channel.value} failed")

            except Exception as e:
                logger.error(f"[{self.name}] Error sending to {channel.value}: {e}")
                channel_results[channel.value] = False
                errors.append(f"{channel.value}: {str(e)}")
                self.increment_error_count()

        # Overall success if at least one channel succeeded
        overall_success = any(channel_results.values())
        error_message = "; ".join(errors) if errors else None

        return overall_success, channel_results, error_message

    async def _send_to_channel(
        self, channel: NotificationChannel, request: NotificationRequest
    ) -> bool:
        """
        Send notification to a specific channel.

        Args:
            channel: Target notification channel
            request: Notification request

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if channel == NotificationChannel.CONSOLE:
                return await self._send_console(request)
            elif channel == NotificationChannel.EMAIL:
                return await self._send_email(request)
            elif channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook(request)
            elif channel == NotificationChannel.PUSH:
                return await self._send_push(request)
            elif channel == NotificationChannel.SMS:
                return await self._send_sms(request)
            elif channel == NotificationChannel.GUI:
                return await self._send_gui(request)
            else:
                logger.warning(f"[{self.name}] Unknown channel: {channel}")
                return False

        except Exception as e:
            logger.error(f"[{self.name}] Error in {channel.value} channel: {e}")
            return False

    # Channel Implementations

    async def _send_console(self, request: NotificationRequest) -> bool:
        """
        Send notification to console (logger).

        Args:
            request: Notification request

        Returns:
            True (console notifications always succeed)
        """
        icon_map = {
            NotificationType.INFO: "ℹ️",
            NotificationType.SUCCESS: "✅",
            NotificationType.WARNING: "⚠️",
            NotificationType.ERROR: "❌",
            NotificationType.ALERT: "🚨",
        }

        icon = icon_map.get(request.type, "📨")
        log_message = f"[{self.name}] {icon} {request.message}"

        # Log at appropriate level
        if request.type == NotificationType.ERROR or request.type == NotificationType.ALERT:
            logger.error(log_message)
        elif request.type == NotificationType.WARNING:
            logger.warning(log_message)
        elif request.type == NotificationType.SUCCESS:
            logger.success(log_message)
        else:
            logger.info(log_message)

        return True

    async def _send_email(self, request: NotificationRequest) -> bool:
        """
        Send notification via email.

        Args:
            request: Notification request

        Returns:
            True if email sent successfully
        """
        if not config.notification_email_enabled:
            logger.debug(f"[{self.name}] Email notifications disabled in config")
            return False

        # TODO: Implement email backend
        # Example: await self._email_backend.send(recipient, subject, body)
        logger.info(f"[{self.name}] 📧 [MOCK] Email sent to {request.recipient or 'default'}")
        await asyncio.sleep(0.1)  # Simulate network delay

        return True

    async def _send_webhook(self, request: NotificationRequest) -> bool:
        """
        Send notification via webhook.

        Args:
            request: Notification request

        Returns:
            True if webhook called successfully
        """
        if not config.notification_webhook_enabled:
            logger.debug(f"[{self.name}] Webhook notifications disabled in config")
            return False

        # TODO: Implement webhook backend
        # Example: await self._webhook_backend.post(url, payload)
        logger.info(f"[{self.name}] 🔗 [MOCK] Webhook called")
        await asyncio.sleep(0.05)  # Simulate network delay

        return True

    async def _send_push(self, request: NotificationRequest) -> bool:
        """
        Send push notification.

        Args:
            request: Notification request

        Returns:
            True if push notification sent successfully
        """
        if not config.notification_push_enabled:
            logger.debug(f"[{self.name}] Push notifications disabled in config")
            return False

        # TODO: Implement push notification backend (FCM, APNS, etc.)
        logger.info(f"[{self.name}] 📱 [MOCK] Push notification sent")
        await asyncio.sleep(0.1)  # Simulate network delay

        return True

    async def _send_sms(self, request: NotificationRequest) -> bool:
        """
        Send SMS notification.

        Args:
            request: Notification request

        Returns:
            True if SMS sent successfully
        """
        if not config.notification_sms_enabled:
            logger.debug(f"[{self.name}] SMS notifications disabled in config")
            return False

        # TODO: Implement SMS backend (Twilio, etc.)
        logger.info(f"[{self.name}] 💬 [MOCK] SMS sent to {request.recipient or 'default'}")
        await asyncio.sleep(0.1)  # Simulate network delay

        return True

    async def _send_gui(self, request: NotificationRequest) -> bool:
        """
        Send notification to GUI service via message bus.

        Args:
            request: Notification request

        Returns:
            True if published to message bus successfully
        """
        try:
            await self.message_bus.publish(
                "gui.notification",
                {
                    "type": request.type.value,
                    "message": request.message,
                    "subject": request.subject,
                    "priority": request.priority.value,
                    "timestamp": datetime.now().isoformat(),
                },
            )
            logger.debug(f"[{self.name}] 🖥️ GUI notification published")
            return True

        except Exception as e:
            logger.error(f"[{self.name}] Failed to publish GUI notification: {e}")
            return False

    # Backend Management

    async def _initialize_backends(self) -> None:
        """
        Initialize notification channel backends.

        Raises:
            Exception: If backend initialization fails
        """
        logger.debug(f"[{self.name}] Initializing notification backends...")

        # TODO: Initialize actual backends based on config
        # Example:
        # if config.notification_email_enabled:
        #     self._email_backend = EmailBackend(config.email_smtp_host, ...)

        logger.debug(f"[{self.name}] Backends initialized (using mock implementations)")

    async def _cleanup_backends(self) -> None:
        """Cleanup and close notification backends."""
        logger.debug(f"[{self.name}] Cleaning up notification backends...")

        # TODO: Cleanup actual backends
        # Example:
        # if self._email_backend:
        #     await self._email_backend.close()

        logger.debug(f"[{self.name}] Backends cleaned up")

    # Metrics

    async def _publish_metrics(self) -> None:
        """Publish current service metrics to message bus."""
        try:
            metrics = NotificationMetrics(
                total_sent=self.total_sent,
                total_failed=self.total_failed,
                success_rate=self._calculate_success_rate(),
                avg_duration_ms=self._calculate_avg_duration(),
                by_channel=self.channel_counts,
                by_type=self.type_counts,
            )

            await self.publish_metrics(metrics.model_dump())

        except Exception as e:
            logger.error(f"[{self.name}] Error publishing metrics: {e}")

    def _calculate_success_rate(self) -> float:
        """
        Calculate notification success rate.

        Returns:
            Success rate between 0.0 and 1.0
        """
        total = self.total_sent + self.total_failed
        if total == 0:
            return 1.0
        return self.total_sent / total

    def _calculate_avg_duration(self) -> Optional[float]:
        """
        Calculate average notification send duration.

        Returns:
            Average duration in milliseconds, or None if no notifications sent
        """
        if self.total_sent == 0:
            return None
        return self.total_duration / self.total_sent
