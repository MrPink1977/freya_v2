"""
Configuration Management - Modular, validated settings for Freya v2.0

Refactored to use nested Pydantic models for better organization and validation.
Each service has its own configuration class with proper validation.

Author: Claude (AI Assistant)
Version: 0.2.0
Date: 2025-12-05
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, HttpUrl, SecretStr
from typing import Optional, Literal, List
from pathlib import Path


# ============================================================================
# REDIS CONFIGURATION
# ============================================================================

class RedisConfig(BaseSettings):
    """Redis message bus configuration."""
    
    model_config = SettingsConfigDict(env_prefix="redis_")
    
    host: str = Field(
        default="redis",
        description="Redis server hostname"
    )
    
    port: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Redis server port"
    )
    
    db: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Redis database number"
    )
    
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum connection retry attempts"
    )
    
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Delay between retries in seconds"
    )
    
    password: Optional[SecretStr] = Field(
        default=None,
        description="Redis password (if authentication enabled)"
    )
    
    def get_url(self) -> str:
        """Get Redis connection URL."""
        if self.password:
            return f"redis://:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


# ============================================================================
# OLLAMA CONFIGURATION
# ============================================================================

class OllamaConfig(BaseSettings):
    """Ollama LLM configuration."""
    
    model_config = SettingsConfigDict(env_prefix="ollama_")
    
    host: str = Field(
        default="http://ollama:11434",
        description="Ollama API host URL"
    )
    
    model: str = Field(
        default="llama3.2:latest",
        description="LLM model to use"
    )
    
    timeout: float = Field(
        default=120.0,
        ge=10.0,
        le=600.0,
        description="Request timeout in seconds"
    )
    
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for response generation"
    )
    
    max_tokens: int = Field(
        default=2048,
        ge=128,
        le=32768,
        description="Maximum tokens in response"
    )
    
    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Ensure host starts with http:// or https://."""
        if not v.startswith(("http://", "https://")):
            return f"http://{v}"
        return v


# ============================================================================
# CHROMADB CONFIGURATION
# ============================================================================

class ChromaDBConfig(BaseSettings):
    """ChromaDB vector database configuration."""
    
    model_config = SettingsConfigDict(env_prefix="chromadb_")
    
    host: str = Field(
        default="chromadb",
        description="ChromaDB server hostname"
    )
    
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="ChromaDB server port"
    )
    
    collection_name: str = Field(
        default="freya_memories",
        description="Collection name for memories"
    )
    
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings"
    )
    
    def get_url(self) -> str:
        """Get ChromaDB connection URL."""
        return f"http://{self.host}:{self.port}"


# ============================================================================
# AUDIO CONFIGURATION
# ============================================================================

class AudioConfig(BaseSettings):
    """Audio input/output configuration."""
    
    model_config = SettingsConfigDict(env_prefix="audio_")
    
    sample_rate: int = Field(
        default=16000,
        description="Audio sample rate in Hz"
    )
    
    channels: int = Field(
        default=1,
        ge=1,
        le=2,
        description="Number of audio channels (1=mono, 2=stereo)"
    )
    
    chunk_size: int = Field(
        default=1024,
        ge=256,
        le=8192,
        description="Audio chunk size for streaming"
    )
    
    input_device: Optional[int] = Field(
        default=None,
        description="Input device index (None = default)"
    )
    
    output_device: Optional[int] = Field(
        default=None,
        description="Output device index (None = default)"
    )
    
    @field_validator('sample_rate')
    @classmethod
    def validate_sample_rate(cls, v: int) -> int:
        """Validate sample rate is a standard value."""
        valid_rates = [8000, 16000, 22050, 44100, 48000]
        if v not in valid_rates:
            raise ValueError(f'Sample rate must be one of {valid_rates}')
        return v


# ============================================================================
# ELEVENLABS CONFIGURATION
# ============================================================================

class ElevenLabsConfig(BaseSettings):
    """ElevenLabs TTS configuration."""
    
    model_config = SettingsConfigDict(env_prefix="elevenlabs_")
    
    api_key: Optional[SecretStr] = Field(
        default=None,
        description="ElevenLabs API key"
    )
    
    voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM",
        description="Voice ID (default: Rachel)"
    )
    
    model: str = Field(
        default="eleven_monolingual_v1",
        description="TTS model"
    )
    
    stability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Voice stability (0=variable, 1=stable)"
    )
    
    similarity_boost: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Voice similarity boost"
    )
    
    optimize_streaming_latency: int = Field(
        default=0,
        ge=0,
        le=4,
        description="Streaming latency optimization (0-4)"
    )


# ============================================================================
# PORCUPINE CONFIGURATION
# ============================================================================

class PorcupineConfig(BaseSettings):
    """Porcupine wake word detection configuration."""
    
    model_config = SettingsConfigDict(env_prefix="porcupine_")
    
    access_key: Optional[SecretStr] = Field(
        default=None,
        description="Porcupine access key"
    )
    
    keyword: str = Field(
        default="jarvis",
        description="Wake word keyword"
    )
    
    sensitivity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Detection sensitivity (0=less, 1=more)"
    )


