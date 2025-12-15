"""Tests for embedding generation."""

import pytest
from app.utils.embeddings import EmbeddingGenerator, get_embedding_generator


def test_embedding_generator_singleton():
    """Test that EmbeddingGenerator is a singleton."""
    gen1 = get_embedding_generator()
    gen2 = get_embedding_generator()
    assert gen1 is gen2


def test_generate_embedding():
    """Test single embedding generation."""
    generator = get_embedding_generator()
    text = "This is a test sentence for embedding."
    
    embedding = generator.generate_embedding(text)
    
    assert isinstance(embedding, list)
    assert len(embedding) == 384  # all-MiniLM-L6-v2 dimension
    assert all(isinstance(x, float) for x in embedding)


def test_batch_generate_embeddings():
    """Test batch embedding generation."""
    generator = get_embedding_generator()
    texts = [
        "First sentence",
        "Second sentence",
        "Third sentence"
    ]
    
    embeddings = generator.batch_generate_embeddings(texts)
    
    assert len(embeddings) == 3
    assert all(len(emb) == 384 for emb in embeddings)


def test_empty_text_error():
    """Test that empty text raises error."""
    generator = get_embedding_generator()
    
    with pytest.raises(Exception):
        generator.generate_embedding("")


def test_embedding_dimension():
    """Test embedding dimension property."""
    generator = get_embedding_generator()
    assert generator.dimension == 384

