# Redis Caching Guide for AI Companion

## Overview

Redis is a high-performance in-memory data store that can dramatically improve your app's speed by caching frequently accessed data.

## Current Implementation

### Already Available (But Disabled)
- ✅ **Redis container** running on port 6379
- ✅ **RedisConversationBuffer** implemented in `app/services/redis_memory.py`
- ❌ **Currently disabled** in configuration

## Benefits of Enabling Redis

### 1. **Conversation Buffers (Already Implemented)**
```
Without Redis:  Stored in Python memory (lost on restart)
With Redis:     Distributed, persistent across restarts
```

### 2. **Performance Improvements**
- **5-10x faster** reads for cached data
- **Reduced database load** (fewer queries)
- **Better scalability** (multiple server instances)

## How to Enable Redis

### Step 1: Update Environment Variables

Edit `.env`:
```bash
# Enable Redis
REDIS_ENABLED=true
REDIS_URL=redis://:THt1mq19MBGl99cNxIfSx@localhost:6379/0
```

### Step 2: Update Main Application

The app already supports Redis! Just set the environment variable and restart.

## What to Cache in Redis

### 🎯 High-Impact Caching Opportunities

#### 1. **Global Personalities** (HIGH IMPACT ⚡)
**Why:** The 8 global personalities are read on EVERY request but never change.

**Implementation:**
```python
# app/services/personality_cache.py
import redis.asyncio as redis
import json
from typing import Optional, Dict

class PersonalityCache:
    """Cache for global personality configurations."""
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.ttl = 3600  # 1 hour (or longer since they rarely change)
    
    async def get_personality(self, personality_name: str) -> Optional[Dict]:
        """Get personality from cache."""
        key = f"personality:global:{personality_name}"
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    async def set_personality(self, personality_name: str, data: Dict):
        """Cache personality data."""
        key = f"personality:global:{personality_name}"
        await self.redis.setex(
            key,
            self.ttl,
            json.dumps(data)
        )
    
    async def invalidate_personality(self, personality_name: str):
        """Clear cached personality (when updated)."""
        key = f"personality:global:{personality_name}"
        await self.redis.delete(key)

# Usage in PersonalityService:
async def get_personality_id(self, user_id: UUID, personality_name: str) -> Optional[UUID]:
    # Try cache first
    cached = await self.cache.get_personality(personality_name)
    if cached:
        return UUID(cached['id'])
    
    # Not in cache, query database
    personality_id = await self._query_db_for_personality(personality_name)
    
    # Store in cache for next time
    if personality_id:
        await self.cache.set_personality(personality_name, {'id': str(personality_id)})
    
    return personality_id
```

**Performance gain:** 
- ❌ **Without cache:** ~5-10ms database query per request
- ✅ **With cache:** <1ms Redis lookup
- 🚀 **5-10x faster** personality resolution

---

#### 2. **User Preferences** (MEDIUM IMPACT ⚡)
**Why:** User preferences are read on every chat request.

```python
# Cache user preferences for 5 minutes
class PreferenceCache:
    async def get_preferences(self, user_id: str) -> Optional[Dict]:
        key = f"prefs:{user_id}"
        cached = await self.redis.get(key)
        return json.loads(cached) if cached else None
    
    async def set_preferences(self, user_id: str, prefs: Dict):
        key = f"prefs:{user_id}"
        await self.redis.setex(key, 300, json.dumps(prefs))  # 5 min TTL
```

---

#### 3. **Conversation Context** (Already Implemented! ✅)
**Why:** Short-term messages need fast read/write.

The `RedisConversationBuffer` already handles this:
```python
# Stores last N messages per conversation
# TTL: 1 hour (auto-expires old conversations)
```

---

#### 4. **Rate Limiting** (SECURITY BENEFIT 🔒)
**Why:** Prevent abuse, track API usage per user.

```python
class RateLimiter:
    async def check_rate_limit(self, user_id: str, limit: int = 30) -> bool:
        """Check if user exceeded rate limit."""
        key = f"ratelimit:{user_id}"
        count = await self.redis.incr(key)
        
        if count == 1:
            # First request in this window
            await self.redis.expire(key, 60)  # 1-minute window
        
        return count <= limit
```

