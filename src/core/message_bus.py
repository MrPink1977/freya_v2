"""
Message Bus - Central event system for Freya v2.0

This module provides a Redis-based pub/sub message bus for decoupled
communication between all services.
"""

import asyncio
import json
from typing import Any, Callable, Dict, Optional
from loguru import logger
import redis.asyncio as aioredis


class MessageBus:
    """
    Asynchronous message bus using Redis pub/sub.
    
    All services communicate by publishing and subscribing to events
    on this bus, enabling loose coupling and independent scaling.
    """
    
    def __init__(self, redis_host: str = "redis", redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.subscribers: Dict[str, list[Callable]] = {}
        self._running = False
        
    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self.redis = await aioredis.from_url(
                f"redis://{self.redis_host}:{self.redis_port}",
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis.pubsub()
            logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        logger.info("Disconnected from Redis")
        
    async def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """
        Publish a message to a channel.
        
        Args:
            channel: The channel name (e.g., "audio.stream", "llm.response")
            message: The message payload as a dictionary
        """
        if not self.redis:
            raise RuntimeError("Message bus not connected")
            
        try:
            payload = json.dumps(message)
            await self.redis.publish(channel, payload)
            logger.debug(f"Published to {channel}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            
    async def subscribe(self, channel: str, callback: Callable) -> None:
        """
        Subscribe to a channel with a callback function.
        
        Args:
            channel: The channel name to subscribe to
            callback: Async function to call when a message is received
        """
        if channel not in self.subscribers:
            self.subscribers[channel] = []
            if self.pubsub:
                await self.pubsub.subscribe(channel)
                logger.info(f"Subscribed to channel: {channel}")
                
        self.subscribers[channel].append(callback)
        
    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a channel."""
        if channel in self.subscribers:
            del self.subscribers[channel]
            if self.pubsub:
                await self.pubsub.unsubscribe(channel)
                logger.info(f"Unsubscribed from channel: {channel}")
                
    async def start(self) -> None:
        """Start listening for messages."""
        if not self.pubsub:
            raise RuntimeError("Message bus not connected")
            
        self._running = True
        logger.info("Message bus started")
        
        async for message in self.pubsub.listen():
            if not self._running:
                break
                
            if message["type"] == "message":
                channel = message["channel"]
                data = json.loads(message["data"])
                
                # Call all registered callbacks for this channel
                if channel in self.subscribers:
                    for callback in self.subscribers[channel]:
                        try:
                            await callback(data)
                        except Exception as e:
                            logger.error(f"Error in callback for {channel}: {e}")
                            
    async def stop(self) -> None:
        """Stop listening for messages."""
        self._running = False
        logger.info("Message bus stopped")
