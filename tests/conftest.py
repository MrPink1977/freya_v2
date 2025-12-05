"""
Pytest configuration and fixtures for Freya v2.0 tests.

This module provides shared fixtures for all tests, including mocks for external
services and common test utilities.
"""

import asyncio
from typing import AsyncGenerator, Dict, Any, List, Callable
from unittest.mock import AsyncMock, MagicMock, Mock
import pytest
import numpy as np
from pathlib import Path


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Mock Redis Client
# ============================================================================

@pytest.fixture
def mock_redis():
    """
    Mock Redis client for testing.
    
    Provides a mock Redis client with common operations.
    
    Returns:
        MagicMock: Mock Redis client
    """
    redis_mock = MagicMock()
    redis_mock.ping = AsyncMock(return_value=True)
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.publish = AsyncMock(return_value=1)
    redis_mock.subscribe = AsyncMock()
    redis_mock.unsubscribe = AsyncMock()
    redis_mock.close = AsyncMock(return_value=None)
    redis_mock.aclose = AsyncMock(return_value=None)  # Some versions use aclose
    
    # Mock pubsub
    pubsub_mock = MagicMock()
    pubsub_mock.subscribe = AsyncMock()
    pubsub_mock.unsubscribe = AsyncMock()
    pubsub_mock.get_message = AsyncMock(return_value=None)
    pubsub_mock.close = AsyncMock(return_value=None)
    redis_mock.pubsub = Mock(return_value=pubsub_mock)
    
    return redis_mock


# ============================================================================
# Mock Message Bus
# ============================================================================

@pytest.fixture
def mock_message_bus():
    """
    Mock MessageBus for testing.
    
    Provides a mock message bus with publish/subscribe capabilities.
    
    Returns:
        AsyncMock: Mock MessageBus
    """
    bus_mock = AsyncMock()
    bus_mock.connect = AsyncMock()
    bus_mock.disconnect = AsyncMock()
    bus_mock.publish = AsyncMock()
    bus_mock.subscribe = AsyncMock()
    bus_mock.unsubscribe = AsyncMock()
    bus_mock.start = AsyncMock()
    bus_mock.stop = AsyncMock()
    bus_mock.is_connected = Mock(return_value=True)
    
    # Store subscriptions for testing
    bus_mock._subscriptions: Dict[str, List[Callable]] = {}
    
    async def mock_subscribe(channel: str, callback: Callable):
        if channel not in bus_mock._subscriptions:
            bus_mock._subscriptions[channel] = []
        bus_mock._subscriptions[channel].append(callback)
    
    async def mock_publish(channel: str, data: Any):
        if channel in bus_mock._subscriptions:
            for callback in bus_mock._subscriptions[channel]:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
    
    bus_mock.subscribe.side_effect = mock_subscribe
    bus_mock.publish.side_effect = mock_publish
    
    return bus_mock


# ============================================================================
# Mock Ollama API
# ============================================================================

@pytest.fixture
def mock_ollama():
    """
    Mock Ollama API for testing.
    
    Returns:
        AsyncMock: Mock Ollama client
    """
    ollama_mock = AsyncMock()
    
    # Mock chat completion
    async def mock_chat(*args, **kwargs):
        return {
            "message": {
                "role": "assistant",
                "content": "This is a mock response from Ollama."
            },
            "model": "llama2",
            "created_at": "2025-12-04T00:00:00Z",
            "done": True
        }
    
    ollama_mock.chat = AsyncMock(side_effect=mock_chat)
    ollama_mock.list = AsyncMock(return_value={"models": [{"name": "llama2"}]})
    ollama_mock.show = AsyncMock(return_value={"modelfile": "FROM llama2"})
    
    return ollama_mock


# ============================================================================
# Mock Whisper (faster-whisper)
# ============================================================================

