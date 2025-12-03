"""
WebSocket Manager for GUI Service.

Manages WebSocket connections to frontend clients and broadcasts
real-time updates from the message bus.

Author: Claude (AI Assistant)
Version: 0.1.0
Date: 2025-12-03
"""

from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from datetime import datetime
import json
import asyncio


class WebSocketManager:
    """
    Manages WebSocket connections and message broadcasting.

    This class handles multiple WebSocket client connections and
    broadcasts messages from the message bus to all connected clients.

    Attributes:
        active_connections: List of active WebSocket connections
        message_queue: Queue of messages to broadcast
    """

    def __init__(self) -> None:
        """Initialize the WebSocket manager."""
        self.active_connections: List[WebSocket] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self._broadcast_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to register
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"[WebSocketManager] ✓ New client connected. "
            f"Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"[WebSocketManager] Client disconnected. "
                f"Total connections: {len(self.active_connections)}"
            )

    async def send_personal_message(
        self,
        message: Dict[str, Any],
        websocket: WebSocket
    ) -> None:
        """
        Send a message to a specific client.

        Args:
            message: Message data to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"[WebSocketManager] Failed to send personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message data to broadcast
        """
        # Add to queue for async broadcasting
        await self.message_queue.put(message)

    async def broadcast_loop(self) -> None:
        """
        Background task that broadcasts queued messages.

        This runs continuously and sends messages from the queue
        to all connected clients.
        """
        logger.info("[WebSocketManager] Starting broadcast loop")

        while True:
            try:
                # Wait for message from queue
                message = await self.message_queue.get()

                # Add timestamp if not present
                if "timestamp" not in message:
                    message["timestamp"] = datetime.now().isoformat()

                # Send to all connected clients
                disconnected_clients = []

                for connection in self.active_connections:
                    try:
                        await connection.send_json(message)
                    except WebSocketDisconnect:
                        disconnected_clients.append(connection)
                    except Exception as e:
                        logger.error(
                            f"[WebSocketManager] Error broadcasting to client: {e}"
                        )
                        disconnected_clients.append(connection)

                # Remove disconnected clients
                for client in disconnected_clients:
                    self.disconnect(client)

            except asyncio.CancelledError:
                logger.info("[WebSocketManager] Broadcast loop cancelled")
                break
            except Exception as e:
                logger.error(f"[WebSocketManager] Error in broadcast loop: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on errors

    async def start_broadcasting(self) -> None:
        """Start the background broadcast loop."""
        if self._broadcast_task is None or self._broadcast_task.done():
            self._broadcast_task = asyncio.create_task(self.broadcast_loop())
            logger.success("[WebSocketManager] ✓ Broadcast loop started")

    async def stop_broadcasting(self) -> None:
        """Stop the background broadcast loop."""
        if self._broadcast_task and not self._broadcast_task.done():
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
            logger.info("[WebSocketManager] Broadcast loop stopped")

    async def send_system_status(self, status_data: Dict[str, Any]) -> None:
        """
        Broadcast system status update to all clients.

        Args:
            status_data: System status information
        """
        await self.broadcast({
            "type": "system_status",
            "data": status_data
        })

    async def send_service_update(self, service_data: Dict[str, Any]) -> None:
        """
        Broadcast service status update to all clients.

        Args:
            service_data: Service status information
        """
        await self.broadcast({
            "type": "service_status",
            "data": service_data
        })

    async def send_chat_message(self, message_data: Dict[str, Any]) -> None:
        """
        Broadcast chat message to all clients.

        Args:
            message_data: Chat message information
        """
        await self.broadcast({
            "type": "chat_message",
            "data": message_data
        })

    async def send_tool_call(self, tool_data: Dict[str, Any]) -> None:
        """
        Broadcast tool call information to all clients.

        Args:
            tool_data: Tool call information
        """
        await self.broadcast({
            "type": "tool_call",
            "data": tool_data
        })

    def get_connection_count(self) -> int:
        """
        Get the number of active connections.

        Returns:
            Number of active WebSocket connections
        """
        return len(self.active_connections)
