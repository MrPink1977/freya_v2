"""
Unit tests for MessageBus

Tests the core message bus functionality including pub/sub operations.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.message_bus import MessageBus, MessageBusError


class TestMessageBus:
    """Test suite for MessageBus class."""

    @pytest.fixture
    async def message_bus(self, mock_redis):
        """Create a MessageBus instance with mocked Redis."""
        # Patch redis.asyncio.from_url which is what MessageBus actually uses
        with patch('redis.asyncio.from_url', new_callable=AsyncMock, return_value=mock_redis):
            bus = MessageBus(redis_host="localhost", redis_port=6379)
            yield bus
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test MessageBus initialization."""
        bus = MessageBus(redis_host="localhost", redis_port=6379)
        assert bus.redis_host == "localhost"
        assert bus.redis_port == 6379
        assert not bus.is_connected()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_connect(self, message_bus, mock_redis):
        """Test connecting to Redis."""
        await message_bus.connect()
        assert message_bus.is_connected()
        mock_redis.ping.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_disconnect(self, message_bus, mock_redis):
        """Test disconnecting from Redis."""
        await message_bus.connect()
        await message_bus.disconnect()
        assert not message_bus.is_connected()
        mock_redis.close.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_publish(self, message_bus, mock_redis):
        """Test publishing messages."""
        await message_bus.connect()
        
        test_channel = "test.channel"
        test_data = {"message": "hello", "value": 42}
        
        await message_bus.publish(test_channel, test_data)
        
        # Verify Redis publish was called
        assert mock_redis.publish.called
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe(self, message_bus):
        """Test subscribing to channels."""
        await message_bus.connect()
        
        callback = AsyncMock()
        test_channel = "test.channel"
        
        await message_bus.subscribe(test_channel, callback)

        # Verify subscription was registered
        assert test_channel in message_bus.subscribers
        assert callback in message_bus.subscribers[test_channel]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unsubscribe(self, message_bus):
        """Test unsubscribing from channels."""
        await message_bus.connect()

        callback = AsyncMock()
        test_channel = "test.channel"

        await message_bus.subscribe(test_channel, callback)
        await message_bus.unsubscribe(test_channel)

        # Verify channel was removed or emptied
        assert test_channel not in message_bus.subscribers or \
               len(message_bus.subscribers[test_channel]) == 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_publish_subscribe_flow(self, mock_message_bus):
        """Test complete publish/subscribe flow."""
        received_data = None
        
        async def callback(data):
            nonlocal received_data
            received_data = data
        
        test_channel = "test.flow"
        test_data = {"test": "data"}
        
        # Subscribe
        await mock_message_bus.subscribe(test_channel, callback)
        
        # Publish
        await mock_message_bus.publish(test_channel, test_data)
        
        # Wait a moment for message processing
        await asyncio.sleep(0.1)
        
        # Verify callback was invoked
        assert received_data == test_data
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, mock_message_bus):
        """Test multiple subscribers on same channel."""
        received_data1 = None
        received_data2 = None
        
        async def callback1(data):
            nonlocal received_data1
            received_data1 = data
        
        async def callback2(data):
            nonlocal received_data2
            received_data2 = data
        
        test_channel = "test.multi"
        test_data = {"multi": "subscriber"}
        
        # Subscribe both callbacks
        await mock_message_bus.subscribe(test_channel, callback1)
        await mock_message_bus.subscribe(test_channel, callback2)
        
        # Publish
        await mock_message_bus.publish(test_channel, test_data)
        await asyncio.sleep(0.1)
        
        # Both callbacks should receive the data
        assert received_data1 == test_data
        assert received_data2 == test_data
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Wildcard subscriptions not yet implemented in MessageBus")
    async def test_wildcard_subscription(self, mock_message_bus):
        """Test wildcard channel subscriptions."""
        received_messages = []

        async def callback(data):
            received_messages.append(data)

        # Subscribe to wildcard pattern
        await mock_message_bus.subscribe("service.*.status", callback)

        # Publish to matching channels
        await mock_message_bus.publish("service.stt.status", {"status": "running"})
        await mock_message_bus.publish("service.llm.status", {"status": "idle"})

        await asyncio.sleep(0.1)

        # Should receive both messages
        assert len(received_messages) == 2
