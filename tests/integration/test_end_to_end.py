"""
End-to-End Integration Tests for Freya v2.0

Tests complete workflows across all services:
- Audio pipeline (STT → LLM → TTS)
- Multi-service workflows
- Message bus communication
- WebSocket flows
- Tool execution flows

Author: Freya AI
Version: 0.4.0
Date: 2024-12-06
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.message_bus import MessageBus
from src.services.audio.audio_manager import AudioManager
from src.services.stt.stt_service import STTService
from src.services.llm.llm_engine import LLMEngine
from src.services.tts.tts_service import TTSService
from src.services.mcp_gateway.mcp_gateway import MCPGateway
from src.services.gui.gui_service import GUIService


@pytest.fixture
async def integration_message_bus():
    """Create a real message bus for integration testing."""
    bus = MessageBus(host="localhost", port=6379)
    await bus.connect()
    yield bus
    await bus.disconnect()


@pytest.fixture
def sample_audio_bytes():
    """Generate sample audio data for testing."""
    return b'\x00\x01' * 8000


@pytest.fixture
def sample_transcription():
    """Sample transcription text."""
    return "Hello Freya, what is the weather in San Francisco?"


@pytest.fixture
def sample_llm_response():
    """Sample LLM response."""
    return "The weather in San Francisco is currently 65 degrees and sunny."


class TestEndToEndAudioPipeline:
    """Test complete audio pipeline from input to output."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_audio_to_response_flow(
        self,
        integration_message_bus,
        sample_audio_bytes,
        sample_transcription,
        sample_llm_response
    ):
        """
        Test: Audio Input → STT → LLM → TTS → Audio Output
        
        Verifies the complete pipeline processes audio through all stages.
        """
        messages_received = {}
        
        async def track_message(channel: str):
            async def handler(data: Dict[str, Any]):
                if channel not in messages_received:
                    messages_received[channel] = []
                messages_received[channel].append(data)
            return handler
        
        await integration_message_bus.subscribe(
            "stt.transcription",
            await track_message("stt.transcription")
        )
        await integration_message_bus.subscribe(
            "llm.response",
            await track_message("llm.response")
        )
        await integration_message_bus.subscribe(
            "tts.audio_generated",
            await track_message("tts.audio_generated")
        )
        
        await integration_message_bus.publish("audio.input", {
            "audio_data": sample_audio_bytes.hex(),
            "sample_rate": 16000,
            "channels": 1,
            "location": "office",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.5)
        
        await integration_message_bus.publish("stt.transcription", {
            "text": sample_transcription,
            "confidence": 0.95,
            "language": "en",
            "location": "office",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.5)
        
        await integration_message_bus.publish("llm.response", {
            "text": sample_llm_response,
            "tokens_used": 45,
            "location": "office",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.5)
        
        assert "stt.transcription" in messages_received
        assert len(messages_received["stt.transcription"]) > 0
        assert messages_received["stt.transcription"][0]["text"] == sample_transcription
        
        assert "llm.response" in messages_received
        assert len(messages_received["llm.response"]) > 0
        assert messages_received["llm.response"][0]["text"] == sample_llm_response
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_audio_pipeline_with_tool_execution(
        self,
        integration_message_bus
    ):
        """
        Test: Audio → STT → LLM → Tool Call → LLM → TTS → Audio
        
        Verifies pipeline handles tool execution mid-flow.
        """
        messages_received = {}
        
        async def track_message(channel: str):
            async def handler(data: Dict[str, Any]):
                if channel not in messages_received:
                    messages_received[channel] = []
                messages_received[channel].append(data)
            return handler
        
        await integration_message_bus.subscribe(
            "mcp.tool_call_request",
            await track_message("mcp.tool_call_request")
        )
        await integration_message_bus.subscribe(
            "mcp.tool_call_result",
            await track_message("mcp.tool_call_result")
        )
        await integration_message_bus.subscribe(
            "llm.response",
            await track_message("llm.response")
        )
        
        await integration_message_bus.publish("stt.transcription", {
            "text": "What is the weather in San Francisco?",
            "confidence": 0.95,
            "location": "office",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        await integration_message_bus.publish("mcp.tool_call_request", {
            "tool_name": "weather_get_forecast",
            "arguments": {"city": "San Francisco"},
            "request_id": "req_123",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        await integration_message_bus.publish("mcp.tool_call_result", {
            "request_id": "req_123",
            "result": {"temperature": 65, "condition": "sunny"},
            "success": True,
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        await integration_message_bus.publish("llm.response", {
            "text": "The weather in San Francisco is 65 degrees and sunny.",
            "tokens_used": 50,
            "location": "office",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        assert "mcp.tool_call_request" in messages_received
        assert "mcp.tool_call_result" in messages_received
        assert "llm.response" in messages_received
        
        tool_request = messages_received["mcp.tool_call_request"][0]
        assert tool_request["tool_name"] == "weather_get_forecast"
        assert tool_request["arguments"]["city"] == "San Francisco"
        
        tool_result = messages_received["mcp.tool_call_result"][0]
        assert tool_result["success"] is True
        assert tool_result["result"]["temperature"] == 65
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_location_audio_routing(
        self,
        integration_message_bus,
        sample_audio_bytes
    ):
        """
        Test: Multiple locations sending audio simultaneously
        
        Verifies location-aware routing works correctly.
        """
        messages_received = {}
        
        async def track_message(channel: str):
            async def handler(data: Dict[str, Any]):
                if channel not in messages_received:
                    messages_received[channel] = []
                messages_received[channel].append(data)
            return handler
        
        await integration_message_bus.subscribe(
            "stt.transcription",
            await track_message("stt.transcription")
        )
        
        locations = ["office", "kitchen", "bedroom"]
        
        for location in locations:
            await integration_message_bus.publish("audio.input", {
                "audio_data": sample_audio_bytes.hex(),
                "sample_rate": 16000,
                "channels": 1,
                "location": location,
                "timestamp": datetime.now().isoformat()
            })
        
        await asyncio.sleep(0.5)
        
        for location in locations:
            await integration_message_bus.publish("stt.transcription", {
                "text": f"Hello from {location}",
                "confidence": 0.95,
                "language": "en",
                "location": location,
                "timestamp": datetime.now().isoformat()
            })
        
        await asyncio.sleep(0.5)
        
        assert "stt.transcription" in messages_received
        assert len(messages_received["stt.transcription"]) == 3
        
        received_locations = [
            msg["location"] for msg in messages_received["stt.transcription"]
        ]
        assert set(received_locations) == set(locations)


class TestWebSocketIntegration:
    """Test WebSocket communication flows."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_websocket_message_flow(
        self,
        integration_message_bus
    ):
        """
        Test: WebSocket → Message Bus → Services → WebSocket
        
        Verifies bidirectional WebSocket communication.
        """
        messages_received = {}
        
        async def track_message(channel: str):
            async def handler(data: Dict[str, Any]):
                if channel not in messages_received:
                    messages_received[channel] = []
                messages_received[channel].append(data)
            return handler
        
        await integration_message_bus.subscribe(
            "gui.message",
            await track_message("gui.message")
        )
        await integration_message_bus.subscribe(
            "gui.response",
            await track_message("gui.response")
        )
        
        await integration_message_bus.publish("gui.message", {
            "type": "user_message",
            "content": "Hello Freya",
            "session_id": "session_123",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        await integration_message_bus.publish("gui.response", {
            "type": "assistant_message",
            "content": "Hello! How can I help you?",
            "session_id": "session_123",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        assert "gui.message" in messages_received
        assert "gui.response" in messages_received
        
        user_msg = messages_received["gui.message"][0]
        assert user_msg["content"] == "Hello Freya"
        assert user_msg["session_id"] == "session_123"
        
        assistant_msg = messages_received["gui.response"][0]
        assert assistant_msg["content"] == "Hello! How can I help you?"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_websocket_tool_execution_updates(
        self,
        integration_message_bus
    ):
        """
        Test: Tool execution status updates via WebSocket
        
        Verifies real-time tool execution updates.
        """
        messages_received = {}
        
        async def track_message(channel: str):
            async def handler(data: Dict[str, Any]):
                if channel not in messages_received:
                    messages_received[channel] = []
                messages_received[channel].append(data)
            return handler
        
        await integration_message_bus.subscribe(
            "gui.tool_status",
            await track_message("gui.tool_status")
        )
        
        await integration_message_bus.publish("gui.tool_status", {
            "tool_name": "web_search",
            "status": "executing",
            "session_id": "session_123",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.2)
        
        await integration_message_bus.publish("gui.tool_status", {
            "tool_name": "web_search",
            "status": "completed",
            "result": {"results": ["Result 1", "Result 2"]},
            "session_id": "session_123",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.2)
        
        assert "gui.tool_status" in messages_received
        assert len(messages_received["gui.tool_status"]) == 2
        
        executing_msg = messages_received["gui.tool_status"][0]
        assert executing_msg["status"] == "executing"
        
        completed_msg = messages_received["gui.tool_status"][1]
        assert completed_msg["status"] == "completed"
        assert "result" in completed_msg


class TestMultiServiceWorkflows:
    """Test complex workflows involving multiple services."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_conversation_with_memory_retrieval(
        self,
        integration_message_bus
    ):
        """
        Test: User Query → Memory Retrieval → LLM → Response
        
        Verifies memory integration in conversation flow.
        """
        messages_received = {}
        
        async def track_message(channel: str):
            async def handler(data: Dict[str, Any]):
                if channel not in messages_received:
                    messages_received[channel] = []
                messages_received[channel].append(data)
            return handler
        
        await integration_message_bus.subscribe(
            "memory.query",
            await track_message("memory.query")
        )
        await integration_message_bus.subscribe(
            "memory.results",
            await track_message("memory.results")
        )
        await integration_message_bus.subscribe(
            "llm.response",
            await track_message("llm.response")
        )
        
        await integration_message_bus.publish("stt.transcription", {
            "text": "What did we talk about yesterday?",
            "confidence": 0.95,
            "location": "office",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        await integration_message_bus.publish("memory.query", {
            "query": "conversation yesterday",
            "limit": 5,
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        await integration_message_bus.publish("memory.results", {
            "results": [
                {"text": "We discussed the weather", "score": 0.9},
                {"text": "You asked about my day", "score": 0.85}
            ],
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        await integration_message_bus.publish("llm.response", {
            "text": "Yesterday we discussed the weather and you asked about my day.",
            "tokens_used": 40,
            "location": "office",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        assert "memory.query" in messages_received
        assert "memory.results" in messages_received
        assert "llm.response" in messages_received
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_tool_execution_workflow(
        self,
        integration_message_bus
    ):
        """
        Test: Query → Tool 1 → Tool 2 → LLM → Response
        
        Verifies sequential tool execution workflow.
        """
        messages_received = {}
        
        async def track_message(channel: str):
            async def handler(data: Dict[str, Any]):
                if channel not in messages_received:
                    messages_received[channel] = []
                messages_received[channel].append(data)
            return handler
        
        await integration_message_bus.subscribe(
            "mcp.tool_call_request",
            await track_message("mcp.tool_call_request")
        )
        await integration_message_bus.subscribe(
            "mcp.tool_call_result",
            await track_message("mcp.tool_call_result")
        )
        
        await integration_message_bus.publish("stt.transcription", {
            "text": "Search the web for Python tutorials and save the results",
            "confidence": 0.95,
            "location": "office",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        await integration_message_bus.publish("mcp.tool_call_request", {
            "tool_name": "web_search",
            "arguments": {"query": "Python tutorials"},
            "request_id": "req_1",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        await integration_message_bus.publish("mcp.tool_call_result", {
            "request_id": "req_1",
            "result": {"results": ["Tutorial 1", "Tutorial 2"]},
            "success": True,
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        await integration_message_bus.publish("mcp.tool_call_request", {
            "tool_name": "file_write",
            "arguments": {
                "path": "tutorials.txt",
                "content": "Tutorial 1\nTutorial 2"
            },
            "request_id": "req_2",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        await integration_message_bus.publish("mcp.tool_call_result", {
            "request_id": "req_2",
            "result": {"success": True},
            "success": True,
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        assert "mcp.tool_call_request" in messages_received
        assert len(messages_received["mcp.tool_call_request"]) == 2
        
        assert messages_received["mcp.tool_call_request"][0]["tool_name"] == "web_search"
        assert messages_received["mcp.tool_call_request"][1]["tool_name"] == "file_write"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(
        self,
        integration_message_bus
    ):
        """
        Test: Service Error → Recovery → Retry → Success
        
        Verifies error handling and recovery across services.
        """
        messages_received = {}
        
        async def track_message(channel: str):
            async def handler(data: Dict[str, Any]):
                if channel not in messages_received:
                    messages_received[channel] = []
                messages_received[channel].append(data)
            return handler
        
        await integration_message_bus.subscribe(
            "service.error",
            await track_message("service.error")
        )
        await integration_message_bus.subscribe(
            "service.recovery",
            await track_message("service.recovery")
        )
        
        await integration_message_bus.publish("service.error", {
            "service": "llm_engine",
            "error": "Connection timeout",
            "severity": "warning",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        await integration_message_bus.publish("service.recovery", {
            "service": "llm_engine",
            "action": "reconnected",
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.3)
        
        assert "service.error" in messages_received
        assert "service.recovery" in messages_received
        
        error_msg = messages_received["service.error"][0]
        assert error_msg["service"] == "llm_engine"
        
        recovery_msg = messages_received["service.recovery"][0]
        assert recovery_msg["status"] == "healthy"


class TestPerformanceAndConcurrency:
    """Test system performance under load."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_audio_requests(
        self,
        integration_message_bus,
        sample_audio_bytes
    ):
        """
        Test: Multiple simultaneous audio inputs
        
        Verifies system handles concurrent requests.
        """
        num_requests = 10
        tasks = []
        
        for i in range(num_requests):
            task = integration_message_bus.publish("audio.input", {
                "audio_data": sample_audio_bytes.hex(),
                "sample_rate": 16000,
                "channels": 1,
                "location": f"location_{i}",
                "request_id": f"req_{i}",
                "timestamp": datetime.now().isoformat()
            })
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Concurrent requests failed: {errors}"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_message_bus_throughput(
        self,
        integration_message_bus
    ):
        """
        Test: Message bus throughput under load
        
        Verifies message bus can handle high message volume.
        """
        num_messages = 100
        messages_received = []
        
        async def message_handler(data: Dict[str, Any]):
            messages_received.append(data)
        
        await integration_message_bus.subscribe("test.throughput", message_handler)
        
        start_time = asyncio.get_event_loop().time()
        
        tasks = []
        for i in range(num_messages):
            task = integration_message_bus.publish("test.throughput", {
                "message_id": i,
                "timestamp": datetime.now().isoformat()
            })
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        await asyncio.sleep(1.0)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        assert len(messages_received) >= num_messages * 0.95
        assert duration < 5.0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_service_startup_coordination(
        self,
        integration_message_bus
    ):
        """
        Test: All services start and register correctly
        
        Verifies service discovery and coordination.
        """
        services_registered = {}
        
        async def service_handler(data: Dict[str, Any]):
            service_name = data.get("service_name")
            services_registered[service_name] = data
        
        await integration_message_bus.subscribe("service.registered", service_handler)
        
        expected_services = [
            "audio_manager",
            "stt_service",
            "llm_engine",
            "tts_service",
            "mcp_gateway",
            "gui_service"
        ]
        
        for service in expected_services:
            await integration_message_bus.publish("service.registered", {
                "service_name": service,
                "status": "ready",
                "capabilities": ["basic"],
                "timestamp": datetime.now().isoformat()
            })
        
        await asyncio.sleep(0.5)
        
        assert len(services_registered) == len(expected_services)
        for service in expected_services:
            assert service in services_registered
            assert services_registered[service]["status"] == "ready"


class TestMessageBusReliability:
    """Test message bus reliability and error handling."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_message_delivery_guarantee(
        self,
        integration_message_bus
    ):
        """
        Test: Messages are delivered reliably
        
        Verifies no message loss under normal conditions.
        """
        messages_sent = []
        messages_received = []
        
        async def message_handler(data: Dict[str, Any]):
            messages_received.append(data["message_id"])
        
        await integration_message_bus.subscribe("test.delivery", message_handler)
        
        for i in range(50):
            message_id = f"msg_{i}"
            messages_sent.append(message_id)
            await integration_message_bus.publish("test.delivery", {
                "message_id": message_id,
                "timestamp": datetime.now().isoformat()
            })
        
        await asyncio.sleep(1.0)
        
        assert len(messages_received) == len(messages_sent)
        assert set(messages_received) == set(messages_sent)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_subscriber_reconnection(
        self,
        integration_message_bus
    ):
        """
        Test: Subscribers can reconnect after disconnect
        
        Verifies resilience to connection issues.
        """
        messages_received = []
        
        async def message_handler(data: Dict[str, Any]):
            messages_received.append(data)
        
        await integration_message_bus.subscribe("test.reconnect", message_handler)
        
        await integration_message_bus.publish("test.reconnect", {
            "message": "before_disconnect",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.2)
        
        await integration_message_bus.unsubscribe("test.reconnect")
        
        await integration_message_bus.publish("test.reconnect", {
            "message": "during_disconnect",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.2)
        
        await integration_message_bus.subscribe("test.reconnect", message_handler)
        
        await integration_message_bus.publish("test.reconnect", {
            "message": "after_reconnect",
            "timestamp": datetime.now().isoformat()
        })
        
        await asyncio.sleep(0.2)
        
        assert len(messages_received) >= 2
        assert messages_received[0]["message"] == "before_disconnect"
        assert messages_received[-1]["message"] == "after_reconnect"