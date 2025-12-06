"""
Message schemas for inter-service communication in Freya v2.

This module defines Pydantic models for all messages exchanged between services
via the Redis message bus. All messages follow the pattern: {source}.{data_type}

Schema versioning: v1.0.0
Author: Claude (AI Assistant)
Date: 2025-12-05
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class MessageVersion(str, Enum):
    """Message schema version."""
    V1 = "1.0.0"


class BaseMessage(BaseModel):
    """Base class for all inter-service messages."""
    
    version: str = Field(default=MessageVersion.V1, description="Message schema version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message creation timestamp")
    message_id: Optional[str] = Field(None, description="Unique message identifier for tracing")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# AUDIO MESSAGES
# ============================================================================

class AudioFormat(str, Enum):
    """Supported audio formats."""
    PCM_16 = "pcm_16"
    PCM_24 = "pcm_24"
    WAV = "wav"
    MP3 = "mp3"


class AudioInputMessage(BaseMessage):
    """
    Message for raw audio input from microphone.
    Channel: audio.input.stream
    Publisher: AudioManager
    Subscribers: STTService
    """
    
    audio_data: bytes = Field(..., description="Raw audio bytes")
    sample_rate: int = Field(..., ge=8000, le=48000, description="Audio sample rate in Hz")
    channels: int = Field(..., ge=1, le=2, description="Number of audio channels")
    format: AudioFormat = Field(default=AudioFormat.PCM_16, description="Audio format")
    chunk_size: int = Field(..., gt=0, description="Size of audio chunk in bytes")
    location: str = Field(..., description="Physical location of audio source")
    device_id: Optional[str] = Field(None, description="Audio input device identifier")
    
    @validator('sample_rate')
    def validate_sample_rate(cls, v):
        valid_rates = [8000, 16000, 22050, 44100, 48000]
        if v not in valid_rates:
            raise ValueError(f'Sample rate must be one of {valid_rates}')
        return v


class AudioOutputMessage(BaseMessage):
    """
    Message for audio output to speakers.
    Channel: audio.output.stream
    Publisher: TTSService
    Subscribers: AudioManager
    """
    
    audio_data: bytes = Field(..., description="Audio bytes to play")
    sample_rate: int = Field(..., ge=8000, le=48000, description="Audio sample rate in Hz")
    channels: int = Field(..., ge=1, le=2, description="Number of audio channels")
    format: AudioFormat = Field(default=AudioFormat.PCM_16, description="Audio format")
    location: str = Field(..., description="Target location for audio output")
    device_id: Optional[str] = Field(None, description="Audio output device identifier")
    priority: int = Field(default=0, ge=0, le=10, description="Playback priority (0=normal, 10=urgent)")


class AudioDeviceInfo(BaseModel):
    """Information about an audio device."""
    
    device_id: str
    name: str
    type: str  # "input" or "output"
    channels: int
    sample_rate: int
    is_default: bool


class AudioDeviceListMessage(BaseMessage):
    """
    Message containing list of available audio devices.
    Channel: audio.device.list
    Publisher: AudioManager
    Subscribers: GUIService
    """
    
    devices: List[AudioDeviceInfo] = Field(..., description="List of available audio devices")
    location: str = Field(..., description="Location of devices")


class AudioControlMessage(BaseMessage):
    """
    Message for controlling audio playback.
    Channel: audio.control.*
    Publisher: GUIService, LLMEngine
    Subscribers: AudioManager
    """
    
    action: str = Field(..., description="Control action: start, stop, pause, resume, volume")
    location: str = Field(..., description="Target location")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action-specific parameters")


# ============================================================================
# SPEECH-TO-TEXT MESSAGES
# ============================================================================

class TranscriptionMessage(BaseMessage):
    """
    Message containing transcribed text from audio.
    Channel: stt.transcription
    Publisher: STTService
    Subscribers: LLMEngine
    """
    
    text: str = Field(..., min_length=1, description="Transcribed text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence score")
    language: str = Field(default="en", description="Detected language code (ISO 639-1)")
    location: str = Field(..., description="Location where audio was captured")
    audio_duration: float = Field(..., gt=0, description="Duration of audio in seconds")
    is_final: bool = Field(default=True, description="Whether this is final or interim transcription")


class STTErrorMessage(BaseMessage):
    """
    Message for STT service errors.
    Channel: stt.error
    Publisher: STTService
    Subscribers: GUIService, LLMEngine
    """
    
    error_type: str = Field(..., description="Error type: timeout, api_error, invalid_audio")
    error_message: str = Field(..., description="Human-readable error message")
    location: str = Field(..., description="Location where error occurred")
    recoverable: bool = Field(..., description="Whether the error is recoverable")


# ============================================================================
# LLM MESSAGES
# ============================================================================

class LLMRequestMessage(BaseMessage):
    """
    Message requesting LLM response.
    Channel: llm.request
    Publisher: STTService, GUIService
    Subscribers: LLMEngine
    """
    
    text: str = Field(..., min_length=1, description="Input text for LLM")
    location: str = Field(..., description="Location context for response")
    user_id: Optional[str] = Field(None, description="User identifier for personalization")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context data")
    conversation_id: Optional[str] = Field(None, description="Conversation thread identifier")
    system_prompt_override: Optional[str] = Field(None, description="Override default system prompt")


class LLMResponseMessage(BaseMessage):
    """
    Message containing LLM response.
    Channel: llm.response (streaming) or llm.final_response (complete)
    Publisher: LLMEngine
    Subscribers: TTSService, GUIService
    """
    
    text: str = Field(..., description="LLM generated text")
    location: str = Field(..., description="Location context")
    tokens_used: int = Field(..., ge=0, description="Number of tokens consumed")
    model: str = Field(..., description="Model used for generation")
    is_final: bool = Field(default=True, description="Whether this is final or streaming chunk")
    conversation_id: Optional[str] = Field(None, description="Conversation thread identifier")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tools called during generation")


class LLMErrorMessage(BaseMessage):
    """
    Message for LLM service errors.
    Channel: llm.error
    Publisher: LLMEngine
    Subscribers: GUIService
    """
    
    error_type: str = Field(..., description="Error type: timeout, api_error, context_overflow")
    error_message: str = Field(..., description="Human-readable error message")
    location: str = Field(..., description="Location context")
    request_text: Optional[str] = Field(None, description="Original request text")


# ============================================================================
# TEXT-TO-SPEECH MESSAGES
# ============================================================================

class TTSRequestMessage(BaseMessage):
    """
    Message requesting TTS generation.
    Channel: tts.generate
    Publisher: LLMEngine, GUIService
    Subscribers: TTSService
    """
    
    text: str = Field(..., min_length=1, description="Text to convert to speech")
    location: str = Field(..., description="Target location for audio output")
    voice_id: Optional[str] = Field(None, description="Voice identifier for TTS")
    voice_settings: Optional[Dict[str, Any]] = Field(None, description="Voice customization settings")
    priority: int = Field(default=0, ge=0, le=10, description="Generation priority")


class TTSErrorMessage(BaseMessage):
    """
    Message for TTS service errors.
    Channel: tts.error
    Publisher: TTSService
    Subscribers: GUIService, LLMEngine
    """
    
    error_type: str = Field(..., description="Error type: timeout, api_error, invalid_text")
    error_message: str = Field(..., description="Human-readable error message")
    location: str = Field(..., description="Location context")
    text: Optional[str] = Field(None, description="Text that failed to convert")


# ============================================================================
# MEMORY MESSAGES
# ============================================================================

class MemoryStoreMessage(BaseMessage):
    """
    Message to store information in memory.
    Channel: memory.store
    Publisher: LLMEngine, GUIService
    Subscribers: MemoryManager
    """
    
    content: str = Field(..., description="Content to store")
    metadata: Dict[str, Any] = Field(..., description="Metadata for retrieval")
    location: Optional[str] = Field(None, description="Location context")
    user_id: Optional[str] = Field(None, description="User identifier")
    collection: str = Field(default="conversations", description="Memory collection name")


class MemoryQueryMessage(BaseMessage):
    """
    Message to query memory.
    Channel: memory.query
    Publisher: LLMEngine
    Subscribers: MemoryManager
    """
    
    query: str = Field(..., description="Query text")
    location: Optional[str] = Field(None, description="Location filter")
    user_id: Optional[str] = Field(None, description="User filter")
    collection: str = Field(default="conversations", description="Memory collection to query")
    limit: int = Field(default=5, ge=1, le=50, description="Maximum results to return")


class MemoryResultMessage(BaseMessage):
    """
    Message containing memory query results.
    Channel: memory.result
    Publisher: MemoryManager
    Subscribers: LLMEngine
    """
    
    results: List[Dict[str, Any]] = Field(..., description="Query results")
    query: str = Field(..., description="Original query")
    count: int = Field(..., ge=0, description="Number of results")


# ============================================================================
# MCP GATEWAY MESSAGES
# ============================================================================

class MCPToolCallMessage(BaseMessage):
    """
    Message to execute an MCP tool.
    Channel: mcp.tool.call
    Publisher: LLMEngine
    Subscribers: MCPGateway
    """
    
    tool_name: str = Field(..., description="Name of tool to execute")
    arguments: Dict[str, Any] = Field(..., description="Tool arguments")
    location: Optional[str] = Field(None, description="Location context")
    timeout: int = Field(default=30, ge=1, le=300, description="Execution timeout in seconds")


class MCPToolResultMessage(BaseMessage):
    """
    Message containing MCP tool execution result.
    Channel: mcp.tool.result
    Publisher: MCPGateway
    Subscribers: LLMEngine
    """
    
    tool_name: str = Field(..., description="Name of executed tool")
    result: Any = Field(..., description="Tool execution result")
    success: bool = Field(..., description="Whether execution succeeded")
    duration: float = Field(..., ge=0, description="Execution duration in seconds")
    error: Optional[str] = Field(None, description="Error message if failed")


class MCPToolListMessage(BaseMessage):
    """
    Message containing list of available MCP tools.
    Channel: mcp.tool.list
    Publisher: MCPGateway
    Subscribers: LLMEngine, GUIService
    """
    
    tools: List[Dict[str, Any]] = Field(..., description="List of available tools")
    server_count: int = Field(..., ge=0, description="Number of connected MCP servers")


# ============================================================================
# NOTIFICATION MESSAGES
# ============================================================================

class NotificationMessage(BaseMessage):
    """
    Message for system notifications.
    Channel: notification.send
    Publisher: Any service
    Subscribers: NotificationService, GUIService
    """
    
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    level: str = Field(..., description="Notification level: info, warning, error, critical")
    location: Optional[str] = Field(None, description="Target location")
    action_url: Optional[str] = Field(None, description="URL for notification action")
    
    @validator('level')
    def validate_level(cls, v):
        valid_levels = ['info', 'warning', 'error', 'critical']
        if v not in valid_levels:
            raise ValueError(f'Level must be one of {valid_levels}')
        return v


# ============================================================================
# SERVICE HEALTH MESSAGES
# ============================================================================

class ServiceHealthMessage(BaseMessage):
    """
    Message for service health status.
    Channel: service.health.{service_name}
    Publisher: All services
    Subscribers: GUIService, MonitoringService
    """
    
    service_name: str = Field(..., description="Name of the service")
    status: str = Field(..., description="Service status: starting, started, stopping, stopped, error")
    healthy: bool = Field(..., description="Whether service is healthy")
    uptime: float = Field(..., ge=0, description="Service uptime in seconds")
    error_count: int = Field(default=0, ge=0, description="Number of errors since start")
    last_error: Optional[str] = Field(None, description="Last error message")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Service-specific metrics")
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['starting', 'started', 'stopping', 'stopped', 'error']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}')
        return v


# ============================================================================
# VISION MESSAGES
# ============================================================================

class VisionAnalysisMessage(BaseMessage):
    """
    Message requesting vision analysis.
    Channel: vision.analyze
    Publisher: LLMEngine, GUIService
    Subscribers: VisionService
    """
    
    image_data: bytes = Field(..., description="Image data to analyze")
    image_format: str = Field(..., description="Image format: jpeg, png, webp")
    prompt: Optional[str] = Field(None, description="Analysis prompt/question")
    location: str = Field(..., description="Location where image was captured")


class VisionResultMessage(BaseMessage):
    """
    Message containing vision analysis result.
    Channel: vision.result
    Publisher: VisionService
    Subscribers: LLMEngine, GUIService
    """
    
    description: str = Field(..., description="Image description/analysis")
    objects: Optional[List[str]] = Field(None, description="Detected objects")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence")
    location: str = Field(..., description="Location context")


# ============================================================================
# MESSAGE REGISTRY
# ============================================================================

MESSAGE_REGISTRY = {
    # Audio
    "audio.input.stream": AudioInputMessage,
    "audio.output.stream": AudioOutputMessage,
    "audio.device.list": AudioDeviceListMessage,
    "audio.control.*": AudioControlMessage,
    
    # STT
    "stt.transcription": TranscriptionMessage,
    "stt.error": STTErrorMessage,
    
    # LLM
    "llm.request": LLMRequestMessage,
    "llm.response": LLMResponseMessage,
    "llm.final_response": LLMResponseMessage,
    "llm.error": LLMErrorMessage,
    
    # TTS
    "tts.generate": TTSRequestMessage,
    "tts.error": TTSErrorMessage,
    
    # Memory
    "memory.store": MemoryStoreMessage,
    "memory.query": MemoryQueryMessage,
    "memory.result": MemoryResultMessage,
    
    # MCP
    "mcp.tool.call": MCPToolCallMessage,
    "mcp.tool.result": MCPToolResultMessage,
    "mcp.tool.list": MCPToolListMessage,
    
    # Notifications
    "notification.send": NotificationMessage,
    
    # Service Health
    "service.health.*": ServiceHealthMessage,
    
    # Vision
    "vision.analyze": VisionAnalysisMessage,
    "vision.result": VisionResultMessage,
}


def get_message_schema(channel: str) -> Optional[type[BaseMessage]]:
    """
    Get the message schema for a given channel.
    
    Args:
        channel: Message bus channel name
        
    Returns:
        Message schema class or None if not found
    """
    return MESSAGE_REGISTRY.get(channel)


def validate_message(channel: str, data: Dict[str, Any]) -> BaseMessage:
    """
    Validate and parse message data for a channel.
    
    Args:
        channel: Message bus channel name
        data: Message data dictionary
        
    Returns:
        Validated message instance
        
    Raises:
        ValueError: If channel not found or validation fails
    """
    schema = get_message_schema(channel)
    if not schema:
        raise ValueError(f"No schema found for channel: {channel}")
    
    return schema(**data)