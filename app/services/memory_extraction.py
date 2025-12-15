"""Memory extraction service for identifying and storing facts from conversations."""

import logging
from typing import List, Optional
from uuid import UUID
import re

from app.models.memory import Message, MemoryType
from app.repositories.vector_store import VectorStoreRepository
from app.utils.embeddings import EmbeddingGenerator
from app.services.llm_client import LLMClient
from app.core.config import settings
from app.core.exceptions import MemoryStorageError

logger = logging.getLogger(__name__)


class MemoryExtractor:
    """Service for extracting and storing long-term memories from conversations."""
    
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
        self.min_turns = settings.memory_extraction_min_turns
    
    async def extract_and_store(
        self,
        conversation_id: UUID,
        messages: List[Message]
    ) -> int:
        """
        Extract memories from conversation messages and store them.
        
        Args:
            conversation_id: Conversation identifier
            messages: List of recent messages
            
        Returns:
            Number of memories extracted and stored
        """
        # Only extract after minimum number of turns
        if len(messages) < self.min_turns:
            logger.debug(f"Not enough messages for extraction ({len(messages)} < {self.min_turns})")
            return 0
        
        try:
            # Extract facts using heuristics
            facts = self._extract_facts_heuristic(messages)
            
            if not facts:
                logger.debug("No facts extracted from messages")
                return 0
            
            # Generate embeddings in batch
            contents = [fact['content'] for fact in facts]
            embeddings = self.embedding_generator.batch_generate_embeddings(contents)
            
            # Store each fact
            stored_count = 0
            for fact, embedding in zip(facts, embeddings):
                try:
                    await self.vector_store.store_memory(
                        conversation_id=conversation_id,
                        content=fact['content'],
                        embedding=embedding,
                        memory_type=fact['type'],
                        importance=fact['importance'],
                        metadata=fact.get('metadata', {})
                    )
                    stored_count += 1
                except Exception as e:
                    logger.warning(f"Failed to store memory: {e}")
            
            logger.info(f"Extracted and stored {stored_count} memories for conversation {conversation_id}")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error extracting memories: {e}")
            raise MemoryStorageError(f"Failed to extract memories: {e}")
    
    def _extract_facts_heuristic(self, messages: List[Message]) -> List[dict]:
        """
        Extract facts using rule-based heuristics.
        
        This is a simplified implementation. In production, you could use
        the LLM to identify more nuanced facts.
        
        Args:
            messages: List of messages
            
        Returns:
            List of fact dictionaries
        """
        facts = []
        
        # Patterns that suggest important information
        preference_patterns = [
            r"i (like|love|prefer|enjoy|hate|dislike)",
            r"my favorite",
            r"i'm (interested in|into)",
        ]
        
        fact_patterns = [
            r"my name is (\w+)",
            r"i (work|study|live) (at|in)",
            r"i am (a|an) (\w+)",
            r"i have (a|an|\d+)",
        ]
        
        for message in messages:
            if message.role != "user":
                continue
            
            content_lower = message.content.lower()
            
            # Check for preferences
            for pattern in preference_patterns:
                if re.search(pattern, content_lower):
                    facts.append({
                        'content': message.content,
                        'type': MemoryType.PREFERENCE,
                        'importance': 0.7,
                        'metadata': {'extracted_at': message.timestamp.isoformat()}
                    })
                    break
            
            # Check for facts
            for pattern in fact_patterns:
                if re.search(pattern, content_lower):
                    facts.append({
                        'content': message.content,
                        'type': MemoryType.FACT,
                        'importance': 0.8,
                        'metadata': {'extracted_at': message.timestamp.isoformat()}
                    })
                    break
            
            # Store context for longer, meaningful messages
            if len(message.content.split()) > 15:
                facts.append({
                    'content': message.content,
                    'type': MemoryType.CONTEXT,
                    'importance': 0.5,
                    'metadata': {'extracted_at': message.timestamp.isoformat()}
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
        Extract facts using LLM (advanced method).
        
        This method uses the LLM to identify important facts from conversations.
        Disabled by default for performance.
        
        Args:
            messages: List of messages
            
        Returns:
            List of fact dictionaries
        """
        if self.llm_client is None:
            return []
        
        # Build prompt for extraction
        conversation_text = "\n".join([
            f"{msg.role}: {msg.content}" for msg in messages[-6:]  # Last 6 messages
        ])
        
        extraction_prompt = f"""Analyze this conversation and extract 3-5 key facts worth remembering:

{conversation_text}

List the facts as bullet points. Focus on:
- User preferences and interests
- Important personal information
- Key topics discussed
- Specific requests or goals

Facts:"""
        
        try:
            response = await self.llm_client.chat([
                {"role": "system", "content": "You extract key facts from conversations."},
                {"role": "user", "content": extraction_prompt}
            ])
            
            # Parse response and create fact objects
            # This is simplified - would need more robust parsing
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            facts = []
            
            for line in lines:
                # Remove bullet points
                line = re.sub(r'^[-*•]\s*', '', line)
                if len(line) > 10:  # Reasonable fact length
                    facts.append({
                        'content': line,
                        'type': MemoryType.FACT,
                        'importance': 0.7,
                        'metadata': {'extraction_method': 'llm'}
                    })
            
            return facts[:5]
            
        except Exception as e:
            logger.warning(f"LLM-based extraction failed: {e}")
            return []

