"""Intelligent memory categorization with AI chaining."""

import re
import json
import logging
from typing import Optional, Dict, Any

from app.models.memory import MemoryType
from app.core.config import settings

logger = logging.getLogger(__name__)


class MemoryCategorizer:
    """
    Categorizes memories into types (FACT, PREFERENCE, EVENT, CONTEXT).
    
    Supports multiple categorization methods:
    - Pattern-based (regex matching)
    - LLM-based (AI chaining for semantic understanding)
    - Hybrid (LLM with pattern fallback)
    
    Examples:
    - "I like chocolate" → PREFERENCE (obvious)
    - "Chocolate reminds me of my grandmother" → EVENT (AI understands emotional memory)
    - "I work at Google" → FACT (straightforward)
    - "We were talking about AI safety" → CONTEXT (conversation topic)
    """
    
    def __init__(self, llm_client=None, method: str = None):
        """
        Initialize memory categorizer.
        
        Args:
            llm_client: Optional LLM client for AI-based categorization
            method: Categorization method ("llm", "pattern", "hybrid"). Defaults to config.
        """
        self.llm_client = llm_client
        self.method = method or settings.memory_categorization_method.lower()
        logger.info(f"MemoryCategorizer initialized with method: {self.method}")
    
    async def categorize(
        self,
        content: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Categorize a memory using the configured method.
        
        Args:
            content: Memory content to categorize
            context: Optional conversation context
            
        Returns:
            Dict with 'type' (MemoryType), 'confidence' (float), and 'reasoning' (str)
        """
        if not content or len(content.strip()) < 3:
            return {
                'type': MemoryType.CONTEXT,
                'confidence': 0.5,
                'reasoning': 'Too short to categorize meaningfully'
            }
        
        # Choose categorization method
        if self.method == "llm":
            return await self._categorize_with_llm(content, context)
        elif self.method == "pattern":
            return self._categorize_with_patterns(content)
        else:  # hybrid (default)
            # Try LLM first
            llm_result = await self._categorize_with_llm(content, context)
            if llm_result and llm_result.get('confidence', 0) >= 0.6:
                logger.debug(f"Using LLM categorization (confidence: {llm_result['confidence']:.2f})")
                return llm_result
            # Fallback to patterns
            logger.debug("LLM categorization low confidence, falling back to patterns")
            return self._categorize_with_patterns(content)
    
    def _categorize_with_patterns(self, content: str) -> Dict[str, Any]:
        """
        Categorize memory using pattern matching (original method).
        
        Args:
            content: Memory content
            
        Returns:
            Dict with categorization result
        """
        content_lower = content.lower()
        
        # PREFERENCE patterns
        preference_patterns = [
            r'\b(i|my)\s+(like|love|prefer|enjoy|hate|dislike|can\'?t stand)\b',
            r'\bmy\s+favorite\b',
            r'\bi\'?m\s+(interested in|into|passionate about)\b',
            r'\bi\s+(don\'?t|do not)\s+(like|enjoy|want)\b',
            r'\bi\s+would\s+(rather|prefer)\b',
        ]
        
        for pattern in preference_patterns:
            if re.search(pattern, content_lower):
                return {
                    'type': MemoryType.PREFERENCE,
                    'confidence': 0.8,
                    'reasoning': 'Pattern match: preference expression detected'
                }
        
        # FACT patterns (personal information)
        fact_patterns = [
            r'\bmy\s+name\s+is\b',
            r'\bi\s+(work|study|live|am|have)\s+(at|in|a|an)\b',
            r'\bi\'?m\s+(a|an)\s+\w+\b',
            r'\bi\s+have\s+(a|an|\d+)\b',
            r'\bmy\s+(job|career|profession|occupation)\b',
            r'\bi\s+(was born|grew up)\b',
            r'\bmy\s+(age|birthday|location)\b',
        ]
        
        for pattern in fact_patterns:
            if re.search(pattern, content_lower):
                return {
                    'type': MemoryType.FACT,
                    'confidence': 0.85,
                    'reasoning': 'Pattern match: factual personal information'
                }
        
        # EVENT patterns (experiences, memories)
        event_patterns = [
            r'\b(remember|recall|reminds me)\b',
            r'\b(when i|i once|i used to)\b',
            r'\b(happened|occurred|took place)\b',
            r'\b(experience|memory|story)\b',
            r'\b(yesterday|last week|ago)\b',
            r'\bi\s+(went|did|saw|met)\b',
        ]
        
        for pattern in event_patterns:
            if re.search(pattern, content_lower):
                return {
                    'type': MemoryType.EVENT,
                    'confidence': 0.75,
                    'reasoning': 'Pattern match: event or experience description'
                }
        
        # Default to CONTEXT for everything else
        # Longer messages are more likely to be context
        confidence = 0.6 if len(content.split()) > 15 else 0.5
        
        return {
            'type': MemoryType.CONTEXT,
            'confidence': confidence,
            'reasoning': 'No specific patterns matched, categorized as conversational context'
        }
    
    async def _categorize_with_llm(
        self,
        content: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Categorize memory using LLM (AI chaining for semantic understanding).
        
        Args:
            content: Memory content
            context: Optional conversation context
            
        Returns:
            Dict with categorization result
        """
        if not self.llm_client:
            logger.debug("LLM client not available for memory categorization")
            return {
                'type': MemoryType.CONTEXT,
                'confidence': 0.0,
                'reasoning': 'LLM not available'
            }
        
        # Build context string
        context_str = ""
        if context:
            context_str = f"\n\nConversation context:\n{context}"
        
        prompt = f"""Categorize this memory into the most appropriate type.

Memory to categorize: "{content}"{context_str}

Memory Types:
1. **FACT** - Objective personal information
   - Examples: "I work at Google", "My name is John", "I live in NYC", "I have 2 kids"
   - Characteristics: Verifiable, stable, biographical information

2. **PREFERENCE** - Subjective likes, dislikes, opinions
   - Examples: "I like chocolate", "I hate mornings", "My favorite color is blue"
   - Characteristics: Personal taste, opinions, interests, values

3. **EVENT** - Experiences, memories, stories, past occurrences
   - Examples: "I went to Paris last year", "Chocolate reminds me of my grandmother"
   - Characteristics: Time-bound, narrative, experiential, emotional memories

4. **CONTEXT** - Conversational topics, general discussion
   - Examples: "We were talking about AI", "This is about climate change"
   - Characteristics: Topic references, meta-conversation, general context

Categorization Guidelines:
- Focus on the PRIMARY purpose and nature of the memory
- Consider emotional vs factual content
- Time-bound experiences → EVENT
- Stable personal info → FACT
- Subjective opinions → PREFERENCE
- Topic references → CONTEXT

Return ONLY valid JSON:
{{
  "type": "fact|preference|event|context",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation of why this category fits best"
}}

JSON:"""
        
        try:
            response = await self.llm_client.chat([
                {"role": "system", "content": "You are a memory categorization expert. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ])
            
            # Parse JSON response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                logger.warning("No JSON found in LLM categorization response")
                return {
                    'type': MemoryType.CONTEXT,
                    'confidence': 0.0,
                    'reasoning': 'Failed to parse LLM response'
                }
            
            result = json.loads(json_match.group())
            
            # Validate and map type
            type_map = {
                'fact': MemoryType.FACT,
                'preference': MemoryType.PREFERENCE,
                'event': MemoryType.EVENT,
                'context': MemoryType.CONTEXT
            }
            
            memory_type_str = result.get('type', 'context').lower()
            memory_type = type_map.get(memory_type_str, MemoryType.CONTEXT)
            confidence = float(result.get('confidence', 0.5))
            reasoning = result.get('reasoning', 'LLM categorization')
            
            # Validate confidence range
            confidence = max(0.0, min(1.0, confidence))
            
            logger.info(
                f"LLM categorized as {memory_type.value} "
                f"(confidence: {confidence:.2f})"
            )
            
            return {
                'type': memory_type,
                'confidence': confidence,
                'reasoning': reasoning
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM categorization JSON: {e}")
            return {
                'type': MemoryType.CONTEXT,
                'confidence': 0.0,
                'reasoning': 'JSON parse error'
            }
        except Exception as e:
            logger.error(f"LLM categorization failed: {e}")
            return {
                'type': MemoryType.CONTEXT,
                'confidence': 0.0,
                'reasoning': f'Error: {str(e)}'
            }
