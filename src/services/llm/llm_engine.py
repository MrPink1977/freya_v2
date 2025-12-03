"""
LLM Engine - Core reasoning component for Freya v2.0

Manages the local LLM (via Ollama), handles conversation context,
and generates responses based on user input and retrieved memories.
"""

from typing import Optional, List, Dict
from loguru import logger
import ollama

from src.core.base_service import BaseService
from src.core.message_bus import MessageBus
from src.core.config import config


class LLMEngine(BaseService):
    """
    LLM Engine service for generating intelligent responses.
    
    Subscribes to: stt.transcription
    Publishes to: llm.response, memory.query, tool.query
    """
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("llm_engine", message_bus)
        self.client: Optional[ollama.AsyncClient] = None
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt with Freya's personality."""
        return f"""You are {config.personality_name}, a witty, intelligent, and helpful personal AI assistant.

Your personality traits:
- Witty and playfully sarcastic when appropriate
- Excellent at your job - accurate and helpful
- Context-aware: you know when to be serious vs. playful
- Natural conversationalist who remembers past interactions

You have access to various tools and can remember user preferences. Always be helpful while maintaining your unique personality."""
        
    async def initialize(self) -> None:
        """Initialize the Ollama client."""
        try:
            self.client = ollama.AsyncClient(host=config.ollama_host)
            
            # Test connection and pull model if needed
            logger.info(f"Connecting to Ollama at {config.ollama_host}")
            await self.client.pull(config.ollama_model)
            
            self._healthy = True
            logger.info(f"LLM Engine initialized with model: {config.ollama_model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM Engine: {e}")
            self._healthy = False
            raise
            
    async def start(self) -> None:
        """Start the LLM Engine service."""
        self._running = True
        
        # Subscribe to transcribed text from STT
        await self.message_bus.subscribe("stt.transcription", self._handle_transcription)
        
        await self.publish_status("started")
        logger.info("LLM Engine started")
        
    async def stop(self) -> None:
        """Stop the LLM Engine service."""
        self._running = False
        await self.message_bus.unsubscribe("stt.transcription")
        await self.publish_status("stopped")
        logger.info("LLM Engine stopped")
        
    async def _handle_transcription(self, data: Dict) -> None:
        """
        Handle incoming transcription from STT service.
        
        Args:
            data: {"text": str, "location": str, "timestamp": float}
        """
        user_text = data.get("text", "")
        location = data.get("location", "unknown")
        
        if not user_text:
            return
            
        logger.info(f"[{location}] User: {user_text}")
        
        # TODO: Query memory for relevant context
        # TODO: Determine if tools are needed
        
        # Generate response
        response = await self._generate_response(user_text, location)
        
        # Publish response for TTS
        await self.message_bus.publish("llm.response", {
            "text": response,
            "location": location,
            "timestamp": data.get("timestamp")
        })
        
    async def _generate_response(self, user_input: str, location: str) -> str:
        """
        Generate a response using the LLM.
        
        Args:
            user_input: The user's transcribed speech
            location: The location where the user is speaking from
            
        Returns:
            Generated response text
        """
        if not self.client:
            return "I'm having trouble thinking right now. Give me a moment."
            
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Keep only last 10 exchanges to manage context window
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # Generate response
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history
            
            response = await self.client.chat(
                model=config.ollama_model,
                messages=messages
            )
            
            assistant_response = response['message']['content']
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })
            
            logger.info(f"[{location}] Freya: {assistant_response}")
            return assistant_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error while processing that."
