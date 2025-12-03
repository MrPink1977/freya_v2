"""
Configuration Management - Centralized settings for Freya v2.0

Uses Pydantic Settings for type-safe configuration from environment
variables and .env files.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class FreyaConfig(BaseSettings):
    """Main configuration for Freya v2.0"""
    
    # Redis Configuration
    redis_host: str = Field(default="redis", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    
    # Ollama Configuration
    ollama_host: str = Field(default="http://ollama:11434", description="Ollama API host")
    ollama_model: str = Field(default="llama3.2:latest", description="LLM model to use")
    
    # ChromaDB Configuration
    chromadb_host: str = Field(default="chromadb", description="ChromaDB host")
    chromadb_port: int = Field(default=8000, description="ChromaDB port")
    
    # ElevenLabs Configuration
    elevenlabs_api_key: Optional[str] = Field(default=None, description="ElevenLabs API key")
    elevenlabs_voice_id: str = Field(default="21m00Tcm4TlvDq8ikWAM", description="Voice ID")
    
    # Porcupine Configuration
    porcupine_access_key: Optional[str] = Field(default=None, description="Porcupine access key")
    porcupine_keyword: str = Field(default="jarvis", description="Wake word")
    
    # GUI Configuration
    gui_backend_port: int = Field(default=8080, description="GUI backend port")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Personality Configuration
    personality_name: str = Field(default="Freya", description="Assistant name")
    personality_style: str = Field(
        default="witty_sarcastic",
        description="Personality style: witty_sarcastic, professional, casual"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global config instance
config = FreyaConfig()
