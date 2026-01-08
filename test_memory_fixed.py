#!/usr/bin/env python3
"""Fixed memory test - reuses conversation_id across turns."""

import asyncio
import httpx
import time
import json

BASE_URL = "http://localhost:8000"


def extract_response_and_conv_id(sse_text):
    """Extract text and conversation_id from SSE response."""
    response_text = ""
    conv_id = None
    for line in sse_text.split('\n'):
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                if data.get('type') == 'chunk':
                    response_text += data.get('chunk', '')
                if not conv_id and 'conversation_id' in data:
                    conv_id = data['conversation_id']
            except:
                pass
    return response_text, conv_id


async def chat(client, user_id, personality_name, message, conversation_id=None):
    """Send a chat message, optionally continuing a conversation."""
    payload = {"message": message, "personality_name": personality_name}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    response = await client.post(
        f"{BASE_URL}/chat",
        headers={"X-User-Id": user_id},
        json=payload
    )
    return extract_response_and_conv_id(response.text)


async def test_memory():
    """Test memory with proper conversation continuity."""
    print("🧪 Fixed Memory Test (with conversation continuity)\n")
    print("=" * 70)
    
    user_id = f"memtest_{int(time.time())}"
    conv_id = None
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Turn 1
        print("\n[Turn 1] User: 'Hi, my name is Alex'")
        resp1, conv_id = await chat(client, user_id, "elara", "Hi, my name is Alex", conv_id)
        print(f"Elara: {resp1[:80]}...")
        print(f"   Conversation ID: {conv_id}")
        
        # Turn 2 - Continue same conversation!
        print("\n[Turn 2] User: 'I work at SpaceX as an engineer'")
        resp2, conv_id = await chat(client, user_id, "elara", "I work at SpaceX as an engineer", conv_id)
        print(f"Elara: {resp2[:80]}...")
        
        # Turn 3 - This should trigger memory extraction!
        print("\n[Turn 3] User: 'My favorite color is purple'")
        resp3, conv_id = await chat(client, user_id, "elara", "My favorite color is purple", conv_id)
        print(f"Elara: {resp3[:80]}...")
        
        # Wait for background memory extraction
        print("\n⏳ Waiting 15 seconds for background memory extraction...")
        await asyncio.sleep(15)
        
        # Turn 4 - Test recall
        print("\n[Turn 4] User: 'What's my name?'")
        resp4, conv_id = await chat(client, user_id, "elara", "What's my name?", conv_id)
        print(f"Elara: {resp4}")
        
        if 'alex' in resp4.lower():
            print("✅ Elara remembered the name!")
        else:
            print("❌ Elara didn't remember the name")
        
        # Turn 5 - Test recall
        print("\n[Turn 5] User: 'Where do I work?'")
        resp5, conv_id = await chat(client, user_id, "elara", "Where do I work?", conv_id)
        print(f"Elara: {resp5}")
        
        if 'spacex' in resp5.lower():
            print("✅ Elara remembered the workplace!")
        else:
            print("❌ Elara didn't remember the workplace")
        
        # Turn 6 - Test recall
        print("\n[Turn 6] User: 'What's my favorite color?'")
        resp6, conv_id = await chat(client, user_id, "elara", "What's my favorite color?", conv_id)
        print(f"Elara: {resp6}")
        
        if 'purple' in resp6.lower():
            print("✅ Elara remembered the favorite color!")
        else:
            print("❌ Elara didn't remember the favorite color")
        
        # Test personality isolation - NEW conversation with Seraphina
        print("\n\n" + "=" * 70)
        print("Testing Personality Isolation")
        print("=" * 70)
        
        print("\n[Seraphina] Asking: 'What's my name?' (new conversation)")
        resp_s, _ = await chat(client, user_id, "seraphina", "What's my name?")
        print(f"Seraphina: {resp_s}")
        
        if 'alex' not in resp_s.lower():
            print("✅ Seraphina correctly doesn't know (memory isolated!)")
        else:
            print("❌ Seraphina knows Alex's name (memory NOT isolated!)")
        
        print("\n" + "=" * 70)
        print("✅ Test Complete!")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_memory())

