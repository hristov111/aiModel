"""Intelligent memory importance scoring system."""

import re
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MemoryImportanceScorer:
    """
    Calculates importance scores for memories based on multiple factors.
    
    Factors:
    1. Emotional Significance (0-1): Presence of emotional keywords/context
    2. Explicit Mention (0-1): User explicitly said "remember this"
    3. Frequency Referenced (0-1): How often similar topic mentioned
    4. Recency (0-1): How recent the memory is
    5. Specificity (0-1): Level of detail (specific > vague)
    6. Personal Relevance (0-1): How personally relevant (names, goals, preferences)
    """
    
    # Configurable weights for each factor
    WEIGHTS = {
        'emotional_significance': 0.30,
        'explicit_mention': 0.25,
        'frequency_referenced': 0.15,
        'recency': 0.10,
        'specificity': 0.10,
        'personal_relevance': 0.10
    }
    
    # Emotional keywords (high importance indicators)
    EMOTIONAL_KEYWORDS = {
        'love', 'hate', 'fear', 'excited', 'nervous', 'proud', 'ashamed',
        'grateful', 'angry', 'sad', 'happy', 'worried', 'anxious', 'thrilled',
        'devastated', 'heartbroken', 'overjoyed', 'disappointed', 'frustrated',
        'passionate', 'traumatic', 'important', 'significant', 'crucial',
        'life-changing', 'unforgettable', 'memorable'
    }
    
    # Explicit memory markers
    EXPLICIT_MARKERS = [
        r'remember (this|that|when)',
        r'don\'?t forget',
        r'(important|crucial|key) (to|that|fact)',
        r'i want you to (know|remember)',
        r'keep in mind',
        r'note (this|that)',
        r'(always|never) forget',
        r'for (future reference|later)',
        r'make (a )?note'
    ]
    
    # Personal relevance indicators
    PERSONAL_INDICATORS = {
        'names': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Proper names
        'relationships': ['my wife', 'my husband', 'my mom', 'my dad', 'my son', 'my daughter',
                         'my brother', 'my sister', 'my friend', 'my boss', 'my partner'],
        'possessive': ['my', 'mine', 'our'],
        'goals': ['goal', 'want to', 'planning to', 'hope to', 'dream',
                 'aspire', 'working toward', 'trying to achieve'],
        'preferences': ['i prefer', 'i like', 'i love', 'i hate', 'i dislike',
                       'favorite', 'always', 'never'],
        'life_events': ['birthday', 'anniversary', 'wedding', 'graduation',
                       'promotion', 'moving', 'buying', 'selling']
    }
    
    def calculate_importance(
        self,
        memory_content: str,
        memory_type: str,
        conversation_context: Optional[Dict] = None,
        historical_data: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Calculate comprehensive importance score.
        
        Args:
            memory_content: The memory text
            memory_type: Type of memory (fact, preference, goal, etc.)
            conversation_context: Context from conversation (emotion, etc.)
            historical_data: Historical reference data (access count, etc.)
            
        Returns:
            Dict with individual scores and final importance score
        """
        scores = {}
        
        # 1. Emotional Significance
        scores['emotional_significance'] = self._score_emotional_significance(
            memory_content,
            conversation_context
        )
        
        # 2. Explicit Mention
        scores['explicit_mention'] = self._score_explicit_mention(memory_content)
        
        # 3. Frequency Referenced
        scores['frequency_referenced'] = self._score_frequency(
            memory_content,
            memory_type,
            historical_data
        )
        
        # 4. Recency
        scores['recency'] = self._score_recency(historical_data)
        
        # 5. Specificity
        scores['specificity'] = self._score_specificity(memory_content)
        
        # 6. Personal Relevance
        scores['personal_relevance'] = self._score_personal_relevance(
            memory_content,
            memory_type
        )
        
        # Calculate weighted final score
        final_score = sum(
            scores[factor] * weight
            for factor, weight in self.WEIGHTS.items()
        )
        
        # Normalize to 0-1
        final_score = max(0.0, min(1.0, final_score))
        
        result = {
            **scores,
            'final_importance': final_score
        }
        
        logger.debug(f"Importance scores: {result}")
        
        return result
    
    def _score_emotional_significance(
        self,
        content: str,
        context: Optional[Dict]
    ) -> float:
        """Score based on emotional content."""
        score = 0.0
        content_lower = content.lower()
        
        # Check for emotional keywords
        emotional_word_count = sum(
            1 for word in self.EMOTIONAL_KEYWORDS
            if word in content_lower
        )
        
        if emotional_word_count > 0:
            # Each emotional word adds 0.2, capped at 0.7
            score += min(emotional_word_count * 0.2, 0.7)
        
        # Boost if emotion was detected in conversation
        if context and context.get('detected_emotion'):
            emotion_confidence = context.get('emotion_confidence', 0)
            score += emotion_confidence * 0.3
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def _score_explicit_mention(self, content: str) -> float:
        """Score based on explicit memory markers."""
        content_lower = content.lower()
        
        for pattern in self.EXPLICIT_MARKERS:
            if re.search(pattern, content_lower):
                return 1.0  # Explicitly marked as important
        
        return 0.0
    
    def _score_frequency(
        self,
        content: str,
        memory_type: str,
        historical_data: Optional[Dict]
    ) -> float:
        """Score based on how often topic is mentioned."""
        if not historical_data:
            return 0.3  # Default for new memories
        
        # Get access count if available
        access_count = historical_data.get('access_count', 0)
        
        # Logarithmic scaling: frequent access = higher importance
        if access_count == 0:
            return 0.2
        elif access_count < 5:
            return 0.4
        elif access_count < 10:
            return 0.6
        elif access_count < 20:
            return 0.8
        else:
            return 1.0
    
    def _score_recency(self, historical_data: Optional[Dict]) -> float:
        """Score based on how recent the memory is."""
        if not historical_data or 'created_at' not in historical_data:
            return 0.9  # New memories are recent
        
        created_at = historical_data['created_at']
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        # Calculate age in days
        age_days = (datetime.utcnow() - created_at).days
        
        # Decay function: fresh memories more important
        if age_days == 0:
            return 1.0
        elif age_days < 7:
            return 0.9
        elif age_days < 30:
            return 0.7
        elif age_days < 90:
            return 0.5
        elif age_days < 180:
            return 0.3
        else:
            return 0.1
    
    def _score_specificity(self, content: str) -> float:
        """Score based on level of detail."""
        # Factors:
        # - Length (longer = more specific)
        # - Numbers (specific dates, quantities)
        # - Proper nouns
        # - Details (who, what, when, where, why)
        
        score = 0.0
        
        # Length scoring (20-200 chars is sweet spot)
        length = len(content)
        if 20 <= length <= 200:
            score += 0.4
        elif length > 200:
            score += 0.3  # Too long can be vague
        else:
            score += 0.1  # Too short lacks detail
        
        # Numbers (dates, quantities, etc.)
        numbers = re.findall(r'\b\d+\b', content)
        if numbers:
            score += min(len(numbers) * 0.1, 0.3)
        
        # Proper nouns (capitalized words)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', content)
        if len(proper_nouns) >= 2:
            score += 0.2
        elif len(proper_nouns) == 1:
            score += 0.1
        
        # Time references (specific > vague)
        time_specific = ['yesterday', 'today', 'tomorrow', 'monday', 'january',
                        'last week', 'next month', '2024', '2023']
        if any(word in content.lower() for word in time_specific):
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_personal_relevance(self, content: str, memory_type: str) -> float:
        """Score based on personal relevance."""
        score = 0.0
        content_lower = content.lower()
        
        # Memory type bonus
        personal_types = ['preference', 'goal', 'relationship', 'achievement', 'challenge']
        if memory_type in personal_types:
            score += 0.3
        
        # Names (proper nouns with context)
        if re.search(self.PERSONAL_INDICATORS['names'], content):
            score += 0.2
        
        # Relationship mentions
        for rel in self.PERSONAL_INDICATORS['relationships']:
            if rel in content_lower:
                score += 0.3
                break
        
        # Personal possessive words
        possessive_count = sum(
            content_lower.count(word)
            for word in self.PERSONAL_INDICATORS['possessive']
        )
        if possessive_count > 0:
            score += min(possessive_count * 0.1, 0.2)
        
        # Goals
        for goal_word in self.PERSONAL_INDICATORS['goals']:
            if goal_word in content_lower:
                score += 0.2
                break
        
        # Preferences
        for pref_phrase in self.PERSONAL_INDICATORS['preferences']:
            if pref_phrase in content_lower:
                score += 0.2
                break
        
        # Life events
        for event in self.PERSONAL_INDICATORS['life_events']:
            if event in content_lower:
                score += 0.3
                break
        
        return min(score, 1.0)
    
    def recalculate_importance_over_time(
        self,
        current_importance: float,
        current_scores: Dict[str, float],
        days_since_created: int,
        days_since_accessed: Optional[int],
        access_count: int
    ) -> Dict[str, float]:
        """
        Recalculate importance as memories age.
        
        Important memories that are never accessed may decay.
        Frequently accessed memories stay important.
        """
        updated_scores = current_scores.copy()
        
        # Update recency score based on age
        if days_since_created < 7:
            updated_scores['recency'] = 0.9
        elif days_since_created < 30:
            updated_scores['recency'] = 0.7
        elif days_since_created < 90:
            updated_scores['recency'] = 0.5
        elif days_since_created < 180:
            updated_scores['recency'] = 0.3
        else:
            updated_scores['recency'] = 0.1
        
        # Update frequency score based on access count
        if access_count == 0:
            updated_scores['frequency_referenced'] = 0.1
        elif access_count < 5:
            updated_scores['frequency_referenced'] = 0.4
        elif access_count < 10:
            updated_scores['frequency_referenced'] = 0.6
        elif access_count < 20:
            updated_scores['frequency_referenced'] = 0.8
        else:
            updated_scores['frequency_referenced'] = 1.0
        
        # If not accessed in long time, reduce importance
        if days_since_accessed and days_since_accessed > 90:
            decay_factor = max(0.5, 1.0 - (days_since_accessed - 90) / 365)
            for key in updated_scores:
                if key != 'explicit_mention':  # Don't decay explicit memories
                    updated_scores[key] *= decay_factor
        
        # Recalculate final score
        final_score = sum(
            updated_scores[factor] * weight
            for factor, weight in self.WEIGHTS.items()
        )
        
        updated_scores['final_importance'] = max(0.0, min(1.0, final_score))
        
        return updated_scores

