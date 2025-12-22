"""Service for extracting and managing user communication preferences."""

import re
import logging
from typing import Dict, Optional, List
from datetime import datetime

from app.models.memory import Message

logger = logging.getLogger(__name__)


class CommunicationPreferences:
    """Structure for user communication preferences."""
    
    def __init__(self):
        self.language: Optional[str] = None  # "English", "Spanish", "French", etc.
        self.formality: Optional[str] = None  # "casual", "formal", "professional"
        self.tone: Optional[str] = None  # "enthusiastic", "calm", "neutral", "friendly"
        self.emoji_usage: Optional[bool] = None  # True/False
        self.response_length: Optional[str] = None  # "brief", "detailed", "balanced"
        self.explanation_style: Optional[str] = None  # "simple", "technical", "analogies"
        self.last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "language": self.language,
            "formality": self.formality,
            "tone": self.tone,
            "emoji_usage": self.emoji_usage,
            "response_length": self.response_length,
            "explanation_style": self.explanation_style,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CommunicationPreferences':
        """Create from dictionary."""
        prefs = cls()
        prefs.language = data.get('language')
        prefs.formality = data.get('formality')
        prefs.tone = data.get('tone')
        prefs.emoji_usage = data.get('emoji_usage')
        prefs.response_length = data.get('response_length')
        prefs.explanation_style = data.get('explanation_style')
        
        last_updated = data.get('last_updated')
        if last_updated:
            prefs.last_updated = datetime.fromisoformat(last_updated)
        
        return prefs


