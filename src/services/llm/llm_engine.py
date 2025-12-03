"""
LLM Engine - Core reasoning component for Freya v2.0

Manages the local LLM (via Ollama), handles conversation context,
and generates responses based on user input and retrieved memories.

Author: MrPink1977
Version: 0.1.0
Date: 2025-12-03
"""

from typing import Optional, List, Dict, Any
from loguru import logger
import ollama
from datetime import datetime
import asyncio
import uuid

from src.core.base_service import BaseService, ServiceError
from src.core.message_bus import MessageBus
from src.core.config import config


class LLMEngineError(ServiceError):
    """Exception raised for LLM Engine specific errors."""
    pass


class LLMEngine(BaseService):
    """
    LLM Engine service for generating intelligent responses.
    
    This service manages the local LLM, maintains conversation history,
    and coordinates with other services (memory, tools) to generate
    contextually aware responses.
    
    Subscribes to:
        - stt.transcription: Incoming user speech transcriptions
        
    Publishes to:
        - llm.response: Generated responses for TTS
        - memory.query: Memory retrieval requests
        - tool.query: Tool execution requests
        - llm.thinking: Internal reasoning process (for GUI)
        
    Attributes:
        client: Ollama async client instance
        conversation_history: List of recent conversation messages
        system_prompt: System prompt defining Freya's personality
        max_history_length: Maximum conversation history to maintain
        
    Example:
        >>> llm = LLMEngine(message_bus)
        >>> await llm.initialize()
        >>> await llm.start()
    """
    
    def __init__(self, message_bus: MessageBus) -> None:
        """
        Initialize the LLM Engine.
        
        Args:
            message_bus: Shared MessageBus instance
        """
        super().__init__("llm_engine", message_bus)
        self.client: Optional[ollama.AsyncClient] = None
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = self._build_system_prompt()
        self.max_history_length = config.memory_max_short_term
        self._generation_count = 0
        self._total_tokens = 0

        # Tool calling support (Phase 1.5)
        self.available_tools: Dict[str, Any] = {}
        self.tool_call_count = 0
        self._pending_tool_results: Dict[str, Any] = {}

        logger.debug(f"[{self.name}] Initialized with model: {config.ollama_model}")
        
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt with Freya's personality.
        
        Returns:
            System prompt string
        """
        personality_traits = {
            "witty_sarcastic": """You are witty, playfully sarcastic, and engaging. 
You know when to be serious and when to add humor. You're excellent at your job 
and provide accurate, helpful responses while maintaining your unique charm.""",
            "professional": """You are professional, courteous, and efficient. 
You provide clear, accurate information and maintain a respectful tone.""",
            "casual": """You are friendly, casual, and approachable. 
You speak naturally and make users feel comfortable.""",
            "friendly": """You are warm, supportive, and encouraging. 
