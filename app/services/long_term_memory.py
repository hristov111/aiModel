"""Long-term memory service facade combining retrieval and extraction."""

from typing import List
from uuid import UUID
import logging

from app.models.memory import Memory, Message
from app.repositories.vector_store import VectorStoreRepository
from app.services.memory_retrieval import MemoryRetrieval
from app.services.memory_extraction import MemoryExtractor
from app.utils.embeddings import EmbeddingGenerator
from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class LongTermMemoryService:
    """Facade service for long-term memory operations."""
    
    def __init__(
        self,
        vector_store: VectorStoreRepository,
        embedding_generator: EmbeddingGenerator,
        llm_client: LLMClient = None
    ):
        """
        Initialize long-term memory service.
        
        Args:
            vector_store: Vector store repository
            embedding_generator: Embedding generator
            llm_client: Optional LLM client for extraction
        """
        self.vector_store = vector_store
        self.retrieval = MemoryRetrieval(vector_store, embedding_generator)
        self.extraction = MemoryExtractor(vector_store, embedding_generator, llm_client)
    
    async def retrieve_relevant_memories(
        self,
        conversation_id: UUID,
        query_text: str,
        top_k: int = None
    ) -> List[Memory]:
        """
        Retrieve relevant memories for a query.
        
        Args:
            conversation_id: Conversation identifier
            query_text: Query text
            top_k: Number of memories to retrieve
            
        Returns:
            List of relevant memories
        """
        return await self.retrieval.retrieve_relevant(
            conversation_id=conversation_id,
            query_text=query_text,
            top_k=top_k
        )
    
    async def extract_and_store_memories(
        self,
        conversation_id: UUID,
        messages: List[Message]
    ) -> int:
        """
        Extract and store memories from messages.
        
        Args:
            conversation_id: Conversation identifier
            messages: Recent messages
            
        Returns:
            Number of memories stored
        """
        return await self.extraction.extract_and_store(
            conversation_id=conversation_id,
            messages=messages
        )
    
    async def clear_memories(self, conversation_id: UUID) -> int:
        """
        Clear all memories for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Number of memories cleared
        """
        return await self.vector_store.clear_conversation_memories(conversation_id)