---

#### 5. **Session State** (For Multi-Instance Deployments)
**Why:** Track active sessions across multiple server instances.

```python
class SessionCache:
    async def set_session(self, user_id: str, session_data: Dict):
        key = f"session:{user_id}"
        await self.redis.setex(key, 3600, json.dumps(session_data))
    
    async def get_session(self, user_id: str) -> Optional[Dict]:
        key = f"session:{user_id}"
        cached = await self.redis.get(key)
        return json.loads(cached) if cached else None
```

---

#### 6. **Memory Retrieval Cache** (OPTIONAL)
**Why:** If same query asked multiple times, reuse results.

```python
# Cache memory search results for 5 minutes
key = f"memory_search:{conversation_id}:{hash(query)}"
cached_memories = await redis.get(key)
if cached_memories:
    return json.loads(cached_memories)

# Query database and cache
memories = await self.vector_store.search_similar(...)
await redis.setex(key, 300, json.dumps(memories))
```

---

## Quick Win Implementation

### Option 1: Enable Existing Redis (Conversation Buffers)

**1. Update `.env`:**
```bash
REDIS_ENABLED=true
REDIS_URL=redis://:THt1mq19MBGl99cNxIfSx@localhost:6379/0
```

**2. Update `app/main.py`:**
```python
from app.services.redis_memory import RedisConversationBuffer
from app.core.config import settings

# Initialize conversation buffer
if settings.redis_enabled and settings.redis_url:
    conversation_buffer = RedisConversationBuffer(
        redis_url=settings.redis_url,
        max_size=settings.short_term_memory_size
    )
else:
    conversation_buffer = ConversationBuffer(
        max_size=settings.short_term_memory_size
    )
```

**3. Restart service:**
```bash
docker-compose restart ai_companion_service_dev
```

---

### Option 2: Add Personality Caching (HIGH IMPACT)

This caches the 8 global personalities for instant lookups.

**Create `app/services/personality_cache.py`:**
```python
"""Redis cache for personality configurations."""

import redis.asyncio as redis
import json
import logging
from typing import Optional, Dict, Any
from uuid import UUID

logger = logging.getLogger(__name__)


class PersonalityCache:
    """Cache for global personality configurations."""
    
    def __init__(self, redis_url: str):
        """
        Initialize personality cache.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
        self.ttl = 86400  # 24 hours (personalities rarely change)
    
    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=2
            )
        return self._client
    
    async def get_personality_id(self, personality_name: str) -> Optional[str]:
        """
        Get personality ID from cache.
        
        Args:
            personality_name: Name of personality (e.g., 'elara')
            
        Returns:
            Personality ID (UUID as string) or None
        """
        try:
            client = await self._get_client()
            key = f"personality:global:{personality_name}:id"
            cached_id = await client.get(key)
            
            if cached_id:
                logger.debug(f"✅ Cache HIT: {personality_name} -> {cached_id}")
                return cached_id
            
            logger.debug(f"❌ Cache MISS: {personality_name}")
            return None
            
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
            return None
    
    async def set_personality_id(self, personality_name: str, personality_id: str):
        """
        Cache personality ID.
        
        Args:
            personality_name: Name of personality
            personality_id: UUID of personality (as string)
        """
        try:
            client = await self._get_client()
            key = f"personality:global:{personality_name}:id"
            await client.setex(key, self.ttl, personality_id)
            logger.debug(f"✅ Cached: {personality_name} -> {personality_id}")
            
        except Exception as e:
            logger.warning(f"Redis cache set error: {e}")
    
    async def get_personality_config(self, personality_name: str) -> Optional[Dict[str, Any]]:
        """
        Get full personality configuration from cache.
        
        Args:
            personality_name: Name of personality
            
        Returns:
            Personality config dict or None
        """
        try:
            client = await self._get_client()
            key = f"personality:global:{personality_name}:config"
            cached = await client.get(key)
            
            if cached:
                logger.debug(f"✅ Config cache HIT: {personality_name}")
                return json.loads(cached)
            
            return None
            
        except Exception as e:
            logger.warning(f"Redis config cache error: {e}")
            return None
    
    async def set_personality_config(self, personality_name: str, config: Dict[str, Any]):
        """
        Cache full personality configuration.
        
        Args:
            personality_name: Name of personality
            config: Full personality configuration dict
        """
        try:
            client = await self._get_client()
            key = f"personality:global:{personality_name}:config"
            await client.setex(key, self.ttl, json.dumps(config))
            logger.debug(f"✅ Config cached: {personality_name}")
            
        except Exception as e:
            logger.warning(f"Redis config cache set error: {e}")
    
    async def invalidate_personality(self, personality_name: str):
        """
        Clear cached personality data (when updated).
        
        Args:
            personality_name: Name of personality to invalidate
        """
        try:
            client = await self._get_client()
            keys = [
                f"personality:global:{personality_name}:id",
                f"personality:global:{personality_name}:config"
            ]
            await client.delete(*keys)
            logger.info(f"🗑️ Invalidated cache: {personality_name}")
            
        except Exception as e:
            logger.warning(f"Redis cache invalidation error: {e}")
    
    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
```

