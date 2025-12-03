"""
MCP Gateway - Model Context Protocol Gateway for Freya v2.0

Manages connections to MCP servers, tool discovery, and tool execution.
Provides a unified interface for the LLM to interact with external tools
and services through the Model Context Protocol.

Author: Claude (AI Assistant)
Version: 0.1.0
Date: 2025-12-03
"""

from typing import Optional, Dict, List, Any, Callable
from loguru import logger
from datetime import datetime
import asyncio
import yaml
from pathlib import Path
import subprocess
import json

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    logger.warning("mcp package not installed. MCP Gateway will not be available.")
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None

from src.core.base_service import BaseService, ServiceError
from src.core.message_bus import MessageBus
from src.core.config import config


class MCPGatewayError(ServiceError):
    """Exception raised for MCP Gateway specific errors."""
    pass


class MCPServerConnection:
    """
    Represents a connection to a single MCP server.

    Manages the lifecycle of an MCP server connection including
    initialization, tool discovery, and command execution.

    Attributes:
        name: Server name (e.g., "filesystem", "web-search")
        command: Command to start the server
        args: Arguments for the server command
        session: Active MCP client session
        tools: Dictionary of available tools from this server
    """

    def __init__(
        self,
        name: str,
        command: str,
        args: List[str],
        env: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Initialize MCP server connection.

        Args:
            name: Server identifier
            command: Command to execute (e.g., "npx", "node")
            args: Command arguments
            env: Optional environment variables
        """
        self.name = name
        self.command = command
        self.args = args
        self.env = env or {}
        self.session: Optional[ClientSession] = None
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._connected = False
        self._read_stream = None
        self._write_stream = None

    async def connect(self) -> None:
        """
        Connect to the MCP server.

        Raises:
            MCPGatewayError: If connection fails
        """
        try:
            logger.info(f"[MCPGateway] Connecting to MCP server: {self.name}")

            # Create server parameters
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env if self.env else None
            )

            # Connect using stdio client
            read, write = await stdio_client(server_params)
            self._read_stream = read
            self._write_stream = write

            # Create session
            self.session = ClientSession(read, write)
            await self.session.initialize()

            self._connected = True
            logger.success(f"[MCPGateway] ✓ Connected to {self.name}")

        except Exception as e:
            logger.error(f"[MCPGateway] ❌ Failed to connect to {self.name}: {e}")
            raise MCPGatewayError(f"Connection to {self.name} failed: {e}") from e

    async def discover_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover available tools from the MCP server.

        Returns:
            Dictionary mapping tool names to their schemas

        Raises:
            MCPGatewayError: If tool discovery fails
        """
        try:
            if not self.session:
                raise MCPGatewayError(f"Not connected to {self.name}")

            logger.debug(f"[MCPGateway] Discovering tools from {self.name}...")

            # List available tools
            tools_list = await self.session.list_tools()

            # Convert to dictionary with full metadata
            self.tools = {}
            for tool in tools_list.tools:
                self.tools[tool.name] = {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                    "server": self.name
                }

            logger.info(
                f"[MCPGateway] ✓ Discovered {len(self.tools)} tools from {self.name}: "
                f"{', '.join(self.tools.keys())}"
            )

            return self.tools

        except Exception as e:
            logger.error(f"[MCPGateway] ❌ Tool discovery failed for {self.name}: {e}")
            raise MCPGatewayError(f"Tool discovery failed for {self.name}: {e}") from e

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Execute a tool on this MCP server.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            MCPGatewayError: If tool execution fails
        """
        try:
            if not self.session:
                raise MCPGatewayError(f"Not connected to {self.name}")

            if tool_name not in self.tools:
                raise MCPGatewayError(
                    f"Tool '{tool_name}' not found in {self.name}. "
                    f"Available: {list(self.tools.keys())}"
                )

            logger.debug(
                f"[MCPGateway] Executing tool '{tool_name}' on {self.name} "
                f"with args: {arguments}"
            )

            # Call the tool
            result = await self.session.call_tool(tool_name, arguments)

            logger.debug(f"[MCPGateway] ✓ Tool '{tool_name}' executed successfully")

            return result

        except Exception as e:
            logger.error(
                f"[MCPGateway] ❌ Tool execution failed for '{tool_name}' "
                f"on {self.name}: {e}"
            )
            raise MCPGatewayError(
                f"Tool execution failed for '{tool_name}': {e}"
            ) from e

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        try:
            if self.session:
                logger.info(f"[MCPGateway] Disconnecting from {self.name}...")
                await self.session.close()
                self.session = None

            self._connected = False
            self.tools = {}
            logger.success(f"[MCPGateway] ✓ Disconnected from {self.name}")

        except Exception as e:
            logger.error(f"[MCPGateway] Error disconnecting from {self.name}: {e}")

    def is_connected(self) -> bool:
        """Check if connected to the server."""
        return self._connected and self.session is not None


class MCPGateway(BaseService):
    """
    MCP Gateway service for managing tool integrations.

    This service connects to multiple MCP servers, discovers available tools,
    and provides a unified interface for tool execution. It acts as a bridge
    between the LLM Engine and external tools/services.

    Subscribes to:
        - mcp.tool.execute: Tool execution requests from LLM Engine

    Publishes to:
        - mcp.tool.registry: Available tools catalog
        - mcp.tool.result: Tool execution results
        - service.mcp_gateway.status: Service status updates
        - service.mcp_gateway.metrics: Performance metrics

    Attributes:
        servers: Dictionary of connected MCP server connections
        tool_registry: Unified catalog of all available tools
        tool_call_count: Total number of tool calls executed

    Example:
        >>> gateway = MCPGateway(message_bus)
        >>> await gateway.initialize()
        >>> await gateway.start()
    """

    def __init__(self, message_bus: MessageBus) -> None:
        """
        Initialize the MCP Gateway.

        Args:
            message_bus: Shared MessageBus instance

        Raises:
            MCPGatewayError: If MCP SDK is not available
        """
        super().__init__("mcp_gateway", message_bus)

        if ClientSession is None or stdio_client is None:
            raise MCPGatewayError(
                "MCP SDK not installed. Install with: pip install mcp"
            )

        self.servers: Dict[str, MCPServerConnection] = {}
        self.tool_registry: Dict[str, Dict[str, Any]] = {}
        self.tool_call_count = 0
        self._servers_config_path = Path(config.mcp_servers_config)

        logger.debug(f"[{self.name}] Initialized with config: {self._servers_config_path}")

    async def initialize(self) -> None:
        """
        Initialize the MCP Gateway and load server configurations.

        Raises:
            MCPGatewayError: If initialization fails
        """
        try:
            logger.info(f"[{self.name}] Initializing MCP Gateway...")

            # Load server configurations
            servers_config = await self._load_servers_config()

            if not servers_config:
                logger.warning(f"[{self.name}] No MCP servers configured")
                self._healthy = True
                return

            # Create server connections (don't connect yet)
            for server_name, server_config in servers_config.items():
                if not server_config.get("enabled", True):
                    logger.info(f"[{self.name}] Skipping disabled server: {server_name}")
                    continue

                connection = MCPServerConnection(
                    name=server_name,
                    command=server_config["command"],
                    args=server_config.get("args", []),
                    env=server_config.get("env", {})
                )
                self.servers[server_name] = connection
                logger.debug(f"[{self.name}] Registered server: {server_name}")

            self._healthy = True
            logger.success(
                f"[{self.name}] ✓ MCP Gateway initialized with "
                f"{len(self.servers)} servers configured"
            )

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Initialization failed: {e}")
            self._healthy = False
            self.increment_error_count()
            raise MCPGatewayError(f"Initialization failed: {e}") from e

    async def start(self) -> None:
        """
        Start the MCP Gateway service.

        Connects to all configured MCP servers and discovers available tools.

        Raises:
            MCPGatewayError: If service fails to start
        """
        try:
            if not config.mcp_enabled:
                logger.warning(f"[{self.name}] MCP Gateway is disabled in config")
                return

            logger.info(f"[{self.name}] Starting MCP Gateway...")

            # Connect to all servers
            await self._connect_all_servers()

            # Discover tools from all servers
            await self._discover_all_tools()

            # Subscribe to tool execution requests
            await self.message_bus.subscribe("mcp.tool.execute", self._handle_tool_execution)

            self._mark_started()
            await self.publish_status("started")

            logger.success(
                f"[{self.name}] ✓ MCP Gateway started successfully. "
                f"Total tools available: {len(self.tool_registry)}"
            )

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Failed to start: {e}")
            self.increment_error_count()
            raise MCPGatewayError(f"Service start failed: {e}") from e

    async def stop(self) -> None:
        """
        Stop the MCP Gateway service gracefully.

        Disconnects from all MCP servers and cleans up resources.
        """
        try:
            logger.info(f"[{self.name}] Stopping MCP Gateway...")

            # Unsubscribe from channels
            await self.message_bus.unsubscribe("mcp.tool.execute")

            # Disconnect from all servers
            for server_name, server in self.servers.items():
                if server.is_connected():
                    await server.disconnect()

            self._mark_stopped()
            await self.publish_status("stopped")

            # Publish final metrics
            await self._publish_metrics()

            logger.success(
                f"[{self.name}] ✓ MCP Gateway stopped. "
                f"Total tool calls: {self.tool_call_count}"
            )

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Error during shutdown: {e}")
            self.increment_error_count()
            raise MCPGatewayError(f"Service stop failed: {e}") from e

    async def health_check(self) -> bool:
        """
        Check if the MCP Gateway is healthy.

        Returns:
            True if service is operational, False otherwise
        """
        if not await super().health_check():
            return False

        # Check if at least one server is connected
        connected_count = sum(1 for server in self.servers.values() if server.is_connected())

        if connected_count == 0 and len(self.servers) > 0:
            logger.warning(f"[{self.name}] ⚠️  No MCP servers connected")
            return False

        return True

    async def _load_servers_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Load MCP server configurations from YAML file.

        Returns:
            Dictionary of server configurations

        Raises:
            MCPGatewayError: If config file cannot be loaded
        """
        try:
            if not self._servers_config_path.exists():
                logger.warning(
                    f"[{self.name}] Config file not found: {self._servers_config_path}"
                )
                return {}

            with open(self._servers_config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            servers = config_data.get("mcp_servers", {})
            logger.info(f"[{self.name}] Loaded {len(servers)} server configurations")

            return servers

        except Exception as e:
            raise MCPGatewayError(f"Failed to load server config: {e}") from e

    async def _connect_all_servers(self) -> None:
        """Connect to all configured MCP servers."""
        logger.info(f"[{self.name}] Connecting to {len(self.servers)} MCP servers...")

        for server_name, server in self.servers.items():
            try:
                await server.connect()
            except MCPGatewayError as e:
                logger.error(
                    f"[{self.name}] Failed to connect to {server_name}: {e}. "
                    "Continuing with other servers..."
                )
                self.increment_error_count()

        connected_count = sum(1 for s in self.servers.values() if s.is_connected())
        logger.info(f"[{self.name}] Connected to {connected_count}/{len(self.servers)} servers")

    async def _discover_all_tools(self) -> None:
        """Discover tools from all connected servers and build unified registry."""
        logger.info(f"[{self.name}] Discovering tools from all servers...")

        self.tool_registry = {}

        for server_name, server in self.servers.items():
            if not server.is_connected():
                logger.warning(f"[{self.name}] Skipping tool discovery for disconnected server: {server_name}")
                continue

            try:
                tools = await server.discover_tools()
                self.tool_registry.update(tools)
            except MCPGatewayError as e:
                logger.error(f"[{self.name}] Tool discovery failed for {server_name}: {e}")
                self.increment_error_count()

        logger.success(
            f"[{self.name}] ✓ Tool discovery complete. "
            f"Total tools: {len(self.tool_registry)}"
        )

        # Publish tool registry to message bus
        await self._publish_tool_registry()

    async def _publish_tool_registry(self) -> None:
        """Publish the tool registry to the message bus."""
        try:
            registry_message = {
                "tools": list(self.tool_registry.values()),
                "tool_count": len(self.tool_registry),
                "servers": list(self.servers.keys()),
                "timestamp": datetime.now().isoformat()
            }

            await self.message_bus.publish("mcp.tool.registry", registry_message)
            logger.debug(f"[{self.name}] 📤 Published tool registry")

        except Exception as e:
            logger.error(f"[{self.name}] Failed to publish tool registry: {e}")

    async def _handle_tool_execution(self, data: Dict[str, Any]) -> None:
        """
        Handle tool execution requests from LLM Engine.

        Args:
            data: Tool execution request with format:
                {
                    "tool_name": str,
                    "arguments": Dict[str, Any],
                    "request_id": str (optional)
                }
        """
        request_id = data.get("request_id", "unknown")

        try:
            tool_name = data.get("tool_name")
            arguments = data.get("arguments", {})

            if not tool_name:
                raise MCPGatewayError("Missing 'tool_name' in request")

            logger.info(f"[{self.name}] 📥 Received tool call: {tool_name}")

            if config.mcp_log_tool_calls:
                logger.debug(f"[{self.name}] Tool arguments: {arguments}")

            # Find which server has this tool
            tool_info = self.tool_registry.get(tool_name)
            if not tool_info:
                raise MCPGatewayError(f"Tool '{tool_name}' not found in registry")

            server_name = tool_info["server"]
            server = self.servers.get(server_name)

            if not server or not server.is_connected():
                raise MCPGatewayError(f"Server '{server_name}' not connected")

            # Execute the tool
            start_time = datetime.now()
            result = await server.call_tool(tool_name, arguments)
            duration = (datetime.now() - start_time).total_seconds()

            # Publish result
            result_message = {
                "request_id": request_id,
                "tool_name": tool_name,
                "result": result,
                "success": True,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            }

            await self.message_bus.publish("mcp.tool.result", result_message)

            self.tool_call_count += 1

            logger.info(
                f"[{self.name}] ✓ Tool '{tool_name}' executed successfully "
                f"in {duration:.2f}s"
            )

            # Publish metrics periodically
            if self.tool_call_count % 10 == 0:
                await self._publish_metrics()

        except MCPGatewayError as e:
            logger.error(f"[{self.name}] ❌ Tool execution error: {e}")
            self.increment_error_count()

            # Publish error result
            error_message = {
                "request_id": request_id,
                "tool_name": data.get("tool_name", "unknown"),
                "result": None,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            await self.message_bus.publish("mcp.tool.result", error_message)

        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Unexpected error: {e}")
            self.increment_error_count()

    async def _publish_metrics(self) -> None:
        """Publish service metrics to the message bus."""
        try:
            connected_servers = [
                name for name, server in self.servers.items()
                if server.is_connected()
            ]

            metrics = {
                "service": self.name,
                "tool_call_count": self.tool_call_count,
                "total_tools": len(self.tool_registry),
                "servers_configured": len(self.servers),
                "servers_connected": len(connected_servers),
                "connected_servers": connected_servers,
                "error_count": self._error_count,
                "uptime": self.get_uptime(),
                "timestamp": datetime.now().isoformat()
            }

            await self.message_bus.publish("service.mcp_gateway.metrics", metrics)

            logger.debug(
                f"[{self.name}] 📊 Metrics: {self.tool_call_count} tool calls, "
                f"{len(connected_servers)}/{len(self.servers)} servers connected"
            )

        except Exception as e:
            logger.error(f"[{self.name}] Failed to publish metrics: {e}")
