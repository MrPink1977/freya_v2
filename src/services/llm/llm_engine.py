"""
LLM Engine - Core reasoning component for Freya v2.0

Manages the local LLM (via Ollama), handles conversation context,
and generates responses based on user input and retrieved memories.

Author: MrPink1977
Version: 0.2.0
Date: 2024-12-06
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
from src.core.retry import retry_with_backoff, RetryExhaustedError
from src.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


class LLMEngineError(ServiceError):
    """LLM Engine specific errors."""
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
        
        # Circuit breaker for Ollama calls
        self.ollama_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30.0,
            expected_exception=Exception,
            name="OllamaCircuitBreaker"
        )
        
        # Tool calling support
        self.available_tools: Dict[str, Any] = {}
        self.tool_call_count = 0
        self._pending_tool_results: Dict[str, Any] = {}

        logger.debug(f"[{self.name}] Initialized with model: {config.ollama.model}")
        
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
You communicate in a relaxed, conversational style.""",
            "friendly": """You are warm, supportive, and genuinely interested in helping. 
You balance professionalism with a personal touch."""
        }
        
        personality_style = config.personality_style
        personality_desc = personality_traits.get(
            personality_style,
            personality_traits["friendly"]
        )
        
        return f"""You are Freya, a voice-first AI assistant with genuine personality.

{personality_desc}

CORE CAPABILITIES:
- You have access to tools for time/date, calculations, file operations, web search, 
  web scraping, system info, commands, and performance monitoring
- Use tools naturally without announcing "I will use tool X"
- You have both short-term (this conversation) and long-term (across sessions) memory
- You're running locally on the user's computer for privacy

COMMUNICATION STYLE:
- Keep responses concise and natural for voice interaction
- Be conversational, not robotic
- Show appropriate emotion and personality
- Ask follow-up questions when helpful

CURRENT CONTEXT:
- Today's date: {datetime.now().strftime('%Y-%m-%d')}
- You're in voice mode - keep responses brief unless detail is requested
"""

    async def initialize(self) -> None:
        """
        Initialize the LLM Engine service.
        
        Connects to Ollama and verifies the model is available.
        
        Raises:
            LLMEngineError: If initialization fails
        """
        try:
            logger.info(f"[{self.name}] Initializing LLM Engine...")
            
            # Initialize Ollama client
            self.client = ollama.AsyncClient(host=config.ollama.host)
            
            # Test connection with timeout
            try:
                await asyncio.wait_for(
                    self.client.list(),
                    timeout=10.0
                )
                logger.success(f"[{self.name}] ✓ Connected to Ollama successfully")
            except asyncio.TimeoutError:
                raise LLMEngineError(
                    f"Timeout connecting to Ollama at {config.ollama.host}. "
                    "Please ensure Ollama is running."
                )
            
            # Pull model if needed
            logger.info(f"[{self.name}] Ensuring model {config.ollama.model} is available...")
            try:
                await self.client.pull(config.ollama.model)
                logger.success(f"[{self.name}] ✓ Model {config.ollama.model} ready")
            except Exception as e:
                logger.warning(
                    f"[{self.name}] Could not pull model {config.ollama.model}: {e}. "
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
        
        Subscribes to message bus topics and begins processing.
        """
        try:
            logger.info(f"[{self.name}] Starting LLM Engine...")
            
            # Subscribe to transcriptions
            await self.message_bus.subscribe("stt.transcription", self._handle_transcription)
            
            # Subscribe to GUI messages
            await self.message_bus.subscribe("gui.user_message", self._handle_gui_message)
            
            # Subscribe to tool registry updates
            await self.message_bus.subscribe("mcp.tool_registry", self._handle_tool_registry)
            
            self._running = True
            logger.success(f"[{self.name}] ✓ LLM Engine started successfully")
            
        except Exception as e:
            error_msg = f"Failed to start LLM Engine: {e}"
            logger.exception(f"[{self.name}] {error_msg}")
            raise LLMEngineError(error_msg) from e
            
    async def stop(self) -> None:
        """Stop the LLM Engine service."""
        try:
            logger.info(f"[{self.name}] Stopping LLM Engine...")
            self._running = False
            
            # Unsubscribe from topics
            await self.message_bus.unsubscribe("stt.transcription", self._handle_transcription)
            await self.message_bus.unsubscribe("gui.user_message", self._handle_gui_message)
            await self.message_bus.unsubscribe("mcp.tool_registry", self._handle_tool_registry)
            
            logger.success(f"[{self.name}] ✓ LLM Engine stopped")
            
        except Exception as e:
            logger.exception(f"[{self.name}] Error stopping LLM Engine: {e}")
            raise LLMEngineError(f"Failed to stop LLM Engine: {e}") from e

    async def _handle_transcription(self, data: Dict[str, Any]) -> None:
        """
        Handle incoming transcription from STT service.
        
        Args:
            data: Message containing:
                - text (str): Transcribed user speech
                - location (str): Source location identifier
                - timestamp (str): ISO format timestamp
        """
        try:
            user_text = data.get("text", "").strip()
            location = data.get("location", "unknown")
            timestamp = data.get("timestamp", datetime.now().isoformat())
            
            if not user_text:
                logger.warning(f"[{self.name}] Received empty transcription")
                return
            
            logger.info(
                f"[{self.name}] 🎤 [{location}] User: \"{user_text}\""
            )
            
            # Publish thinking status
            await self.message_bus.publish("llm.thinking", {
                "status": "processing",
                "input": user_text,
                "location": location
            })
            
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
            
        except CircuitBreakerOpenError as e:
            logger.error(f"[{self.name}] Circuit breaker open: {e}")
            await self.message_bus.publish("llm.response", {
                "text": "I'm having trouble thinking right now. Give me a moment to recover.",
                "location": data.get("location", "unknown"),
                "error": True
            })
            
        except RetryExhaustedError as e:
            logger.error(f"[{self.name}] All retries exhausted: {e}")
            await self.message_bus.publish("llm.response", {
                "text": "I'm sorry, I'm having persistent issues. Please try again in a moment.",
                "location": data.get("location", "unknown"),
                "error": True
            })
            
        except Exception as e:
            logger.exception(f"[{self.name}] Error handling transcription: {e}")
            self.increment_error_count()
            
            await self.message_bus.publish("llm.response", {
                "text": "I'm sorry, I encountered an error processing that. Could you try again?",
                "location": data.get("location", "unknown"),
                "error": True
            })

    async def _handle_gui_message(self, data: Dict[str, Any]) -> None:
        """
        Handle incoming user messages from GUI.

        Args:
            data: Message containing:
                - content (str): User's message text
                - source (str): Source identifier ("web_gui")
                - timestamp (str): ISO format timestamp
        """
        try:
            user_text = data.get("content", "").strip()
            source = data.get("source", "web_gui")
            timestamp_str = data.get("timestamp", datetime.now().isoformat())

            if not user_text:
                logger.warning(f"[{self.name}] Received empty message from GUI")
                return

            logger.info(
                f"[{self.name}] 📝 [GUI] User: \"{user_text}\""
            )

            # Publish thinking status for GUI
            await self.message_bus.publish("llm.thinking", {
                "status": "processing",
                "input": user_text,
                "location": source
            })

            # Generate response
            start_time = datetime.now()
            response = await self._generate_response(user_text, source)
            generation_time = (datetime.now() - start_time).total_seconds()

            # Publish response for GUI
            await self.message_bus.publish("llm.response", {
                "text": response,
                "location": source,
                "timestamp": timestamp_str,
                "generation_time": generation_time
            })

            logger.info(
                f"[{self.name}] 💬 [GUI] Freya: \"{response}\" "
                f"({generation_time:.2f}s)"
            )

        except CircuitBreakerOpenError as e:
            logger.error(f"[{self.name}] Circuit breaker open: {e}")
            await self.message_bus.publish("llm.response", {
                "text": "I'm having trouble thinking right now. Give me a moment to recover.",
                "location": data.get("source", "web_gui"),
                "error": True
            })
            
        except RetryExhaustedError as e:
            logger.error(f"[{self.name}] All retries exhausted: {e}")
            await self.message_bus.publish("llm.response", {
                "text": "I'm sorry, I'm having persistent issues. Please try again in a moment.",
                "location": data.get("source", "web_gui"),
                "error": True
            })
            
        except Exception as e:
            logger.exception(f"[{self.name}] Error handling GUI message: {e}")
            self.increment_error_count()

            await self.message_bus.publish("llm.response", {
                "text": "I'm sorry, I encountered an error processing that. Could you try again?",
                "location": data.get("source", "web_gui"),
                "error": True
            })

    @retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        exceptions=(ollama.ResponseError, asyncio.TimeoutError, ConnectionError)
    )
    async def _call_ollama_with_retry(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call Ollama API with retry logic and circuit breaker protection.
        
        Args:
            model: Model name
            messages: Conversation messages
            tools: Available tools for function calling
            options: Generation options
            
        Returns:
            Ollama response dictionary
            
        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            RetryExhaustedError: If all retries failed
        """
        # Check circuit breaker
        if self.ollama_breaker.is_open:
            raise CircuitBreakerOpenError(
                "Ollama service is temporarily unavailable. Please try again in a moment."
            )
        
        try:
            response = await self.client.chat(
                model=model,
                messages=messages,
                tools=tools,
                options=options or {}
            )
            
            # Success - reset circuit breaker failure count
            self.ollama_breaker._on_success()
            return response
            
        except Exception as e:
            # Record failure in circuit breaker
            self.ollama_breaker._on_failure(e)
            raise

    async def _generate_response(
        self,
        user_text: str,
        location: str = "unknown"
    ) -> str:
        """
        Generate a response using the LLM.
        
        Args:
            user_text: User's input text
            location: Source location identifier
            
        Returns:
            Generated response text
            
        Raises:
            LLMEngineError: If generation fails
        """
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_text
            })
            
            # Trim history if needed
            if len(self.conversation_history) > self.max_history_length:
                self.conversation_history = self.conversation_history[-self.max_history_length:]
            
            # Build messages for LLM
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history
            
            # Prepare tools for function calling
            tools_param = None
            if self.available_tools:
                tools_param = list(self.available_tools.values())
                logger.debug(f"[{self.name}] Available tools: {len(tools_param)}")

            # Generate response (with potential tool calls)
            max_tool_iterations = 5
            iteration = 0

            while iteration < max_tool_iterations:
                iteration += 1

                # Call LLM with retry protection
                response = await self._call_ollama_with_retry(
                    model=config.ollama.model,
                    messages=messages,
                    tools=tools_param,
                    options={"temperature": config.ollama.options.get("temperature", 0.7)}
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

                # Add assistant message with tool calls to history
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
            
        except CircuitBreakerOpenError:
            raise
        except RetryExhaustedError:
            raise
        except ollama.ResponseError as e:
            error_msg = f"Ollama API error: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.increment_error_count()
            raise LLMEngineError(error_msg) from e
            
        except asyncio.TimeoutError as e:
            error_msg = f"LLM generation timed out"
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
            data: Tool registry data containing available tools
        """
        try:
            tools = data.get("tools", {})
            self.available_tools = tools
            logger.info(
                f"[{self.name}] Updated tool registry: {len(tools)} tools available"
            )
        except Exception as e:
            logger.exception(f"[{self.name}] Error updating tool registry: {e}")

    async def _execute_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Execute a tool call via MCP Gateway.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            LLMEngineError: If tool execution fails
        """
        try:
            call_id = str(uuid.uuid4())
            
            logger.info(
                f"[{self.name}] Executing tool: {tool_name} with args: {arguments}"
            )
            
            # Publish tool execution request
            await self.message_bus.publish("mcp.tool_call", {
                "call_id": call_id,
                "tool_name": tool_name,
                "arguments": arguments
            })
            
            # Wait for result with timeout
            timeout = 30.0
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                if call_id in self._pending_tool_results:
                    result = self._pending_tool_results.pop(call_id)
                    
                    if result.get("error"):
                        raise LLMEngineError(f"Tool error: {result['error']}")
                    
                    return result.get("result", "Tool executed successfully")
                
                await asyncio.sleep(0.1)
            
            raise LLMEngineError(f"Tool execution timeout: {tool_name}")
            
        except LLMEngineError:
            raise
        except Exception as e:
            error_msg = f"Failed to execute tool {tool_name}: {e}"
            logger.exception(f"[{self.name}] {error_msg}")
            raise LLMEngineError(error_msg) from e

    async def get_status(self) -> Dict[str, Any]:
        """
        Get current LLM Engine status.
        
        Returns:
            Status dictionary with metrics and health info
        """
        return {
            "service": self.name,
            "healthy": self._healthy,
            "running": self._running,
            "model": config.ollama.model,
            "ollama_host": config.ollama.host,
            "conversation_length": len(self.conversation_history),
            "generation_count": self._generation_count,
            "total_tokens": self._total_tokens,
            "available_tools": len(self.available_tools),
            "circuit_breaker": self.ollama_breaker.get_stats(),
            "error_count": self._error_count
        }

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        logger.info(f"[{self.name}] Conversation history cleared")