@pytest.fixture
def mock_whisper():
    """
    Mock faster-whisper for testing.
    
    Returns:
        MagicMock: Mock WhisperModel
    """
    whisper_mock = MagicMock()
    
    # Mock transcription segments
    mock_segment = MagicMock()
    mock_segment.text = "This is a test transcription"
    mock_segment.start = 0.0
    mock_segment.end = 2.5
    
    # Mock transcribe method
    def mock_transcribe(*args, **kwargs):
        segments = [mock_segment]
        info = MagicMock()
        info.language = "en"
        info.language_probability = 0.95
        info.duration = 2.5
        return segments, info
    
    whisper_mock.transcribe = Mock(side_effect=mock_transcribe)
    
    return whisper_mock


# ============================================================================
# Mock PyAudio
# ============================================================================

@pytest.fixture
def mock_pyaudio():
    """
    Mock PyAudio for testing audio I/O.
    
    Returns:
        MagicMock: Mock PyAudio instance
    """
    pyaudio_mock = MagicMock()
    
    # Mock stream
    stream_mock = MagicMock()
    stream_mock.read = Mock(return_value=b'\x00\x00' * 1024)  # Silent audio
    stream_mock.write = Mock()
    stream_mock.start_stream = Mock()
    stream_mock.stop_stream = Mock()
    stream_mock.close = Mock()
    stream_mock.is_active = Mock(return_value=True)
    
    # Mock PyAudio instance
    pyaudio_mock.open = Mock(return_value=stream_mock)
    pyaudio_mock.get_device_count = Mock(return_value=2)
    pyaudio_mock.get_device_info_by_index = Mock(return_value={
        "index": 0,
        "name": "Test Device",
        "maxInputChannels": 2,
        "maxOutputChannels": 2,
        "defaultSampleRate": 16000.0
    })
    pyaudio_mock.terminate = Mock()
    
    # Audio format constants
    pyaudio_mock.paInt16 = 8
    pyaudio_mock.paFloat32 = 1
    
    return pyaudio_mock


# ============================================================================
# Mock ElevenLabs API
# ============================================================================

@pytest.fixture
def mock_elevenlabs():
    """
    Mock ElevenLabs API for testing TTS.
    
    Returns:
        AsyncMock: Mock ElevenLabs client
    """
    elevenlabs_mock = AsyncMock()
    
    # Mock generate method
    async def mock_generate(*args, **kwargs):
        # Return mock audio data (silent audio)
        return b'\x00\x00' * 16000  # 1 second of silent 16-bit audio
    
    elevenlabs_mock.generate = AsyncMock(side_effect=mock_generate)
    
    # Mock voices
    elevenlabs_mock.voices = AsyncMock(return_value=[
        {"voice_id": "test_voice_1", "name": "Test Voice 1"},
        {"voice_id": "test_voice_2", "name": "Test Voice 2"}
    ])
    
    return elevenlabs_mock


# ============================================================================
# Mock MCP Gateway
# ============================================================================

@pytest.fixture
def mock_mcp_gateway():
    """
    Mock MCP Gateway for testing MCP tool calls.
    
    Returns:
        AsyncMock: Mock MCP Gateway
    """
    mcp_mock = AsyncMock()
    
    # Mock call_tool method
    async def mock_call_tool(server: str, tool: str, **kwargs):
        if server == "elevenlabs" and tool == "text_to_speech":
            return {
                "success": True,
                "audio_data": b'\x00\x00' * 16000,
                "format": "mp3"
            }
        return {"success": True, "result": "Mock result"}
    
    mcp_mock.call_tool = AsyncMock(side_effect=mock_call_tool)
    mcp_mock.list_tools = AsyncMock(return_value=[
        {"name": "text_to_speech", "description": "Generate speech from text"}
    ])
    mcp_mock.initialize = AsyncMock()
    mcp_mock.shutdown = AsyncMock()
    
    return mcp_mock


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_audio_data() -> bytes:
    """
    Generate sample audio data for testing.
    
    Returns:
        bytes: 16-bit PCM audio data (1 second, 16kHz, mono)
    """
    sample_rate = 16000
    duration = 1.0
    frequency = 440  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * frequency * t)
    audio = (audio * 32767).astype(np.int16)
    
    return audio.tobytes()


