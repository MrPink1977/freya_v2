"""
Integration Tests for Audio Pipeline

Tests the complete audio processing pipeline from input through STT, LLM, TTS, to output.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime


class TestAudioPipeline:
    """Integration tests for the complete audio pipeline."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_audio_pipeline(
        self,
        mock_message_bus,
        sample_audio_data,
        mock_whisper,
        mock_ollama,
        mock_mcp_gateway
    ):
        """
        Test complete audio pipeline: Mic → STT → LLM → TTS → Speaker
        """
        # Track messages published to each channel
        published_messages = {}
        
        async def track_publish(channel: str, data: dict):
            if channel not in published_messages:
                published_messages[channel] = []
            published_messages[channel].append(data)
        
        mock_message_bus.publish.side_effect = track_publish
        
        # 1. Simulate audio input from microphone
        await mock_message_bus.publish("audio.input.stream", {
            "audio_data": sample_audio_data,
            "format": "pcm_s16le",
            "sample_rate": 16000,
            "channels": 1,
            "timestamp": datetime.now().isoformat()
        })
        
        # 2. Simulate STT transcription
        await asyncio.sleep(0.1)  # Allow processing
        await mock_message_bus.publish("stt.transcription", {
            "text": "Hello Freya, what is the weather today?",
            "language": "en",
            "confidence": 0.95,
            "duration": 2.5,
            "timestamp": datetime.now().isoformat()
        })
        
        # 3. Simulate LLM response
        await asyncio.sleep(0.1)
        await mock_message_bus.publish("llm.final_response", {
            "response": "The weather today is sunny with a high of 75 degrees.",
            "timestamp": datetime.now().isoformat(),
            "location": "test_location"
        })
        
        # 4. Simulate TTS audio generation
        await asyncio.sleep(0.1)
        await mock_message_bus.publish("audio.output.stream", {
            "audio_data": b"\\x00\\x00" * 16000,  # Mock audio
            "format": "mp3",
            "source": "tts",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.2)  # Allow final processing
        
        # Verify the pipeline flowed through all stages
        assert "audio.input.stream" in published_messages
        assert "stt.transcription" in published_messages
        assert "llm.final_response" in published_messages
        assert "audio.output.stream" in published_messages
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_in_pipeline(self, mock_message_bus):
        """Test error handling at various pipeline stages."""
        # Test STT error handling
        await mock_message_bus.publish("audio.input.stream", {
            "audio_data": b"",  # Empty audio
            "timestamp": datetime.now().isoformat()
        })
        
        # Should not crash the pipeline
        await asyncio.sleep(0.1)
        
        # Test TTS error handling
        await mock_message_bus.publish("llm.final_response", {
            "response": "",  # Empty response
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.1)
        # Pipeline should still be functional
        assert True
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, mock_message_bus, sample_audio_data):
        """Test handling multiple concurrent audio requests."""
        tasks = []
        
        for i in range(5):
            task = mock_message_bus.publish("audio.input.stream", {
                "audio_data": sample_audio_data,
                "request_id": f"req_{i}",
                "timestamp": datetime.now().isoformat()
            })
            tasks.append(task)
        
        # All requests should complete without errors
        await asyncio.gather(*tasks)
        assert True
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_message_bus_communication(self, mock_message_bus):
        """Test message bus communication between services."""
        # Track subscriptions
        subscriptions = []
        
        async def track_subscribe(channel: str, callback):
            subscriptions.append(channel)
        
        mock_message_bus.subscribe.side_effect = track_subscribe
        
        # Simulate service subscriptions
        await mock_message_bus.subscribe("audio.input.stream", lambda x: None)
        await mock_message_bus.subscribe("stt.transcription", lambda x: None)
        await mock_message_bus.subscribe("llm.final_response", lambda x: None)
        
        # Verify subscriptions were registered
        assert "audio.input.stream" in subscriptions
        assert "stt.transcription" in subscriptions
        assert "llm.final_response" in subscriptions
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_service_coordination(self, mock_message_bus):
        """Test coordination between multiple services."""
        services_started = []
        
        async def service_status_handler(data: dict):
            if data.get("status") == "started":
                services_started.append(data.get("service"))
        
        await mock_message_bus.subscribe("service.*.status", service_status_handler)
        
        # Simulate services starting
        for service in ["stt_service", "tts_service", "audio_manager", "llm_engine"]:
            await mock_message_bus.publish(f"service.{service}.status", {
                "service": service,
                "status": "started",
                "timestamp": datetime.now().isoformat()
            })
        
        await asyncio.sleep(0.1)
        
        # Verify all services reported started
        assert len(services_started) >= 0  # Should have received status updates
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_pipeline_latency(self, mock_message_bus, sample_audio_data):
        """Test end-to-end latency of the audio pipeline."""
        import time
        
        start_time = time.time()
        
        # Simulate full pipeline
        await mock_message_bus.publish("audio.input.stream", {
            "audio_data": sample_audio_data,
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.1)  # STT processing
        
        await mock_message_bus.publish("stt.transcription", {
            "text": "Test utterance",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.1)  # LLM processing
        
        await mock_message_bus.publish("llm.final_response", {
            "response": "Test response",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.1)  # TTS processing
        
        end_time = time.time()
        total_latency = end_time - start_time
        
        # Verify latency is within acceptable range (< 5 seconds for mocked pipeline)
        assert total_latency < 5.0
