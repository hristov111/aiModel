"""Tests for short-term memory (conversation buffer)."""

import pytest
from uuid import uuid4
from app.services.short_term_memory import ConversationBuffer


def test_add_and_get_messages():
    """Test adding and retrieving messages."""
    buffer = ConversationBuffer(max_messages=5)
    conv_id = uuid4()
    
    buffer.add_message(conv_id, "user", "Hello")
    buffer.add_message(conv_id, "assistant", "Hi there!")
    
    messages = buffer.get_recent_messages(conv_id)
    
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "Hello"
    assert messages[1].role == "assistant"
    assert messages[1].content == "Hi there!"


def test_max_messages_limit():
    """Test that buffer respects max messages limit."""
    buffer = ConversationBuffer(max_messages=3)
    conv_id = uuid4()
    
    for i in range(5):
        buffer.add_message(conv_id, "user", f"Message {i}")
    
    messages = buffer.get_recent_messages(conv_id)
    
    assert len(messages) == 3
    assert messages[0].content == "Message 2"
    assert messages[-1].content == "Message 4"


def test_get_recent_n_messages():
    """Test getting last N messages."""
    buffer = ConversationBuffer(max_messages=10)
    conv_id = uuid4()
    
    for i in range(5):
        buffer.add_message(conv_id, "user", f"Message {i}")
    
    messages = buffer.get_recent_messages(conv_id, n=2)
    
    assert len(messages) == 2
    assert messages[0].content == "Message 3"


def test_summary_operations():
    """Test summary get and update."""
    buffer = ConversationBuffer()
    conv_id = uuid4()
    
    # Initially no summary
    assert buffer.get_or_create_summary(conv_id) is None
    
    # Update summary
    buffer.update_summary(conv_id, "This is a summary")
    
    # Retrieve summary
    assert buffer.get_or_create_summary(conv_id) == "This is a summary"


def test_reset_conversation():
    """Test resetting conversation."""
    buffer = ConversationBuffer()
    conv_id = uuid4()
    
    buffer.add_message(conv_id, "user", "Hello")
    buffer.update_summary(conv_id, "Summary")
    
    buffer.reset_conversation(conv_id)
    
    messages = buffer.get_recent_messages(conv_id)
    summary = buffer.get_or_create_summary(conv_id)
    
    assert len(messages) == 0
    assert summary == "Summary"  # Summary preserved


def test_clear_conversation():
    """Test clearing conversation completely."""
    buffer = ConversationBuffer()
    conv_id = uuid4()
    
    buffer.add_message(conv_id, "user", "Hello")
    buffer.update_summary(conv_id, "Summary")
    
    buffer.clear_conversation(conv_id)
    
    messages = buffer.get_recent_messages(conv_id)
    summary = buffer.get_or_create_summary(conv_id)
    
    assert len(messages) == 0
    assert summary is None


def test_multiple_conversations():
    """Test handling multiple conversations."""
    buffer = ConversationBuffer()
    conv1 = uuid4()
    conv2 = uuid4()
    
    buffer.add_message(conv1, "user", "Conv1 Message")
    buffer.add_message(conv2, "user", "Conv2 Message")
    
    messages1 = buffer.get_recent_messages(conv1)
    messages2 = buffer.get_recent_messages(conv2)
    
    assert len(messages1) == 1
    assert len(messages2) == 1
    assert messages1[0].content == "Conv1 Message"
    assert messages2[0].content == "Conv2 Message"

