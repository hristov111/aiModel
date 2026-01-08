"""Redis cache for personality configurations."""

import redis.asyncio as redis
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PersonalityCache:
    """Cache for global personality configurations."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize personality cache.
        
        Args:
            redis_url: Redis connection URL (None disables caching)
        """
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
        self._enabled = bool(redis_url)
        self.ttl = 86400  # 24 hours (personalities rarely change)
        
        if not self._enabled:
            logger.info("PersonalityCache: Redis not configured, caching disabled")
    
    async def _get_client(self) -> Optional[redis.Redis]:
        """Get or create Redis client."""
        if not self._enabled:
            return None
            
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_keepalive=True
                )
                # Test connection
                await self._client.ping()
                logger.info("✅ PersonalityCache: Connected to Redis")
            except Exception as e:
                logger.warning(f"⚠️ PersonalityCache: Redis connection failed: {e}")
                self._enabled = False
                return None
        
        return self._client
    
    async def get_personality_id(self, personality_name: str) -> Optional[str]:
        """
        Get personality ID from cache.
        
        Args:
            personality_name: Name of personality (e.g., 'elara')
            
        Returns:
            Personality ID (UUID as string) or None
        """
        if not self._enabled:
            return None
            
        try:
            client = await self._get_client()
            if not client:
                return None
                
            key = f"personality:global:{personality_name}:id"
            cached_id = await client.get(key)
            
            if cached_id:
                logger.debug(f"✅ Cache HIT: {personality_name} -> {cached_id}")
                return cached_id
            
            logger.debug(f"❌ Cache MISS: {personality_name}")
            return None
            
        except Exception as e:
            logger.warning(f"PersonalityCache get error: {e}")
            return None
    
    async def set_personality_id(self, personality_name: str, personality_id: str):
        """
        Cache personality ID.
        
        Args:
            personality_name: Name of personality
            personality_id: UUID of personality (as string)
        """
        if not self._enabled:
            return
            
        try:
            client = await self._get_client()
            if not client:
                return
                
            key = f"personality:global:{personality_name}:id"
            await client.setex(key, self.ttl, personality_id)
            logger.debug(f"✅ Cached: {personality_name} -> {personality_id}")
            
        except Exception as e:
            logger.warning(f"PersonalityCache set error: {e}")
    
    async def get_personality_config(self, personality_name: str) -> Optional[Dict[str, Any]]:
        """
        Get full personality configuration from cache.
        
        Args:
            personality_name: Name of personality
            
        Returns:
            Personality config dict or None
        """
        if not self._enabled:
            return None
            
        try:
            client = await self._get_client()
            if not client:
                return None
                
            key = f"personality:global:{personality_name}:config"
            cached = await client.get(key)
            
            if cached:
                logger.debug(f"✅ Config cache HIT: {personality_name}")
                return json.loads(cached)
            
            logger.debug(f"❌ Config cache MISS: {personality_name}")
            return None
            
        except Exception as e:
            logger.warning(f"PersonalityCache config get error: {e}")
            return None
    
    async def set_personality_config(self, personality_name: str, config: Dict[str, Any]):
        """
        Cache full personality configuration.
        
        Args:
            personality_name: Name of personality
            config: Full personality configuration dict
        """
        if not self._enabled:
            return
            
        try:
            client = await self._get_client()
            if not client:
                return
                
            key = f"personality:global:{personality_name}:config"
            # Don't store None values in JSON
            clean_config = {k: v for k, v in config.items() if v is not None}
            await client.setex(key, self.ttl, json.dumps(clean_config, default=str))
            logger.debug(f"✅ Config cached: {personality_name}")
            
        except Exception as e:
            logger.warning(f"PersonalityCache config set error: {e}")
    
    async def invalidate_personality(self, personality_name: str):
        """
        Clear cached personality data (when updated).
        
        Args:
            personality_name: Name of personality to invalidate
        """
        if not self._enabled:
            return
            
        try:
            client = await self._get_client()
            if not client:
                return
                
            keys = [
                f"personality:global:{personality_name}:id",
                f"personality:global:{personality_name}:config"
            ]
            deleted = await client.delete(*keys)
            logger.info(f"🗑️ Invalidated cache for {personality_name}: {deleted} keys deleted")
            
        except Exception as e:
            logger.warning(f"PersonalityCache invalidation error: {e}")
    
    async def warm_cache(self, personalities: Dict[str, Dict[str, Any]]):
        """
        Pre-populate cache with personality data (warm start).
        
        Args:
            personalities: Dict of {personality_name: {id: ..., config: ...}}
        """
        if not self._enabled:
            return
            
        try:
            client = await self._get_client()
            if not client:
                return
                
            count = 0
            for name, data in personalities.items():
                if 'id' in data:
                    await self.set_personality_id(name, str(data['id']))
                    count += 1
                if 'config' in data:
                    await self.set_personality_config(name, data['config'])
            
            logger.info(f"🔥 Warmed cache with {count} personalities")
            
        except Exception as e:
            logger.warning(f"PersonalityCache warm error: {e}")
    
    async def close(self):
        """Close Redis connection."""
        if self._client:
            try:
                await self._client.close()
                logger.info("PersonalityCache: Redis connection closed")
            except Exception as e:
                logger.warning(f"PersonalityCache close error: {e}")

