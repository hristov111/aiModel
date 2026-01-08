"""Memory extraction service for identifying and storing facts from conversations."""

import logging
from typing import List, Optional
from uuid import UUID
import re

from app.models.memory import Message, MemoryType
from app.repositories.vector_store import VectorStoreRepository
from app.utils.embeddings import EmbeddingGenerator
from app.services.llm_client import LLMClient
from app.services.memory_categorizer import MemoryCategorizer
from app.core.config import settings
from app.core.exceptions import MemoryStorageError

logger = logging.getLogger(__name__)


class MemoryExtractor:
    """
    Service for extracting and storing long-term memories from conversations.
    
    Now includes intelligent memory categorization via AI chaining!
    """
    
    def __init__(
        self,
        vector_store: VectorStoreRepository,
        embedding_generator: EmbeddingGenerator,
        llm_client: Optional[LLMClient] = None
    ):
        """
        Initialize memory extractor.
        
        Args:
            vector_store: Vector store repository
            embedding_generator: Embedding generator
            llm_client: Optional LLM client for advanced extraction
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.llm_client = llm_client
        self.categorizer = MemoryCategorizer(llm_client=llm_client)
        self.min_turns = settings.memory_extraction_min_turns
    
    async def extract_and_store(
        self,
        conversation_id: UUID,
        messages: List[Message],
        personality_id: Optional[UUID] = None
    ) -> int:
        """
        Extract memories from conversation messages and store them.
        
        Uses configurable extraction method (LLM, heuristic, or hybrid).
        
        Args:
            conversation_id: Conversation identifier
            messages: List of recent messages
            personality_id: Optional personality UUID to link memories to
            
        Returns:
            Number of memories extracted and stored
        """
        # Only extract after minimum number of turns
        if len(messages) < self.min_turns:
            logger.debug(f"Not enough messages for extraction ({len(messages)} < {self.min_turns})")
            return 0
        
        try:
            # Choose extraction method based on configuration
            extraction_method = settings.memory_extraction_method.lower()
            facts = []
            
            if extraction_method == "llm":
                # Use LLM-based extraction only
                logger.debug("Using LLM-based memory extraction")
                facts = await self._extract_facts_with_llm(messages)
                
            elif extraction_method == "heuristic":
                # Use pattern-based extraction only
                logger.debug("Using heuristic-based memory extraction")
                facts = self._extract_facts_heuristic(messages)
                
            else:  # hybrid (default)
                # Try LLM first, fall back to heuristic if LLM fails or returns nothing
                logger.debug("Using hybrid memory extraction (LLM with heuristic fallback)")
                facts = await self._extract_facts_with_llm(messages)
                
                if not facts:
                    logger.info("LLM extraction returned nothing, falling back to heuristic method")
                    facts = self._extract_facts_heuristic(messages)
                else:
                    logger.info(f"LLM successfully extracted {len(facts)} memories")
            
            if not facts:
                logger.debug("No facts extracted from messages")
                return 0
            
            # 🔍 LOG: Show extracted facts
            logger.info(f"📝 MEMORY EXTRACTION: Extracted {len(facts)} facts from conversation")
            for idx, fact in enumerate(facts, 1):
                logger.info(f"  └─ Fact {idx}: '{fact}'")
            
            # Generate embeddings in batch
            contents = [fact['content'] for fact in facts]
            embeddings = self.embedding_generator.batch_generate_embeddings(contents)
            
            # Store each fact (with deduplication)
            stored_count = 0
            skipped_duplicates = 0
            
            for fact, embedding in zip(facts, embeddings):
                try:
                    # Check for duplicate memories (similarity > 0.95 = very similar)
                    existing_similar = await self.vector_store.search_similar(
                        conversation_id=conversation_id,
                        query_embedding=embedding,
                        top_k=1,
                        min_similarity=0.95,  # Very high threshold for duplicates
                        personality_id=personality_id
                    )
                    
                    # If very similar memory exists, skip storing
                    if existing_similar and len(existing_similar) > 0:
                        similar_memory = existing_similar[0]
                        logger.debug(
                            f"Skipping duplicate memory: '{fact['content'][:50]}...' "
                            f"(similar to existing: '{similar_memory.content[:50]}...')"
                        )
                        skipped_duplicates += 1
                        continue
                    
                    # Store new unique memory
                    await self.vector_store.store_memory(
                        conversation_id=conversation_id,
                        content=fact['content'],
                        embedding=embedding,
                        memory_type=fact['type'],
                        importance=fact['importance'],
                        metadata=fact.get('metadata', {}),
                        personality_id=personality_id
                    )
                    stored_count += 1
                    logger.debug(
                        f"Stored memory: '{fact['content'][:50]}...' "
                        f"(type={fact['type'].value}, importance={fact['importance']:.2f}, "
                        f"method={fact.get('metadata', {}).get('extraction_method', 'unknown')})"
                    )
                except Exception as e:
                    logger.warning(f"Failed to store memory: {e}")
            
            logger.info(
                f"Extracted and stored {stored_count} memories for conversation {conversation_id} "
                f"using {extraction_method} method (skipped {skipped_duplicates} duplicates)"
            )
            return stored_count
            
        except Exception as e:
            logger.error(f"Error extracting memories: {e}")
            raise MemoryStorageError(f"Failed to extract memories: {e}")
    
    def _extract_facts_heuristic(self, messages: List[Message]) -> List[dict]:
        """
        Extract facts using rule-based heuristics with intelligent categorization.
        
        Now uses MemoryCategorizer for better type detection!
        
        Args:
            messages: List of messages
            
        Returns:
            List of fact dictionaries
        """
        facts = []
        
        # Patterns that suggest important information worth storing
        important_patterns = [
            r"i (don't|dont|do not|really|actually)?\s?(like|love|prefer|enjoy|hate|dislike)",
            r"my (favorite|name)",
            r"i'm (interested in|into|not interested in)",
            r"i (work|study|live) (at|in)",
            r"i am (a|an) (\w+)",
            r"i have (a|an|\d+)",
            r"(remember|reminds me)",
            r"(when i|i once|i used to)",
        ]
        
        for message in messages:
            if message.role != "user":
                continue
            
            content_lower = message.content.lower()
            content_stripped = message.content.strip()
            
            # Skip questions - they're not facts to remember
            is_question = (
                content_stripped.endswith('?') or
                re.match(r'^(do|does|did|is|are|was|were|can|could|will|would|should|what|when|where|why|how|who)\s', content_lower) or
                re.search(r'\b(do you know|can you tell me|what is|what are|what do)\b', content_lower)
            )
            
            if is_question:
                logger.debug(f"Skipping question: '{content_stripped[:50]}...'")
                continue
            
            should_store = False
            
            # Check if message matches important patterns
            for pattern in important_patterns:
                if re.search(pattern, content_lower):
                    should_store = True
                    break
            
            # Also store longer, meaningful messages
            if not should_store and len(message.content.split()) > 15:
                should_store = True
            
            if should_store:
                # Use categorizer to intelligently determine type
                categorization = self.categorizer._categorize_with_patterns(message.content)
                
                # Determine importance based on type
                importance_map = {
                    MemoryType.FACT: 0.8,
                    MemoryType.PREFERENCE: 0.7,
                    MemoryType.EVENT: 0.75,
                    MemoryType.CONTEXT: 0.5
                }
                
                importance = importance_map.get(
                    categorization['type'],
                    0.6
                )
                
                facts.append({
                    'content': message.content,
                    'type': categorization['type'],
                    'importance': importance,
                    'metadata': {
                        'extracted_at': message.timestamp.isoformat(),
                        'categorization_confidence': categorization['confidence'],
                        'categorization_reasoning': categorization['reasoning']
                    }
                })
        
        # Deduplicate and limit
        unique_facts = []
        seen_contents = set()
        
        for fact in facts:
            content_key = fact['content'].lower().strip()
            if content_key not in seen_contents:
                unique_facts.append(fact)
                seen_contents.add(content_key)
        
        # Limit to top N most important
        unique_facts.sort(key=lambda f: f['importance'], reverse=True)
        return unique_facts[:5]  # Max 5 facts per extraction
    
    async def _extract_facts_with_llm(self, messages: List[Message]) -> List[dict]:
        """
        Extract facts using LLM (advanced method with intelligent importance scoring).
        
        This method uses the LLM to intelligently identify important facts from conversations.
        The LLM determines what's worth remembering, handles context and nuance,
        and scores importance automatically.
        
        Args:
            messages: List of messages
            
        Returns:
            List of fact dictionaries
        """
        if self.llm_client is None:
            logger.debug("LLM client not available for memory extraction")
            return []
        
        # Build conversation context (last 10 messages for better context)
        conversation_text = "\n".join([
            f"{msg.role}: {msg.content}" for msg in messages[-10:]
        ])
        
        extraction_prompt = f"""You are a memory extraction assistant. Analyze this conversation and identify information worth remembering about the user.

