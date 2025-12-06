"""
Unit tests for LLMEngine

Tests the LLM Engine service including initialization, message handling,
tool integration, and response generation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.llm.llm_engine import LLMEngine, LLMEngineError
from src.core.config import config


class TestLLMEngine:
    """Test suite for LLMEngine class."""
    
    @pytest.fixture
    async def llm_engine(self, mock_message_bus):
        """Create an LLMEngine instance with mocked dependencies."""
        engine = LLMEngine(mock_message_bus)
        yield engine
        if engine._running:
            await engine.stop()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialization(self, mock_message_bus):
        """Test LLMEngine initialization."""
        engine = LLMEngine(mock_message_bus)
        
        assert engine.name == "llm_engine"
        assert engine.message_bus == mock_message_bus
        assert engine.client is None
        assert engine.conversation_history == []
        assert engine.system_prompt is not None
        assert engine.max_history_length == config.memory_max_short_term
        assert engine._generation_count == 0
        assert engine._total_tokens == 0
        assert engine.available_tools == {}
        assert engine.tool_call_count == 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_system_prompt_building(self, mock_message_bus):
        """Test system prompt generation with different personalities."""
        engine = LLMEngine(mock_message_bus)
        
        prompt = engine._build_system_prompt()
        
        assert config.personality_name in prompt
        assert "AI assistant" in prompt
        assert "capabilities" in prompt.lower()
        assert len(prompt) > 100
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialize_success(self, llm_engine):
        """Test successful Ollama client initialization."""
        mock_client = AsyncMock()
        mock_client.list = AsyncMock(return_value=[])
        mock_client.pull = AsyncMock()
        
        with patch('ollama.AsyncClient', return_value=mock_client):
            await llm_engine.initialize()
            
            assert llm_engine.client is not None
            mock_client.list.assert_called_once()
            mock_client.pull.assert_called_once_with(config.ollama_model)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialize_connection_timeout(self, llm_engine):
        """Test initialization failure due to connection timeout."""
        mock_client = AsyncMock()
        mock_client.list = AsyncMock(side_effect=asyncio.TimeoutError())
        
        with patch('ollama.AsyncClient', return_value=mock_client):
            with pytest.raises(LLMEngineError, match="Timeout connecting to Ollama"):
                await llm_engine.initialize()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialize_model_pull_failure(self, llm_engine):
        """Test initialization failure during model pull."""
        mock_client = AsyncMock()
        mock_client.list = AsyncMock(return_value=[])
        mock_client.pull = AsyncMock(side_effect=Exception("Model not found"))
        
        with patch('ollama.AsyncClient', return_value=mock_client):
            with pytest.raises(LLMEngineError, match="Failed to pull model"):
                await llm_engine.initialize()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_subscribes_to_channels(self, llm_engine, mock_message_bus):
        """Test that start() subscribes to required channels."""
        await llm_engine.start()
        
        assert llm_engine._running is True
        
        subscribe_calls = [call[0][0] for call in mock_message_bus.subscribe.call_args_list]
        assert "stt.transcription" in subscribe_calls
        assert "mcp.tool.result" in subscribe_calls
        assert "memory.query.result" in subscribe_calls
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stop_cleanup(self, llm_engine):
        """Test service cleanup on stop."""
        await llm_engine.start()
        await llm_engine.stop()
        
        assert llm_engine._running is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_transcription_valid_message(self, llm_engine, mock_message_bus):
        """Test handling a valid transcription message."""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'message': {'content': 'Test response'},
            'done': True
        })
        llm_engine.client = mock_client
        
        test_message = {
            'text': 'Hello Freya',
            'location': 'living_room',
            'timestamp': '2025-12-05T10:00:00',
            'confidence': 0.95
        }
        
        await llm_engine._handle_transcription(test_message)
        
        mock_client.chat.assert_called_once()
        mock_message_bus.publish.assert_called()
        
        publish_calls = [call[0][0] for call in mock_message_bus.publish.call_args_list]
        assert "llm.response" in publish_calls
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_transcription_empty_text(self, llm_engine, mock_message_bus):
        """Test handling transcription with empty text."""
        test_message = {
            'text': '',
            'location': 'bedroom',
            'timestamp': '2025-12-05T10:00:00'
        }
        
        await llm_engine._handle_transcription(test_message)
        
        mock_message_bus.publish.assert_not_called()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_basic(self, llm_engine):
        """Test basic response generation."""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'message': {'content': 'Generated response'},
            'done': True,
            'eval_count': 50
        })
        llm_engine.client = mock_client
        
        response = await llm_engine._generate_response(
            user_message="Test input",
            location="kitchen"
        )
        
        assert response == "Generated response"
        assert llm_engine._generation_count == 1
        assert llm_engine._total_tokens == 50
        mock_client.chat.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_response_with_tools(self, llm_engine):
        """Test response generation with tool calling."""
        mock_client = AsyncMock()
        
        mock_client.chat = AsyncMock(side_effect=[
            {
                'message': {
                    'content': '',
                    'tool_calls': [{
                        'function': {
                            'name': 'get_weather',
                            'arguments': '{"location": "Seattle"}'
                        }
                    }]
                },
                'done': True
            },
            {
                'message': {'content': 'The weather is sunny'},
                'done': True,
                'eval_count': 30
            }
        ])
        
        llm_engine.client = mock_client
        llm_engine.available_tools = {
            'get_weather': {
                'name': 'get_weather',
                'description': 'Get weather information'
            }
        }
        
        with patch.object(llm_engine, '_execute_tool_call', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "Sunny, 72°F"
            
            response = await llm_engine._generate_response(
                user_message="What's the weather?",
                location="office"
            )
            
            assert response == "The weather is sunny"
            assert llm_engine.tool_call_count == 1
            mock_execute.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_conversation_history_management(self, llm_engine):
        """Test conversation history is properly maintained."""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'message': {'content': 'Response'},
            'done': True
        })
        llm_engine.client = mock_client
        
        for i in range(llm_engine.max_history_length + 5):
            await llm_engine._generate_response(
                user_message=f"Message {i}",
                location="bedroom"
            )
        
        assert len(llm_engine.conversation_history) <= llm_engine.max_history_length * 2
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_tool_result(self, llm_engine):
        """Test handling tool execution results."""
        tool_result = {
            'tool_call_id': 'test-123',
            'result': 'Tool execution successful',
            'success': True
        }
        
        llm_engine._pending_tool_results['test-123'] = asyncio.Future()
        
        await llm_engine._handle_tool_result(tool_result)
        
        assert llm_engine._pending_tool_results['test-123'].done()
        assert llm_engine._pending_tool_results['test-123'].result() == 'Tool execution successful'
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_register_tools(self, llm_engine):
        """Test tool registration."""
        tools_message = {
            'tools': [
                {
                    'name': 'calculator',
                    'description': 'Perform calculations',
                    'parameters': {}
                },
                {
                    'name': 'web_search',
                    'description': 'Search the web',
                    'parameters': {}
                }
            ]
        }
        
        await llm_engine._handle_tool_discovery(tools_message)
        
        assert 'calculator' in llm_engine.available_tools
        assert 'web_search' in llm_engine.available_tools
        assert len(llm_engine.available_tools) == 2
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_handling_in_generation(self, llm_engine, mock_message_bus):
        """Test error handling during response generation."""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(side_effect=Exception("LLM error"))
        llm_engine.client = mock_client
        
        with pytest.raises(LLMEngineError, match="Failed to generate response"):
            await llm_engine._generate_response(
                user_message="Test",
                location="office"
            )
        
        assert llm_engine._error_count > 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_metrics_tracking(self, llm_engine):
        """Test that metrics are properly tracked."""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'message': {'content': 'Response'},
            'done': True,
            'eval_count': 100
        })
        llm_engine.client = mock_client
        
        initial_count = llm_engine._generation_count
        initial_tokens = llm_engine._total_tokens
        
        await llm_engine._generate_response("Test", "bedroom")
        
        assert llm_engine._generation_count == initial_count + 1
        assert llm_engine._total_tokens == initial_tokens + 100
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_location_awareness(self, llm_engine):
        """Test that location context is included in prompts."""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value={
            'message': {'content': 'Response'},
            'done': True
        })
        llm_engine.client = mock_client
        
        await llm_engine._generate_response(
            user_message="Turn on the lights",
            location="kitchen"
        )
        
        call_args = mock_client.chat.call_args
        messages = call_args[1]['messages']
        
        location_mentioned = any('kitchen' in str(msg).lower() for msg in messages)
        assert location_mentioned