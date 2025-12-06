"""
Unit tests for MCPGateway

Tests the MCP Gateway service including server connections, tool discovery,
tool execution, and message bus integration.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
from src.services.mcp_gateway.mcp_gateway import (
    MCPGateway,
    MCPGatewayError,
    MCPServerConnection
)


class TestMCPServerConnection:
    """Test suite for MCPServerConnection class."""
    
    @pytest.fixture
    def server_connection(self):
        """Create an MCPServerConnection instance."""
        return MCPServerConnection(
            name="test-server",
            command="npx",
            args=["@modelcontextprotocol/server-test"],
            env={"TEST_VAR": "test_value"}
        )
    
    @pytest.mark.unit
    def test_initialization(self, server_connection):
        """Test MCPServerConnection initialization."""
        assert server_connection.name == "test-server"
        assert server_connection.command == "npx"
        assert server_connection.args == ["@modelcontextprotocol/server-test"]
        assert server_connection.env == {"TEST_VAR": "test_value"}
        assert server_connection.session is None
        assert server_connection.tools == {}
        assert server_connection._connected is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_connect_success(self, server_connection):
        """Test successful connection to MCP server."""
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        
        with patch('src.services.mcp_gateway.mcp_gateway.stdio_client', return_value=(mock_read, mock_write)):
            with patch('src.services.mcp_gateway.mcp_gateway.ClientSession', return_value=mock_session):
                await server_connection.connect()
                
                assert server_connection._connected is True
                assert server_connection.session == mock_session
                mock_session.initialize.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_connect_failure(self, server_connection):
        """Test connection failure handling."""
        with patch('src.services.mcp_gateway.mcp_gateway.stdio_client', side_effect=Exception("Connection failed")):
            with pytest.raises(MCPGatewayError, match="Connection to test-server failed"):
                await server_connection.connect()
            
            assert server_connection._connected is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_discover_tools_success(self, server_connection):
        """Test successful tool discovery."""
        mock_tool1 = MagicMock()
        mock_tool1.name = "read_file"
        mock_tool1.description = "Read a file"
        mock_tool1.inputSchema = {"type": "object", "properties": {"path": {"type": "string"}}}
        
        mock_tool2 = MagicMock()
        mock_tool2.name = "write_file"
        mock_tool2.description = "Write a file"
        mock_tool2.inputSchema = {"type": "object", "properties": {"path": {"type": "string"}}}
        
        mock_tools_list = MagicMock()
        mock_tools_list.tools = [mock_tool1, mock_tool2]
        
        mock_session = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=mock_tools_list)
        server_connection.session = mock_session
        
        tools = await server_connection.discover_tools()
        
        assert len(tools) == 2
        assert "read_file" in tools
        assert "write_file" in tools
        assert tools["read_file"]["description"] == "Read a file"
        assert tools["read_file"]["server"] == "test-server"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_discover_tools_not_connected(self, server_connection):
        """Test tool discovery when not connected."""
        with pytest.raises(MCPGatewayError, match="Not connected to test-server"):
            await server_connection.discover_tools()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_call_tool_success(self, server_connection):
        """Test successful tool execution."""
        mock_result = {"content": [{"type": "text", "text": "File contents"}]}
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value=mock_result)
        
        server_connection.session = mock_session
        server_connection.tools = {
            "read_file": {
                "name": "read_file",
                "description": "Read a file",
                "server": "test-server"
            }
        }
        
        result = await server_connection.call_tool("read_file", {"path": "/test.txt"})
        
        assert result == mock_result
        mock_session.call_tool.assert_called_once_with("read_file", {"path": "/test.txt"})
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self, server_connection):
        """Test tool execution when not connected."""
        with pytest.raises(MCPGatewayError, match="Not connected to test-server"):
            await server_connection.call_tool("read_file", {})
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_call_tool_not_found(self, server_connection):
        """Test tool execution with unknown tool."""
        mock_session = AsyncMock()
        server_connection.session = mock_session
        server_connection.tools = {"read_file": {}}
        
        with pytest.raises(MCPGatewayError, match="Tool 'unknown_tool' not found"):
            await server_connection.call_tool("unknown_tool", {})
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_disconnect(self, server_connection):
        """Test disconnecting from MCP server."""
        mock_session = AsyncMock()
        mock_session.__aexit__ = AsyncMock()
        server_connection.session = mock_session
        server_connection._connected = True
        
        await server_connection.disconnect()
        
        assert server_connection._connected is False
        assert server_connection.session is None


class TestMCPGateway:
    """Test suite for MCPGateway class."""
    
    @pytest.fixture
    def mock_config_yaml(self):
        """Mock MCP servers configuration."""
        return """
