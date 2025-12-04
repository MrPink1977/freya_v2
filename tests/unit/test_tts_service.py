"""
Unit tests for TTS Service

Tests text-to-speech functionality with mocked ElevenLabs/MCP.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.tts.tts_service import TTSService, TTSServiceError


class TestTTSService:
    """Test suite for TTSService class."""
    
    @pytest.fixture
    async def tts_service(self, mock_message_bus, mock_config):
        """Create a TTSService instance for testing."""
        with patch('src.services.tts.tts_service.config', mock_config):
            service = TTSService(mock_message_bus)
            yield service
            if service._running:
                await service.stop()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialization(self, mock_message_bus, mock_config):
        """Test TTS service initialization."""
        with patch('src.services.tts.tts_service.config', mock_config):
            service = TTSService(mock_message_bus)
            
            assert service.name == "tts_service"
            assert service.generation_count == 0
            assert service.total_characters == 0
            assert service.voice_id == mock_config.tts_voice_id
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialize(self, tts_service):
        """Test service initialization."""
        await tts_service.initialize()
        assert tts_service._healthy is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_stop(self, tts_service, mock_message_bus):
        """Test service start and stop."""
        await tts_service.initialize()
        await tts_service.start()
        
        assert tts_service._running is True
        assert mock_message_bus.subscribe.called
        
        await tts_service.stop()
        assert tts_service._running is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_llm_response(self, tts_service, mock_message_bus):
        """Test handling LLM responses."""
        await tts_service.initialize()
        await tts_service.start()
        
        # Mock the speech generation
        with patch.object(tts_service, '_generate_speech', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = b'mock_audio_data'
            
            # Simulate LLM response
            await tts_service._handle_llm_response({
                \"response\": \"Hello, this is a test response\",
                \"location\": \"test_location\"
            })
            
            # Verify speech generation was called
            assert mock_gen.called
            call_args = mock_gen.call_args[0]
            assert \"Hello\" in call_args[0]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_tts_request(self, tts_service, mock_message_bus):
        \"\"\"Test direct TTS requests.\"\"\"
        await tts_service.initialize()
        await tts_service.start()
        
        with patch.object(tts_service, '_generate_speech', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = b'mock_audio_data'
            
            await tts_service._handle_tts_request({
                \"text\": \"Direct TTS request\",
                \"location\": \"test_location\"
            })
            
            assert mock_gen.called
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skip_short_responses(self, tts_service):
        \"\"\"Test that very short responses are skipped.\"\"\"
        await tts_service.initialize()
        await tts_service.start()
        
        with patch.object(tts_service, '_generate_speech', new_callable=AsyncMock) as mock_gen:
            # Very short response should be skipped
            await tts_service._handle_llm_response({
                \"response\": \"Ok\"
            })
            
            # Speech generation should not be called
            assert not mock_gen.called
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generation_metrics(self, tts_service):
        \"\"\"Test that generation metrics are tracked.\"\"\"
        await tts_service.initialize()
        
        # Mock MCP call
        with patch.object(tts_service, '_call_mcp_tool', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = {
                \"success\": True,
                \"audio_data\": b'mock_audio'
            }
            
            await tts_service._generate_speech(\"Test text\")
            
            # Check metrics were updated
            assert tts_service.generation_count == 1
            assert tts_service.total_characters > 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_health_check(self, tts_service):
        \"\"\"Test health check functionality.\"\"\"
        # Unhealthy before initialization
        assert await tts_service.health_check() is False
        
        # Healthy after initialization
        await tts_service.initialize()
        assert await tts_service.health_check() is True
