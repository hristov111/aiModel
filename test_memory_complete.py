#!/usr/bin/env python3
"""Complete test for memory storage and retrieval with enough message turns."""

import asyncio
import httpx
import time
import json

BASE_URL = "http://localhost:8000"


def extract_response(sse_text):
    """Extract text from SSE response."""
    response_text = ""
    for line in sse_text.split('\n'):
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                if data.get('type') == 'chunk':
                    response_text += data.get('chunk', '')
            except:
                pass
    return response_text


async def chat(client, user_id, personality_name, message):
    """Send a chat message."""
    response = await client.post(
        f"{BASE_URL}/chat",
        headers={"X-User-Id": user_id},
        json={"message": message, "personality_name": personality_name}
    )
    return extract_response(response.text)


async def test_memory():
    """Test memory with enough turns for extraction."""
    print("🧪 Complete Memory Test (with 3+ message turns)\n")
    print("=" * 70)
    
    user_id = f"memtest_{int(time.time())}"
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Turn 1
        print("\n[Turn 1] User: 'Hi, my name is Alex'")
        resp1 = await chat(client, user_id, "elara", "Hi, my name is Alex")
        print(f"Elara: {resp1[:80]}...")
        
        # Turn 2
        print("\n[Turn 2] User: 'I work at SpaceX as an engineer'")
        resp2 = await chat(client, user_id, "elara", "I work at SpaceX as an engineer")
        print(f"Elara: {resp2[:80]}...")
        
        # Turn 3 - This triggers memory extraction!
        print("\n[Turn 3] User: 'My favorite color is purple'")
        resp3 = await chat(client, user_id, "elara", "My favorite color is purple")
        print(f"Elara: {resp3[:80]}...")
        
        # Wait for background memory extraction
        print("\n⏳ Waiting 12 seconds for background memory extraction...")
        await asyncio.sleep(12)
        
        # Turn 4 - Test recall
        print("\n[Turn 4] User: 'What's my name?'")
        resp4 = await chat(client, user_id, "elara", "What's my name?")
        print(f"Elara: {resp4[:200]}...")
        
        if 'alex' in resp4.lower():
            print("✅ Elara remembered the name!")
        else:
            print("❌ Elara didn't remember the name")
        
        # Turn 5 - Test recall
        print("\n[Turn 5] User: 'Where do I work?'")
        resp5 = await chat(client, user_id, "elara", "Where do I work?")
        print(f"Elara: {resp5[:200]}...")
        
        if 'spacex' in resp5.lower():
            print("✅ Elara remembered the workplace!")
        else:
            print("❌ Elara didn't remember the workplace")
        
        # Turn 6 - Test recall
        print("\n[Turn 6] User: 'What's my favorite color?'")
        resp6 = await chat(client, user_id, "elara", "What's my favorite color?")
        print(f"Elara: {resp6[:200]}...")
        
        if 'purple' in resp6.lower():
            print("✅ Elara remembered the favorite color!")
        else:
            print("❌ Elara didn't remember the favorite color")
        
        # Test personality isolation
        print("\n\n" + "=" * 70)
        print("Testing Personality Isolation")
        print("=" * 70)
        
        print("\n[Seraphina] Asking: 'What's my name?'")
        resp_s = await chat(client, user_id, "seraphina", "What's my name?")
        print(f"Seraphina: {resp_s[:200]}...")
        
        if 'alex' not in resp_s.lower() and ("don't" in resp_s.lower() or "not sure" in resp_s.lower()):
            print("✅ Seraphina correctly doesn't know (memory isolated!)")
        elif 'alex' in resp_s.lower():
            print("❌ Seraphina knows Alex's name (memory NOT isolated!)")
        else:
            print("⚠️  Unclear if Seraphina has the memory")
        
        print("\n" + "=" * 70)
        print("✅ Test Complete!")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_memory())

