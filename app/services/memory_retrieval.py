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
            # Enhance query for better retrieval (especially for questions)
            enhanced_query = self._enhance_query(query_text)
            logger.debug(f"Query: '{query_text[:50]}...' → Enhanced: '{enhanced_query[:50]}...'")
            
            # Generate query embedding
            logger.debug(f"Generating embedding for query: {enhanced_query[:50]}...")
            query_embedding = self.embedding_generator.generate_embedding(enhanced_query)
            logger.info(f"Generated embedding with {len(query_embedding)} dimensions")
            
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
    
    def _enhance_query(self, query_text: str) -> str:
        """
        Enhance query for better retrieval by rewriting questions into statement form.
        
        Examples:
        - "What is my name?" → "my name"
        - "What do I like?" → "I like"
        - "Where do I live?" → "I live"
        - "Do I like chocolate?" → "I like chocolate"
        
        Args:
            query_text: Original query text
            
        Returns:
            Enhanced query text
        """
        import re
        
        query_lower = query_text.lower().strip()
        
        # Pattern 1: "What is my X?" → "my X"
        match = re.match(r"what(?:'s| is) my (\w+)", query_lower)
        if match:
            return f"my {match.group(1)}"
        
        # Pattern 2: "What do I X?" → "I X"
        match = re.match(r"what do i (\w+)", query_lower)
        if match:
            return f"I {match.group(1)}"
        
        # Pattern 3: "Where do I X?" → "I X"
        match = re.match(r"where do i (\w+)", query_lower)
        if match:
            return f"I {match.group(1)}"
        
        # Pattern 4: "Do I X Y?" → "I X Y"
        match = re.match(r"do i (.+)\?", query_lower)
        if match:
            return f"I {match.group(1)}"
        
        # Pattern 5: "Am I X?" → "I am X"
        match = re.match(r"am i (.+)\?", query_lower)
        if match:
            return f"I am {match.group(1)}"
        
        # Pattern 6: "Did I X?" → "I X"
        match = re.match(r"did i (.+)\?", query_lower)
        if match:
            return f"I {match.group(1)}"
        
        # Pattern 7: "Have I X?" → "I X"
        match = re.match(r"have i (.+)\?", query_lower)
        if match:
            return f"I {match.group(1)}"
        
        # Pattern 8: Remove question marks and question words for generic questions
        if query_lower.endswith('?'):
            # Remove common question starters
            enhanced = re.sub(r'^(what|where|when|why|how|who|which|do|does|did|is|are|was|were|can|could|should|would)\s+', '', query_lower)
            enhanced = enhanced.rstrip('?').strip()
            if enhanced:
                return enhanced
        
        # Return original if no pattern matches
        return query_text
    
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
                if memory.metadata is None:
                    memory.metadata = {}
                memory.metadata['combined_score'] = combined_score
        
        # Sort by combined score
        memories.sort(
            key=lambda m: m.metadata.get('combined_score', 0) if m.metadata else 0,
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

