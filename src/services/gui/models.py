"""
Pydantic models for GUI Service API responses.

This module defines the data models used by the GUI Service for
API responses and WebSocket messages.

Author: Claude (AI Assistant)
Version: 0.1.0
Date: 2025-12-03
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    """Model for individual service status."""

    name: str
    status: str  # "starting", "started", "stopped", "error"
    healthy: bool
    uptime: float
    error_count: int
    last_updated: str


class SystemStatus(BaseModel):
    """Model for overall system status."""

    services: List[ServiceStatus]
    total_services: int
    healthy_services: int
    timestamp: str


class ChatMessage(BaseModel):
    """Model for chat conversation messages."""

    id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    location: Optional[str] = None  # e.g., "bedroom", "front_door"


class ToolCall(BaseModel):
    """Model for tool execution log entries."""

    id: str
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    success: bool
    duration: Optional[float] = None
    timestamp: str
    error: Optional[str] = None


class WebSocketMessage(BaseModel):
    """Model for WebSocket messages sent to frontend."""

    type: str  # "service_status", "chat_message", "tool_call", "system_event"
    data: Dict[str, Any]
    timestamp: str


class ConfigParameter(BaseModel):
    """Model for configuration parameter."""

    key: str
    value: Any
    description: Optional[str] = None
    type: str  # "string", "integer", "boolean", etc.


class APIResponse(BaseModel):
    """Generic API response wrapper."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str