# ============================================================================
# STT CONFIGURATION
# ============================================================================

class STTConfig(BaseSettings):
    """Speech-to-Text configuration."""
    
    model_config = SettingsConfigDict(env_prefix="stt_")
    
    model: str = Field(
        default="base",
        description="Whisper model size"
    )
    
    language: str = Field(
        default="en",
        description="Primary language for STT"
    )
    
    device: Literal["cpu", "cuda", "auto"] = Field(
        default="auto",
        description="Device for STT inference"
    )
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate Whisper model size."""
        valid_models = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
        if v not in valid_models:
            raise ValueError(f'Model must be one of {valid_models}')
        return v


# ============================================================================
# GUI CONFIGURATION
# ============================================================================

class GUISecurityConfig(BaseSettings):
    """GUI security settings."""
    
    model_config = SettingsConfigDict(env_prefix="gui_")
    
    jwt_secret: SecretStr = Field(
        default=SecretStr("change-this-secret-in-production"),
        description="JWT secret key for WebSocket authentication"
    )
    
    token_expiry: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="JWT token expiration time in seconds"
    )
    
    session_timeout: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Session timeout in seconds"
    )
    
    max_sessions: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum concurrent WebSocket sessions"
    )
    
    rate_limit_rate: float = Field(
        default=10.0,
        ge=1.0,
        le=100.0,
        description="Rate limit requests per second per session"
    )
    
    rate_limit_burst: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Rate limit burst size"
    )


class GUIConfig(BaseSettings):
    """GUI service configuration."""
    
    model_config = SettingsConfigDict(env_prefix="gui_")
    
    enabled: bool = Field(
        default=True,
        description="Enable GUI service"
    )
    
    host: str = Field(
        default="0.0.0.0",
        description="GUI server host"
    )
    
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="GUI server port"
    )
    
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    websocket_heartbeat: int = Field(
        default=30,
        ge=5,
        le=300,
        description="WebSocket heartbeat interval in seconds"
    )
    
    log_retention: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Number of log entries to retain"
    )
    
    security: GUISecurityConfig = Field(
        default_factory=GUISecurityConfig,
        description="Security settings"
    )


# ============================================================================
# MCP CONFIGURATION
# ============================================================================

class MCPConfig(BaseSettings):
    """MCP Gateway configuration."""
    
    model_config = SettingsConfigDict(env_prefix="mcp_")
    
    enabled: bool = Field(
        default=True,
        description="Enable MCP Gateway service"
    )
    
    servers_config: Path = Field(
        default=Path("config/mcp_servers.yaml"),
        description="Path to MCP servers configuration file"
    )
    
    connection_timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Server connection timeout in seconds"
    )
    
    tool_timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Tool execution timeout in seconds"
    )
    
    retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retry attempts for failed operations"
    )
    
    cache_tool_schemas: bool = Field(
        default=True,
        description="Cache tool schemas to reduce discovery overhead"
    )
    
    log_tool_calls: bool = Field(
        default=True,
        description="Log all tool calls and results for debugging"
    )


# ============================================================================
# NOTIFICATION CONFIGURATION
# ============================================================================

class EmailNotificationConfig(BaseSettings):
    """Email notification configuration."""
    
    model_config = SettingsConfigDict(env_prefix="notification_email_")
    
    enabled: bool = Field(
        default=False,
        description="Enable email notifications"
    )
    
    smtp_host: str = Field(
        default="smtp.gmail.com",
        description="SMTP server hostname"
    )
    
    smtp_port: int = Field(
        default=587,
        ge=1,
        le=65535,
        description="SMTP server port"
    )
    
    from_address: str = Field(
        default="freya@example.com",
        description="Email sender address"
    )
    
    username: Optional[str] = Field(
        default=None,
        description="SMTP authentication username"
    )
    
    password: Optional[SecretStr] = Field(
        default=None,
        description="SMTP authentication password"
    )


class WebhookNotificationConfig(BaseSettings):
    """Webhook notification configuration."""
    
    model_config = SettingsConfigDict(env_prefix="notification_webhook_")
    
    enabled: bool = Field(
        default=False,
        description="Enable webhook notifications"
    )
    
    url: Optional[str] = Field(
        default=None,
        description="Webhook URL"
    )
    
    secret: Optional[SecretStr] = Field(
        default=None,
        description="Webhook secret for request signing"
    )


class PushNotificationConfig(BaseSettings):
    """Push notification configuration."""
    
    model_config = SettingsConfigDict(env_prefix="notification_push_")
    
    enabled: bool = Field(
        default=False,
        description="Enable push notifications"
    )
    
    provider: Literal["fcm", "apns", "none"] = Field(
        default="none",
        description="Push notification provider"
    )
    
    api_key: Optional[SecretStr] = Field(
        default=None,
        description="Push notification API key"
    )


class SMSNotificationConfig(BaseSettings):
    """SMS notification configuration."""
    
    model_config = SettingsConfigDict(env_prefix="notification_sms_")
    
    enabled: bool = Field(
        default=False,
        description="Enable SMS notifications"
    )
    
    provider: Literal["twilio", "none"] = Field(
        default="none",
        description="SMS provider"
    )
    
    account_sid: Optional[str] = Field(
        default=None,
        description="SMS provider account SID"
    )
    
    auth_token: Optional[SecretStr] = Field(
        default=None,
        description="SMS provider auth token"
    )
    
    from_number: Optional[str] = Field(
        default=None,
        description="SMS sender phone number"
    )


class NotificationConfig(BaseSettings):
    """Notification service configuration."""
    
    model_config = SettingsConfigDict(env_prefix="notification_")
    
    email: EmailNotificationConfig = Field(
        default_factory=EmailNotificationConfig,
        description="Email notification settings"
    )
    
    webhook: WebhookNotificationConfig = Field(
        default_factory=WebhookNotificationConfig,
        description="Webhook notification settings"
    )
    
    push: PushNotificationConfig = Field(
        default_factory=PushNotificationConfig,
        description="Push notification settings"
    )
    
    sms: SMSNotificationConfig = Field(
        default_factory=SMSNotificationConfig,
        description="SMS notification settings"
    )


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

class LoggingConfig(BaseSettings):
    """Logging configuration."""
    
    model_config = SettingsConfigDict(env_prefix="log_")
    
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    dir: Path = Field(
        default=Path("logs"),
        description="Directory for log files"
    )
    
    rotation: str = Field(
        default="1 day",
        description="Log rotation interval"
    )
    
    retention: str = Field(
        default="7 days",
        description="Log retention period"
    )
    
    format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        description="Loguru log format string"
    )
    
    @field_validator("dir")
    @classmethod
    def create_log_dir(cls, v: Path) -> Path:
        """Ensure log directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v


