"""Tests for Redis-based distributed memory."""

import pytest
from uuid import uuid4
from app.services.redis_memory import RedisConversationBuffer


@pytest.mark.asyncio
class TestRedisMemory:
    """Test Redis-based conversation buffer."""
    
    async def test_redis_memory_fallback(self):
        """Test that Redis memory falls back to in-memory when Redis unavailable."""
        # Create buffer without Redis URL
        buffer = RedisConversationBuffer(redis_url=None, max_size=5)
        
        # Should work with in-memory fallback
        conversation_id = uuid4()
        
        await buffer.add_message(
            conversation_id,
            role="user",
            content="Hello"
        )
        
        messages = await buffer.get_messages(conversation_id)
        
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
    
    async def test_add_and_retrieve_messages(self):
        """Test adding and retrieving messages."""
        buffer = RedisConversationBuffer(redis_url=None, max_size=5)
        conversation_id = uuid4()
        
        # Add multiple messages
        await buffer.add_message(conversation_id, "user", "First message")
        await buffer.add_message(conversation_id, "assistant", "Response")
        await buffer.add_message(conversation_id, "user", "Follow-up")
        
        messages = await buffer.get_messages(conversation_id)
        
        assert len(messages) == 3
        assert messages[0]["content"] == "First message"
        assert messages[1]["content"] == "Response"
        assert messages[2]["content"] == "Follow-up"
    
    async def test_max_size_limit(self):
        """Test that buffer respects max size limit."""
        buffer = RedisConversationBuffer(redis_url=None, max_size=3)
        conversation_id = uuid4()
        
        # Add more messages than max size
        for i in range(5):
            await buffer.add_message(
                conversation_id,
                role="user",
                content=f"Message {i+1}"
            )
        
        messages = await buffer.get_messages(conversation_id)
        
        # Should only keep last 3 messages
        assert len(messages) == 3
        assert messages[0]["content"] == "Message 3"
        assert messages[2]["content"] == "Message 5"
    
    async def test_clear_conversation(self):
        """Test clearing conversation."""
        buffer = RedisConversationBuffer(redis_url=None, max_size=5)
        conversation_id = uuid4()
        
        # Add messages
        await buffer.add_message(conversation_id, "user", "Test")
        await buffer.add_message(conversation_id, "assistant", "Response")
        
        # Verify messages exist
        messages = await buffer.get_messages(conversation_id)
        assert len(messages) == 2
        
        # Clear conversation
        await buffer.clear_conversation(conversation_id)
        
        # Verify messages cleared
        messages = await buffer.get_messages(conversation_id)
        assert len(messages) == 0
    
    async def test_message_metadata(self):
        """Test storing message metadata."""
        buffer = RedisConversationBuffer(redis_url=None, max_size=5)
        conversation_id = uuid4()
        
        metadata = {
            "emotion": "happy",
            "confidence": 0.85
        }
        
        await buffer.add_message(
            conversation_id,
            role="user",
            content="I'm so happy!",
            metadata=metadata
        )
        
        messages = await buffer.get_messages(conversation_id)
        
        assert len(messages) == 1
        assert messages[0]["metadata"] == metadata

