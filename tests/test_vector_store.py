"""Tests for vector store repository."""

import pytest
from uuid import uuid4
from app.repositories.vector_store import VectorStoreRepository
from app.models.memory import MemoryType


@pytest.mark.asyncio
async def test_store_and_search_memory(db_session):
    """Test storing and searching memories."""
    repo = VectorStoreRepository(db_session)
    conv_id = uuid4()
    
    # Create embedding (384-dim)
    embedding = [0.1] * 384
    
    # Store memory
    memory_id = await repo.store_memory(
        conversation_id=conv_id,
        content="I love programming in Python",
        embedding=embedding,
        memory_type=MemoryType.PREFERENCE,
        importance=0.8,
        metadata={"source": "test"}
    )
    
    assert memory_id is not None
    
    # Search for similar memories
    query_embedding = [0.1] * 384  # Similar embedding
    results = await repo.search_similar(
        conversation_id=conv_id,
        query_embedding=query_embedding,
        top_k=5,
        min_similarity=0.5
    )
    
    assert len(results) == 1
    assert results[0].content == "I love programming in Python"
    assert results[0].memory_type == MemoryType.PREFERENCE
    assert results[0].importance == 0.8


@pytest.mark.asyncio
async def test_search_no_results(db_session):
    """Test search with no matching results."""
    repo = VectorStoreRepository(db_session)
    conv_id = uuid4()
    
    # Search in empty database
    query_embedding = [0.1] * 384
    results = await repo.search_similar(
        conversation_id=conv_id,
        query_embedding=query_embedding,
        top_k=5
    )
    
    assert len(results) == 0


@pytest.mark.asyncio
async def test_clear_conversation_memories(db_session):
    """Test clearing all memories for a conversation."""
    repo = VectorStoreRepository(db_session)
    conv_id = uuid4()
    
    # Store multiple memories
    embedding = [0.1] * 384
    for i in range(3):
        await repo.store_memory(
            conversation_id=conv_id,
            content=f"Memory {i}",
            embedding=embedding,
            memory_type=MemoryType.FACT,
            importance=0.5
        )
    
    # Clear memories
    count = await repo.clear_conversation_memories(conv_id)
    
    assert count == 3
    
    # Verify cleared
    results = await repo.search_similar(
        conversation_id=conv_id,
        query_embedding=embedding,
        top_k=10
    )
    
    assert len(results) == 0


@pytest.mark.asyncio
async def test_delete_low_importance_memories(db_session):
    """Test deleting low importance memories."""
    repo = VectorStoreRepository(db_session)
    conv_id = uuid4()
    
    # Store memories with different importance
    embedding = [0.1] * 384
    await repo.store_memory(conv_id, "High importance", embedding, MemoryType.FACT, 0.9)
    await repo.store_memory(conv_id, "Medium importance", embedding, MemoryType.FACT, 0.5)
    await repo.store_memory(conv_id, "Low importance", embedding, MemoryType.FACT, 0.2)
    
    # Delete low importance (< 0.3)
    count = await repo.delete_low_importance_memories(conv_id, threshold=0.3)
    
    assert count == 1
    
    # Verify remaining
    results = await repo.search_similar(conv_id, embedding, top_k=10, min_similarity=0.0)
    
    assert len(results) == 2