Conversation:
{conversation_text}

Extract meaningful facts about the user. For each fact, determine:
1. What information should be remembered
2. The type (preference, fact, event, or context)
3. Importance score (0.0-1.0)

Memory Types:
- **preference**: Likes, dislikes, interests, opinions
- **fact**: Objective personal information (job, location, name)
- **event**: Experiences, memories, stories, past occurrences
- **context**: General conversational topics

Consider storing:
- Personal preferences and dislikes (likes/dislikes, interests) → preference
- Important life facts (job, location, family, health conditions) → fact
- Goals and aspirations → fact
- Significant events or experiences → event
- Strong opinions or values → preference
- Behavioral patterns or habits → fact
- Things user explicitly asks to remember → appropriate type

IGNORE and do NOT store:
- Generic responses ("ok", "thanks", "lol", "yes", "no")
- Questions to the AI (anything ending with ?, starting with "do", "can", "what", "how", etc.)
- Questions about what the AI knows or remembers ("do I like X?", "what's my name?", "do you remember?")
- Temporary conversational context
- Politeness phrases
- Commands or instructions to the AI
- Requests for information without providing new information

Importance scoring guide:
- 0.9-1.0: Critical personal info (health, family, core values)
- 0.7-0.8: Important preferences and facts
- 0.5-0.6: Useful context and interests
- 0.3-0.4: Minor preferences
- Below 0.3: Don't store

