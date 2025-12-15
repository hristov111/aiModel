"""Embedding generation using sentence-transformers."""

import threading
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import logging

from app.core.config import settings
from app.core.exceptions import EmbeddingGenerationError

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Thread-safe singleton for generating embeddings using sentence-transformers."""
    
    _instance: Optional['EmbeddingGenerator'] = None
    _lock = threading.Lock()
    _model: Optional[SentenceTransformer] = None
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the embedding generator (lazy loading)."""
        if self._model is None:
            self._load_model()
    
    def _load_model(self) -> None:
        """Load the sentence-transformers model."""
        try:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self._model = SentenceTransformer(settings.embedding_model)
            logger.info(f"Embedding model loaded successfully. Dimension: {self._model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise EmbeddingGenerationError(f"Failed to load embedding model: {e}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        if not text or not text.strip():
            raise EmbeddingGenerationError("Cannot generate embedding for empty text")
        
        try:
            # Normalize whitespace
            text = " ".join(text.split())
            
            # Generate embedding
            embedding = self._model.encode(text, convert_to_numpy=True)
            
            # Convert to list and return
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise EmbeddingGenerationError(f"Failed to generate embedding: {e}")
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (more efficient than individual calls).
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingGenerationError: If batch embedding generation fails
        """
        if not texts:
            return []
        
        try:
            # Normalize whitespace for all texts
            normalized_texts = [" ".join(text.split()) for text in texts]
            
            # Generate embeddings in batch
            embeddings = self._model.encode(normalized_texts, convert_to_numpy=True, batch_size=32)
            
            # Convert to list of lists
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise EmbeddingGenerationError(f"Failed to generate batch embeddings: {e}")
    
    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        if self._model is None:
            self._load_model()
        return self._model.get_sentence_embedding_dimension()


# Global instance
_embedding_generator: Optional[EmbeddingGenerator] = None


def get_embedding_generator() -> EmbeddingGenerator:
    """Get or create the global embedding generator instance."""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator

