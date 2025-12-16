"""Vector store repository for long-term memory with pgvector."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.database import MemoryModel, ConversationModel
from app.models.memory import Memory, MemoryType
from app.core.exceptions import MemoryStorageError, MemoryRetrievalError
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreRepository:
    """Repository for managing memories with vector embeddings in PostgreSQL."""
    
    def __init__(self, session: AsyncSession, llm_client=None):
        """
        Initialize vector store repository.
        
        Args:
            session: Async database session
            llm_client: Optional LLM client for AI-powered contradiction detection
        """
        self.session = session
        self.llm_client = llm_client
    
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
            
            # Get user_id from conversation if not provided
            if not user_db_id:
                from app.models.database import ConversationModel
                from sqlalchemy import select
                result = await self.session.execute(
                    select(ConversationModel).where(ConversationModel.id == conversation_id)
                )
                conversation = result.scalar_one_or_none()
                if conversation:
                    user_db_id = conversation.user_id
                else:
                    logger.warning(f"Conversation {conversation_id} not found in database, cannot store memory")
                    raise MemoryStorageError(f"Conversation {conversation_id} not found")
            
            # Convert domain MemoryType to database enum (use lowercase as defined in DB)
            db_memory_type = memory_type.value  # Already lowercase: 'fact', 'preference', etc.
            
            # Create memory record
            memory = MemoryModel(
                conversation_id=conversation_id,
                user_id=user_db_id,
                content=content,
                embedding=embedding,
                memory_type=db_memory_type,
                importance=importance,
                extra_metadata=metadata or {}
            )
            
            self.session.add(memory)
            await self.session.flush()
            
            # Check for contradictory or duplicate memories
            await self._check_and_consolidate(memory, user_db_id)
            
            await self.session.commit()  # Commit to ensure memory is persisted
            
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
        min_similarity: float = None,
        user_external_id: Optional[str] = None
    ) -> List[Memory]:
        """
        Search for similar memories using vector similarity.
        
        Args:
            conversation_id: Conversation identifier
            query_embedding: Query vector embedding
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold (0.0 to 1.0), defaults to config value
            user_external_id: Optional user ID for additional security check
            
        Returns:
            List of similar memories with similarity scores
            
        Raises:
            MemoryRetrievalError: If search fails
        """
        # Use config value as default if not specified
        if min_similarity is None:
            min_similarity = settings.memory_similarity_threshold
        
        try:
            from app.models.database import UserModel
            
            # Get user_id from conversation to search across all their memories
            from app.models.database import ConversationModel
            result = await self.session.execute(
                select(ConversationModel).where(ConversationModel.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found for memory search")
                return []
            
            # Use pgvector cosine similarity operator (<=>)
            # Note: <=> returns distance, so lower is better (0 = identical)
            # Similarity = 1 - distance
            # Search across ALL user's memories, not just current conversation
            # Only return active memories (exclude superseded/consolidated ones)
            query_builder = (
                select(
                    MemoryModel,
                    (1 - MemoryModel.embedding.cosine_distance(query_embedding)).label('similarity')
                )
                .where(MemoryModel.user_id == conversation.user_id)
                .where(MemoryModel.is_active == True)
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
            
            logger.info(f"Executing similarity search for user {conversation.user_id} with threshold {min_similarity}")
            logger.debug(f"Query embedding type: {type(query_embedding)}, length: {len(query_embedding) if hasattr(query_embedding, '__len__') else 'N/A'}")
            
            result = await self.session.execute(query)
            rows = result.all()
            
            logger.info(f"Found {len(rows)} memories for user with similarity >= {min_similarity}")
            if len(rows) == 0:
                # Try to understand why - check total memories for user
                count_query = select(func.count()).select_from(MemoryModel).where(MemoryModel.user_id == conversation.user_id)
                total_result = await self.session.execute(count_query)
                total_count = total_result.scalar()
                logger.warning(f"No memories found with similarity >= {min_similarity}, but user has {total_count} total memories")
            
            # Convert to domain Memory objects
            memories = []
            for row in rows:
                memory_model, similarity = row
                logger.debug(f"Memory: '{memory_model.content[:50]}...' similarity={similarity:.3f}")
                # memory_type is now a plain string from the database
                memory = Memory(
                    id=memory_model.id,
                    conversation_id=memory_model.conversation_id,
                    content=memory_model.content,
                    embedding=None,  # Don't return embedding in results
                    memory_type=MemoryType(memory_model.memory_type),  # String value like 'preference'
                    importance=memory_model.importance,
                    created_at=memory_model.created_at,
                    metadata=memory_model.extra_metadata or {},
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
    
    async def _check_and_consolidate(
        self,
        new_memory: MemoryModel,
        user_id: UUID
    ) -> None:
        """
        Check if new memory contradicts or duplicates existing memories.
        Automatically supersedes contradictory memories.
        
        Args:
            new_memory: Newly created memory
            user_id: User ID
        """
        try:
            # Only check preference and fact type memories
            if new_memory.memory_type not in ['preference', 'fact']:
                return
            
            # Get recent similar memories from same user
            stmt = (
                select(
                    MemoryModel,
                    (1 - MemoryModel.embedding.cosine_distance(new_memory.embedding)).label('similarity')
                )
                .where(
                    and_(
                        MemoryModel.user_id == user_id,
                        MemoryModel.memory_type == new_memory.memory_type,
                        MemoryModel.is_active == True,
                        MemoryModel.id != new_memory.id,
                        # Check memories with high similarity (same topic)
                        (1 - MemoryModel.embedding.cosine_distance(new_memory.embedding)) >= 0.7
                    )
                )
                .order_by((1 - MemoryModel.embedding.cosine_distance(new_memory.embedding)).desc())
                .limit(5)
            )
            
            result = await self.session.execute(stmt)
            similar_memories = result.all()
            
            if not similar_memories:
                return
            
            # Check each similar memory for contradictions
            for old_memory_model, similarity in similar_memories:
                is_contradictory = await self._is_contradictory(
                    old_memory_model.content,
                    new_memory.content
                )
                
                if is_contradictory:
                    logger.info(
                        f"Detected contradiction! Old: '{old_memory_model.content}' "
                        f"New: '{new_memory.content}' (similarity: {similarity:.2f})"
                    )
                    
                    # Determine which is newer
                    if new_memory.created_at > old_memory_model.created_at:
                        # New memory supersedes old one
                        logger.info(
                            f"Superseding old memory {old_memory_model.id} with "
                            f"new memory {new_memory.id}"
                        )
                        old_memory_model.is_active = False
                        old_memory_model.superseded_by = new_memory.id
                        old_memory_model.updated_at = datetime.utcnow()
                    else:
                        # Old memory is newer (shouldn't happen but handle it)
                        logger.info(
                            f"New memory {new_memory.id} contradicted by existing "
                            f"memory {old_memory_model.id}, marking new as inactive"
                        )
                        new_memory.is_active = False
                        new_memory.superseded_by = old_memory_model.id
                        new_memory.updated_at = datetime.utcnow()
                    
                    # Only consolidate with first contradiction found
                    break
            
        except Exception as e:
            # Log error but don't fail the memory storage
            logger.error(f"Error during memory consolidation: {e}")
    
    async def _is_contradictory(
        self,
        content1: str,
        content2: str
    ) -> bool:
        """
        Detect if two memory contents contradict each other.
        
        Uses AI chaining (LLM) or pattern matching based on configuration.
        
        Args:
            content1: First memory content
            content2: Second memory content
            
        Returns:
            True if contents are contradictory, False otherwise
        """
        method = settings.contradiction_detection_method.lower()
        
        if method == "llm":
            return await self._is_contradictory_llm(content1, content2)
        elif method == "pattern":
            return self._is_contradictory_patterns(content1, content2)
        else:  # hybrid (default)
            # Try LLM first
            llm_result = await self._is_contradictory_llm(content1, content2)
            if llm_result is not None:
                return llm_result
            # Fallback to patterns
            logger.debug("LLM contradiction detection unavailable, using pattern fallback")
            return self._is_contradictory_patterns(content1, content2)
    
    async def _is_contradictory_llm(
        self,
        content1: str,
        content2: str
    ) -> Optional[bool]:
        """
        Detect contradictions using LLM (AI chaining).
        
        Args:
            content1: First memory content
            content2: Second memory content
            
        Returns:
            True if contradictory, False if not, None if LLM unavailable
        """
        if not self.llm_client:
            return None
        
        import json
        import re
        
        prompt = f"""Analyze if these two statements contradict each other.

