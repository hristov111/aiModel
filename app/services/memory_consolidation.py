"""Memory consolidation engine for merging and organizing memories."""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from uuid import UUID
import numpy as np

from app.models.memory import Memory

logger = logging.getLogger(__name__)


class MemoryConsolidationEngine:
    """
    Consolidates similar memories to prevent clutter and improve quality.
    
    Strategies:
    1. Merge duplicate/similar memories (same topic, different wording)
    2. Update memories with new information
    3. Promote important memories over trivial ones
    4. Archive superseded memories
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize consolidation engine.
        
        Args:
            similarity_threshold: Cosine similarity threshold for merging (0-1)
        """
        self.similarity_threshold = similarity_threshold
    
    def find_consolidation_candidates(
        self,
        memories: List[Memory],
        category_match: bool = True
    ) -> List[Tuple[Memory, Memory, float]]:
        """
        Find pairs of memories that could be consolidated.
        
        Args:
            memories: List of memories to analyze
            category_match: Only match memories in same category
            
        Returns:
            List of (memory1, memory2, similarity_score) tuples
        """
        candidates = []
        
        for i in range(len(memories)):
            for j in range(i + 1, len(memories)):
                mem1 = memories[i]
                mem2 = memories[j]
                
                # Skip if different categories and category matching required
                if category_match and hasattr(mem1, 'category') and hasattr(mem2, 'category'):
                    if mem1.category and mem2.category and mem1.category != mem2.category:
                        continue
                
                # Calculate similarity
                similarity = self._calculate_similarity(mem1, mem2)
                
                if similarity >= self.similarity_threshold:
                    candidates.append((mem1, mem2, similarity))
        
        # Sort by similarity (highest first)
        candidates.sort(key=lambda x: x[2], reverse=True)
        
        return candidates
    
    def consolidate_memories(
        self,
        memory1: Memory,
        memory2: Memory,
        strategy: str = 'merge'
    ) -> Dict:
        """
        Consolidate two memories into one.
        
        Args:
            memory1: First memory
            memory2: Second memory
            strategy: 'merge', 'update', or 'supersede'
            
        Returns:
            Consolidated memory data dict
        """
        if strategy == 'merge':
            return self._merge_memories(memory1, memory2)
        elif strategy == 'update':
            return self._update_memory(memory1, memory2)
        elif strategy == 'supersede':
            return self._supersede_memory(memory1, memory2)
        else:
            raise ValueError(f"Unknown consolidation strategy: {strategy}")
    
    def _merge_memories(
        self,
        memory1: Memory,
        memory2: Memory
    ) -> Dict:
        """
        Merge two memories by combining their content.
        
        Keeps the more important memory as base,
        adds details from the other.
        """
        # Determine which is more important
        importance1 = getattr(memory1, 'importance', 0.5)
        importance2 = getattr(memory2, 'importance', 0.5)
        
        if importance1 >= importance2:
            primary = memory1
            secondary = memory2
        else:
            primary = memory2
            secondary = memory1
        
        # Merge content intelligently
        merged_content = self._intelligent_merge_text(
            primary.content,
            secondary.content
        )
        
        # Combine importance (weighted average, biased toward higher)
        merged_importance = (importance1 * 0.6 + importance2 * 0.4)
        
        # Merge related entities
        merged_entities = self._merge_entities(
            getattr(primary, 'related_entities', {}),
            getattr(secondary, 'related_entities', {})
        )
        
        # Track consolidation
        consolidated_from = []
        if hasattr(primary, 'consolidated_from') and primary.consolidated_from:
            consolidated_from.extend(primary.consolidated_from)
        if hasattr(secondary, 'consolidated_from') and secondary.consolidated_from:
            consolidated_from.extend(secondary.consolidated_from)
        consolidated_from.append(str(secondary.id))
        
        # Calculate access count (sum)
        access_count = (
            getattr(primary, 'access_count', 0) +
            getattr(secondary, 'access_count', 0)
        )
        
        return {
            'id': primary.id,  # Keep primary ID
            'content': merged_content,
            'importance': min(merged_importance, 1.0),
            'related_entities': merged_entities,
            'consolidated_from': consolidated_from,
            'access_count': access_count,
            'updated_at': datetime.utcnow(),
            'metadata': {
                **getattr(primary, 'metadata', {}),
                'consolidation_type': 'merge',
                'merged_with': str(secondary.id),
                'merged_at': datetime.utcnow().isoformat()
            }
        }
    
    def _update_memory(
        self,
        old_memory: Memory,
        new_memory: Memory
    ) -> Dict:
        """
        Update a memory with newer information.
        
        Used when new memory is clearly an update to old one
        (e.g., "I work at Google" -> "I work at Microsoft now").
        """
        # New memory takes precedence
        updated_content = new_memory.content
        
        # But note the update in metadata
        update_history = []
        if hasattr(old_memory, 'metadata') and old_memory.extra_metadata:
            update_history = old_memory.extra_metadata.get('update_history', [])
        
        update_history.append({
            'previous_content': old_memory.content,
            'updated_at': datetime.utcnow().isoformat(),
            'reason': 'newer_information'
        })
        
        # Inherit importance (slightly boosted)
        new_importance = getattr(new_memory, 'importance', 0.5)
        old_importance = getattr(old_memory, 'importance', 0.5)
        updated_importance = max(new_importance, old_importance * 1.1)
        
        return {
            'id': old_memory.id,  # Keep old ID (it's an update)
            'content': updated_content,
            'importance': min(updated_importance, 1.0),
            'superseded_by': None,  # Not superseded, updated
            'updated_at': datetime.utcnow(),
            'metadata': {
                **getattr(old_memory, 'metadata', {}),
                'update_history': update_history,
                'consolidation_type': 'update'
            }
        }
    
    def _supersede_memory(
        self,
        old_memory: Memory,
        new_memory: Memory
    ) -> Dict:
        """
        Mark old memory as superseded by new one.
        
        Used when new memory completely replaces old one.
        """
        # Mark old memory as inactive
        old_data = {
            'id': old_memory.id,
            'is_active': False,
            'superseded_by': new_memory.id,
            'updated_at': datetime.utcnow()
        }
        
        # New memory gets importance boost
        new_importance = getattr(new_memory, 'importance', 0.5)
        old_importance = getattr(old_memory, 'importance', 0.5)
        boosted_importance = max(new_importance, old_importance)
        
        new_data = {
            'id': new_memory.id,
            'importance': min(boosted_importance, 1.0),
            'metadata': {
                **getattr(new_memory, 'metadata', {}),
                'supersedes': str(old_memory.id),
                'superseded_at': datetime.utcnow().isoformat()
            }
        }
        
        return {
            'old': old_data,
            'new': new_data
        }
    
    def _calculate_similarity(
        self,
        memory1: Memory,
        memory2: Memory
    ) -> float:
        """
        Calculate similarity between two memories.
        
        Uses embedding cosine similarity if available,
        falls back to text similarity.
        """
        # Try embedding similarity first
        if hasattr(memory1, 'embedding') and hasattr(memory2, 'embedding'):
            if memory1.embedding is not None and memory2.embedding is not None:
                try:
                    emb1 = np.array(memory1.embedding)
                    emb2 = np.array(memory2.embedding)
                    
                    # Cosine similarity
                    dot_product = np.dot(emb1, emb2)
                    norm1 = np.linalg.norm(emb1)
                    norm2 = np.linalg.norm(emb2)
                    
                    if norm1 > 0 and norm2 > 0:
                        similarity = dot_product / (norm1 * norm2)
                        return float(similarity)
                except Exception as e:
                    logger.error(f"Error calculating embedding similarity: {e}")
        
        # Fallback: Simple text similarity
        return self._text_similarity(memory1.content, memory2.content)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate basic text similarity using word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        # Jaccard similarity
        return len(intersection) / len(union) if union else 0.0
    
    def _intelligent_merge_text(
        self,
        text1: str,
        text2: str
    ) -> str:
        """
        Intelligently merge two text strings.
        
        Tries to combine without redundancy.
        """
        # If one is substring of other, use the longer one
        if text1.lower() in text2.lower():
            return text2
        if text2.lower() in text1.lower():
            return text1
        
        # Otherwise, combine with connector
        # Remove redundant endings/beginnings
        text1 = text1.strip().rstrip('.')
        text2 = text2.strip()
        
        # Check if they're complementary (one adds detail to other)
        if len(text2) > len(text1):
            return f"{text2}. Additional context: {text1}"
        else:
            return f"{text1}. {text2}"
    
    def _merge_entities(
        self,
        entities1: Dict,
        entities2: Dict
    ) -> Dict:
        """Merge entity dictionaries."""
        if not entities1:
            return entities2 or {}
        if not entities2:
            return entities1 or {}
        
        merged = {}
        all_keys = set(entities1.keys()) | set(entities2.keys())
        
        for key in all_keys:
            list1 = entities1.get(key, [])
            list2 = entities2.get(key, [])
            # Combine and deduplicate
            merged[key] = list(set(list1 + list2))
        
        return merged
    
    def suggest_consolidation_strategy(
        self,
        memory1: Memory,
        memory2: Memory,
        similarity: float
    ) -> str:
        """
        Suggest best consolidation strategy for two memories.
        
        Returns: 'merge', 'update', 'supersede', or 'keep_both'
        """
        # Check for contradictions first (most important)
        if self._is_contradictory(memory1, memory2):
            # Contradictory memories - newer should supersede older
            time1 = memory1.created_at
            time2 = memory2.created_at
            
            if time2 > time1:
                return 'supersede'  # Newer contradicts older
            else:
                return 'supersede'  # Still supersede but swap them
        
        # Very high similarity - likely duplicates
        if similarity >= 0.95:
            # Check if one is clearly newer/better
            time1 = memory1.created_at
            time2 = memory2.created_at
            
            if time2 > time1:
                # Newer might supersede older
                importance_diff = getattr(memory2, 'importance', 0.5) - getattr(memory1, 'importance', 0.5)
                if importance_diff > 0.1:
                    return 'supersede'  # Newer and more important
                else:
                    return 'update'  # Just update
            else:
                return 'merge'  # Older, just merge
        
        # High similarity but not identical
        elif similarity >= self.similarity_threshold:
            # Check content lengths - one might add details to other
            len1 = len(memory1.content)
            len2 = len(memory2.content)
            
            if abs(len1 - len2) > 50:
                # Significant length difference - merge to combine details
                return 'merge'
            else:
                # Similar length - might be update
                if memory2.created_at > memory1.created_at:
                    return 'update'
                else:
                    return 'merge'
        
        # Below threshold
        else:
            return 'keep_both'
    
    def _is_contradictory(
        self,
        memory1: Memory,
        memory2: Memory
    ) -> bool:
        """
        Detect if two memories contradict each other.
        
        Looks for opposite sentiment/preferences about the same topic.
        
        Returns:
            True if memories are contradictory, False otherwise
        """
        content1 = memory1.content.lower()
        content2 = memory2.content.lower()
        
        # Patterns for positive preferences
        positive_patterns = [
            r'\b(i\s+like|i\s+love|i\s+enjoy|i\s+prefer|my\s+favorite|i\'m\s+interested\s+in|i\'m\s+into)\b',
            r'\b(yes|yeah|yep|sure|definitely|absolutely)\b'
        ]
        
        # Patterns for negative preferences
        negative_patterns = [
            r'\b(i\s+don\'t\s+like|i\s+hate|i\s+dislike|i\s+don\'t\s+enjoy|i\s+don\'t\s+prefer|not\s+my\s+favorite)\b',
            r'\b(no|nope|nah|not\s+really|don\'t|never)\b'
        ]
        
        # Check if one is positive and other is negative
        has_positive_1 = any(re.search(pattern, content1) for pattern in positive_patterns)
        has_negative_1 = any(re.search(pattern, content1) for pattern in negative_patterns)
        has_positive_2 = any(re.search(pattern, content2) for pattern in positive_patterns)
        has_negative_2 = any(re.search(pattern, content2) for pattern in negative_patterns)
        
        # Extract common subject/topic
        # Remove preference words to find the subject
        subject1 = re.sub(r'\b(i|like|love|hate|dislike|enjoy|don\'t|do|really|very|much|a|lot)\b', '', content1).strip()
        subject2 = re.sub(r'\b(i|like|love|hate|dislike|enjoy|don\'t|do|really|very|much|a|lot)\b', '', content2).strip()
        
        # Check if they share significant words (same topic)
        words1 = set(subject1.split())
        words2 = set(subject2.split())
        common_words = words1 & words2
        
        # If they share common words and have opposite sentiment, they're contradictory
        if len(common_words) > 0:
            # One is positive, other is negative
            if (has_positive_1 and has_negative_2) or (has_negative_1 and has_positive_2):
                return True
        
        return False