class PreferenceExtractor:
    """
    Extracts communication preferences from user messages.
    
    Uses hybrid approach:
    1. Try LLM-based extraction (intelligent, flexible)
    2. Fall back to pattern matching (reliable, fast)
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize preference extractor.
        
        Args:
            llm_client: Optional LLM client for AI-based extraction
        """
        self.llm_client = llm_client
    
    # Pattern definitions for detecting preferences
    LANGUAGE_PATTERNS = {
        'spanish': [r'speak spanish', r'talk in spanish', r'use spanish', r'en español', r'habla español'],
        'french': [r'speak french', r'talk in french', r'use french', r'en français', r'parle français'],
        'german': [r'speak german', r'talk in german', r'use german', r'auf deutsch', r'sprich deutsch'],
        'english': [r'speak english', r'talk in english', r'use english', r'in english'],
    }
    
    FORMALITY_PATTERNS = {
        'casual': [
            r'(speak|talk|be) (more |)casual',
            r'(speak|talk) informally',
            r'don\'t be (so |)formal',
            r'be (more |)relaxed',
            r'keep it casual',
            r'(use|speak with) casual language'
        ],
        'formal': [
            r'(speak|talk|be) (more |)formal',
            r'(speak|talk) formally',
            r'be (more |)professional',
            r'use formal language',
            r'be polite and formal'
        ],
        'professional': [
            r'(speak|talk|be) professional',
            r'business (tone|language)',
            r'professional manner',
            r'corporate (style|language)'
        ]
    }
    
    TONE_PATTERNS = {
        'enthusiastic': [
            r'be (more |)enthusiastic',
            r'be (more |)energetic',
            r'be (more |)excited',
            r'show (more |)enthusiasm',
            r'be upbeat'
        ],
        'calm': [
            r'be (more |)calm',
            r'be (more |)measured',
            r'speak calmly',
            r'keep (it|things) calm',
            r'be (more |)relaxed'
        ],
        'friendly': [
            r'be (more |)friendly',
            r'be (more |)warm',
            r'be (more |)welcoming',
            r'friendly (tone|manner)'
        ],
        'neutral': [
            r'be (more |)neutral',
            r'be objective',
            r'keep it neutral',
            r'no emotion'
        ]
    }
    
    EMOJI_PATTERNS = {
        # Check False (negative) patterns FIRST by putting them first in dict
        False: [
            r'no emojis',
            r'don\'t use emojis',
            r'dont use emojis',  # Without apostrophe
            r'do not use emojis',
            r'please (don\'t|dont|do not) use emojis',
            r'without emojis',
            r'skip (the |)emojis',
            r'avoid emojis',
            r'stop using emojis',
            r'i (don\'t like|dont like|hate|dislike) emojis'
        ],
        True: [
            # Use positive lookbehind to ensure not preceded by "don't/dont/not"
            r'(?<!don\'t )(?<!dont )(?<!not )use emojis',
            r'(?<!don\'t )(?<!dont )add emojis',
            r'(?<!don\'t )(?<!dont )include emojis',
            r'with emojis',
            r'i (like|love|prefer) emojis',
            r'please use emojis'
        ]
    }
    
    LENGTH_PATTERNS = {
        'brief': [
            r'(be|keep it) (more |)brief',
            r'short (answers|responses)',
            r'keep it short',
            r'concise (answers|responses)',
            r'brief (answers|responses)'
        ],
        'detailed': [
            r'(be|give) (more |)detailed',
            r'long(er|) (answers|responses|explanations)',
            r'in-depth (answers|responses)',
            r'detailed (answers|responses|explanations)',
            r'thorough (answers|responses)'
        ],
        'balanced': [
            r'balanced (answers|responses)',
            r'medium length',
            r'not too (long|short)',
            r'moderate (length|detail)'
        ]
    }
    
    EXPLANATION_PATTERNS = {
        'simple': [
            r'explain (it |)simply',
            r'simple (terms|explanations|language)',
            r'easy to understand',
            r'like i\'m (five|5|a beginner)',
            r'layman\'s terms'
        ],
        'technical': [
            r'(be|get) technical',
            r'technical (terms|explanations|details)',
            r'use technical language',
            r'in-depth technical',
            r'technical details'
        ],
        'analogies': [
            r'use analogies',
            r'with analogies',
            r'explain with examples',
            r'use metaphors',
            r'compare it to'
        ]
    }
    
    async def extract_from_message(self, message: str) -> CommunicationPreferences:
        """
        Extract preferences from a single message using hybrid approach.
        
        Tries LLM first, falls back to patterns if LLM fails or returns low confidence.
        
        Args:
            message: User message text
            
        Returns:
            CommunicationPreferences with detected preferences
        """
        # Try LLM-based extraction first if available
        if self.llm_client:
            try:
                llm_prefs = await self._extract_with_llm(message)
                if llm_prefs and self._has_preferences(llm_prefs):
                    logger.info(f"LLM extracted preferences: {llm_prefs.to_dict()}")
                    return llm_prefs
                else:
                    logger.debug("LLM returned no preferences, falling back to patterns")
            except Exception as e:
                logger.warning(f"LLM preference extraction failed: {e}, falling back to patterns")
        
        # Fall back to pattern-based extraction
        prefs = self._extract_with_patterns(message)
        if self._has_preferences(prefs):
            logger.info(f"Pattern-based extracted preferences: {prefs.to_dict()}")
        
        return prefs
    
    def _extract_with_patterns(self, message: str) -> CommunicationPreferences:
        """
        Extract preferences using pattern matching (fallback method).
        
        Args:
            message: User message text
            
        Returns:
            CommunicationPreferences with detected preferences
        """
        prefs = CommunicationPreferences()
        message_lower = message.lower()
        
        # Check each preference category
        prefs.language = self._match_patterns(message_lower, self.LANGUAGE_PATTERNS)
        prefs.formality = self._match_patterns(message_lower, self.FORMALITY_PATTERNS)
        prefs.tone = self._match_patterns(message_lower, self.TONE_PATTERNS)
        prefs.emoji_usage = self._match_patterns(message_lower, self.EMOJI_PATTERNS)
        prefs.response_length = self._match_patterns(message_lower, self.LENGTH_PATTERNS)
        prefs.explanation_style = self._match_patterns(message_lower, self.EXPLANATION_PATTERNS)
        
        # Set timestamp if any preference was detected
        if self._has_preferences(prefs):
            prefs.last_updated = datetime.utcnow()
        
        return prefs
    
    async def _extract_with_llm(self, message: str) -> Optional[CommunicationPreferences]:
        """
        Extract preferences using LLM (AI-based method).
        
        Args:
            message: User message text
            
        Returns:
            CommunicationPreferences or None if extraction failed
        """
        prompt = f"""Analyze if this message contains communication preferences for how the AI should respond.

Message: "{message}"

Detect these preference types:
1. Language: English, Spanish, French, German, etc.
2. Formality: casual, formal, professional
3. Tone: enthusiastic, calm, neutral, friendly
4. Emoji usage: true (use emojis) or false (don't use emojis)
5. Response length: brief, detailed, balanced
6. Explanation style: simple, technical, analogies

Return ONLY valid JSON:
{{
  "language": "language name or null",
  "formality": "casual|formal|professional or null",
  "tone": "enthusiastic|calm|neutral|friendly or null",
  "emoji_usage": true|false|null,
  "response_length": "brief|detailed|balanced or null",
  "explanation_style": "simple|technical|analogies or null",
  "confidence": 0.0-1.0
}}

If NO preferences detected, return: {{"confidence": 0.0}}

JSON:"""

        try:
            response = await self.llm_client.chat([
                {"role": "system", "content": "You are a communication preference expert. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ])
            
            # Parse JSON response
            import json
            result = json.loads(response)
            
            # Check confidence
            confidence = result.get('confidence', 0.0)
            if confidence < 0.5:
                logger.debug(f"LLM preference detection low confidence: {confidence}")
                return None
            
            # Build preferences object
            prefs = CommunicationPreferences()
            prefs.language = result.get('language')
            prefs.formality = result.get('formality')
            prefs.tone = result.get('tone')
            prefs.emoji_usage = result.get('emoji_usage')
            prefs.response_length = result.get('response_length')
            prefs.explanation_style = result.get('explanation_style')
            prefs.last_updated = datetime.utcnow()
            
            return prefs
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM preference response: {e}")
            return None
    
    def _has_preferences(self, prefs: CommunicationPreferences) -> bool:
        """Check if any preferences were detected."""
        return any([
            prefs.language,
            prefs.formality,
            prefs.tone,
            prefs.emoji_usage is not None,
            prefs.response_length,
            prefs.explanation_style
        ])
    
    async def extract_from_messages(self, messages: List[Message]) -> CommunicationPreferences:
        """
        Extract preferences from multiple messages (most recent wins).
        
        Args:
            messages: List of user messages
            
        Returns:
            CommunicationPreferences with detected preferences
        """
        combined_prefs = CommunicationPreferences()
        
        # Process messages in order (later messages override earlier ones)
        for message in messages:
            if message.role != "user":
                continue
            
            msg_prefs = await self.extract_from_message(message.content)
            
            # Update combined preferences (non-None values override)
            if msg_prefs.language:
                combined_prefs.language = msg_prefs.language
            if msg_prefs.formality:
                combined_prefs.formality = msg_prefs.formality
            if msg_prefs.tone:
                combined_prefs.tone = msg_prefs.tone
            if msg_prefs.emoji_usage is not None:
                combined_prefs.emoji_usage = msg_prefs.emoji_usage
            if msg_prefs.response_length:
                combined_prefs.response_length = msg_prefs.response_length
            if msg_prefs.explanation_style:
                combined_prefs.explanation_style = msg_prefs.explanation_style
            if msg_prefs.last_updated:
                combined_prefs.last_updated = msg_prefs.last_updated
        
        return combined_prefs
    
    def _match_patterns(self, text: str, pattern_dict: Dict) -> Optional[any]:
        """
        Match text against pattern dictionary.
        
        Args:
            text: Text to search
            pattern_dict: Dictionary of value -> patterns
            
        Returns:
            Matched value or None
        """
        for value, patterns in pattern_dict.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return value
        return None
    
    def merge_preferences(
        self,
        existing: CommunicationPreferences,
        new: CommunicationPreferences
    ) -> CommunicationPreferences:
        """
        Merge new preferences into existing ones (new overwrites existing).
        
        Args:
            existing: Current preferences
            new: New preferences to merge
            
        Returns:
            Merged preferences
        """
        merged = CommunicationPreferences()
        
        # New preferences override existing ones
        merged.language = new.language if new.language else existing.language
        merged.formality = new.formality if new.formality else existing.formality
        merged.tone = new.tone if new.tone else existing.tone
        merged.emoji_usage = new.emoji_usage if new.emoji_usage is not None else existing.emoji_usage
        merged.response_length = new.response_length if new.response_length else existing.response_length
        merged.explanation_style = new.explanation_style if new.explanation_style else existing.explanation_style
        
        # Use most recent timestamp
        if new.last_updated and existing.last_updated:
            merged.last_updated = max(new.last_updated, existing.last_updated)
        else:
            merged.last_updated = new.last_updated or existing.last_updated
        
        return merged