Statement 1: "{content1}"
Statement 2: "{content2}"

Consider:
1. Opposite sentiments about the same topic (like vs hate, enjoy vs dislike)
2. Conflicting facts about the same subject
3. Semantic meaning, not just keywords
4. Temporal context (past vs present statements may not contradict)
5. Specificity (specific cases may not contradict general statements)

Examples of contradictions:
- "I like chocolate" vs "I don't like chocolate" → CONTRADICTS
- "I work at Google" vs "I work at Microsoft" → CONTRADICTS
- "I'm vegan" vs "I love eating steak" → CONTRADICTS

Examples of NON-contradictions:
- "I used to like chocolate" vs "I don't like chocolate" → Same meaning
- "I like chocolate" vs "I don't like dark chocolate" → Specific vs general
- "I went to Paris" vs "I went to London" → Different events

Return ONLY valid JSON:
{{
  "contradicts": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}

JSON:"""
        
        try:
            response = await self.llm_client.chat([
                {"role": "system", "content": "You are a semantic contradiction detection expert. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ])
            
            # Parse JSON response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                logger.warning("No JSON found in LLM contradiction response")
                return None
            
            result = json.loads(json_match.group())
            
            # Validate result
            contradicts = result.get('contradicts', False)
            confidence = float(result.get('confidence', 0))
            reasoning = result.get('reasoning', '')
            
            # Only return True if high confidence
            if confidence >= 0.7:
                logger.info(
                    f"LLM contradiction detection: contradicts={contradicts}, "
                    f"confidence={confidence:.2f}, reasoning='{reasoning}'"
                )
                return contradicts
            else:
                logger.debug(f"LLM contradiction confidence too low: {confidence:.2f}")
                return None
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM contradiction JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM contradiction detection failed: {e}")
            return None
    
    def _is_contradictory_patterns(
        self,
        content1: str,
        content2: str
    ) -> bool:
        """
        Detect contradictions using pattern matching (original method).
        
        Args:
            content1: First memory content
            content2: Second memory content
            
        Returns:
            True if contradictory, False otherwise
        """
        import re
        
        c1_lower = content1.lower()
        c2_lower = content2.lower()
        
        # Patterns for positive preferences
        positive_patterns = [
            r'\b(i\s+like|i\s+love|i\s+enjoy|i\s+prefer|my\s+favorite|i\'m\s+interested\s+in|i\'m\s+into)\b',
            r'\b(yes|yeah|yep|sure|definitely|absolutely)\b',
        ]
        
        # Patterns for negative preferences  
        negative_patterns = [
            r'\b(i\s+don\'t\s+like|i\s+hate|i\s+dislike|i\s+don\'t\s+enjoy|i\s+don\'t\s+prefer|not\s+my\s+favorite)\b',
            r'\b(i\s+do\s+not\s+like|i\s+do\s+not\s+enjoy)\b',
            r'\b(no|nope|nah|not\s+really|don\'t|never)\b',
        ]
        
        # Check sentiment in each content
        has_positive_1 = any(re.search(pattern, c1_lower) for pattern in positive_patterns)
        has_negative_1 = any(re.search(pattern, c1_lower) for pattern in negative_patterns)
        has_positive_2 = any(re.search(pattern, c2_lower) for pattern in positive_patterns)
        has_negative_2 = any(re.search(pattern, c2_lower) for pattern in negative_patterns)
        
        # Extract common subject/topic by removing preference words
        subject1 = re.sub(
            r'\b(i|like|love|hate|dislike|enjoy|don\'t|do|really|very|much|a|lot|not|my|favorite|yes|no)\b',
            '',
            c1_lower
        ).strip()
        subject2 = re.sub(
            r'\b(i|like|love|hate|dislike|enjoy|don\'t|do|really|very|much|a|lot|not|my|favorite|yes|no)\b',
            '',
            c2_lower
        ).strip()
        
        # Check if they share significant words (same topic)
        words1 = set(w for w in subject1.split() if len(w) > 2)
        words2 = set(w for w in subject2.split() if len(w) > 2)
        common_words = words1 & words2
        
        # If they share common words and have opposite sentiment, they're contradictory
        if len(common_words) > 0:
            # One is positive, other is negative
            if (has_positive_1 and has_negative_2) or (has_negative_1 and has_positive_2):
                logger.debug(
                    f"Pattern contradiction detected: common words={common_words}, "
                    f"c1_positive={has_positive_1}, c1_negative={has_negative_1}, "
                    f"c2_positive={has_positive_2}, c2_negative={has_negative_2}"
                )
                return True
        
        return False

