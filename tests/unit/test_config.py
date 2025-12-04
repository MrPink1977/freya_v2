"""
Unit tests for Configuration Management

Tests configuration loading, validation, and environment variable handling.
"""

import pytest
import os
from pathlib import Path
from pydantic import ValidationError
from src.core.config import FreyaConfig


class TestFreyaConfig:
    """Test suite for FreyaConfig class."""
    
    @pytest.mark.unit
    def test_default_values(self):
        """Test that default configuration values are set correctly."""
        config = FreyaConfig()
        
        # Redis defaults
        assert config.redis_host == "redis"
        assert config.redis_port == 6379
        assert config.redis_max_retries == 3
        
        # Ollama defaults
        assert config.ollama_host.startswith("http")
        assert config.ollama_model == "llama3.2:latest"
        assert config.ollama_temperature == 0.7
        
        # Audio defaults
        assert config.audio_sample_rate == 16000
        assert config.audio_channels == 1
        assert config.audio_chunk_size == 1024
        
        # GUI defaults
        assert config.gui_enabled is True
        assert config.gui_port == 8000
    
    @pytest.mark.unit
    def test_environment_variable_override(self, monkeypatch):
        """Test that environment variables override defaults."""
        # Set environment variables
        monkeypatch.setenv("REDIS_HOST", "custom-redis")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")
        
        config = FreyaConfig()
        
        assert config.redis_host == "custom-redis"
        assert config.redis_port == 6380
        assert config.ollama_model == "llama3.2:3b"
    
    @pytest.mark.unit
    def test_validation_port_range(self):
        """Test port number validation."""
        # Valid port
        config = FreyaConfig(redis_port=8080)
        assert config.redis_port == 8080
        
        # Invalid port (too high)
        with pytest.raises(ValidationError):
            FreyaConfig(redis_port=70000)
        
        # Invalid port (too low)
        with pytest.raises(ValidationError):
            FreyaConfig(redis_port=0)
    
    @pytest.mark.unit
    def test_validation_temperature_range(self):
        """Test LLM temperature validation."""
        # Valid temperature
        config = FreyaConfig(ollama_temperature=0.5)
        assert config.ollama_temperature == 0.5
        
        # Invalid temperature (too high)
        with pytest.raises(ValidationError):
            FreyaConfig(ollama_temperature=3.0)
        
        # Invalid temperature (negative)
        with pytest.raises(ValidationError):
            FreyaConfig(ollama_temperature=-0.1)
    
    @pytest.mark.unit
    def test_url_helpers(self):
        """Test URL helper methods."""
        config = FreyaConfig(
            redis_host="redis-server",
            redis_port=6379,
            chromadb_host="chromadb-server",
            chromadb_port=8000
        )
        
        assert config.get_redis_url() == "redis://redis-server:6379"
        assert config.get_chromadb_url() == "http://chromadb-server:8000"
    
    @pytest.mark.unit
    def test_environment_checks(self):
        """Test environment check methods."""
        dev_config = FreyaConfig(environment="development")
        assert dev_config.is_development() is True
        assert dev_config.is_production() is False
        
        prod_config = FreyaConfig(environment="production")
        assert prod_config.is_production() is True
        assert prod_config.is_development() is False
    
    @pytest.mark.unit
    def test_log_dir_creation(self, tmp_path):
        """Test that log directory is created automatically."""
        log_dir = tmp_path / "test_logs"
        config = FreyaConfig(log_dir=str(log_dir))
        
        assert log_dir.exists()
        assert log_dir.is_dir()
    
    @pytest.mark.unit
    def test_ollama_host_normalization(self):
        """Test that Ollama host URL is normalized."""
        # Without protocol
        config1 = FreyaConfig(ollama_host="localhost:11434")
        assert config1.ollama_host.startswith("http://")
        
        # With http protocol
        config2 = FreyaConfig(ollama_host="http://ollama:11434")
        assert config2.ollama_host.startswith("http://")
        
        # With https protocol
        config3 = FreyaConfig(ollama_host="https://ollama:11434")
        assert config3.ollama_host.startswith("https://")
    
    @pytest.mark.unit
    def test_gui_security_config(self):
        """Test GUI security configuration fields."""
        config = FreyaConfig()
        
        # Verify security fields exist and have defaults
        assert hasattr(config, 'gui_jwt_secret')
        assert hasattr(config, 'gui_token_expiry')
        assert hasattr(config, 'gui_session_timeout')
        assert hasattr(config, 'gui_max_sessions')
        assert hasattr(config, 'gui_rate_limit_rate')
        assert hasattr(config, 'gui_rate_limit_burst')
        
        # Check defaults
        assert config.gui_token_expiry == 3600
        assert config.gui_session_timeout == 3600
        assert config.gui_max_sessions == 100
        assert config.gui_rate_limit_rate == 10.0
        assert config.gui_rate_limit_burst == 20
    
    @pytest.mark.unit
    def test_stt_config(self):
        """Test STT configuration fields."""
        config = FreyaConfig()
        
        assert config.stt_model == "base"
        assert config.stt_language == "en"
        assert config.stt_device in ["cpu", "cuda", "auto"]
    
    @pytest.mark.unit
    def test_tts_config(self):
        """Test TTS configuration fields."""
        config = FreyaConfig()
        
        assert hasattr(config, 'elevenlabs_api_key')
        assert hasattr(config, 'elevenlabs_voice_id')
        assert hasattr(config, 'elevenlabs_model')
        assert hasattr(config, 'elevenlabs_stability')
        assert hasattr(config, 'elevenlabs_similarity_boost')
        
        # Check stability is in valid range
        assert 0.0 <= config.elevenlabs_stability <= 1.0
        assert 0.0 <= config.elevenlabs_similarity_boost <= 1.0
    
    @pytest.mark.unit
    def test_mcp_config(self):
        """Test MCP configuration fields."""
        config = FreyaConfig()
        
        assert config.mcp_enabled is True
        assert config.mcp_connection_timeout == 30
        assert config.mcp_tool_timeout == 60
        assert config.mcp_retry_attempts == 3
