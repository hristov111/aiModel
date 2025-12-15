"""Memory retrieval service with semantic search and re-ranking."""

from typing import List
from uuid import UUID
import logging

from app.models.memory import Memory
from app.repositories.vector_store import VectorStoreRepository
from app.utils.embeddings import EmbeddingGenerator
from app.core.config import settings
from app.core.exceptions import MemoryRetrievalError

logger = logging.getLogger(__name__)


class MemoryRetrieval:
    """Service for retrieving relevant long-term memories."""
    
    def __init__(
        self,
        vector_store: VectorStoreRepository,
        embedding_generator: EmbeddingGenerator
    ):
        """
        Initialize memory retrieval service.
        
        Args:
            vector_store: Vector store repository instance
            embedding_generator: Embedding generator instance
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
    
    async def retrieve_relevant(
        self,
        conversation_id: UUID,
        query_text: str,
        top_k: int = None
    ) -> List[Memory]:
        """
        Retrieve relevant memories for a query.
        
        Args:
            conversation_id: Conversation identifier
            query_text: Query text to search for
            top_k: Number of memories to retrieve (default from config)
            
        Returns:
            List of relevant memories, sorted by relevance
            
        Raises:
            MemoryRetrievalError: If retrieval fails
        """
        if top_k is None:
            top_k = settings.long_term_memory_top_k
        
        try:
            # Generate query embedding
            logger.debug(f"Generating embedding for query: {query_text[:50]}...")
            query_embedding = self.embedding_generator.generate_embedding(query_text)
            
            # Search vector store
            memories = await self.vector_store.search_similar(
                conversation_id=conversation_id,
                query_embedding=query_embedding,
                top_k=top_k * 2,  # Retrieve more for re-ranking
                min_similarity=settings.memory_similarity_threshold
            )
            
            if not memories:
                logger.debug(f"No relevant memories found for conversation {conversation_id}")
                return []
            
            # Re-rank by combined score (similarity * importance)
            memories = self._rerank_memories(memories)
            
            # Deduplicate similar memories
            memories = self._deduplicate_memories(memories)
            
            # Return top-K after re-ranking
            result = memories[:top_k]
            
            logger.info(f"Retrieved {len(result)} relevant memories for conversation {conversation_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            raise MemoryRetrievalError(f"Failed to retrieve memories: {e}")
    
    def _rerank_memories(self, memories: List[Memory]) -> List[Memory]:
        """
        Re-rank memories by combined score.
        
        Args:
            memories: List of memories with similarity scores
            
        Returns:
            Sorted list of memories
        """
        # Calculate combined score: similarity * importance
        for memory in memories:
            if memory.similarity_score is not None:
                combined_score = memory.similarity_score * memory.importance
                # Store in metadata for debugging
                if memory.extra_metadata is None:
                    memory.extra_metadata = {}
                memory.extra_metadata['combined_score'] = combined_score
        
        # Sort by combined score
        memories.sort(
            key=lambda m: m.extra_metadata.get('combined_score', 0) if m.extra_metadata else 0,
            reverse=True
        )
        
        return memories
    
    def _deduplicate_memories(self, memories: List[Memory], similarity_threshold: float = 0.95) -> List[Memory]:
        """
        Remove near-duplicate memories.
        
        Args:
            memories: List of memories
            similarity_threshold: Threshold for considering memories duplicates
            
        Returns:
            Deduplicated list of memories
        """
        if len(memories) <= 1:
            return memories
        
        deduplicated = []
        seen_contents = []
        
        for memory in memories:
            # Simple content-based deduplication
            content_lower = memory.content.lower().strip()
            
            # Check if very similar to any seen content
            is_duplicate = False
            for seen in seen_contents:
                # Simple similarity check (could be improved with embedding comparison)
                if content_lower == seen or (
                    len(content_lower) > 20 and
                    (content_lower in seen or seen in content_lower)
                ):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(memory)
                seen_contents.append(content_lower)
        
        if len(deduplicated) < len(memories):
            logger.debug(f"Deduplicated {len(memories) - len(deduplicated)} similar memories")
        
        return deduplicated

