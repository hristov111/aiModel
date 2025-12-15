"""Tests for API endpoints."""

import pytest
from uuid import uuid4


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test root endpoint."""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AI Companion Service"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data
    assert "llm" in data


@pytest.mark.asyncio
async def test_reset_conversation(client):
    """Test conversation reset endpoint."""
    conv_id = uuid4()
    
    response = await client.post(
        "/conversation/reset",
        json={"conversation_id": str(conv_id)}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["conversation_id"] == str(conv_id)


@pytest.mark.asyncio
async def test_clear_memory(client):
    """Test memory clear endpoint."""
    conv_id = uuid4()
    
    response = await client.post(
        "/memory/clear",
        json={"conversation_id": str(conv_id)}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["conversation_id"] == str(conv_id)


@pytest.mark.asyncio
async def test_chat_validation(client):
    """Test chat endpoint input validation."""
    # Empty message
    response = await client.post(
        "/chat",
        json={"message": ""}
    )
    
    assert response.status_code == 422  # Validation error

