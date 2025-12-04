"""
Mock MCP Gateway Responses

Provides mock responses for MCP Gateway tool calls used in testing.
"""

from typing import Dict, Any, Optional
import time


def mock_elevenlabs_tts_response(
    text: str,
    voice_id: str,
    success: bool = True,
    audio_size: int = 16000
) -> Dict[str, Any]:
    """
    Generate a mock ElevenLabs TTS response.
    
    Args:
        text: Input text
        voice_id: Voice ID used
        success: Whether the call succeeded
        audio_size: Size of mock audio data in bytes
    
    Returns:
        Mock MCP tool response
    """
    if success:
        # Generate mock audio data (silence)
        mock_audio = b'\x00\x00' * (audio_size // 2)
        
        return {
            "success": True,
            "audio_data": mock_audio,
            "format": "mp3",
            "text": text,
            "voice_id": voice_id,
            "timestamp": time.time()
        }
    else:
        return {
            "success": False,
            "error": "Mock TTS error",
            "timestamp": time.time()
        }


def mock_mcp_tool_call(
    server: str,
    tool: str,
    arguments: Dict[str, Any],
    success: bool = True
) -> Dict[str, Any]:
    """
    Generate a generic mock MCP tool call response.
    
    Args:
        server: MCP server name
        tool: Tool name
        arguments: Tool arguments
        success: Whether the call succeeded
    
    Returns:
        Mock MCP tool response
    """
    if server == "elevenlabs" and tool == "text_to_speech":
        return mock_elevenlabs_tts_response(
            text=arguments.get("text", ""),
            voice_id=arguments.get("voice_id", "test_voice"),
            success=success
        )
    
    # Generic response for other tools
    if success:
        return {
            "success": True,
            "result": f"Mock result for {server}.{tool}",
            "timestamp": time.time()
        }
    else:
        return {
            "success": False,
            "error": f"Mock error for {server}.{tool}",
            "timestamp": time.time()
        }


def mock_mcp_tool_registry() -> Dict[str, Dict[str, Any]]:
    """
    Generate a mock MCP tool registry.
    
    Returns:
        Dictionary of mock tool definitions
    """
    return {
        "text_to_speech": {
            "name": "text_to_speech",
            "description": "Convert text to speech using ElevenLabs",
            "server": "elevenlabs",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "voice_id": {"type": "string"},
                    "model_id": {"type": "string"}
                },
                "required": ["text"]
            }
        }
    }
