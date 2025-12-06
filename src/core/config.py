"""
Configuration Management - YAML-based settings for Freya v2.0

Loads configuration from config/default.yaml with Pydantic validation.
Environment variables can override YAML settings.

Author: MrPink1977
Version: 0.4.0
Date: 2024-12-06
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List, Dict, Any
from pathlib import Path
import yaml


class OllamaConfig(BaseModel):
    """Ollama LLM configuration."""
    host: str = "http://localhost:11434"
    model: str = "llama3.2:3b"
    options: Dict[str, Any] = Field(default_factory=dict)


class AppConfig(BaseModel):
    """Application configuration."""
    system_prompt: str
    max_history: int = 12
    wake_word: str = "Hey, Freya"
    wake_word_sensitivity: float = 0.75
    wake_session_seconds: float = 8.0
    startup_mode: Literal["normal", "diagnostic"] = "normal"
    prompt_for_mode: bool = True
    interaction_mode: Literal["voice", "text"] = "voice"
    mode_toggle_hotkey: str = "ctrl+t"


class STTConfig(BaseModel):
    """Speech-to-Text configuration."""
    model: str = "base"
    device: str = "cuda"
    sample_rate: int = 16000
    silence_threshold: float = 0.02
    silence_duration: float = 1.2
    max_record_seconds: int = 30
    prompt_tone_frequency: int = 880
    prompt_tone_duration: float = 0.2
    prompt_tone_volume: float = 0.2


class ElevenLabsConfig(BaseModel):
    """ElevenLabs TTS configuration."""
    api_key: str = ""
    voice_id: str = "AXdMgz6evoL7OPd7eU12"
    model: str = "eleven_turbo_v2_5"
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True


class TTSConfig(BaseModel):
    """Text-to-Speech configuration."""
    engine: Literal["piper", "elevenlabs"] = "elevenlabs"
    voice_path: str = "voices/en_GB-southern_english_female-low.onnx"
    preload_phrases: List[str] = Field(default_factory=list)
    elevenlabs: ElevenLabsConfig = Field(default_factory=ElevenLabsConfig)


class WakeDetectorConfig(BaseModel):
    """Wake word detector configuration."""
    model: str = "tiny"
    device: str = "cuda"
    sample_rate: int = 16000
    chunk_seconds: float = 2.0


class ShortTermMemoryConfig(BaseModel):
    """Short-term memory configuration."""
    max_history: int = 12
    enable_summarization: bool = True
    summary_trigger_ratio: float = 0.8
    max_summaries: int = 3


class LongTermMemoryConfig(BaseModel):
    """Long-term memory configuration."""
    enabled: bool = True
    store_type: str = "sqlite"
    db_path: str = "data/freya_memory.db"
    recall_limit: int = 3
    min_similarity: float = 0.2
    auto_store_keywords: List[str] = Field(default_factory=list)
    store_assistant_messages: bool = False


class MemoryConfig(BaseModel):
    """Memory system configuration."""
    short_term: ShortTermMemoryConfig = Field(default_factory=ShortTermMemoryConfig)
    long_term: LongTermMemoryConfig = Field(default_factory=LongTermMemoryConfig)


class WebSearchConfig(BaseModel):
    """Web search configuration."""
    enabled: bool = True
    max_results: int = 5
    trigger_keywords: List[str] = Field(default_factory=list)


class FacialRecognitionConfig(BaseModel):
    """Facial recognition configuration."""
    enabled: bool = False
    known_faces_dir: str = "data/faces"
    detection_model: Literal["hog", "cnn"] = "hog"
    encoding_model: Literal["small", "large"] = "small"
    tolerance: float = 0.5
    camera_channel: Optional[int] = None
    min_recognition_interval: float = 5.0


class VisionConfig(BaseModel):
    """Vision system configuration."""
    facial_recognition: FacialRecognitionConfig = Field(default_factory=FacialRecognitionConfig)


class PersonalityTraits(BaseModel):
    """Personality trait values."""
    directness: float = Field(default=0.8, ge=0.0, le=1.0)
    humor_level: float = Field(default=0.7, ge=0.0, le=1.0)
    empathy: float = Field(default=0.7, ge=0.0, le=1.0)
    formality: float = Field(default=0.2, ge=0.0, le=1.0)
    verbosity: float = Field(default=0.3, ge=0.0, le=1.0)
    curiosity: float = Field(default=0.5, ge=0.0, le=1.0)
    sassiness: float = Field(default=0.6, ge=0.0, le=1.0)
    patience: float = Field(default=0.8, ge=0.0, le=1.0)


class PersonalityConfig(BaseModel):
    """Personality system configuration."""
    enabled: bool = True
    traits: PersonalityTraits = Field(default_factory=PersonalityTraits)


class FreyaConfig(BaseModel):
    """Main Freya configuration loaded from YAML."""
    ollama: OllamaConfig
    app: AppConfig
    stt: STTConfig
    tts: TTSConfig
    wake_detector: WakeDetectorConfig
    memory: MemoryConfig
    web_search: WebSearchConfig
    vision: VisionConfig
    personality: PersonalityConfig
    
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_max_retries: int = 3
    redis_retry_delay: float = 1.0
    
    gui_enabled: bool = True
    gui_host: str = "0.0.0.0"
    gui_port: int = 8000
    gui_cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    gui_websocket_heartbeat: int = 30
    gui_log_retention: int = 1000
    gui_jwt_secret: str = "change-this-secret-in-production"
    gui_token_expiry: int = 3600
    gui_session_timeout: int = 3600
    gui_max_sessions: int = 100
    gui_rate_limit_rate: float = 10.0
    gui_rate_limit_burst: int = 20
    
    mcp_enabled: bool = True
    mcp_servers_config: str = "config/mcp_servers.yaml"
    mcp_connection_timeout: int = 30
    mcp_tool_timeout: int = 60
    mcp_max_retries: int = 3
    
    chromadb_host: str = "chromadb"
    chromadb_port: int = 8000
    chromadb_collection_name: str = "freya_memories"
    
    notification_enabled: bool = True
    notification_default_duration: int = 5
    notification_sound_enabled: bool = True
    
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    audio_chunk_size: int = 1024
    
    personality_name: str = "Freya"
    personality_style: Literal["witty_sarcastic", "professional", "casual", "friendly"] = "witty_sarcastic"
    personality_verbosity: Literal["concise", "normal", "verbose"] = "concise"
    
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    log_rotation: str = "100 MB"
    log_retention: str = "1 week"
    log_file: str = "logs/freya.log"
    
    @classmethod
    def load_from_yaml(cls, yaml_path: str = "config/default.yaml") -> "FreyaConfig":
        """Load configuration from YAML file."""
        config_file = Path(yaml_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")
        
        with open(config_file, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
        
        return cls(**yaml_data)


def load_config() -> FreyaConfig:
    """Load Freya configuration from YAML file."""
    return FreyaConfig.load_from_yaml()


config = load_config()