"""
Notification Service Message Models

Pydantic models for notification service message bus communication.

Author: Freya AI
Version: 0.1.0
Date: 2025-12-06
"""

from typing import Optional, Dict, Any, Literal, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(str, Enum):
    """Notification types."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ALERT = "alert"


class NotificationChannel(str, Enum):
    """Available notification channels."""

    CONSOLE = "console"
    EMAIL = "email"
    WEBHOOK = "webhook"
    PUSH = "push"
    SMS = "sms"
    GUI = "gui"


class NotificationRequest(BaseModel):
    """
    Message model for notification send requests.

    Published to: notification.send
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Notification message content",
        examples=["User login detected from new location"]
    )

    type: NotificationType = Field(
        default=NotificationType.INFO,
        description="Type of notification"
    )

    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL,
        description="Notification priority level"
    )

    channels: List[NotificationChannel] = Field(
        default=[NotificationChannel.CONSOLE],
        description="Channels to send notification through"
    )

    recipient: Optional[str] = Field(
        default=None,
        description="Specific recipient identifier (email, user ID, etc.)",
        examples=["user@example.com", "user_123"]
    )

    subject: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Notification subject/title (for email, push)",
        examples=["Security Alert", "System Update"]
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the notification"
    )

    expires_at: Optional[str] = Field(
        default=None,
        description="ISO format timestamp when notification expires",
        examples=["2025-12-06T12:00:00Z"]
    )

    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO format timestamp when notification was created"
    )

    @field_validator("timestamp", "expires_at")
    @classmethod
    def validate_timestamp(cls, v: Optional[str]) -> Optional[str]:
        """Validate timestamp is valid ISO format."""
        if v is None:
            return v
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid ISO timestamp format: {v}") from e


class SystemAlert(BaseModel):
    """
    Message model for system alerts.

    Published to: system.alert
    """

    message: str = Field(
        ...,
        min_length=1,
        description="Alert message content"
    )

    priority: NotificationPriority = Field(
        default=NotificationPriority.HIGH,
        description="Alert priority level"
    )

    source: str = Field(
        ...,
        description="Service or component that generated the alert",
        examples=["llm_service", "memory_manager", "audio_service"]
    )

    error_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error or context details"
    )

    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO format timestamp"
    )


class NotificationResult(BaseModel):
    """
    Message model for notification results.

    Published to: notification.sent or notification.failed
    """

    success: bool = Field(
        ...,
        description="Whether notification was sent successfully"
    )

    message: str = Field(
        ...,
        description="Original notification message"
    )

    type: NotificationType = Field(
        ...,
        description="Notification type"
    )

    channels: List[NotificationChannel] = Field(
        ...,
        description="Channels used for notification"
    )

    channel_results: Dict[str, bool] = Field(
        default_factory=dict,
        description="Per-channel success status",
        examples=[{"console": True, "email": False}]
    )

    error: Optional[str] = Field(
        default=None,
        description="Error message if notification failed"
    )

    duration_ms: Optional[float] = Field(
        default=None,
        ge=0,
        description="Time taken to send notification in milliseconds"
    )

    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO format timestamp"
    )


class NotificationMetrics(BaseModel):
    """
    Message model for notification service metrics.

    Published to: service.notification_service.metrics
    """

    total_sent: int = Field(
        default=0,
        ge=0,
        description="Total notifications sent successfully"
    )

    total_failed: int = Field(
        default=0,
        ge=0,
        description="Total notifications that failed"
    )

    success_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Success rate (0.0 to 1.0)"
    )

    avg_duration_ms: Optional[float] = Field(
        default=None,
        ge=0,
        description="Average notification send duration in milliseconds"
    )

    by_channel: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of notifications per channel",
        examples=[{"console": 100, "email": 50, "webhook": 25}]
    )

    by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of notifications per type",
        examples=[{"info": 75, "warning": 20, "error": 5}]
    )

    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO format timestamp"
    )