@pytest.fixture
def sample_wav_file(tmp_path: Path, sample_audio_data: bytes) -> Path:
    """
    Create a temporary WAV file for testing.
    
    Args:
        tmp_path: Pytest temporary directory
        sample_audio_data: Audio data to write
    
    Returns:
        Path: Path to temporary WAV file
    """
    import wave
    
    wav_path = tmp_path / "test_audio.wav"
    
    with wave.open(str(wav_path), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(16000)
        wav_file.writeframes(sample_audio_data)
    
    return wav_path


@pytest.fixture
def sample_transcription() -> Dict[str, Any]:
    """
    Sample transcription data for testing.
    
    Returns:
        dict: Transcription data
    """
    return {
        "text": "This is a test transcription",
        "language": "en",
        "confidence": 0.95,
        "duration": 2.5,
        "timestamp": "2025-12-04T00:00:00Z"
    }


@pytest.fixture
def sample_llm_response() -> Dict[str, Any]:
    """
    Sample LLM response for testing.
    
    Returns:
        dict: LLM response data
    """
    return {
        "text": "This is a test response from the LLM.",
        "model": "llama2",
        "timestamp": "2025-12-04T00:00:00Z",
        "metadata": {
            "tokens": 10,
            "duration": 0.5
        }
    }


# ============================================================================
# Service Fixtures
# ============================================================================

@pytest.fixture
def mock_config():
    """
    Mock configuration for testing.
    
    Returns:
        MagicMock: Mock configuration object
    """
    config_mock = MagicMock()
    
    # Redis
    config_mock.redis_host = "localhost"
    config_mock.redis_port = 6379
    
    # STT
    config_mock.stt_model = "base"
    config_mock.stt_device = "cpu"
    config_mock.stt_compute_type = "int8"
    config_mock.stt_language = "en"
    config_mock.stt_beam_size = 5
    
    # TTS
    config_mock.tts_voice_id = "test_voice"
    config_mock.elevenlabs_voice_id = "test_voice"  # TTS Service uses this
    config_mock.elevenlabs_model = "eleven_monolingual_v1"  # TTS Service uses this
    config_mock.tts_model = "eleven_monolingual_v1"
    config_mock.tts_stability = 0.5
    config_mock.tts_similarity_boost = 0.5
    
    # Audio
    config_mock.audio_sample_rate = 16000
    config_mock.audio_channels = 1
    config_mock.audio_chunk_size = 1024
    config_mock.audio_input_device_index = None
    config_mock.audio_output_device_index = None
    
    # LLM
    config_mock.llm_model = "llama2"
    config_mock.llm_temperature = 0.7
    config_mock.llm_max_tokens = 2000
    
    # GUI
    config_mock.gui_host = "0.0.0.0"
    config_mock.gui_port = 8080
    config_mock.gui_jwt_secret = "test_secret"
    config_mock.gui_token_expiry = 3600
    config_mock.gui_rate_limit_rate = 10
    config_mock.gui_rate_limit_burst = 20
    
    return config_mock


@pytest.fixture
async def mock_base_service(mock_message_bus, mock_config):
    """
    Mock BaseService for testing.
    
    Returns:
        AsyncMock: Mock BaseService instance
    """
    service_mock = AsyncMock()
    service_mock.name = "test_service"
    service_mock.message_bus = mock_message_bus
    service_mock.config = mock_config
    service_mock.initialize = AsyncMock()
    service_mock.start = AsyncMock()
    service_mock.stop = AsyncMock()
    service_mock.health_check = AsyncMock(return_value={
        "status": "healthy",
        "service": "test_service"
    })
    
    return service_mock


# ============================================================================
# Async Utilities
# ============================================================================

@pytest.fixture
async def async_timeout():
    """
    Utility fixture for testing async operations with timeout.
    
    Returns:
        Callable: Async timeout context manager
    """
    async def timeout(seconds: float):
        return asyncio.wait_for(asyncio.sleep(seconds), timeout=seconds)
    
    return timeout
