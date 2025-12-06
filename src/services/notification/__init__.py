"""
Notification Service Package

Provides multi-channel notification capabilities for the Freya AI system.

Author: Freya AI
Version: 0.1.0
Date: 2025-12-06
"""

from src.services.notification.notification_service import (
    NotificationService,
    NotificationServiceError,
)
from src.services.notification.models import (
    NotificationRequest,
    NotificationResult,
    SystemAlert,
    NotificationMetrics,
    NotificationChannel,
    NotificationType,
    NotificationPriority,
)

__all__ = [
    "NotificationService",
    "NotificationServiceError",
    "NotificationRequest",
    "NotificationResult",
    "SystemAlert",
    "NotificationMetrics",
    "NotificationChannel",
    "NotificationType",
    "NotificationPriority",
]
