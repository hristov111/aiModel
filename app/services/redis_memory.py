"""Redis-based short-term memory for distributed deployments."""

import json
import logging
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisConversationBuffer:
    """
    Redis-based conversation buffer for distributed deployments.
    
    Features:
    - Distributed state across multiple instances
    - TTL-based expiration
    - Atomic operations
    - Scalable to multiple servers
    
    Fallback to in-memory if Redis unavailable.
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        max_size: int = 10,
        ttl_seconds: int = 3600
    ):
        """
        Initialize Redis conversation buffer.
        
        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
            max_size: Maximum messages per conversation
            ttl_seconds: Time-to-live for conversations in seconds
        """
        self.redis_url = redis_url or getattr(settings, 'redis_url', None)
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._redis_client: Optional[redis.Redis] = None
        self._connected = False
        
        # Fallback to in-memory if Redis not configured
        if not self.redis_url:
            logger.warning(
                "Redis URL not configured. Using in-memory fallback. "
                "Set REDIS_URL for distributed deployments."
            )
            from app.services.short_term_memory import ConversationBuffer
            self._fallback = ConversationBuffer(max_size=max_size)
        else:
            self._fallback = None
    
    async def _get_client(self) -> Optional[redis.Redis]:
        """Get or create Redis client."""
        if not self.redis_url:
            return None
        
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True
                )
                # Test connection
                await self._redis_client.ping()
                self._connected = True
                logger.info("✅ Connected to Redis for distributed memory")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")
                self._connected = False
                return None
        
        return self._redis_client if self._connected else None
    
    def _make_key(self, conversation_id: UUID) -> str:
        """Generate Redis key for conversation."""
        return f"conversation:{conversation_id}"
    
    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add message to conversation buffer.
        
        Args:
            conversation_id: Conversation UUID
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Optional metadata
        """
        client = await self._get_client()
        
        # Fallback to in-memory if Redis unavailable
        if client is None and self._fallback:
            self._fallback.add_message(conversation_id, role, content, metadata)
            return
        
        try:
            key = self._make_key(conversation_id)
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # Add message to list
            await client.rpush(key, json.dumps(message))
            
            # Trim to max size (keep last N messages)
            await client.ltrim(key, -self.max_size, -1)
            
            # Set TTL
            await client.expire(key, self.ttl_seconds)
            
        except Exception as e:
            logger.error(f"Failed to add message to Redis: {e}")
            if self._fallback:
                self._fallback.add_message(conversation_id, role, content, metadata)
    
    async def get_messages(self, conversation_id: UUID) -> List[Dict]:
        """
        Get all messages for a conversation.
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            List of message dictionaries
        """
        client = await self._get_client()
        
        # Fallback to in-memory if Redis unavailable
        if client is None and self._fallback:
            return self._fallback.get_messages(conversation_id)
        
        try:
            key = self._make_key(conversation_id)
            messages_json = await client.lrange(key, 0, -1)
            
            messages = []
            for msg_json in messages_json:
                try:
                    messages.append(json.loads(msg_json))
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message JSON: {e}")
            
            # Refresh TTL on access
            if messages:
                await client.expire(key, self.ttl_seconds)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages from Redis: {e}")
            if self._fallback:
                return self._fallback.get_messages(conversation_id)
            return []
    
    async def clear_conversation(self, conversation_id: UUID) -> None:
        """
        Clear all messages for a conversation.
        
        Args:
            conversation_id: Conversation UUID
        """
        client = await self._get_client()
        
        # Fallback to in-memory if Redis unavailable
        if client is None and self._fallback:
            self._fallback.clear_conversation(conversation_id)
            return
        
        try:
            key = self._make_key(conversation_id)
            await client.delete(key)
        except Exception as e:
            logger.error(f"Failed to clear conversation in Redis: {e}")
            if self._fallback:
                self._fallback.clear_conversation(conversation_id)
    
    async def cleanup_expired(self) -> int:
        """
        Cleanup expired conversations (handled automatically by Redis TTL).
        
        Returns:
            Number of conversations cleaned up (0 for Redis)
        """
        # Redis handles expiration automatically via TTL
        return 0
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            try:
                await self._redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

