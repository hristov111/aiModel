#!/usr/bin/env python3
"""Test Redis caching for personalities."""

import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000"


async def test_cache():
    """Test personality caching."""
    print("🧪 Testing Redis Personality Cache\n")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Test 1: First request (should populate cache)
        print("\n[Test 1] First request - populating cache...")
        start = time.time()
        
        response1 = await client.post(
            f"{BASE_URL}/chat",
            headers={"X-User-Id": f"cache_test_{int(time.time())}"},
            json={"message": "Hello", "personality_name": "elara"}
        )
        
        elapsed1 = time.time() - start
        print(f"✓ First request completed in {elapsed1:.3f}s")
        print(f"  Status: {response1.status_code}")
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Test 2: Second request (should use cache)
        print("\n[Test 2] Second request - should use cache...")
        start = time.time()
        
        response2 = await client.post(
            f"{BASE_URL}/chat",
            headers={"X-User-Id": f"cache_test_{int(time.time())}"},
            json={"message": "Hi", "personality_name": "elara"}
        )
        
        elapsed2 = time.time() - start
        print(f"✓ Second request completed in {elapsed2:.3f}s")
        print(f"  Status: {response2.status_code}")
        
        # Test 3: Different personality
        print("\n[Test 3] Different personality (seraphina)...")
        start = time.time()
        
        response3 = await client.post(
            f"{BASE_URL}/chat",
            headers={"X-User-Id": f"cache_test_{int(time.time())}"},
            json={"message": "Hey", "personality_name": "seraphina"}
        )
        
        elapsed3 = time.time() - start
        print(f"✓ Third request completed in {elapsed3:.3f}s")
        print(f"  Status: {response3.status_code}")
        
        # Test 4: Same personality again (should be cached now)
        print("\n[Test 4] Seraphina again (should be cached)...")
        start = time.time()
        
        response4 = await client.post(
            f"{BASE_URL}/chat",
            headers={"X-User-Id": f"cache_test_{int(time.time())}"},
            json={"message": "Hello again", "personality_name": "seraphina"}
        )
        
        elapsed4 = time.time() - start
        print(f"✓ Fourth request completed in {elapsed4:.3f}s")
        print(f"  Status: {response4.status_code}")
    
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"  Request 1 (elara, cache miss):  {elapsed1:.3f}s")
    print(f"  Request 2 (elara, cache hit):   {elapsed2:.3f}s")
    print(f"  Request 3 (seraphina, miss):    {elapsed3:.3f}s")
    print(f"  Request 4 (seraphina, hit):     {elapsed4:.3f}s")
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_cache())

