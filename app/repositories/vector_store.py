"""Vector store repository for long-term memory with pgvector."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.database import MemoryModel, ConversationModel, MemoryTypeEnum
from app.models.memory import Memory, MemoryType
from app.core.exceptions import MemoryStorageError, MemoryRetrievalError

logger = logging.getLogger(__name__)


class VectorStoreRepository:
    """Repository for managing memories with vector embeddings in PostgreSQL."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize vector store repository.
        
        Args:
            session: Async database session
        """
        self.session = session
    
    async def ensure_conversation_exists(self, conversation_id: UUID, user_db_id: UUID) -> None:
        """
        Ensure a conversation record exists.
        
        Args:
            conversation_id: Conversation identifier
            user_db_id: User's database UUID (not external_user_id)
        """
        try:
            result = await self.session.execute(
                select(ConversationModel).where(ConversationModel.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            
            if conversation is None:
                conversation = ConversationModel(
                    id=conversation_id,
                    user_id=user_db_id
                )
                self.session.add(conversation)
                await self.session.flush()
                logger.debug(f"Created new conversation: {conversation_id} for user: {user_db_id}")
        except Exception as e:
            logger.error(f"Error ensuring conversation exists: {e}")
            raise MemoryStorageError(f"Failed to create conversation: {e}")
    
    async def store_memory(
        self,
        conversation_id: UUID,
        content: str,
        embedding: List[float],
        memory_type: MemoryType,
        importance: float,
        metadata: Optional[dict] = None,
        user_db_id: Optional[UUID] = None
    ) -> UUID:
        """
        Store a new memory with its embedding.
        
        Args:
            conversation_id: Conversation identifier
            content: Memory content text
            embedding: Vector embedding
            memory_type: Type of memory
            importance: Importance score (0.0 to 1.0)
            metadata: Optional metadata dictionary
            user_db_id: User's database UUID (required for new conversations)
            
        Returns:
            UUID of the created memory
            
        Raises:
            MemoryStorageError: If storage fails
        """
        try:
            # Ensure conversation exists (only create if user_db_id provided)
            if user_db_id:
                await self.ensure_conversation_exists(conversation_id, user_db_id)
            
            # Convert domain MemoryType to database enum
            db_memory_type = MemoryTypeEnum[memory_type.value.upper()]
            
            # Create memory record
            memory = MemoryModel(
                conversation_id=conversation_id,
                content=content,
                embedding=embedding,
                memory_type=db_memory_type,
                importance=importance,
                metadata=metadata or {}
            )
            
            self.session.add(memory)
            await self.session.flush()
            
            logger.debug(f"Stored memory {memory.id} for conversation {conversation_id}")
            return memory.id
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            raise MemoryStorageError(f"Failed to store memory: {e}")
    
    async def search_similar(
        self,
        conversation_id: UUID,
        query_embedding: List[float],
        top_k: int = 5,
        min_similarity: float = 0.7,
        user_external_id: Optional[str] = None
    ) -> List[Memory]:
        """
        Search for similar memories using vector similarity.
        
        Args:
            conversation_id: Conversation identifier
            query_embedding: Query vector embedding
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            user_external_id: Optional user ID for additional security check
            
        Returns:
            List of similar memories with similarity scores
            
        Raises:
            MemoryRetrievalError: If search fails
        """
        try:
            from app.models.database import UserModel
            
            # Use pgvector cosine similarity operator (<=>)
            # Note: <=> returns distance, so lower is better (0 = identical)
            # Similarity = 1 - distance
            query_builder = (
                select(
                    MemoryModel,
                    (1 - MemoryModel.embedding.cosine_distance(query_embedding)).label('similarity')
                )
                .where(MemoryModel.conversation_id == conversation_id)
                .where((1 - MemoryModel.embedding.cosine_distance(query_embedding)) >= min_similarity)
            )
            
            # Add user ownership check if user_external_id provided
            if user_external_id:
                from app.models.database import UserModel
                query_builder = query_builder.join(ConversationModel).join(UserModel).where(
                    UserModel.external_user_id == user_external_id
                )
            
            query = query_builder.order_by(
                (1 - MemoryModel.embedding.cosine_distance(query_embedding)).desc()
            ).limit(top_k)
            
            result = await self.session.execute(query)
            rows = result.all()
            
            # Convert to domain Memory objects
            memories = []
            for row in rows:
                memory_model, similarity = row
                memory = Memory(
                    id=memory_model.id,
                    conversation_id=memory_model.conversation_id,
                    content=memory_model.content,
                    embedding=None,  # Don't return embedding in results
                    memory_type=MemoryType(memory_model.memory_type.value),
                    importance=memory_model.importance,
                    created_at=memory_model.created_at,
                    metadata=memory_model.metadata,
                    similarity_score=float(similarity)
                )
                memories.append(memory)
            
            logger.debug(f"Found {len(memories)} similar memories for conversation {conversation_id}")
            return memories
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise MemoryRetrievalError(f"Failed to search memories: {e}")
    
    async def clear_conversation_memories(self, conversation_id: UUID) -> int:
        """
        Delete all memories for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Number of memories deleted
        """
        try:
            result = await self.session.execute(
                delete(MemoryModel).where(MemoryModel.conversation_id == conversation_id)
            )
            count = result.rowcount
            logger.info(f"Deleted {count} memories for conversation {conversation_id}")
            return count
        except Exception as e:
            logger.error(f"Error clearing memories: {e}")
            raise MemoryStorageError(f"Failed to clear memories: {e}")
    
    async def delete_low_importance_memories(
        self,
        conversation_id: UUID,
        threshold: float = 0.3
    ) -> int:
        """
        Delete memories below an importance threshold (cleanup).
        
        Args:
            conversation_id: Conversation identifier
            threshold: Minimum importance to keep
            
        Returns:
            Number of memories deleted
        """
        try:
            result = await self.session.execute(
                delete(MemoryModel).where(
                    and_(
                        MemoryModel.conversation_id == conversation_id,
                        MemoryModel.importance < threshold
                    )
                )
            )
            count = result.rowcount
            if count > 0:
                logger.info(f"Deleted {count} low-importance memories for conversation {conversation_id}")
            return count
        except Exception as e:
            logger.error(f"Error deleting low-importance memories: {e}")
            raise MemoryStorageError(f"Failed to delete low-importance memories: {e}")

