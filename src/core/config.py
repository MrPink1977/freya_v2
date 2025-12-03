"""
Configuration Management - Centralized settings for Freya v2.0

Uses Pydantic Settings for type-safe configuration from environment
variables and .env files with comprehensive validation.

Author: MrPink1977
Version: 0.1.0
Date: 2025-12-03
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, HttpUrl
from typing import Optional, Literal
from pathlib import Path


class FreyaConfig(BaseSettings):
    """
    Main configuration for Freya v2.0.
    
    All settings can be overridden via environment variables.
    Settings are loaded from .env file if present.
    
    Example:
        >>> config = FreyaConfig()
        >>> print(config.ollama_host)
        'http://ollama:11434'
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore unknown env vars
    )
    
    # ==================== Redis Configuration ====================
    redis_host: str = Field(
        default="redis",
        description="Redis server hostname",
        examples=["redis", "localhost", "192.168.1.100"]
    )
    
    redis_port: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Redis server port"
    )
    
    redis_max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum connection retry attempts"
    )
    
    redis_retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Delay between retries in seconds"
    )
    
    # ==================== Ollama Configuration ====================
    ollama_host: str = Field(
        default="http://ollama:11434",
        description="Ollama API host URL",
        examples=["http://ollama:11434", "http://localhost:11434"]
    )
    
    ollama_model: str = Field(
        default="llama3.2:latest",
        description="LLM model to use",
        examples=["llama3.2:latest", "llama3.2:3b", "mistral:latest"]
    )
    
    ollama_timeout: float = Field(
        default=120.0,
        ge=10.0,
        description="Ollama request timeout in seconds"
    )
    
    ollama_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature for response generation"
    )
    
    # ==================== ChromaDB Configuration ====================
    chromadb_host: str = Field(
        default="chromadb",
        description="ChromaDB server hostname"
    )
    
    chromadb_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="ChromaDB server port"
    )
    
    chromadb_collection_name: str = Field(
        default="freya_memories",
        description="ChromaDB collection name for memories"
    )
    
    # ==================== ElevenLabs Configuration ====================
    elevenlabs_api_key: Optional[str] = Field(
        default=None,
        description="ElevenLabs API key for TTS"
    )
    
    elevenlabs_voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM",
        description="ElevenLabs voice ID (default: Rachel)"
    )
    
    elevenlabs_model: str = Field(
        default="eleven_monolingual_v1",
        description="ElevenLabs TTS model"
    )
    
    elevenlabs_stability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Voice stability (0=variable, 1=stable)"
    )
    
    elevenlabs_similarity_boost: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Voice similarity boost"
    )
    
    # ==================== Porcupine Configuration ====================
    porcupine_access_key: Optional[str] = Field(
        default=None,
        description="Porcupine access key for wake word detection"
    )
    
    porcupine_keyword: str = Field(
        default="jarvis",
        description="Wake word keyword",
        examples=["jarvis", "alexa", "hey google"]
    )
    
    porcupine_sensitivity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Wake word detection sensitivity (0=less sensitive, 1=more sensitive)"
    )
    
    # ==================== Audio Configuration ====================
    audio_sample_rate: int = Field(
        default=16000,
        description="Audio sample rate in Hz"
    )
    
    audio_channels: int = Field(
        default=1,
        ge=1,
        le=2,
        description="Number of audio channels (1=mono, 2=stereo)"
    )
    
    audio_chunk_size: int = Field(
        default=1024,
        ge=256,
        le=8192,
        description="Audio chunk size for streaming"
    )
    
    # ==================== STT Configuration ====================
    stt_model: str = Field(
        default="base",
        description="Whisper model size",
        examples=["tiny", "base", "small", "medium", "large"]
    )

    stt_language: str = Field(
        default="en",
        description="Primary language for STT"
    )

    stt_device: Literal["cpu", "cuda", "auto"] = Field(
        default="auto",
        description="Device for STT inference"
    )

    stt_compute_type: Literal["int8", "int8_float16", "float16", "float32"] = Field(
        default="float16",
        description="Compute type for STT model (affects speed and memory)"
    )

    stt_beam_size: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Beam size for STT decoding (higher=better quality, slower)"
    )

    stt_vad_filter: bool = Field(
        default=True,
        description="Enable Voice Activity Detection to filter silence"
    )

    stt_condition_on_previous_text: bool = Field(
        default=True,
        description="Condition on previous text for better context"
    )
    
    # ==================== GUI Configuration ====================
    gui_backend_host: str = Field(
        default="0.0.0.0",
        description="GUI backend host"
    )
    
    gui_backend_port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        description="GUI backend port"
    )
    
    gui_enable_cors: bool = Field(
        default=True,
        description="Enable CORS for GUI backend"
    )
    
    # ==================== Logging Configuration ====================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    log_dir: Path = Field(
        default=Path("logs"),
        description="Directory for log files"
    )
    
    log_rotation: str = Field(
        default="1 day",
        description="Log rotation interval"
    )
    
    log_retention: str = Field(
        default="7 days",
        description="Log retention period"
    )
    
    log_format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        description="Loguru log format string"
    )
    
    # ==================== Personality Configuration ====================
    personality_name: str = Field(
        default="Freya",
        description="Assistant name"
    )
    
    personality_style: Literal["witty_sarcastic", "professional", "casual", "friendly"] = Field(
        default="witty_sarcastic",
        description="Personality style"
    )
    
    personality_verbosity: Literal["concise", "normal", "verbose"] = Field(
        default="normal",
        description="Response verbosity level"
    )
    
    # ==================== Memory Configuration ====================
    memory_max_short_term: int = Field(
        default=20,
        ge=5,
        le=100,
        description="Maximum short-term memory entries"
    )
    
    memory_similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for memory deduplication"
    )
    
    memory_auto_summarize: bool = Field(
        default=True,
        description="Enable automatic memory summarization"
    )
    
    # ==================== System Configuration ====================
    environment: Literal["development", "production", "testing"] = Field(
        default="development",
        description="Runtime environment"
    )
    
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    @field_validator("log_dir")
    @classmethod
    def create_log_dir(cls, v: Path) -> Path:
        """Ensure log directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v
        
    @field_validator("ollama_host")
    @classmethod
    def validate_ollama_host(cls, v: str) -> str:
        """Ensure Ollama host starts with http:// or https://."""
        if not v.startswith(("http://", "https://")):
            return f"http://{v}"
        return v
        
    def get_redis_url(self) -> str:
        """
        Get the full Redis connection URL.
        
        Returns:
            Redis URL string
        """
        return f"redis://{self.redis_host}:{self.redis_port}"
        
    def get_chromadb_url(self) -> str:
        """
        Get the full ChromaDB connection URL.
        
        Returns:
            ChromaDB URL string
        """
        return f"http://{self.chromadb_host}:{self.chromadb_port}"
        
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
        
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


# Global config instance
# This is the single source of truth for all configuration
config = FreyaConfig()
