#!/usr/bin/env python3
"""Test that memories are being stored and retrieved with personality_id."""

import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000"


async def test_memory_with_personality():
    """Test memory storage and retrieval with personality."""
    print("🧪 Testing Memory Storage with Personality\n")
    print("=" * 60)
    
    user_id = f"memory_test_{int(time.time())}"
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Step 1: Tell Elara something memorable
        print("\n[Step 1] Telling Elara: 'My favorite color is purple'...")
        response1 = await client.post(
            f"{BASE_URL}/chat",
            headers={"X-User-Id": user_id},
            json={
                "message": "Hi! My favorite color is purple and I love painting.",
                "personality_name": "elara"  # ← THIS IS CRITICAL!
            }
        )
        print(f"✓ Elara responded (Status: {response1.status_code})")
        
        # Wait for memory extraction
        print("   Waiting 10s for memory extraction...")
        await asyncio.sleep(10)
        
        # Step 2: Ask Elara if she remembers
        print("\n[Step 2] Asking Elara: 'What's my favorite color?'...")
        response2 = await client.post(
            f"{BASE_URL}/chat",
            headers={"X-User-Id": user_id},
            json={
                "message": "What's my favorite color?",
                "personality_name": "elara"  # ← Must use same personality!
            }
        )
        
        # Extract response text
        response_text = ""
        for line in response2.text.split('\n'):
            if line.startswith('data: '):
                try:
                    import json
                    data = json.loads(line[6:])
                    if data.get('type') == 'chunk':
                        response_text += data.get('chunk', '')
                except:
                    pass
        
        print(f"✓ Elara responded: \"{response_text[:150]}...\"")
        
        # Check if she remembers
        if 'purple' in response_text.lower():
            print("\n✅ SUCCESS! Elara remembered the favorite color!")
        else:
            print("\n❌ FAIL: Elara didn't remember the favorite color.")
            print(f"   Response didn't mention 'purple'")
        
        # Step 3: Verify Seraphina DOESN'T know (different personality)
        print("\n[Step 3] Asking Seraphina (different personality): 'What's my favorite color?'...")
        response3 = await client.post(
            f"{BASE_URL}/chat",
            headers={"X-User-Id": user_id},
            json={
                "message": "What's my favorite color?",
                "personality_name": "seraphina"  # ← Different personality!
            }
        )
        
        response_text3 = ""
        for line in response3.text.split('\n'):
            if line.startswith('data: '):
                try:
                    import json
                    data = json.loads(line[6:])
                    if data.get('type') == 'chunk':
                        response_text3 += data.get('chunk', '')
                except:
                    pass
        
        print(f"✓ Seraphina responded: \"{response_text3[:150]}...\"")
        
        if 'purple' not in response_text3.lower() and ("don't" in response_text3.lower() or "not sure" in response_text3.lower()):
            print("\n✅ SUCCESS! Seraphina correctly doesn't know (memory isolation working!)")
        else:
            print("\n⚠️ WARNING: Seraphina might have access to Elara's memories")
    
    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(test_memory_with_personality())

