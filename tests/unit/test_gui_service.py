"""
Unit tests for GUIService

Tests the GUI Service including FastAPI endpoints, WebSocket connections,
authentication, rate limiting, session management, and message bus integration.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import WebSocket
from src.services.gui.gui_service import GUIService, GUIServiceError
from src.services.gui.models import APIResponse, SystemStatus, ServiceStatus
from src.core.config import config


class TestGUIService:
    """Test suite for GUIService class."""
    
    @pytest.fixture
    async def gui_service(self, mock_message_bus):
        """Create a GUIService instance with mocked dependencies."""
        with patch('src.services.gui.gui_service.config') as mock_config:
            mock_config.gui_jwt_secret = "test-secret-key-min-32-characters-long"
            mock_config.gui_token_expiry = 3600
            mock_config.gui_max_sessions = 100
            mock_config.gui_session_timeout = 3600
            mock_config.gui_rate_limit_rate = 10.0
            mock_config.gui_rate_limit_burst = 20
            mock_config.gui_cors_origins = ["http://localhost:5173"]
            mock_config.gui_enabled = True
            mock_config.gui_host = "0.0.0.0"
            mock_config.gui_port = 8000
            
            service = GUIService(mock_message_bus)
            yield service
            
            if service._running:
                await service.stop()
    
    @pytest.fixture
    def test_client(self, gui_service):
        """Create a FastAPI TestClient for HTTP endpoint testing."""
        return TestClient(gui_service.app)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialization(self, mock_message_bus):
        """Test GUIService initialization."""
        with patch('src.services.gui.gui_service.config') as mock_config:
            mock_config.gui_jwt_secret = "test-secret-key-min-32-characters-long"
            mock_config.gui_token_expiry = 3600
            mock_config.gui_max_sessions = 100
            mock_config.gui_session_timeout = 3600
            mock_config.gui_rate_limit_rate = 10.0
            mock_config.gui_rate_limit_burst = 20
            mock_config.gui_cors_origins = ["http://localhost:5173"]
            
            service = GUIService(mock_message_bus)
            
            assert service.name == "gui_service"
            assert service.message_bus == mock_message_bus
            assert service.app is not None
            assert service.ws_manager is not None
            assert service.token_manager is not None
            assert service.session_manager is not None
            assert service.rate_limiter is not None
            assert service.service_statuses == {}
            assert service.chat_history == []
            assert service.tool_history == []
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialize_success(self, gui_service):
        """Test successful service initialization."""
        with patch.object(gui_service.ws_manager, 'start_broadcasting', new_callable=AsyncMock):
            with patch.object(gui_service.session_manager, 'start_cleanup_task', new_callable=AsyncMock):
                with patch.object(gui_service.rate_limiter, 'start_cleanup_task', new_callable=AsyncMock):
                    await gui_service.initialize()
                    
                    assert gui_service._healthy is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialize_failure(self, gui_service):
        """Test initialization failure handling."""
        with patch.object(gui_service.ws_manager, 'start_broadcasting', side_effect=Exception("Broadcast error")):
            with pytest.raises(GUIServiceError, match="Initialization failed"):
                await gui_service.initialize()
            
            assert gui_service._healthy is False
            assert gui_service._error_count > 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_subscribes_to_channels(self, gui_service, mock_message_bus):
        """Test that start() subscribes to required message bus channels."""
        with patch.object(gui_service, '_server_task', None):
            with patch('uvicorn.Server') as mock_server:
                mock_server_instance = AsyncMock()
                mock_server.return_value = mock_server_instance
                
                await gui_service.start()
                
                assert gui_service._running is True
                
                subscribe_calls = [call[0][0] for call in mock_message_bus.subscribe.call_args_list]
                assert "service.*.status" in subscribe_calls
                assert "service.*.metrics" in subscribe_calls
                assert "mcp.tool.execute" in subscribe_calls
                assert "mcp.tool.result" in subscribe_calls
                assert "llm.final_response" in subscribe_calls
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stop_cleanup(self, gui_service):
        """Test service cleanup on stop."""
        gui_service._server = AsyncMock()
        gui_service._server.should_exit = False
        gui_service._server_task = AsyncMock()
        
        with patch.object(gui_service.ws_manager, 'stop_broadcasting', new_callable=AsyncMock):
            with patch.object(gui_service.session_manager, 'stop_cleanup_task', new_callable=AsyncMock):
                with patch.object(gui_service.rate_limiter, 'stop_cleanup_task', new_callable=AsyncMock):
                    await gui_service.start()
                    await gui_service.stop()
                    
                    assert gui_service._running is False
                    assert gui_service._server.should_exit is True
    
    @pytest.mark.unit
    def test_health_endpoint(self, test_client):
        """Test /api/health endpoint."""
        response = test_client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @pytest.mark.unit
    def test_create_token_endpoint(self, test_client, gui_service):
        """Test /api/auth/token endpoint for token creation."""
        with patch.object(gui_service.session_manager, 'create_session', return_value="test-session-123"):
            with patch.object(gui_service.token_manager, 'generate_token', return_value="test-jwt-token"):
                response = test_client.post("/api/auth/token")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["token"] == "test-jwt-token"
                assert data["data"]["session_id"] == "test-session-123"
                assert "expires_in" in data["data"]
    
    @pytest.mark.unit
    def test_create_token_session_limit_exceeded(self, test_client, gui_service):
        """Test token creation when session limit is exceeded."""
        with patch.object(gui_service.session_manager, 'create_session', side_effect=RuntimeError("Max sessions")):
            response = test_client.post("/api/auth/token")
            
            assert response.status_code == 503
            assert "Max sessions" in response.json()["detail"]
    
    @pytest.mark.unit
    def test_refresh_token_endpoint_success(self, test_client, gui_service):
        """Test /api/auth/refresh endpoint with valid token."""
        with patch.object(gui_service.token_manager, 'refresh_token', return_value="new-jwt-token"):
            response = test_client.post("/api/auth/refresh?token=old-token")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["token"] == "new-jwt-token"
    
    @pytest.mark.unit
    def test_refresh_token_endpoint_invalid(self, test_client, gui_service):
        """Test /api/auth/refresh endpoint with invalid token."""
        with patch.object(gui_service.token_manager, 'refresh_token', return_value=None):
            response = test_client.post("/api/auth/refresh?token=invalid-token")
            
            assert response.status_code == 401
            assert "Invalid or expired token" in response.json()["detail"]
    
    @pytest.mark.unit
    def test_status_endpoint(self, test_client, gui_service):
        """Test /api/status endpoint."""
        gui_service._start_time = datetime.now()
        gui_service._healthy = True
        gui_service._running = True
        
        response = test_client.get("/api/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "uptime" in data["data"]
        assert data["data"]["healthy"] is True
        assert data["data"]["running"] is True
    
    @pytest.mark.unit
    def test_services_endpoint(self, test_client, gui_service):
        """Test /api/services endpoint."""
        gui_service.service_statuses = {
            "llm_engine": {
                "status": "running",
                "healthy": True,
                "uptime": 3600
            },
            "audio_manager": {
                "status": "running",
                "healthy": True,
                "uptime": 3600
            }
        }
        
        response = test_client.get("/api/services")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert "llm_engine" in data["data"]
        assert "audio_manager" in data["data"]
    
    @pytest.mark.unit
    def test_conversation_endpoint(self, test_client, gui_service):
        """Test /api/conversation endpoint."""
        gui_service.chat_history = [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": "2025-12-05T10:00:00"
            },
            {
                "role": "assistant",
                "content": "Hi there!",
                "timestamp": "2025-12-05T10:00:01"
            }
        ]
        
        response = test_client.get("/api/conversation")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["role"] == "user"
        assert data["data"][1]["role"] == "assistant"
    
    @pytest.mark.unit
    def test_tools_endpoint(self, test_client, gui_service):
        """Test /api/tools endpoint."""
        gui_service.tool_history = [
            {
                "tool": "web_search",
                "arguments": {"query": "test"},
                "result": "Search results",
                "timestamp": "2025-12-05T10:00:00"
            }
        ]
        
        response = test_client.get("/api/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["tool"] == "web_search"
    
    @pytest.mark.unit
    def test_message_endpoint_success(self, test_client, gui_service, mock_message_bus):
        """Test /api/message endpoint for sending user messages."""
        response = test_client.post(
            "/api/message",
            json={
                "text": "Hello Freya",
                "location": "living_room"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        mock_message_bus.publish.assert_called_once()
        call_args = mock_message_bus.publish.call_args
        assert call_args[0][0] == "gui.user.message"
        assert call_args[0][1]["text"] == "Hello Freya"
        assert call_args[0][1]["location"] == "living_room"
    
    @pytest.mark.unit
    def test_message_endpoint_empty_text(self, test_client):
        """Test /api/message endpoint with empty text."""
        response = test_client.post(
            "/api/message",
            json={
                "text": "",
                "location": "bedroom"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_service_status(self, gui_service):
        """Test handling service status updates."""
        status_data = {
            "service": "llm_engine",
            "status": "running",
            "healthy": True,
            "uptime": 3600,
            "timestamp": "2025-12-05T10:00:00"
        }
        
        await gui_service._handle_service_status(status_data)
        
        assert "llm_engine" in gui_service.service_statuses
        assert gui_service.service_statuses["llm_engine"]["status"] == "running"
        assert gui_service.service_statuses["llm_engine"]["healthy"] is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_llm_response(self, gui_service):
        """Test handling LLM response messages."""
        response_data = {
            "text": "This is a response",
            "location": "kitchen",
            "timestamp": "2025-12-05T10:00:00"
        }
        
        await gui_service._handle_llm_response(response_data)
        
        assert len(gui_service.chat_history) == 1
        assert gui_service.chat_history[0]["role"] == "assistant"
        assert gui_service.chat_history[0]["content"] == "This is a response"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_tool_execute(self, gui_service):
        """Test handling tool execution requests."""
        tool_data = {
            "tool": "calculator",
            "arguments": {"expression": "2+2"},
            "timestamp": "2025-12-05T10:00:00"
        }
        
        await gui_service._handle_tool_execute(tool_data)
        
        assert len(gui_service.tool_history) == 1
        assert gui_service.tool_history[0]["tool"] == "calculator"
        assert gui_service.tool_history[0]["status"] == "executing"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_tool_result(self, gui_service):
        """Test handling tool execution results."""
        gui_service.tool_history = [
            {
                "tool": "calculator",
                "arguments": {"expression": "2+2"},
                "status": "executing",
                "timestamp": "2025-12-05T10:00:00"
            }
        ]
        
        result_data = {
            "tool": "calculator",
            "result": "4",
            "success": True,
            "timestamp": "2025-12-05T10:00:01"
        }
        
        await gui_service._handle_tool_result(result_data)
        
        assert gui_service.tool_history[0]["status"] == "completed"
        assert gui_service.tool_history[0]["result"] == "4"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_chat_history_limit(self, gui_service):
        """Test that chat history is limited to prevent memory issues."""
        for i in range(150):
            await gui_service._handle_llm_response({
                "text": f"Response {i}",
                "location": "bedroom",
                "timestamp": "2025-12-05T10:00:00"
            })
        
        assert len(gui_service.chat_history) <= 100
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_tool_history_limit(self, gui_service):
        """Test that tool history is limited to prevent memory issues."""
        for i in range(150):
            await gui_service._handle_tool_execute({
                "tool": f"tool_{i}",
                "arguments": {},
                "timestamp": "2025-12-05T10:00:00"
            })
        
        assert len(gui_service.tool_history) <= 100
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_websocket_authentication_success(self, gui_service):
        """Test WebSocket connection with valid authentication."""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(side_effect=["test message", asyncio.CancelledError()])
        mock_websocket.send_json = AsyncMock()
        
        with patch.object(gui_service.token_manager, 'validate_token', return_value={"session_id": "test-123"}):
            with patch.object(gui_service.session_manager, 'validate_session', return_value=True):
                with patch.object(gui_service.rate_limiter, 'check_rate_limit', return_value=True):
                    try:
                        await gui_service._handle_websocket(mock_websocket, token="valid-token")
                    except asyncio.CancelledError:
                        pass
                    
                    mock_websocket.accept.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_websocket_authentication_failure(self, gui_service):
        """Test WebSocket connection with invalid authentication."""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.close = AsyncMock()
        
        with patch.object(gui_service.token_manager, 'validate_token', return_value=None):
            await gui_service._handle_websocket(mock_websocket, token="invalid-token")
            
            mock_websocket.close.assert_called_once_with(code=1008, reason="Invalid or expired token")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_websocket_rate_limit_exceeded(self, gui_service):
        """Test WebSocket rate limiting."""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        with patch.object(gui_service.token_manager, 'validate_token', return_value={"session_id": "test-123"}):
            with patch.object(gui_service.session_manager, 'validate_session', return_value=True):
                with patch.object(gui_service.rate_limiter, 'check_rate_limit', return_value=False):
                    await gui_service._handle_websocket(mock_websocket, token="valid-token")
                    
                    mock_websocket.close.assert_called_once_with(code=1008, reason="Rate limit exceeded")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cors_configuration(self, gui_service):
        """Test CORS middleware is properly configured."""
        middleware = None
        for m in gui_service.app.user_middleware:
            if "CORSMiddleware" in str(m):
                middleware = m
                break
        
        assert middleware is not None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_handling_in_message_handlers(self, gui_service):
        """Test error handling in message bus handlers."""
        invalid_data = {"invalid": "data"}
        
        await gui_service._handle_service_status(invalid_data)
        
        assert gui_service._error_count > 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_metrics_tracking(self, gui_service):
        """Test that service metrics are properly tracked."""
        metrics_data = {
            "service": "llm_engine",
            "generation_count": 42,
            "total_tokens": 1000,
            "timestamp": "2025-12-05T10:00:00"
        }
        
        await gui_service._handle_service_metrics(metrics_data)
        
        assert "llm_engine" in gui_service.service_statuses
        assert "metrics" in gui_service.service_statuses["llm_engine"]