Return ONLY a valid JSON array with this exact format:
[
  {{
    "content": "brief, clear statement of the fact in first person",
    "type": "preference",
    "importance": 0.8,
    "reasoning": "why this is important to remember"
  }}
]

If nothing important to remember, return: []

JSON array:"""
        
        try:
            response = await self.llm_client.chat([
                {"role": "system", "content": "You are a precise memory extraction system. Output only valid JSON arrays."},
                {"role": "user", "content": extraction_prompt}
            ])
            
            # Parse JSON response (handle markdown code blocks)
            import json
            
            # Try to extract JSON from response (might have markdown formatting)
            json_match = re.search(r'\[[\s\S]*\]', response)
            if not json_match:
                logger.warning("No JSON array found in LLM response")
                return []
            
            facts_data = json.loads(json_match.group())
            
            if not isinstance(facts_data, list):
                logger.warning(f"LLM returned non-list: {type(facts_data)}")
                return []
            
            # Convert to memory facts
            facts = []
            for item in facts_data:
                if not isinstance(item, dict):
                    continue
                
                # Validate required fields
                if 'content' not in item or 'type' not in item or 'importance' not in item:
                    logger.warning(f"Skipping invalid fact: {item}")
                    continue
                
                # Map string type to MemoryType enum
                type_map = {
                    'preference': MemoryType.PREFERENCE,
                    'fact': MemoryType.FACT,
                    'event': MemoryType.EVENT,
                    'goal': MemoryType.FACT,  # Store goals as facts for now
                    'context': MemoryType.CONTEXT
                }
                
                mem_type = type_map.get(item['type'].lower(), MemoryType.FACT)
                importance = float(item['importance'])
                
                # Only store if importance is above threshold
                if importance >= 0.3:
                    facts.append({
                        'content': item['content'],
                        'type': mem_type,
                        'importance': min(importance, 1.0),  # Cap at 1.0
                        'metadata': {
                            'extraction_method': 'llm',
                            'reasoning': item.get('reasoning', ''),
                            'extracted_at': messages[-1].timestamp.isoformat() if messages else None
                        }
                    })
            
            logger.info(f"LLM extracted {len(facts)} facts from {len(messages)} messages")
            
            # Sort by importance and limit to top 5
            facts.sort(key=lambda f: f['importance'], reverse=True)
            return facts[:5]
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Response was: {response[:200]}...")
            return []
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return []