mcp_servers:
  filesystem:
    enabled: true
    type: local
    command: npx
    args:
      - "@modelcontextprotocol/server-filesystem"
      - "/home/ubuntu"
    description: "Local file system access"
  
  calculator:
    enabled: true
    type: local
    command: npx
    args:
      - "@modelcontextprotocol/server-calculator"
    description: "Mathematical calculations"
  
  disabled-server:
    enabled: false
    command: npx
    args:
      - "@modelcontextprotocol/server-disabled"
"""
    
    @pytest.fixture
    async def mcp_gateway(self, mock_message_bus, mock_config_yaml):
        """Create an MCPGateway instance with mocked dependencies."""
        with patch('builtins.open', mock_open(read_data=mock_config_yaml)):
            with patch('pathlib.Path.exists', return_value=True):
                gateway = MCPGateway(mock_message_bus)
                yield gateway
                
                if gateway._running:
                    await gateway.stop()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialization(self, mock_message_bus, mock_config_yaml):
        """Test MCPGateway initialization."""
        with patch('builtins.open', mock_open(read_data=mock_config_yaml)):
            with patch('pathlib.Path.exists', return_value=True):
                gateway = MCPGateway(mock_message_bus)
                
                assert gateway.name == "mcp_gateway"
                assert gateway.message_bus == mock_message_bus
                assert gateway.servers == {}
                assert gateway.available_tools == {}
                assert gateway._tool_call_count == 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_config_success(self, mcp_gateway):
        """Test successful configuration loading."""
        config = mcp_gateway._load_config()
        
        assert "mcp_servers" in config
        assert "filesystem" in config["mcp_servers"]
        assert "calculator" in config["mcp_servers"]
        assert config["mcp_servers"]["filesystem"]["enabled"] is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_config_file_not_found(self, mock_message_bus):
        """Test configuration loading when file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(MCPGatewayError, match="Configuration file not found"):
                MCPGateway(mock_message_bus)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_config_invalid_yaml(self, mock_message_bus):
        """Test configuration loading with invalid YAML."""
        invalid_yaml = "invalid: yaml: content: ["
        
        with patch('builtins.open', mock_open(read_data=invalid_yaml)):
            with patch('pathlib.Path.exists', return_value=True):
                with pytest.raises(MCPGatewayError, match="Failed to parse configuration"):
                    MCPGateway(mock_message_bus)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialize_creates_server_connections(self, mcp_gateway):
        """Test that initialize creates server connections for enabled servers."""
        await mcp_gateway.initialize()
        
        assert "filesystem" in mcp_gateway.servers
        assert "calculator" in mcp_gateway.servers
        assert "disabled-server" not in mcp_gateway.servers
        assert isinstance(mcp_gateway.servers["filesystem"], MCPServerConnection)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_connect_all_servers_success(self, mcp_gateway):
        """Test connecting to all MCP servers."""
        mock_server1 = AsyncMock(spec=MCPServerConnection)
        mock_server1.connect = AsyncMock()
        mock_server1.discover_tools = AsyncMock(return_value={"tool1": {"name": "tool1"}})
        
        mock_server2 = AsyncMock(spec=MCPServerConnection)
        mock_server2.connect = AsyncMock()
        mock_server2.discover_tools = AsyncMock(return_value={"tool2": {"name": "tool2"}})
        
        mcp_gateway.servers = {
            "server1": mock_server1,
            "server2": mock_server2
        }
        
        await mcp_gateway._connect_all_servers()
        
        mock_server1.connect.assert_called_once()
        mock_server2.connect.assert_called_once()
        mock_server1.discover_tools.assert_called_once()
        mock_server2.discover_tools.assert_called_once()
        
        assert len(mcp_gateway.available_tools) == 2
        assert "tool1" in mcp_gateway.available_tools
        assert "tool2" in mcp_gateway.available_tools
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_connect_all_servers_partial_failure(self, mcp_gateway):
        """Test connecting when some servers fail."""
        mock_server1 = AsyncMock(spec=MCPServerConnection)
        mock_server1.connect = AsyncMock(side_effect=MCPGatewayError("Connection failed"))
        
        mock_server2 = AsyncMock(spec=MCPServerConnection)
        mock_server2.connect = AsyncMock()
        mock_server2.discover_tools = AsyncMock(return_value={"tool2": {"name": "tool2"}})
        
        mcp_gateway.servers = {
            "server1": mock_server1,
            "server2": mock_server2
        }
        
        await mcp_gateway._connect_all_servers()
        
        assert len(mcp_gateway.available_tools) == 1
        assert "tool2" in mcp_gateway.available_tools
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_subscribes_to_channels(self, mcp_gateway, mock_message_bus):
        """Test that start() subscribes to required message bus channels."""
        with patch.object(mcp_gateway, '_connect_all_servers', new_callable=AsyncMock):
            await mcp_gateway.start()
            
            assert mcp_gateway._running is True
            
            subscribe_calls = [call[0][0] for call in mock_message_bus.subscribe.call_args_list]
            assert "mcp.tool.execute" in subscribe_calls
            assert "mcp.tools.list" in subscribe_calls
            assert "mcp.servers.status" in subscribe_calls
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stop_disconnects_servers(self, mcp_gateway):
        """Test that stop() disconnects all servers."""
        mock_server1 = AsyncMock(spec=MCPServerConnection)
        mock_server1.disconnect = AsyncMock()
        
        mock_server2 = AsyncMock(spec=MCPServerConnection)
        mock_server2.disconnect = AsyncMock()
        
        mcp_gateway.servers = {
            "server1": mock_server1,
            "server2": mock_server2
        }
        mcp_gateway._running = True
        
        await mcp_gateway.stop()
        
        mock_server1.disconnect.assert_called_once()
        mock_server2.disconnect.assert_called_once()
        assert mcp_gateway._running is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_tool_execute_success(self, mcp_gateway, mock_message_bus):
        """Test successful tool execution."""
        mock_server = AsyncMock(spec=MCPServerConnection)
        mock_server.call_tool = AsyncMock(return_value={"result": "success"})
        
        mcp_gateway.servers = {"test-server": mock_server}
        mcp_gateway.available_tools = {
            "test_tool": {
                "name": "test_tool",
                "server": "test-server",
                "description": "Test tool"
            }
        }
        
        request_data = {
            "tool": "test_tool",
            "arguments": {"arg1": "value1"},
            "request_id": "req-123"
        }
        
        await mcp_gateway._handle_tool_execute(request_data)
        
        mock_server.call_tool.assert_called_once_with("test_tool", {"arg1": "value1"})
        
        publish_calls = mock_message_bus.publish.call_args_list
        assert len(publish_calls) == 1
        assert publish_calls[0][0][0] == "mcp.tool.result"
        assert publish_calls[0][0][1]["success"] is True
        assert publish_calls[0][0][1]["request_id"] == "req-123"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_tool_execute_tool_not_found(self, mcp_gateway, mock_message_bus):
        """Test tool execution with unknown tool."""
        mcp_gateway.available_tools = {}
        
        request_data = {
            "tool": "unknown_tool",
            "arguments": {},
            "request_id": "req-123"
        }
        
        await mcp_gateway._handle_tool_execute(request_data)
        
        publish_calls = mock_message_bus.publish.call_args_list
        assert len(publish_calls) == 1
        assert publish_calls[0][0][0] == "mcp.tool.result"
        assert publish_calls[0][0][1]["success"] is False
        assert "not found" in publish_calls[0][0][1]["error"].lower()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_tool_execute_execution_failure(self, mcp_gateway, mock_message_bus):
        """Test tool execution failure handling."""
        mock_server = AsyncMock(spec=MCPServerConnection)
        mock_server.call_tool = AsyncMock(side_effect=Exception("Execution failed"))
        
        mcp_gateway.servers = {"test-server": mock_server}
        mcp_gateway.available_tools = {
            "test_tool": {
                "name": "test_tool",
                "server": "test-server"
            }
        }
        
        request_data = {
            "tool": "test_tool",
            "arguments": {},
            "request_id": "req-123"
        }
        
        await mcp_gateway._handle_tool_execute(request_data)
        
        publish_calls = mock_message_bus.publish.call_args_list
        assert len(publish_calls) == 1
        assert publish_calls[0][0][1]["success"] is False
        assert "Execution failed" in publish_calls[0][0][1]["error"]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_tools_list_request(self, mcp_gateway, mock_message_bus):
        """Test listing available tools."""
        mcp_gateway.available_tools = {
            "tool1": {"name": "tool1", "description": "First tool"},
            "tool2": {"name": "tool2", "description": "Second tool"}
        }
        
        await mcp_gateway._handle_tools_list({})
        
        publish_calls = mock_message_bus.publish.call_args_list
        assert len(publish_calls) == 1
        assert publish_calls[0][0][0] == "mcp.tools.available"
        assert len(publish_calls[0][0][1]["tools"]) == 2
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_servers_status_request(self, mcp_gateway, mock_message_bus):
        """Test server status reporting."""
        mock_server1 = MagicMock(spec=MCPServerConnection)
        mock_server1._connected = True
        mock_server1.tools = {"tool1": {}}
        
        mock_server2 = MagicMock(spec=MCPServerConnection)
        mock_server2._connected = False
        mock_server2.tools = {}
        
        mcp_gateway.servers = {
            "server1": mock_server1,
            "server2": mock_server2
        }
        
        await mcp_gateway._handle_servers_status({})
        
        publish_calls = mock_message_bus.publish.call_args_list
        assert len(publish_calls) == 1
        assert publish_calls[0][0][0] == "mcp.servers.info"
        
        servers_info = publish_calls[0][0][1]["servers"]
        assert servers_info["server1"]["connected"] is True
        assert servers_info["server1"]["tool_count"] == 1
        assert servers_info["server2"]["connected"] is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_tool_call_count_tracking(self, mcp_gateway, mock_message_bus):
        """Test that tool calls are counted."""
        mock_server = AsyncMock(spec=MCPServerConnection)
        mock_server.call_tool = AsyncMock(return_value={"result": "success"})
        
        mcp_gateway.servers = {"test-server": mock_server}
        mcp_gateway.available_tools = {
            "test_tool": {"name": "test_tool", "server": "test-server"}
        }
        
        initial_count = mcp_gateway._tool_call_count
        
        await mcp_gateway._handle_tool_execute({
            "tool": "test_tool",
            "arguments": {},
            "request_id": "req-1"
        })
        
        assert mcp_gateway._tool_call_count == initial_count + 1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reconnect_server(self, mcp_gateway):
        """Test reconnecting to a specific server."""
        mock_server = AsyncMock(spec=MCPServerConnection)
        mock_server.disconnect = AsyncMock()
        mock_server.connect = AsyncMock()
        mock_server.discover_tools = AsyncMock(return_value={"tool1": {"name": "tool1"}})
        
        mcp_gateway.servers = {"test-server": mock_server}
        
        await mcp_gateway._reconnect_server("test-server")
        
        mock_server.disconnect.assert_called_once()
        mock_server.connect.assert_called_once()
        mock_server.discover_tools.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_tool_schema(self, mcp_gateway):
        """Test retrieving tool schema."""
        mcp_gateway.available_tools = {
            "test_tool": {
                "name": "test_tool",
                "description": "Test tool",
                "inputSchema": {"type": "object"}
            }
        }
        
        schema = mcp_gateway._get_tool_schema("test_tool")
        
        assert schema is not None
        assert schema["name"] == "test_tool"
        assert schema["description"] == "Test tool"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_tool_schema_not_found(self, mcp_gateway):
        """Test retrieving schema for unknown tool."""
        mcp_gateway.available_tools = {}
        
        schema = mcp_gateway._get_tool_schema("unknown_tool")
        
        assert schema is None