"""Tests for prompt builder."""

import pytest
from datetime import datetime
from uuid import uuid4
from app.services.prompt_builder import PromptBuilder
from app.models.memory import Memory, Message, MemoryType


def test_build_system_prompt_basic():
    """Test basic system prompt building."""
    builder = PromptBuilder(persona="a helpful assistant")
    
    prompt = builder.build_system_prompt(
        relevant_memories=[],
        conversation_summary=None
    )
    
    assert "helpful assistant" in prompt
    assert "Instructions:" in prompt


def test_build_system_prompt_with_memories():
    """Test system prompt with memories."""
    builder = PromptBuilder()
    
    memories = [
        Memory(
            id=uuid4(),
            conversation_id=uuid4(),
            content="User likes Python programming",
            embedding=None,
            memory_type=MemoryType.PREFERENCE,
            importance=0.8,
            created_at=datetime.utcnow()
        )
    ]
    
    prompt = builder.build_system_prompt(
        relevant_memories=memories,
        conversation_summary=None
    )
    
    assert "Python programming" in prompt
    assert "preference" in prompt.lower()


def test_build_system_prompt_with_summary():
    """Test system prompt with conversation summary."""
    builder = PromptBuilder()
    
    prompt = builder.build_system_prompt(
        relevant_memories=[],
        conversation_summary="Previously discussed AI topics"
    )
    
    assert "Previously discussed AI topics" in prompt
    assert "Recent conversation summary:" in prompt


def test_build_chat_messages():
    """Test building chat messages."""
    builder = PromptBuilder()
    system_prompt = "You are helpful"
    
    recent_messages = [
        Message(role="user", content="Hello", timestamp=datetime.utcnow()),
        Message(role="assistant", content="Hi!", timestamp=datetime.utcnow())
    ]
    
    messages = builder.build_chat_messages(
        system_prompt=system_prompt,
        recent_messages=recent_messages,
        current_user_message="How are you?"
    )
    
    assert len(messages) == 4  # system + 2 history + current
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == system_prompt
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "How are you?"


def test_format_memory_for_display():
    """Test memory formatting."""
    builder = PromptBuilder()
    
    memory = Memory(
        id=uuid4(),
        conversation_id=uuid4(),
        content="Test memory content",
        embedding=None,
        memory_type=MemoryType.FACT,
        importance=0.75,
        created_at=datetime.utcnow(),
        similarity_score=0.92
    )
    
    formatted = builder.format_memory_for_display(memory)
    
    assert "Test memory content" in formatted
    assert "0.75" in formatted
    assert "0.92" in formatted

