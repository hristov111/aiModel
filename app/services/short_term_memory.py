"""Short-term memory manager for conversation buffering."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID
import threading
import logging

from app.models.memory import Message

logger = logging.getLogger(__name__)


class ConversationBuffer:
    """
    Thread-safe in-memory buffer for short-term conversation memory.
    
    Stores recent messages and summaries per conversation.
    In production, consider using Redis for distributed deployments.
    """
    
    def __init__(self, max_messages: int = 10, ttl_hours: int = 24):
        """
        Initialize conversation buffer.
        
        Args:
            max_messages: Maximum messages to keep per conversation
            ttl_hours: Time-to-live for inactive conversations
        """
        self.max_messages = max_messages
        self.ttl_hours = ttl_hours
        
        # Storage: conversation_id -> list of messages
        self._messages: Dict[UUID, List[Message]] = defaultdict(list)
        
        # Storage: conversation_id -> summary text
        self._summaries: Dict[UUID, str] = {}
        
        # Track last access time for TTL
        self._last_access: Dict[UUID, datetime] = {}
        
        # Thread lock for thread safety
        self._lock = threading.RLock()
    
    def add_message(self, conversation_id: UUID, role: str, content: str) -> None:
        """
        Add a message to the conversation buffer.
        
        Args:
            conversation_id: Conversation identifier
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        with self._lock:
            message = Message(
                role=role,
                content=content,
                timestamp=datetime.utcnow()
            )
            
            self._messages[conversation_id].append(message)
            
            # Keep only the most recent N messages
            if len(self._messages[conversation_id]) > self.max_messages:
                self._messages[conversation_id] = self._messages[conversation_id][-self.max_messages:]
            
            # Update last access time
            self._last_access[conversation_id] = datetime.utcnow()
            
            logger.debug(f"Added {role} message to conversation {conversation_id}")
    
    def get_recent_messages(self, conversation_id: UUID, n: Optional[int] = None) -> List[Message]:
        """
        Get recent messages from a conversation.
        
        Args:
            conversation_id: Conversation identifier
            n: Number of recent messages to retrieve (default: all available)
            
        Returns:
            List of recent messages
        """
        with self._lock:
            messages = self._messages.get(conversation_id, [])
            
            # Update last access time
            if conversation_id in self._messages:
                self._last_access[conversation_id] = datetime.utcnow()
            
            if n is None:
                return messages.copy()
            return messages[-n:] if len(messages) > n else messages.copy()
    
    def get_or_create_summary(self, conversation_id: UUID) -> Optional[str]:
        """
        Get the conversation summary if it exists.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Summary text or None
        """
        with self._lock:
            return self._summaries.get(conversation_id)
    
    def update_summary(self, conversation_id: UUID, summary: str) -> None:
        """
        Update the conversation summary.
        
        Args:
            conversation_id: Conversation identifier
            summary: New summary text
        """
        with self._lock:
            self._summaries[conversation_id] = summary
            self._last_access[conversation_id] = datetime.utcnow()
            logger.debug(f"Updated summary for conversation {conversation_id}")
    
    def reset_conversation(self, conversation_id: UUID) -> None:
        """
        Reset a conversation (clear messages but keep summary).
        
        Args:
            conversation_id: Conversation identifier
        """
        with self._lock:
            if conversation_id in self._messages:
                self._messages[conversation_id].clear()
                logger.info(f"Reset conversation {conversation_id}")
    
    def clear_conversation(self, conversation_id: UUID) -> None:
        """
        Completely clear a conversation (messages and summary).
        
        Args:
            conversation_id: Conversation identifier
        """
        with self._lock:
            if conversation_id in self._messages:
                del self._messages[conversation_id]
            if conversation_id in self._summaries:
                del self._summaries[conversation_id]
            if conversation_id in self._last_access:
                del self._last_access[conversation_id]
            logger.info(f"Cleared conversation {conversation_id}")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired conversations based on TTL.
        
        Returns:
            Number of conversations removed
        """
        with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(hours=self.ttl_hours)
            
            expired = [
                conv_id for conv_id, last_access in self._last_access.items()
                if last_access < cutoff
            ]
            
            for conv_id in expired:
                self.clear_conversation(conv_id)
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired conversations")
            
            return len(expired)
    
    def get_conversation_count(self) -> int:
        """Get the number of active conversations."""
        with self._lock:
            return len(self._messages)


# Global instance
_conversation_buffer: Optional[ConversationBuffer] = None
_buffer_lock = threading.Lock()


def get_conversation_buffer() -> ConversationBuffer:
    """Get or create the global conversation buffer instance."""
    global _conversation_buffer
    
    if _conversation_buffer is None:
        with _buffer_lock:
            if _conversation_buffer is None:
                from app.core.config import settings
                _conversation_buffer = ConversationBuffer(
                    max_messages=settings.short_term_memory_size
                )
    
    return _conversation_buffer