**Update `app/services/personality_service.py`:**
```python
from app.services.personality_cache import PersonalityCache

class PersonalityService:
    def __init__(self, db_session: AsyncSession, llm_client=None, cache: PersonalityCache = None):
        self.db = db_session
        self.llm_client = llm_client
        self.cache = cache  # Add cache support
    
    async def get_personality_id(self, user_id: UUID, personality_name: str) -> Optional[UUID]:
        # Try cache first (for global personalities)
        if self.cache:
            cached_id = await self.cache.get_personality_id(personality_name)
            if cached_id:
                return UUID(cached_id)
        
        # Original database query logic...
        personality_id = await self._query_database(personality_name)
        
        # Cache for next time
        if personality_id and self.cache:
            await self.cache.set_personality_id(personality_name, str(personality_id))
        
        return personality_id
```

---

## Expected Performance Gains

| Operation | Without Redis | With Redis | Improvement |
|-----------|--------------|------------|-------------|
| Get personality ID | ~5-10ms | <1ms | **5-10x faster** |
| Get user preferences | ~3-5ms | <1ms | **3-5x faster** |
| Conversation messages | ~2-5ms | <0.5ms | **4-10x faster** |
| Rate limit check | N/A | <0.1ms | **New feature** |

### Overall Chat Response Time:
- **Current:** ~3-4 seconds to first chunk
- **With Redis:** **~2-3 seconds** (20-30% faster)

---

## Monitoring Redis

### Check Cache Hit Rate
```bash
redis-cli -a THt1mq19MBGl99cNxIfSx INFO stats | grep hit
```

### View Cached Keys
```bash
redis-cli -a THt1mq19MBGl99cNxIfSx KEYS "personality:*"
```

### Clear Cache (if needed)
```bash
redis-cli -a THt1mq19MBGl99cNxIfSx FLUSHDB
```

---

## Recommendations

### For Instant Messaging Performance:

1. ✅ **Enable Redis for conversations** (already implemented)
   - Prevents memory loss on restart
   - Enables horizontal scaling

2. ⚡ **Add personality caching** (HIGH IMPACT)
   - 8 global personalities read on EVERY request
   - Perfect cache candidate (rarely changes)
   - **5-10x faster lookups**

3. 🔒 **Add rate limiting** (SECURITY)
   - Prevent abuse
   - Track usage per user

4. 💾 **Cache user preferences** (NICE TO HAVE)
   - Faster preference lookups
   - Reduced database load

### Priority Order:
1. Enable existing Redis conversation buffer
2. Add personality caching (biggest win for your use case)
3. Add rate limiting
4. Add preference caching

---

## Next Steps

1. **Quick Win:** Enable Redis conversation buffer
   ```bash
   # Update .env
   REDIS_ENABLED=true
   REDIS_URL=redis://:THt1mq19MBGl99cNxIfSx@localhost:6379/0
   
   # Restart service
   docker-compose restart ai_companion_service_dev
   ```

2. **High Impact:** Implement personality caching (see code above)

3. **Monitor:** Check cache hit rates and performance improvements

Would you like me to implement any of these caching strategies?