# ============================================================================
# PERSONALITY CONFIGURATION
# ============================================================================

class PersonalityConfig(BaseSettings):
    """Personality configuration."""
    
    model_config = SettingsConfigDict(env_prefix="personality_")
    
    name: str = Field(
        default="Freya",
        description="Assistant name"
    )
    
    style: Literal["witty_sarcastic", "professional", "casual", "friendly"] = Field(
        default="witty_sarcastic",
        description="Personality style"
    )
    
    verbosity: Literal["concise", "normal", "verbose"] = Field(
        default="normal",
        description="Response verbosity level"
    )


# ============================================================================
# MEMORY CONFIGURATION
# ============================================================================

class MemoryConfig(BaseSettings):
    """Memory management configuration."""
    
    model_config = SettingsConfigDict(env_prefix="memory_")
    
    max_short_term: int = Field(
        default=20,
        ge=5,
        le=100,
        description="Maximum short-term memory entries"
    )
    
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for memory deduplication"
    )
    
    auto_summarize: bool = Field(
        default=True,
        description="Enable automatic memory summarization"
    )


# ============================================================================
# MAIN CONFIGURATION
# ============================================================================

class FreyaConfig(BaseSettings):
    """
    Main configuration for Freya v2.0.
    
    All settings can be overridden via environment variables.
    Settings are loaded from .env file if present.
    
    Example:
        >>> config = FreyaConfig()
        >>> print(config.ollama.host)
        'http://ollama:11434'
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__"
    )
    
    # Service configurations
    redis: RedisConfig = Field(
        default_factory=RedisConfig,
        description="Redis message bus configuration"
    )
    
    ollama: OllamaConfig = Field(
        default_factory=OllamaConfig,
        description="Ollama LLM configuration"
    )
    
    chromadb: ChromaDBConfig = Field(
        default_factory=ChromaDBConfig,
        description="ChromaDB vector database configuration"
    )
    
    audio: AudioConfig = Field(
        default_factory=AudioConfig,
        description="Audio input/output configuration"
    )
    
    elevenlabs: ElevenLabsConfig = Field(
        default_factory=ElevenLabsConfig,
        description="ElevenLabs TTS configuration"
    )
    
    porcupine: PorcupineConfig = Field(
        default_factory=PorcupineConfig,
        description="Porcupine wake word detection configuration"
    )
    
    stt: STTConfig = Field(
        default_factory=STTConfig,
        description="Speech-to-Text configuration"
    )
    
    gui: GUIConfig = Field(
        default_factory=GUIConfig,
        description="GUI service configuration"
    )
    
    mcp: MCPConfig = Field(
        default_factory=MCPConfig,
        description="MCP Gateway configuration"
    )
    
    notification: NotificationConfig = Field(
        default_factory=NotificationConfig,
        description="Notification service configuration"
    )
    
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration"
    )
    
    personality: PersonalityConfig = Field(
        default_factory=PersonalityConfig,
        description="Personality configuration"
    )
    
    memory: MemoryConfig = Field(
        default_factory=MemoryConfig,
        description="Memory management configuration"
    )
    
    # System configuration
    environment: Literal["development", "production", "testing"] = Field(
        default="development",
        description="Runtime environment"
    )
    
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    # Helper methods
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == "testing"


# Global config instance
config = FreyaConfig()