You're always positive and helpful."""
        }
        
        personality_desc = personality_traits.get(
            config.personality_style, 
            personality_traits["witty_sarcastic"]
        )
        
        return f"""You are {config.personality_name}, a personal AI assistant.

{personality_desc}

Key capabilities:
- You have access to various tools and can perform actions
- You remember past conversations and user preferences
- You are location-aware and know which room the user is in
- You can be proactive and offer helpful suggestions

Always be helpful, accurate, and maintain your personality consistently."""
        
    async def initialize(self) -> None:
        """
        Initialize the Ollama client and pull the model.
        
        Raises:
            LLMEngineError: If initialization fails
        """
        try:
            logger.info(f"[{self.name}] Initializing Ollama client...")
            logger.info(f"[{self.name}] Host: {config.ollama_host}")
            logger.info(f"[{self.name}] Model: {config.ollama_model}")
            
            self.client = ollama.AsyncClient(
                host=config.ollama_host,
                timeout=config.ollama_timeout
            )
            
            # Test connection
            try:
                logger.info(f"[{self.name}] Testing Ollama connection...")
                await asyncio.wait_for(
                    self.client.list(),
                    timeout=10.0
                )
                logger.success(f"[{self.name}] ✓ Connected to Ollama successfully")
            except asyncio.TimeoutError:
                raise LLMEngineError(
                    f"Timeout connecting to Ollama at {config.ollama_host}. "
                    "Please ensure Ollama is running."
                )
            
            # Pull model if needed
            logger.info(f"[{self.name}] Ensuring model {config.ollama_model} is available...")
            try:
                await self.client.pull(config.ollama_model)
                logger.success(f"[{self.name}] ✓ Model {config.ollama_model} ready")
            except Exception as e:
                logger.warning(
                    f"[{self.name}] Could not pull model {config.ollama_model}: {e}. "
                    "Will attempt to use existing model."
                )
            
            self._healthy = True
            logger.success(f"[{self.name}] ✓ LLM Engine initialized successfully")
            
        except LLMEngineError:
            raise
        except Exception as e:
            error_msg = f"Failed to initialize LLM Engine: {e}"
            logger.exception(f"[{self.name}] {error_msg}")
            self._healthy = False
            raise LLMEngineError(error_msg) from e
            
    async def start(self) -> None:
        """
        Start the LLM Engine service.
        
        Raises:
            LLMEngineError: If service fails to start
        """
        try:
            if not self._healthy:
                raise LLMEngineError("Cannot start unhealthy service. Call initialize() first.")
                
            self._mark_started()

            # Subscribe to transcribed text from STT
            await self.message_bus.subscribe("stt.transcription", self._handle_transcription)
            logger.info(f"[{self.name}] Subscribed to stt.transcription")

            # Subscribe to tool registry from MCP Gateway (Phase 1.5)
            if config.mcp_enabled:
                await self.message_bus.subscribe("mcp.tool.registry", self._handle_tool_registry)
                await self.message_bus.subscribe("mcp.tool.result", self._handle_tool_result)
                logger.info(f"[{self.name}] Subscribed to MCP tool channels")

            await self.publish_status("started", {
                "model": config.ollama_model,
                "personality": config.personality_style,
                "tools_enabled": config.mcp_enabled
            })
            
            logger.success(f"[{self.name}] ✓ LLM Engine started and ready")
            
        except Exception as e:
            error_msg = f"Failed to start LLM Engine: {e}"
            logger.exception(f"[{self.name}] {error_msg}")
            raise LLMEngineError(error_msg) from e
        
    async def stop(self) -> None:
        """
        Stop the LLM Engine service.
        
        Raises:
            LLMEngineError: If service fails to stop
        """
        try:
            logger.info(f"[{self.name}] Stopping LLM Engine...")

            await self.message_bus.unsubscribe("stt.transcription")
            logger.debug(f"[{self.name}] Unsubscribed from stt.transcription")

            # Unsubscribe from MCP channels if enabled
            if config.mcp_enabled:
                await self.message_bus.unsubscribe("mcp.tool.registry")
                await self.message_bus.unsubscribe("mcp.tool.result")
                logger.debug(f"[{self.name}] Unsubscribed from MCP tool channels")

            self._mark_stopped()
            
            await self.publish_status("stopped", {
                "total_generations": self._generation_count,
                "total_tokens": self._total_tokens
            })
            
            logger.success(f"[{self.name}] ✓ LLM Engine stopped successfully")
            
        except Exception as e:
            error_msg = f"Failed to stop LLM Engine: {e}"
            logger.exception(f"[{self.name}] {error_msg}")
            raise LLMEngineError(error_msg) from e
        
    async def _handle_transcription(self, data: Dict[str, Any]) -> None:
        """
        Handle incoming transcription from STT service.
        
        Args:
            data: Message containing:
                - text (str): Transcribed user speech
                - location (str): Where the user is speaking from
                - timestamp (float): When the speech was captured
                - confidence (float, optional): Transcription confidence
        """
        try:
            user_text = data.get("text", "").strip()
            location = data.get("location", "unknown")
            timestamp = data.get("timestamp", datetime.now().timestamp())
            confidence = data.get("confidence")
            
            if not user_text:
                logger.warning(f"[{self.name}] Received empty transcription from {location}")
                return
                
            logger.info(
                f"[{self.name}] 📝 [{location}] User: \"{user_text}\" "
                f"(confidence: {confidence:.2f})" if confidence else ""
            )
            
            # Publish thinking status for GUI
            await self.message_bus.publish("llm.thinking", {
                "status": "processing",
                "input": user_text,
                "location": location
            })
            
            # TODO Phase 4: Query memory for relevant context
            # memory_context = await self._query_memory(user_text)
            
            # TODO Phase 3: Determine if tools are needed
            # tool_results = await self._execute_tools_if_needed(user_text)
            
            # Generate response
            start_time = datetime.now()
            response = await self._generate_response(user_text, location)
            generation_time = (datetime.now() - start_time).total_seconds()
            
            # Publish metrics
            await self.publish_metric("generation_time", generation_time, "seconds")
            await self.publish_metric("input_length", len(user_text), "characters")
            await self.publish_metric("output_length", len(response), "characters")
            
            # Publish response for TTS
            await self.message_bus.publish("llm.response", {
                "text": response,
                "location": location,
                "timestamp": timestamp,
                "generation_time": generation_time
            })
            
            logger.info(
                f"[{self.name}] 💬 [{location}] Freya: \"{response}\" "
                f"({generation_time:.2f}s)"
            )
            
        except Exception as e:
            logger.exception(f"[{self.name}] Error handling transcription: {e}")
            self.increment_error_count()
            
            # Send error response
            await self.message_bus.publish("llm.response", {
                "text": "I'm sorry, I encountered an error processing that. Could you try again?",
                "location": data.get("location", "unknown"),
                "error": True
            })
        
    async def _generate_response(self, user_input: str, location: str) -> str:
        """
        Generate a response using the LLM.
        
        Args:
            user_input: The user's transcribed speech
            location: The location where the user is speaking from
            
        Returns:
            Generated response text
            
        Raises:
            LLMEngineError: If generation fails
        """
        if not self.client:
            raise LLMEngineError("LLM client not initialized")
            
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Trim history to max length (keep pairs of user/assistant messages)
            if len(self.conversation_history) > self.max_history_length:
                # Keep the most recent messages
                self.conversation_history = self.conversation_history[-self.max_history_length:]
                logger.debug(
                    f"[{self.name}] Trimmed conversation history to "
                    f"{len(self.conversation_history)} messages"
                )
            
            # Build messages for LLM
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history
            
            # Add location context
            if location != "unknown":
                messages.append({
                    "role": "system",
                    "content": f"Note: The user is currently at the {location}."
                })
            
            logger.debug(f"[{self.name}] Generating response with {len(messages)} messages")

            # Prepare tools for Ollama if available and MCP is enabled
            tools_param = None
            if config.mcp_enabled and self.available_tools:
                tools_param = list(self.available_tools.values())
                logger.debug(
                    f"[{self.name}] Including {len(tools_param)} tools in LLM call"
                )

            # Generate response (with potential tool calls)
            max_tool_iterations = 5  # Prevent infinite tool calling loops
            iteration = 0

            while iteration < max_tool_iterations:
                iteration += 1

                # Call LLM
                response = await self.client.chat(
                    model=config.ollama_model,
                    messages=messages,
                    tools=tools_param,
                    options={
                        "temperature": config.ollama_temperature,
                    }
                )

                assistant_message = response['message']

                # Check if LLM wants to call tools
                tool_calls = assistant_message.get('tool_calls')

                if not tool_calls:
                    # No tool calls - we have the final response
                    assistant_response = assistant_message.get('content', '').strip()
                    break

                # LLM wants to call tools
                logger.info(
                    f"[{self.name}] 🔧 LLM requested {len(tool_calls)} tool call(s)"
                )

                # Add assistant's tool call message to history
                messages.append(assistant_message)

                # Execute each tool call
                for tool_call in tool_calls:
                    function = tool_call.get('function', {})
                    tool_name = function.get('name')
                    arguments = function.get('arguments', {})

                    try:
                        # Execute the tool
                        result = await self._execute_tool_call(tool_name, arguments)

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "content": str(result)
                        })

                    except LLMEngineError as e:
                        logger.error(f"[{self.name}] Tool execution failed: {e}")
                        # Add error as tool result
                        messages.append({
                            "role": "tool",
                            "content": f"Error executing {tool_name}: {str(e)}"
                        })

                # Continue loop to let LLM process tool results
                logger.debug(
                    f"[{self.name}] Tool execution complete, getting final response..."
                )

            else:
                # Hit max iterations
                logger.warning(
                    f"[{self.name}] Reached max tool calling iterations ({max_tool_iterations})"
                )
                assistant_response = "I apologize, but I'm having trouble completing that request. Could you try rephrasing it?"
            
            # Track metrics
            self._generation_count += 1
            if 'eval_count' in response:
                self._total_tokens += response['eval_count']
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })
            
            logger.debug(
                f"[{self.name}] Generated response: {len(assistant_response)} characters, "
                f"total generations: {self._generation_count}"
            )
            
            return assistant_response
            
        except ollama.ResponseError as e:
            error_msg = f"Ollama API error: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.increment_error_count()
            raise LLMEngineError(error_msg) from e
            
        except asyncio.TimeoutError as e:
            error_msg = f"LLM generation timed out after {config.ollama_timeout}s"
            logger.error(f"[{self.name}] {error_msg}")
            self.increment_error_count()
            raise LLMEngineError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error generating response: {e}"
            logger.exception(f"[{self.name}] {error_msg}")
            self.increment_error_count()
            raise LLMEngineError(error_msg) from e

    async def _handle_tool_registry(self, data: Dict[str, Any]) -> None:
        """
        Handle tool registry updates from MCP Gateway.

        Args:
            data: Tool registry message with format:
                {
                    "tools": List[Dict],
                    "tool_count": int,
                    "servers": List[str],
                    "timestamp": str
                }
        """
        try:
            tools = data.get("tools", [])
            tool_count = data.get("tool_count", 0)

            # Convert to format suitable for Ollama
            self.available_tools = {}
            for tool in tools:
                tool_name = tool.get("name")
                if tool_name:
                    self.available_tools[tool_name] = {
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "description": tool.get("description", ""),
                            "parameters": tool.get("inputSchema", {})
                        }
                    }

            logger.info(
                f"[{self.name}] 🔧 Tool registry updated: {tool_count} tools available"
            )

            if config.mcp_log_tool_calls:
                logger.debug(
                    f"[{self.name}] Available tools: {list(self.available_tools.keys())}"
                )

        except Exception as e:
            logger.error(f"[{self.name}] Error handling tool registry: {e}")

    async def _handle_tool_result(self, data: Dict[str, Any]) -> None:
        """
        Handle tool execution results from MCP Gateway.

        Args:
            data: Tool result message with format:
                {
                    "request_id": str,
                    "tool_name": str,
                    "result": Any,
                    "success": bool,
                    "error": str (optional),
                    "duration": float
                }
        """
        try:
            request_id = data.get("request_id")
            if request_id:
                self._pending_tool_results[request_id] = data

        except Exception as e:
            logger.error(f"[{self.name}] Error handling tool result: {e}")

    async def _execute_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool call via MCP Gateway.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            LLMEngineError: If tool execution fails
        """
        try:
            request_id = str(uuid.uuid4())

            logger.info(f"[{self.name}] 🔧 Executing tool: {tool_name}")

            if config.mcp_log_tool_calls:
                logger.debug(f"[{self.name}] Tool arguments: {arguments}")

            # Send tool execution request
            await self.message_bus.publish("mcp.tool.execute", {
                "request_id": request_id,
                "tool_name": tool_name,
                "arguments": arguments
            })

            # Wait for result (with timeout)
            timeout = config.mcp_tool_timeout
            start_time = datetime.now()

            while (datetime.now() - start_time).total_seconds() < timeout:
                if request_id in self._pending_tool_results:
                    result_data = self._pending_tool_results.pop(request_id)

                    if result_data.get("success"):
                        logger.success(
                            f"[{self.name}] ✓ Tool '{tool_name}' completed in "
                            f"{result_data.get('duration', 0):.2f}s"
                        )
                        self.tool_call_count += 1
                        return result_data.get("result")
                    else:
                        error = result_data.get("error", "Unknown error")
                        raise LLMEngineError(f"Tool execution failed: {error}")

                await asyncio.sleep(0.1)

            # Timeout
            raise LLMEngineError(
                f"Tool execution timed out after {timeout}s"
            )

        except LLMEngineError:
            raise
        except Exception as e:
            error_msg = f"Tool execution error for '{tool_name}': {e}"
            logger.error(f"[{self.name}] {error_msg}")
            raise LLMEngineError(error_msg) from e

    async def health_check(self) -> bool:
        """
        Perform a health check on the LLM Engine.
        
        Returns:
            True if healthy, False otherwise
        """
        if not await super().health_check():
            return False
            
        try:
            if not self.client:
                return False
                
            # Test if we can list models
            await asyncio.wait_for(self.client.list(), timeout=5.0)
            return True
            
        except Exception as e:
            logger.warning(f"[{self.name}] Health check failed: {e}")
            return False
            
    def clear_history(self) -> None:
        """Clear the conversation history."""
        history_length = len(self.conversation_history)
        self.conversation_history.clear()
        logger.info(f"[{self.name}] Cleared {history_length} messages from conversation history")
        
    def get_history_length(self) -> int:
        """
        Get the current conversation history length.
        
        Returns:
            Number of messages in history
        """
        return len(self.conversation_history)
