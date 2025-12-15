"""Enhanced memory service with intelligence, consolidation, and temporal awareness."""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import MemoryModel
from app.models.memory import Memory
from app.services.memory_importance import MemoryImportanceScorer
from app.services.memory_categorizer import MemoryCategorizer
from app.services.memory_consolidation import MemoryConsolidationEngine
from app.utils.embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


class EnhancedMemoryService:
    """
    Enhanced memory service with intelligent features:
    - Importance scoring
    - Automatic categorization
    - Entity extraction
    - Memory consolidation
    - Temporal decay
    - Smart retrieval
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        embedding_generator: EmbeddingGenerator
    ):
        """
        Initialize enhanced memory service.
        
        Args:
            db_session: Database session
            embedding_generator: Embedding generator for vectorization
        """
        self.db = db_session
        self.embedding_generator = embedding_generator
        self.importance_scorer = MemoryImportanceScorer()
        self.categorizer = MemoryCategorizer()
        self.consolidation_engine = MemoryConsolidationEngine()
    
    async def store_memory(
        self,
        user_id: UUID,
        conversation_id: UUID,
        content: str,
        memory_type: str = 'fact',
        conversation_context: Optional[Dict] = None
    ) -> Memory:
        """
        Store a memory with enhanced intelligence.
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            content: Memory content
            memory_type: Type of memory
            conversation_context: Context (emotion, etc.)
            
        Returns:
            Created Memory object
        """
        # Generate embedding
        embedding = self.embedding_generator.generate(content)
        
        # Categorize memory
        category = self.categorizer.categorize(content, memory_type)
        
        # Extract entities
        entities = self.categorizer.extract_entities(content)
        
        # Calculate importance
        importance_scores = self.importance_scorer.calculate_importance(
            memory_content=content,
            memory_type=memory_type,
            conversation_context=conversation_context
        )
        
        # Create memory model
        memory = MemoryModel(
            user_id=user_id,
            conversation_id=conversation_id,
            content=content,
            embedding=embedding,
            memory_type=memory_type,
            category=category,
            importance=importance_scores['final_importance'],
            importance_scores=importance_scores,
            related_entities=entities,
            access_count=0,
            decay_factor=1.0,
            is_active=True
        )
        
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        
        logger.info(
            f"Stored memory for user {user_id}: category={category}, "
            f"importance={importance_scores['final_importance']:.2f}"
        )
        
        # Check for consolidation opportunities (async)
        await self._check_consolidation(user_id, memory)
        
        return self._model_to_memory(memory)
    
    async def retrieve_memories(
        self,
        user_id: UUID,
        query_text: str,
        limit: int = 10,
        category_filter: Optional[str] = None,
        min_importance: float = 0.0,
        include_inactive: bool = False
    ) -> List[Memory]:
        """
        Retrieve memories with enhanced filtering and ranking.
        
        Args:
            user_id: User ID
            query_text: Query for semantic search
            limit: Maximum memories to return
            category_filter: Filter by category
            min_importance: Minimum importance threshold
            include_inactive: Include consolidated/superseded memories
            
        Returns:
            List of Memory objects
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate(query_text)
        
        # Build query
        stmt = select(MemoryModel).where(
            MemoryModel.user_id == user_id
        )
        
        # Filter by active status
        if not include_inactive:
            stmt = stmt.where(MemoryModel.is_active == True)
        
        # Filter by category
        if category_filter:
            stmt = stmt.where(MemoryModel.category == category_filter)
        
        # Filter by minimum importance
        if min_importance > 0:
            stmt = stmt.where(MemoryModel.importance >= min_importance)
        
        # Order by similarity (using pgvector)
        # In actual implementation, would use vector similarity here
        # For now, order by importance and recency
        stmt = stmt.order_by(
            desc(MemoryModel.importance),
            desc(MemoryModel.created_at)
        ).limit(limit * 2)  # Get more for post-processing
        
        result = await self.db.execute(stmt)
        memories = result.scalars().all()
        
        # Calculate similarity scores and re-rank
        scored_memories = []
        for mem in memories:
            # Calculate similarity (simplified - would use actual vector similarity)
            similarity = self._calculate_simple_similarity(query_embedding, mem.embedding)
            
            # Apply temporal decay
            decay_adjusted_importance = self._apply_temporal_decay(mem)
            
            # Combined score: similarity + importance + recency
            combined_score = (
                similarity * 0.5 +
                decay_adjusted_importance * 0.3 +
                (1.0 if mem.access_count > 0 else 0.5) * 0.2
            )
            
            scored_memories.append((mem, combined_score))
        
        # Sort by combined score
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # Take top memories
        top_memories = [m[0] for m in scored_memories[:limit]]
        
        # Update access tracking
        for mem in top_memories:
            mem.access_count += 1
            mem.last_accessed = datetime.utcnow()
        
        await self.db.commit()
        
        return [self._model_to_memory(m) for m in top_memories]
    
    async def get_memories_by_category(
        self,
        user_id: UUID,
        category: str,
        limit: int = 50
    ) -> List[Memory]:
        """Get all memories in a specific category."""
        stmt = (
            select(MemoryModel)
            .where(
                and_(
                    MemoryModel.user_id == user_id,
                    MemoryModel.category == category,
                    MemoryModel.is_active == True
                )
            )
            .order_by(desc(MemoryModel.importance), desc(MemoryModel.created_at))
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        memories = result.scalars().all()
        
        return [self._model_to_memory(m) for m in memories]
    
    async def get_memory_stats(self, user_id: UUID) -> Dict:
        """Get statistics about user's memories."""
        # Total memories
        total_stmt = select(func.count(MemoryModel.id)).where(
            and_(
                MemoryModel.user_id == user_id,
                MemoryModel.is_active == True
            )
        )
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()
        
        # By category
        category_stmt = (
            select(
                MemoryModel.category,
                func.count(MemoryModel.id).label('count'),
                func.avg(MemoryModel.importance).label('avg_importance')
            )
            .where(
                and_(
                    MemoryModel.user_id == user_id,
                    MemoryModel.is_active == True
                )
            )
            .group_by(MemoryModel.category)
        )
        category_result = await self.db.execute(category_stmt)
        categories = [
            {
                'category': row.category,
                'count': row.count,
                'avg_importance': round(row.avg_importance, 2) if row.avg_importance else 0
            }
            for row in category_result
        ]
        
        # Most accessed
        most_accessed_stmt = (
            select(MemoryModel)
            .where(
                and_(
                    MemoryModel.user_id == user_id,
                    MemoryModel.is_active == True
                )
            )
            .order_by(desc(MemoryModel.access_count))
            .limit(5)
        )
        most_accessed_result = await self.db.execute(most_accessed_stmt)
        most_accessed = [
            {
                'content': m.content[:100] + '...' if len(m.content) > 100 else m.content,
                'access_count': m.access_count,
                'importance': m.importance
            }
            for m in most_accessed_result.scalars()
        ]
        
        return {
            'total_memories': total,
            'by_category': categories,
            'most_accessed': most_accessed
        }
    
    async def consolidate_user_memories(
        self,
        user_id: UUID,
        dry_run: bool = False
    ) -> Dict:
        """
        Run consolidation process on user's memories.
        
        Args:
            user_id: User ID
            dry_run: If True, only report what would be done
            
        Returns:
            Summary of consolidation actions
        """
        # Get all active memories
        stmt = (
            select(MemoryModel)
            .where(
                and_(
                    MemoryModel.user_id == user_id,
                    MemoryModel.is_active == True
                )
            )
            .order_by(MemoryModel.created_at)
        )
        
        result = await self.db.execute(stmt)
        memories = [self._model_to_memory(m) for m in result.scalars()]
        
        # Find consolidation candidates
        candidates = self.consolidation_engine.find_consolidation_candidates(memories)
        
        actions = {
            'candidates_found': len(candidates),
            'actions_taken': [],
            'dry_run': dry_run
        }
        
        if dry_run:
            for mem1, mem2, similarity in candidates[:10]:  # Show top 10
                strategy = self.consolidation_engine.suggest_consolidation_strategy(
                    mem1, mem2, similarity
                )
                actions['actions_taken'].append({
                    'memory1': mem1.content[:50],
                    'memory2': mem2.content[:50],
                    'similarity': similarity,
                    'suggested_strategy': strategy
                })
        else:
            # Actually consolidate
            for mem1, mem2, similarity in candidates:
                strategy = self.consolidation_engine.suggest_consolidation_strategy(
                    mem1, mem2, similarity
                )
                
                if strategy != 'keep_both':
                    # Perform consolidation
                    consolidated = self.consolidation_engine.consolidate_memories(
                        mem1, mem2, strategy
                    )
                    
                    # Update database (implementation depends on strategy)
                    # This would update the actual MemoryModel records
                    
                    actions['actions_taken'].append({
                        'memory1_id': str(mem1.id),
                        'memory2_id': str(mem2.id),
                        'strategy': strategy,
                        'similarity': similarity
                    })
        
        return actions
    
    async def apply_temporal_decay_all(self, user_id: UUID) -> Dict:
        """
        Apply temporal decay to all user memories.
        
        Updates importance scores based on age and access patterns.
        """
        stmt = (
            select(MemoryModel)
            .where(
                and_(
                    MemoryModel.user_id == user_id,
                    MemoryModel.is_active == True
                )
            )
        )
        
        result = await self.db.execute(stmt)
        memories = result.scalars().all()
        
        updated_count = 0
        for mem in memories:
            days_since_created = (datetime.utcnow() - mem.created_at).days
            days_since_accessed = (datetime.utcnow() - mem.last_accessed).days if mem.last_accessed else days_since_created
            
            # Recalculate importance
            if mem.importance_scores:
                updated_scores = self.importance_scorer.recalculate_importance_over_time(
                    current_importance=mem.importance,
                    current_scores=mem.importance_scores,
                    days_since_created=days_since_created,
                    days_since_accessed=days_since_accessed,
                    access_count=mem.access_count
                )
                
                # Update if significant change
                if abs(updated_scores['final_importance'] - mem.importance) > 0.05:
                    mem.importance = updated_scores['final_importance']
                    mem.importance_scores = updated_scores
                    mem.updated_at = datetime.utcnow()
                    updated_count += 1
        
        await self.db.commit()
        
        return {
            'total_memories': len(memories),
            'updated_count': updated_count
        }
    
    async def _check_consolidation(
        self,
        user_id: UUID,
        new_memory: MemoryModel
    ) -> None:
        """Check if new memory should be consolidated with existing ones."""
        # Get recent memories in same category
        if not new_memory.category:
            return
        
        stmt = (
            select(MemoryModel)
            .where(
                and_(
                    MemoryModel.user_id == user_id,
                    MemoryModel.category == new_memory.category,
                    MemoryModel.is_active == True,
                    MemoryModel.id != new_memory.id
                )
            )
            .order_by(desc(MemoryModel.created_at))
            .limit(10)
        )
        
        result = await self.db.execute(stmt)
        recent_memories = result.scalars().all()
        
        # Check similarity with each
        for mem in recent_memories:
            # Simple similarity check
            if self._calculate_simple_similarity(new_memory.embedding, mem.embedding) > 0.9:
                logger.info(
                    f"Found potential duplicate for memory {new_memory.id}: "
                    f"similar to {mem.id}"
                )
                # Could auto-consolidate here or flag for review
                break
    
    def _apply_temporal_decay(self, memory: MemoryModel) -> float:
        """Calculate decay-adjusted importance."""
        if not memory.created_at:
            return memory.importance
        
        days_old = (datetime.utcnow() - memory.created_at).days
        
        # Exponential decay (slower for frequently accessed memories)
        access_factor = min(memory.access_count / 10, 1.0)  # Normalize to 0-1
        decay_rate = 0.01 * (1 - access_factor)  # Less decay for accessed memories
        
        decay = 1.0 / (1.0 + decay_rate * days_old)
        
        return memory.importance * decay * memory.decay_factor
    
    def _calculate_simple_similarity(self, emb1, emb2) -> float:
        """Simple embedding similarity (placeholder for actual implementation)."""
        try:
            import numpy as np
            arr1 = np.array(emb1)
            arr2 = np.array(emb2)
            
            dot_product = np.dot(arr1, arr2)
            norm1 = np.linalg.norm(arr1)
            norm2 = np.linalg.norm(arr2)
            
            if norm1 > 0 and norm2 > 0:
                return float(dot_product / (norm1 * norm2))
        except:
            pass
        
        return 0.5  # Default
    
    def _model_to_memory(self, model: MemoryModel) -> Memory:
        """Convert MemoryModel to Memory domain object."""
        from app.models.memory import MemoryTypeEnum
        
        return Memory(
            id=model.id,
            conversation_id=model.conversation_id,
            content=model.content,
            embedding=model.embedding,
            memory_type=model.memory_type,
            importance=model.importance,
            created_at=model.created_at,
            metadata=model.extra_metadata or {},
            similarity_score=None  # Will be set during retrieval
        )

