"""
GUI Service - Web Dashboard for Freya v2.0

Provides a comprehensive web dashboard with real-time monitoring,
conversation logging, tool call visualization, and system control.

Author: Claude (AI Assistant)
Version: 0.1.0
Date: 2025-12-03
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
from pathlib import Path
import asyncio
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
import uvicorn

from src.core.base_service import BaseService, ServiceError
from src.core.message_bus import MessageBus
from src.core.config import config
from src.services.gui.websocket_manager import WebSocketManager
from src.services.gui.models import (
    SystemStatus,
    ServiceStatus,
    ChatMessage,
    ToolCall,
    APIResponse,
)


class GUIServiceError(ServiceError):
    """Exception raised for GUI Service specific errors."""
    pass


class GUIService(BaseService):
    """
    GUI Service for Freya v2.0 Web Dashboard.

    Provides a FastAPI backend that serves the web dashboard and
    streams real-time updates from the message bus to connected clients.

    Subscribes to:
        - service.*.status: All service status updates
        - service.*.metrics: Performance metrics
        - mcp.tool.execute: Tool execution requests
        - mcp.tool.result: Tool execution results
        - gui.user.message: User messages from GUI
        - llm.final_response: LLM responses

    Publishes to:
        - gui.user.message: User input from web interface
        - service.gui_service.status: Service status updates
        - service.gui_service.metrics: Performance metrics

    Attributes:
        app: FastAPI application instance
        ws_manager: WebSocket connection manager
        service_statuses: Cache of service status data
        chat_history: Recent chat messages
        tool_history: Recent tool call logs
    """

    def __init__(self, message_bus: MessageBus) -> None:
        """
        Initialize the GUI Service.

        Args:
            message_bus: Shared MessageBus instance
        """
        super().__init__("gui_service", message_bus)

        # FastAPI application
        self.app: FastAPI = FastAPI(
            title="Freya v2.0 Dashboard",
            description="Real-time monitoring and control interface",
            version="0.2.0"
        )

        # WebSocket manager
        self.ws_manager = WebSocketManager()

        # Data caches
        self.service_statuses: Dict[str, Dict[str, Any]] = {}
        self.chat_history: List[Dict[str, Any]] = []
        self.tool_history: List[Dict[str, Any]] = []

        # Server reference
        self._server: Optional[uvicorn.Server] = None
        self._server_task: Optional[asyncio.Task] = None

        # Setup FastAPI routes and middleware
        self._setup_middleware()
        self._setup_routes()

        logger.debug(f"[{self.name}] Initialized GUI Service")

    def _setup_middleware(self) -> None:
        """Configure CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=config.gui_cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.debug(f"[{self.name}] CORS configured with origins: {config.gui_cors_origins}")

    def _setup_routes(self) -> None:
        """Setup API routes and WebSocket endpoint."""

        # Health check endpoint
        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        # System status endpoint
        @self.app.get("/api/status")
        async def get_system_status():
            """Get overall system status."""
            try:
                service_list = [
                    ServiceStatus(**status)
                    for status in self.service_statuses.values()
                ]

                system_status = SystemStatus(
                    services=service_list,
                    total_services=len(service_list),
                    healthy_services=sum(1 for s in service_list if s.healthy),
                    timestamp=datetime.now().isoformat()
                )

                return APIResponse(
                    success=True,
                    data=system_status.dict(),
                    timestamp=datetime.now().isoformat()
                )
            except Exception as e:
                logger.error(f"[{self.name}] Error getting system status: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Service list endpoint
        @self.app.get("/api/services")
        async def get_services():
            """Get list of all services with status."""
            try:
                return APIResponse(
                    success=True,
                    data=list(self.service_statuses.values()),
                    timestamp=datetime.now().isoformat()
                )
            except Exception as e:
                logger.error(f"[{self.name}] Error getting services: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Chat history endpoint
        @self.app.get("/api/conversation")
        async def get_conversation(limit: int = 50):
            """Get recent conversation history."""
            try:
                messages = self.chat_history[-limit:] if limit > 0 else self.chat_history
                return APIResponse(
                    success=True,
                    data=messages,
                    timestamp=datetime.now().isoformat()
                )
            except Exception as e:
                logger.error(f"[{self.name}] Error getting conversation: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Tool call history endpoint
        @self.app.get("/api/tools")
        async def get_tool_calls(limit: int = 50):
            """Get recent tool execution log."""
            try:
                tools = self.tool_history[-limit:] if limit > 0 else self.tool_history
                return APIResponse(
                    success=True,
                    data=tools,
                    timestamp=datetime.now().isoformat()
                )
            except Exception as e:
                logger.error(f"[{self.name}] Error getting tool calls: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Send user message endpoint
        @self.app.post("/api/message")
        async def send_message(message: Dict[str, str]):
            """Send a user message to Freya."""
            try:
                user_message = message.get("content", "").strip()
                if not user_message:
                    raise HTTPException(status_code=400, detail="Message content is required")

                # Publish to message bus for LLM processing
                await self.message_bus.publish("gui.user.message", {
                    "content": user_message,
                    "source": "web_gui",
                    "timestamp": datetime.now().isoformat()
                })

                # Add to chat history
                chat_msg = {
                    "id": str(uuid.uuid4()),
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now().isoformat(),
                    "location": "web_gui"
                }
                self.chat_history.append(chat_msg)
                self._trim_history(self.chat_history)

                # Broadcast to WebSocket clients
                await self.ws_manager.send_chat_message(chat_msg)

                logger.info(f"[{self.name}] 📤 User message sent: {user_message[:50]}...")

                return APIResponse(
                    success=True,
                    data=chat_msg,
                    timestamp=datetime.now().isoformat()
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"[{self.name}] Error sending message: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # WebSocket endpoint for real-time updates
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time dashboard updates."""
            await self.ws_manager.connect(websocket)
            try:
                # Send initial state
                await websocket.send_json({
                    "type": "initial_state",
                    "data": {
                        "services": list(self.service_statuses.values()),
                        "chat_history": self.chat_history[-50:],
                        "tool_history": self.tool_history[-50:]
                    },
                    "timestamp": datetime.now().isoformat()
                })

                # Keep connection alive and handle incoming messages
                while True:
                    data = await websocket.receive_text()
                    # Handle any client messages if needed
                    logger.debug(f"[{self.name}] Received WebSocket message: {data}")

            except WebSocketDisconnect:
                self.ws_manager.disconnect(websocket)
                logger.info(f"[{self.name}] WebSocket client disconnected")
            except Exception as e:
                logger.error(f"[{self.name}] WebSocket error: {e}")
                self.ws_manager.disconnect(websocket)

        # Serve static frontend files in production
        frontend_dist = Path(__file__).parent.parent.parent.parent / "src" / "gui" / "frontend" / "dist"
        if frontend_dist.exists():
            self.app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static")

            @self.app.get("/")
            async def serve_frontend():
                """Serve the frontend application."""
                index_file = frontend_dist / "index.html"
                if index_file.exists():
                    return FileResponse(str(index_file))
                return {"message": "Frontend not built. Run 'npm run build' in src/gui/frontend/"}

        logger.debug(f"[{self.name}] API routes configured")

    async def initialize(self) -> None:
        """
        Initialize the GUI Service.

        Raises:
            GUIServiceError: If initialization fails
        """
        try:
            logger.info(f"[{self.name}] Initializing GUI Service...")

            # Start WebSocket broadcast loop
            await self.ws_manager.start_broadcasting()

            self._healthy = True
            logger.success(f"[{self.name}] ✓ GUI Service initialized")

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Initialization failed: {e}")
            self._healthy = False
            self.increment_error_count()
            raise GUIServiceError(f"Initialization failed: {e}") from e

    async def start(self) -> None:
        """
        Start the GUI Service.

        Starts the FastAPI server and subscribes to message bus channels.

        Raises:
            GUIServiceError: If service fails to start
        """
        try:
            if not config.gui_enabled:
                logger.warning(f"[{self.name}] GUI Service is disabled in config")
                return

            logger.info(f"[{self.name}] Starting GUI Service...")

            # Subscribe to message bus channels
            await self.message_bus.subscribe("service.*.status", self._handle_service_status)
            await self.message_bus.subscribe("service.*.metrics", self._handle_service_metrics)
            await self.message_bus.subscribe("mcp.tool.execute", self._handle_tool_execute)
            await self.message_bus.subscribe("mcp.tool.result", self._handle_tool_result)
            await self.message_bus.subscribe("llm.final_response", self._handle_llm_response)

            logger.info(f"[{self.name}] Subscribed to message bus channels")

            # Start FastAPI server
            config_obj = uvicorn.Config(
                app=self.app,
                host=config.gui_host,
                port=config.gui_port,
                log_level="info",
                access_log=False
            )
            self._server = uvicorn.Server(config_obj)
            self._server_task = asyncio.create_task(self._server.serve())

            self._mark_started()
            await self.publish_status("started", {
                "host": config.gui_host,
                "port": config.gui_port,
                "url": f"http://{config.gui_host}:{config.gui_port}"
            })

            logger.success(
                f"[{self.name}] ✓ GUI Service started on "
                f"http://{config.gui_host}:{config.gui_port}"
            )

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Failed to start: {e}")
            self.increment_error_count()
            raise GUIServiceError(f"Service start failed: {e}") from e

    async def stop(self) -> None:
        """
        Stop the GUI Service gracefully.

        Disconnects from message bus and shuts down the FastAPI server.
        """
        try:
            logger.info(f"[{self.name}] Stopping GUI Service...")

            # Unsubscribe from message bus
            await self.message_bus.unsubscribe("service.*.status")
            await self.message_bus.unsubscribe("service.*.metrics")
            await self.message_bus.unsubscribe("mcp.tool.execute")
            await self.message_bus.unsubscribe("mcp.tool.result")
            await self.message_bus.unsubscribe("llm.final_response")

            # Stop WebSocket broadcast loop
            await self.ws_manager.stop_broadcasting()

            # Shutdown FastAPI server
            if self._server:
                self._server.should_exit = True
                if self._server_task:
                    try:
                        await asyncio.wait_for(self._server_task, timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"[{self.name}] Server shutdown timed out")

            self._mark_stopped()
            await self.publish_status("stopped")

            logger.success(f"[{self.name}] ✓ GUI Service stopped")

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Error during shutdown: {e}")
            self.increment_error_count()
            raise GUIServiceError(f"Service stop failed: {e}") from e

    async def health_check(self) -> bool:
        """
        Check if the GUI Service is healthy.

        Returns:
            True if service is operational, False otherwise
        """
        if not await super().health_check():
            return False

        # Check if server is running
        if self._server and not self._server.should_exit:
            return True

        if not self._server:
            logger.warning(f"[{self.name}] ⚠️  Server not started")
            return False

        return False

    # Message Bus Handlers

    async def _handle_service_status(self, data: Dict[str, Any]) -> None:
        """Handle service status updates from message bus."""
        try:
            service_name = data.get("service", "unknown")
            status = data.get("status", "unknown")

            # Update service status cache
            if service_name not in self.service_statuses:
                self.service_statuses[service_name] = {
                    "name": service_name,
                    "status": status,
                    "healthy": True,
                    "uptime": 0.0,
                    "error_count": 0,
                    "last_updated": datetime.now().isoformat()
                }
            else:
                self.service_statuses[service_name]["status"] = status
                self.service_statuses[service_name]["last_updated"] = datetime.now().isoformat()

            # Broadcast to WebSocket clients
            await self.ws_manager.send_service_update(self.service_statuses[service_name])

        except Exception as e:
            logger.error(f"[{self.name}] Error handling service status: {e}")

    async def _handle_service_metrics(self, data: Dict[str, Any]) -> None:
        """Handle service metrics updates from message bus."""
        try:
            service_name = data.get("service", "unknown")

            if service_name in self.service_statuses:
                # Update metrics
                self.service_statuses[service_name]["uptime"] = data.get("uptime", 0.0)
                self.service_statuses[service_name]["error_count"] = data.get("error_count", 0)
                self.service_statuses[service_name]["last_updated"] = datetime.now().isoformat()

                # Broadcast update
                await self.ws_manager.send_service_update(self.service_statuses[service_name])

        except Exception as e:
            logger.error(f"[{self.name}] Error handling service metrics: {e}")

    async def _handle_tool_execute(self, data: Dict[str, Any]) -> None:
        """Handle tool execution requests from message bus."""
        try:
            tool_call = {
                "id": data.get("request_id", str(uuid.uuid4())),
                "tool_name": data.get("tool_name", "unknown"),
                "arguments": data.get("arguments", {}),
                "result": None,
                "success": False,
                "duration": None,
                "timestamp": data.get("timestamp", datetime.now().isoformat()),
                "error": None
            }

            self.tool_history.append(tool_call)
            self._trim_history(self.tool_history)

            # Broadcast to WebSocket clients
            await self.ws_manager.send_tool_call(tool_call)

        except Exception as e:
            logger.error(f"[{self.name}] Error handling tool execute: {e}")

    async def _handle_tool_result(self, data: Dict[str, Any]) -> None:
        """Handle tool execution results from message bus."""
        try:
            request_id = data.get("request_id")

            # Find and update the corresponding tool call
            for tool_call in reversed(self.tool_history):
                if tool_call["id"] == request_id:
                    tool_call["result"] = data.get("result")
                    tool_call["success"] = data.get("success", False)
                    tool_call["duration"] = data.get("duration")
                    tool_call["error"] = data.get("error")
                    break

            # Broadcast updated tool call
            await self.ws_manager.send_tool_call(data)

        except Exception as e:
            logger.error(f"[{self.name}] Error handling tool result: {e}")

    async def _handle_llm_response(self, data: Dict[str, Any]) -> None:
        """Handle LLM response messages from message bus."""
        try:
            chat_msg = {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": data.get("response", ""),
                "timestamp": data.get("timestamp", datetime.now().isoformat()),
                "location": data.get("location")
            }

            self.chat_history.append(chat_msg)
            self._trim_history(self.chat_history)

            # Broadcast to WebSocket clients
            await self.ws_manager.send_chat_message(chat_msg)

        except Exception as e:
            logger.error(f"[{self.name}] Error handling LLM response: {e}")

    def _trim_history(self, history: List[Dict[str, Any]]) -> None:
        """
        Trim history list to maximum retention size.

        Args:
            history: List to trim
        """
        max_size = config.gui_log_retention
        if len(history) > max_size:
            history[:] = history[-max_size:]
