"""
TTS Service - Text-to-Speech Service for Freya v2.0

Provides text-to-speech capabilities using ElevenLabs via MCP Gateway.
Subscribes to LLM responses and generates audio output.

Author: Claude (AI Assistant)
Version: 0.1.0
Date: 2025-12-04
"""

from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
import time
from loguru import logger

from src.core.base_service import BaseService, ServiceError
from src.core.message_bus import MessageBus
from src.core.config import config


class TTSServiceError(ServiceError):
    """Exception raised for TTS Service specific errors."""
    pass


class TTSService(BaseService):
    """
    Text-to-Speech Service using ElevenLabs via MCP Gateway.
    
    Converts text responses from the LLM into speech audio using the
    ElevenLabs TTS API through the MCP Gateway.
    
    Subscribes to:
        - llm.final_response: LLM text responses to convert to speech
        - tts.generate: Direct TTS generation requests
    
    Publishes to:
        - audio.output.stream: Generated audio data for playback
        - service.tts_service.status: Service status updates
        - service.tts_service.metrics: Performance metrics
    
    Attributes:
        mcp_gateway: Reference to MCP Gateway for tool calls
        generation_count: Total number of TTS generations
        total_characters: Total characters processed
        total_generation_time: Total time spent generating audio
    """
    
    def __init__(self, message_bus: MessageBus) -> None:
        """
        Initialize the TTS Service.
        
        Args:
            message_bus: Shared MessageBus instance
        """
        super().__init__("tts_service", message_bus)
        
        self.mcp_gateway: Optional[Any] = None  # Will be set after MCP Gateway starts
        self.generation_count = 0
        self.total_characters = 0
        self.total_generation_time = 0.0
        
        # Configuration
        self.voice_id = config.elevenlabs_voice_id
        self.model = config.elevenlabs_model
        self.stability = config.elevenlabs_stability
        self.similarity_boost = config.elevenlabs_similarity_boost
        
        logger.debug(
            f"[{self.name}] Initialized with voice_id={self.voice_id}, "
            f"model={self.model}"
        )
    
    async def initialize(self) -> None:
        """
        Initialize the TTS Service.
        
        Raises:
            TTSServiceError: If initialization fails
        """
        try:
            logger.info(f"[{self.name}] Initializing TTS Service...")
            
            # Verify ElevenLabs API key is configured
            if not config.elevenlabs_api_key:
                logger.warning(
                    f"[{self.name}] ⚠️  ElevenLabs API key not configured. "
                    "Set ELEVENLABS_API_KEY environment variable."
                )
                # Service can still initialize, but TTS calls will fail
            
            self._healthy = True
            logger.success(f"[{self.name}] ✓ TTS Service initialized")
            
        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Initialization failed: {e}")
            self._healthy = False
            self.increment_error_count()
            raise TTSServiceError(f"Initialization failed: {e}") from e
    
    async def start(self) -> None:
        """
        Start the TTS Service.
        
        Subscribes to message bus channels and begins processing.
        
        Raises:
            TTSServiceError: If service fails to start
        """
        try:
            logger.info(f"[{self.name}] Starting TTS Service...")
            
            # Subscribe to LLM responses
            await self.message_bus.subscribe(
                "llm.final_response",
                self._handle_llm_response
            )
            
            # Subscribe to direct TTS requests
            await self.message_bus.subscribe(
                "tts.generate",
                self._handle_tts_request
            )
            
            self._mark_started()
            await self.publish_status("started", {
                "voice_id": self.voice_id,
                "model": self.model
            })
            
            logger.success(f"[{self.name}] ✓ TTS Service started")
            
        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Failed to start: {e}")
            self.increment_error_count()
            raise TTSServiceError(f"Service start failed: {e}") from e
    
    async def stop(self) -> None:
        """
        Stop the TTS Service gracefully.
        """
        try:
            logger.info(f"[{self.name}] Stopping TTS Service...")
            
            # Unsubscribe from message bus
            await self.message_bus.unsubscribe("llm.final_response")
            await self.message_bus.unsubscribe("tts.generate")
            
            self._mark_stopped()
            await self.publish_status("stopped", {
                "total_generations": self.generation_count,
                "total_characters": self.total_characters
            })
            
            logger.success(f"[{self.name}] ✓ TTS Service stopped")
            
        except Exception as e:
            logger.exception(f"[{self.name}] ❌ Error during shutdown: {e}")
            self.increment_error_count()
            raise TTSServiceError(f"Service stop failed: {e}") from e
    
    async def health_check(self) -> bool:
        """
        Check if the TTS Service is healthy.
        
        Returns:
            True if service is operational, False otherwise
        """
        if not await super().health_check():
            return False
        
        # Could add additional checks here (e.g., MCP Gateway availability)
        return True
    
    # Message Bus Handlers
    
    async def _handle_llm_response(self, data: Dict[str, Any]) -> None:
        """
        Handle LLM response and generate speech.
        
        Args:
            data: LLM response data containing text and metadata
        """
        try:
            text = data.get("response") or data.get("text")
            if not text:
                logger.warning(f"[{self.name}] Received LLM response with no text")
                return
            
            # Filter out very short responses (might be errors or acknowledgments)
            if len(text.strip()) < 3:
                logger.debug(f"[{self.name}] Skipping very short response: {text}")
                return
            
            logger.info(
                f"[{self.name}] 🎙️  Generating speech for LLM response "
                f"({len(text)} characters)..."
            )
            
            # Generate audio
            audio_data = await self._generate_speech(text, data.get("location"))
            
            if audio_data:
                # Publish to audio output stream
                await self.message_bus.publish("audio.output.stream", {
                    "audio_data": audio_data,
                    "format": "mp3",
                    "source": "tts",
                    "text": text,
                    "location": data.get("location"),
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.success(
                    f"[{self.name}] ✓ Speech generated and published "
                    f"({len(audio_data)} bytes)"
                )
            
        except Exception as e:
            logger.error(f"[{self.name}] Error handling LLM response: {e}")
            self.increment_error_count()
    
    async def _handle_tts_request(self, data: Dict[str, Any]) -> None:
        """
        Handle direct TTS generation request.
        
        Args:
            data: TTS request data with text and optional parameters
        """
        try:
            text = data.get("text")
            if not text:
                logger.warning(f"[{self.name}] Received TTS request with no text")
                return
            
            logger.info(
                f"[{self.name}] 🎙️  Generating speech for direct request "
                f"({len(text)} characters)..."
            )
            
            # Use custom voice settings if provided
            voice_id = data.get("voice_id", self.voice_id)
            
            # Generate audio
            audio_data = await self._generate_speech(
                text,
                data.get("location"),
                voice_id=voice_id
            )
            
            if audio_data:
                # Publish to audio output stream
                await self.message_bus.publish("audio.output.stream", {
                    "audio_data": audio_data,
                    "format": "mp3",
                    "source": "tts_direct",
                    "text": text,
                    "location": data.get("location"),
                    "request_id": data.get("request_id"),
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.success(f"[{self.name}] ✓ Direct TTS completed")
            
        except Exception as e:
            logger.error(f"[{self.name}] Error handling TTS request: {e}")
            self.increment_error_count()
    
    # Core TTS Methods
    
    async def _generate_speech(
        self,
        text: str,
        location: Optional[str] = None,
        voice_id: Optional[str] = None,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> Optional[bytes]:
        """
        Generate speech audio from text using ElevenLabs via MCP Gateway.
        
        Args:
            text: Text to convert to speech
            location: Optional location context
            voice_id: Voice ID to use (defaults to configured voice)
            retry_count: Current retry attempt
            max_retries: Maximum number of retries
        
        Returns:
            Audio data as bytes, or None if generation fails
        """
        try:
            start_time = time.time()
            
            # Use provided voice_id or default
            voice = voice_id or self.voice_id
            
            # Prepare MCP tool call arguments
            tool_args = {
                "text": text,
                "voice_id": voice,
                "model_id": self.model,
                "voice_settings": {
                    "stability": self.stability,
                    "similarity_boost": self.similarity_boost
                }
            }
            
            logger.debug(
                f"[{self.name}] Calling ElevenLabs via MCP with voice={voice}"
            )
            
            # Call ElevenLabs TTS via MCP Gateway
            # Note: This assumes the MCP Gateway has an elevenlabs server configured
            result = await self._call_mcp_tool("elevenlabs", "text_to_speech", tool_args)
            
            # Extract audio data from result
            if not result or not result.get("success"):
                error_msg = result.get("error", "Unknown error") if result else "No result"
                logger.error(
                    f"[{self.name}] TTS generation failed: {error_msg}"
                )
                return None
            
            audio_data = result.get("audio_data")
            if not audio_data:
                logger.error(f"[{self.name}] No audio data in MCP response")
                return None
            
            # Update metrics
            generation_time = time.time() - start_time
            self.generation_count += 1
            self.total_characters += len(text)
            self.total_generation_time += generation_time
            
            # Publish metrics
            await self.publish_metrics({
                "generation_count": self.generation_count,
                "avg_generation_time": self.total_generation_time / self.generation_count,
                "total_characters": self.total_characters,
                "last_generation_time": generation_time,
                "last_text_length": len(text)
            })
            
            logger.debug(
                f"[{self.name}] Speech generated in {generation_time:.2f}s "
                f"({len(audio_data)} bytes)"
            )
            
            return audio_data
            
        except Exception as e:
            logger.error(f"[{self.name}] Speech generation error: {e}")
            self.increment_error_count()
            
            # Retry logic
            if retry_count < max_retries:
                retry_delay = 2 ** retry_count  # Exponential backoff
                logger.info(
                    f"[{self.name}] Retrying speech generation in {retry_delay}s "
                    f"(attempt {retry_count + 1}/{max_retries})..."
                )
                await asyncio.sleep(retry_delay)
                return await self._generate_speech(
                    text,
                    location,
                    voice_id,
                    retry_count + 1,
                    max_retries
                )
            
            logger.error(
                f"[{self.name}] Speech generation failed after {max_retries} retries"
            )
            return None
    
    async def _call_mcp_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call an MCP tool via the message bus.
        
        Args:
            server_name: MCP server name
            tool_name: Tool name
            arguments: Tool arguments
        
        Returns:
            Tool execution result
        """
        # Generate request ID
        request_id = f"tts_{int(time.time() * 1000)}"
        
        # Publish tool execution request
        await self.message_bus.publish("mcp.tool.execute", {
            "request_id": request_id,
            "server": server_name,
            "tool_name": tool_name,
            "arguments": arguments,
            "timestamp": datetime.now().isoformat()
        })
        
        # Wait for result (with timeout)
        # In a production system, this would use a proper request-response pattern
        # For now, we'll use a simple polling approach
        
        result_received = asyncio.Event()
        result_data = {}
        
        async def result_handler(data: Dict[str, Any]):
            nonlocal result_data
            if data.get("request_id") == request_id:
                result_data = data
                result_received.set()
        
        # Subscribe to results
        await self.message_bus.subscribe("mcp.tool.result", result_handler)
        
        try:
            # Wait for result with timeout
            await asyncio.wait_for(result_received.wait(), timeout=30.0)
            return result_data
        except asyncio.TimeoutError:
            logger.error(f"[{self.name}] MCP tool call timed out")
            return {"success": False, "error": "Timeout waiting for MCP result"}
        finally:
            await self.message_bus.unsubscribe("mcp.tool.result")
