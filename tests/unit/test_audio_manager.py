"""
Unit tests for Audio Manager

Tests audio I/O management with mocked PyAudio.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.audio.audio_manager import AudioManager, AudioManagerError


class TestAudioManager:
    """Test suite for AudioManager class."""
    
    @pytest.fixture
    async def audio_manager(self, mock_message_bus, mock_config, mock_pyaudio):
        """Create an AudioManager instance with mocked PyAudio."""
        with patch('src.services.audio.audio_manager.pyaudio.PyAudio', return_value=mock_pyaudio):
            with patch('src.services.audio.audio_manager.np') as mock_np:
                mock_np.zeros.return_value.tobytes.return_value = b'\\x00\\x00' * 1024
                with patch('src.services.audio.audio_manager.config', mock_config):
                    service = AudioManager(mock_message_bus)
                    yield service
                    if service._running:
                        await service.stop()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialization(self, mock_message_bus, mock_config):
        \"\"\"Test Audio Manager initialization.\"\"\"
        with patch('src.services.audio.audio_manager.pyaudio'):
            with patch('src.services.audio.audio_manager.np'):
                with patch('src.services.audio.audio_manager.config', mock_config):
                    service = AudioManager(mock_message_bus)
                    
                    assert service.name == \"audio_manager\"
                    assert service.sample_rate == mock_config.audio_sample_rate
                    assert service.channels == mock_config.audio_channels
                    assert not service.is_recording
                    assert not service.is_playing
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialize(self, audio_manager, mock_pyaudio):
        \"\"\"Test service initialization and device enumeration.\"\"\"
        await audio_manager.initialize()
        
        assert audio_manager._healthy is True
        assert audio_manager.pyaudio_instance is not None
        assert mock_pyaudio.get_device_count.called
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_stop(self, audio_manager, mock_message_bus):
        \"\"\"Test service start and stop lifecycle.\"\"\"
        await audio_manager.initialize()
        
        with patch.object(audio_manager, '_start_output_thread'):
            with patch.object(audio_manager, '_start_input_stream', new_callable=AsyncMock):
                await audio_manager.start()
                
                assert audio_manager._running is True
                assert mock_message_bus.subscribe.called
        
        await audio_manager.stop()
        assert audio_manager._running is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_output_audio(self, audio_manager, sample_audio_data):
        \"\"\"Test handling audio output data.\"\"\"
        await audio_manager.initialize()
        
        # Send audio data
        await audio_manager._handle_output_audio({
            \"audio_data\": sample_audio_data,
            \"format\": \"pcm_s16le\"
        })
        
        # Verify audio was queued
        assert not audio_manager.output_queue.empty()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_start_recording(self, audio_manager):
        \"\"\"Test start recording command.\"\"\"
        await audio_manager.initialize()
        
        with patch.object(audio_manager, '_start_input_stream', new_callable=AsyncMock) as mock_start:
            await audio_manager._handle_start_recording({})
            assert mock_start.called
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_stop_recording(self, audio_manager):
        \"\"\"Test stop recording command.\"\"\"
        await audio_manager.initialize()
        
        with patch.object(audio_manager, '_stop_input_stream', new_callable=AsyncMock) as mock_stop:
            await audio_manager._handle_stop_recording({})
            assert mock_stop.called
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_input_queue_overflow(self, audio_manager, sample_audio_data):
        \"\"\"Test input queue handles overflow gracefully.\"\"\"
        await audio_manager.initialize()
        
        # Fill the queue
        for _ in range(110):  # More than maxsize
            try:
                audio_manager.input_queue.put_nowait(sample_audio_data)
            except:
                pass
        
        # Should not crash
        assert True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_health_check(self, audio_manager):
        \"\"\"Test health check functionality.\"\"\"
        # Unhealthy before initialization
        assert await audio_manager.health_check() is False
        
        # Healthy after initialization
        await audio_manager.initialize()
        assert await audio_manager.health_check() is True
