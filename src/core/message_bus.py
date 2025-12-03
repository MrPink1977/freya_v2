"""
Message Bus - Central event system for Freya v2.0

This module provides a Redis-based pub/sub message bus for decoupled
communication between all services.

Author: MrPink1977
Version: 0.1.0
Date: 2025-12-03
"""

import asyncio
import json
from typing import Any, Callable, Coroutine, Dict, List, Optional
from loguru import logger
import redis.asyncio as aioredis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError


class MessageBusError(Exception):
    """Base exception for MessageBus errors."""
    pass


class MessageBus:
    """
    Asynchronous message bus using Redis pub/sub.
    
    All services communicate by publishing and subscribing to events
    on this bus, enabling loose coupling and independent scaling.
    
    Attributes:
        redis_host (str): Redis server hostname
        redis_port (int): Redis server port
        redis (Optional[aioredis.Redis]): Redis client instance
        pubsub (Optional[aioredis.client.PubSub]): Redis pub/sub instance
        subscribers (Dict[str, List[Callable]]): Channel subscribers mapping
        
    Example:
        >>> bus = MessageBus("localhost", 6379)
        >>> await bus.connect()
        >>> await bus.subscribe("test.channel", my_callback)
        >>> await bus.publish("test.channel", {"data": "hello"})
        >>> await bus.disconnect()
    """
    
    def __init__(
        self, 
        redis_host: str = "redis", 
        redis_port: int = 6379,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> None:
        """
        Initialize the MessageBus.
        
        Args:
            redis_host: Redis server hostname (default: "redis")
            redis_port: Redis server port (default: 6379)
            max_retries: Maximum connection retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
            
        Raises:
            ValueError: If port is invalid
        """
        if not 1 <= redis_port <= 65535:
            raise ValueError(f"Invalid port number: {redis_port}")
            
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.subscribers: Dict[str, List[Callable[..., Coroutine[Any, Any, None]]]] = {}
        self._running = False
        self._connection_healthy = False
        
        logger.debug(
            f"MessageBus initialized: {redis_host}:{redis_port}, "
            f"max_retries={max_retries}, retry_delay={retry_delay}s"
        )
        
    async def connect(self) -> None:
        """
        Establish connection to Redis with retry logic.
        
        Raises:
            MessageBusError: If connection fails after all retries
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"Attempting to connect to Redis at {self.redis_host}:{self.redis_port} "
                    f"(attempt {attempt}/{self.max_retries})"
                )
                
                self.redis = await aioredis.from_url(
                    f"redis://{self.redis_host}:{self.redis_port}",
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0
                )
                
                # Test connection
                await self.redis.ping()
                
                self.pubsub = self.redis.pubsub()
                self._connection_healthy = True
                
                logger.success(
                    f"✓ Successfully connected to Redis at {self.redis_host}:{self.redis_port}"
                )
                return
                
            except (RedisConnectionError, RedisError) as e:
                logger.warning(
                    f"Connection attempt {attempt}/{self.max_retries} failed: {e}"
                )
                
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay}s...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    error_msg = (
                        f"Failed to connect to Redis after {self.max_retries} attempts. "
                        f"Please ensure Redis is running at {self.redis_host}:{self.redis_port}"
                    )
                    logger.error(error_msg)
                    raise MessageBusError(error_msg) from e
                    
            except Exception as e:
                logger.exception(f"Unexpected error connecting to Redis: {e}")
                raise MessageBusError(f"Unexpected connection error: {e}") from e
            
    async def disconnect(self) -> None:
        """
        Close Redis connection gracefully.
        
        This method ensures all resources are properly cleaned up.
        """
        try:
            if self.pubsub:
                logger.debug("Closing pub/sub connection...")
                await self.pubsub.close()
                self.pubsub = None
                
            if self.redis:
                logger.debug("Closing Redis connection...")
                await self.redis.close()
                self.redis = None
                
            self._connection_healthy = False
            logger.info("✓ Disconnected from Redis successfully")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            raise
        
    async def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """
        Publish a message to a channel.
        
        Args:
            channel: The channel name (e.g., "audio.stream", "llm.response")
            message: The message payload as a dictionary
            
        Raises:
            MessageBusError: If not connected or publish fails
            ValueError: If channel or message is invalid
            
        Example:
            >>> await bus.publish("llm.response", {
            ...     "text": "Hello!",
            ...     "location": "bedroom"
            ... })
        """
        if not channel or not isinstance(channel, str):
            raise ValueError(f"Invalid channel name: {channel}")
            
        if not isinstance(message, dict):
            raise ValueError(f"Message must be a dictionary, got {type(message)}")
            
        if not self.redis or not self._connection_healthy:
            raise MessageBusError("Message bus not connected. Call connect() first.")
            
        try:
            payload = json.dumps(message)
            await self.redis.publish(channel, payload)
            logger.debug(f"📤 Published to [{channel}]: {message}")
            
        except json.JSONEncodeError as e:
            logger.error(f"Failed to serialize message for {channel}: {e}")
            raise MessageBusError(f"Invalid message format: {e}") from e
            
        except RedisError as e:
            logger.error(f"Redis error publishing to {channel}: {e}")
            self._connection_healthy = False
            raise MessageBusError(f"Failed to publish message: {e}") from e
            
        except Exception as e:
            logger.exception(f"Unexpected error publishing to {channel}: {e}")
            raise MessageBusError(f"Unexpected publish error: {e}") from e
            
    async def subscribe(
        self, 
        channel: str, 
        callback: Callable[..., Coroutine[Any, Any, None]]
    ) -> None:
        """
        Subscribe to a channel with a callback function.
        
        Args:
            channel: The channel name to subscribe to
            callback: Async function to call when a message is received.
                     Must accept a single Dict argument.
                     
        Raises:
            MessageBusError: If not connected
            ValueError: If channel or callback is invalid
            
        Example:
            >>> async def my_handler(data: Dict[str, Any]) -> None:
            ...     print(f"Received: {data}")
            >>> await bus.subscribe("test.channel", my_handler)
        """
        if not channel or not isinstance(channel, str):
            raise ValueError(f"Invalid channel name: {channel}")
            
        if not callable(callback):
            raise ValueError(f"Callback must be callable, got {type(callback)}")
            
        if not self.pubsub:
            raise MessageBusError("Message bus not connected. Call connect() first.")
            
        try:
            if channel not in self.subscribers:
                self.subscribers[channel] = []
                await self.pubsub.subscribe(channel)
                logger.info(f"📥 Subscribed to channel: [{channel}]")
                
            self.subscribers[channel].append(callback)
            logger.debug(
                f"Added callback to [{channel}] "
                f"(total callbacks: {len(self.subscribers[channel])})"
            )
            
        except RedisError as e:
            logger.error(f"Redis error subscribing to {channel}: {e}")
            raise MessageBusError(f"Failed to subscribe: {e}") from e
            
        except Exception as e:
            logger.exception(f"Unexpected error subscribing to {channel}: {e}")
            raise MessageBusError(f"Unexpected subscribe error: {e}") from e
        
    async def unsubscribe(self, channel: str) -> None:
        """
        Unsubscribe from a channel.
        
        Args:
            channel: The channel name to unsubscribe from
            
        Raises:
            MessageBusError: If not connected
        """
        if channel in self.subscribers:
            try:
                del self.subscribers[channel]
                if self.pubsub:
                    await self.pubsub.unsubscribe(channel)
                logger.info(f"📤 Unsubscribed from channel: [{channel}]")
                
            except RedisError as e:
                logger.error(f"Redis error unsubscribing from {channel}: {e}")
                raise MessageBusError(f"Failed to unsubscribe: {e}") from e
                
    async def start(self) -> None:
        """
        Start listening for messages.
        
        This method runs indefinitely until stop() is called.
        It processes incoming messages and dispatches them to registered callbacks.
        
        Raises:
            MessageBusError: If not connected
        """
        if not self.pubsub:
            raise MessageBusError("Message bus not connected. Call connect() first.")
            
        self._running = True
        logger.info("🚀 Message bus started and listening...")
        
        try:
            async for message in self.pubsub.listen():
                if not self._running:
                    logger.info("Stop signal received, exiting message loop")
                    break
                    
                if message["type"] == "message":
                    channel = message["channel"]
                    
                    try:
                        data = json.loads(message["data"])
                        logger.debug(f"📨 Received on [{channel}]: {data}")
                        
                    except json.JSONDecodeError as e:
                        logger.error(
                            f"Failed to decode message from {channel}: {e}. "
                            f"Raw data: {message['data']}"
                        )
                        continue
                    
                    # Call all registered callbacks for this channel
                    if channel in self.subscribers:
                        for idx, callback in enumerate(self.subscribers[channel]):
                            try:
                                await callback(data)
                                
                            except Exception as e:
                                logger.exception(
                                    f"Error in callback #{idx} for channel [{channel}]: {e}. "
                                    f"Message: {data}"
                                )
                                # Continue processing other callbacks even if one fails
                                
        except asyncio.CancelledError:
            logger.info("Message bus listener cancelled")
            raise
            
        except Exception as e:
            logger.exception(f"Fatal error in message bus listener: {e}")
            self._running = False
            raise
                            
    async def stop(self) -> None:
        """
        Stop listening for messages.
        
        This signals the listener loop to exit gracefully.
        """
        if self._running:
            self._running = False
            logger.info("🛑 Message bus stop requested")
        else:
            logger.debug("Message bus already stopped")
            
    def is_connected(self) -> bool:
        """
        Check if the message bus is connected to Redis.
        
        Returns:
            True if connected and healthy, False otherwise
        """
        return self._connection_healthy and self.redis is not None
        
    def is_running(self) -> bool:
        """
        Check if the message bus is actively listening.
        
        Returns:
            True if running, False otherwise
        """
        return self._running
        
    async def health_check(self) -> bool:
        """
        Perform a health check on the Redis connection.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.redis:
            return False
            
        try:
            await self.redis.ping()
            self._connection_healthy = True
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            self._connection_healthy = False
            return False
