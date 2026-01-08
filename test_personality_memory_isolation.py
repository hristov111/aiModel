"""Test script for personality-specific memory isolation.

This script tests that memories are properly isolated per personality archetype.
Each personality (Elara, Seraphina) should only see its own memories.
"""

import asyncio
import httpx
import json
from uuid import uuid4

BASE_URL = "http://localhost:8000"
USER_ID = "test_user_multi_personality"


async def test_personality_memory_isolation():
    """Test that each personality has isolated memories."""
    
    print("=" * 80)
    print("TESTING: Per-Personality Memory Isolation")
    print("=" * 80)
    
    async with httpx.AsyncClient() as client:
        
        # Step 1: Create two different personalities
        print("\n[STEP 1] Creating two personalities: Elara (wise_mentor) and Seraphina (supportive_friend)")
        
        # Create Elara
        elara_response = await client.post(
            f"{BASE_URL}/personality",
            headers={"X-User-Id": USER_ID},
            json={
                "personality_name": "elara",
                "archetype": "wise_mentor"
            }
        )
        
        if elara_response.status_code == 201:
            print("✓ Created Elara (wise_mentor)")
        elif elara_response.status_code == 400 and "already exists" in elara_response.text:
            print("✓ Elara already exists")
        else:
            print(f"✗ Failed to create Elara: {elara_response.status_code} - {elara_response.text}")
        
        # Create Seraphina
        seraphina_response = await client.post(
            f"{BASE_URL}/personality",
            headers={"X-User-Id": USER_ID},
            json={
                "personality_name": "seraphina",
                "archetype": "supportive_friend"
            }
        )
        
        if seraphina_response.status_code == 201:
            print("✓ Created Seraphina (supportive_friend)")
        elif seraphina_response.status_code == 400 and "already exists" in seraphina_response.text:
            print("✓ Seraphina already exists")
        else:
            print(f"✗ Failed to create Seraphina: {seraphina_response.status_code} - {seraphina_response.text}")
        
        # Step 2: Chat with Elara and share work information
        print("\n[STEP 2] Chatting with Elara - sharing work information")
        
        elara_conv_id = str(uuid4())
        
        # Tell Elara about work
        async with client.stream(
            "POST",
            f"{BASE_URL}/chat",
            headers={"X-User-Id": USER_ID},
            json={
                "message": "I work at Google as a software engineer.",
                "conversation_id": elara_conv_id,
                "personality_name": "elara"
            },
            timeout=30.0
        ) as response:
            print(f"Response status: {response.status_code}")
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("type") == "chunk":
                        print(data.get("chunk"), end="", flush=True)
            print()  # New line after response
        
        # Give time for memory extraction
        await asyncio.sleep(2)
        
        # Ask Elara to recall
        async with client.stream(
            "POST",
            f"{BASE_URL}/chat",
            headers={"X-User-Id": USER_ID},
            json={
                "message": "Where do I work?",
                "conversation_id": elara_conv_id,
                "personality_name": "elara"
            },
            timeout=30.0
        ) as response:
            print("\n✓ Asking Elara: Where do I work?")
            print("Elara's response: ", end="")
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("type") == "chunk":
                        print(data.get("chunk"), end="", flush=True)
            print()
        
        # Step 3: Chat with Seraphina and share personal information
        print("\n[STEP 3] Chatting with Seraphina - sharing personal information")
        
        seraphina_conv_id = str(uuid4())
        
        # Tell Seraphina about hobby
        async with client.stream(
            "POST",
            f"{BASE_URL}/chat",
            headers={"X-User-Id": USER_ID},
            json={
                "message": "I love hiking in the mountains on weekends.",
                "conversation_id": seraphina_conv_id,
                "personality_name": "seraphina"
            },
            timeout=30.0
        ) as response:
            print(f"Response status: {response.status_code}")
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("type") == "chunk":
                        print(data.get("chunk"), end="", flush=True)
            print()
        
        # Give time for memory extraction
        await asyncio.sleep(2)
        
        # Ask Seraphina to recall
        async with client.stream(
            "POST",
            f"{BASE_URL}/chat",
            headers={"X-User-Id": USER_ID},
            json={
                "message": "What do I love doing on weekends?",
                "conversation_id": seraphina_conv_id,
                "personality_name": "seraphina"
            },
            timeout=30.0
        ) as response:
            print("\n✓ Asking Seraphina: What do I love doing on weekends?")
            print("Seraphina's response: ", end="")
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("type") == "chunk":
                        print(data.get("chunk"), end="", flush=True)
            print()
        
        # Step 4: TEST ISOLATION - Ask Seraphina about work (she shouldn't know)
        print("\n[STEP 4] TESTING ISOLATION - Asking Seraphina about work info")
        print("Expected: Seraphina should NOT know about work (only Elara knows)")
        
        async with client.stream(
            "POST",
            f"{BASE_URL}/chat",
            headers={"X-User-Id": USER_ID},
            json={
                "message": "Where do I work?",
                "conversation_id": seraphina_conv_id,
                "personality_name": "seraphina"
            },
            timeout=30.0
        ) as response:
            print("Seraphina's response: ", end="")
            seraphina_knows_work = False
            response_text = ""
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("type") == "chunk":
                        chunk = data.get("chunk", "")
                        response_text += chunk
                        print(chunk, end="", flush=True)
            print()
            
            # Check if Seraphina knows about Google
            if "google" in response_text.lower() or "software engineer" in response_text.lower():
                print("✗ ISOLATION FAILED: Seraphina knows about work info (should only be in Elara's memory)")
            else:
                print("✓ ISOLATION SUCCESS: Seraphina doesn't know about work info")
        
        # Step 5: TEST ISOLATION - Ask Elara about hobbies (she shouldn't know)
        print("\n[STEP 5] TESTING ISOLATION - Asking Elara about hobby info")
        print("Expected: Elara should NOT know about hiking (only Seraphina knows)")
        
        async with client.stream(
            "POST",
            f"{BASE_URL}/chat",
            headers={"X-User-Id": USER_ID},
            json={
                "message": "What do I love doing on weekends?",
                "conversation_id": elara_conv_id,
                "personality_name": "elara"
            },
            timeout=30.0
        ) as response:
            print("Elara's response: ", end="")
            elara_knows_hobby = False
            response_text = ""
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("type") == "chunk":
                        chunk = data.get("chunk", "")
                        response_text += chunk
                        print(chunk, end="", flush=True)
            print()
            
            # Check if Elara knows about hiking
            if "hiking" in response_text.lower() or "mountains" in response_text.lower():
                print("✗ ISOLATION FAILED: Elara knows about hobby info (should only be in Seraphina's memory)")
            else:
                print("✓ ISOLATION SUCCESS: Elara doesn't know about hobby info")
        
        # Step 6: List all personalities
        print("\n[STEP 6] Listing all personalities for user")
        
        list_response = await client.get(
            f"{BASE_URL}/personality",
            headers={"X-User-Id": USER_ID}
        )
        
        if list_response.status_code == 200:
            personalities = list_response.json()
            print(f"✓ Found {personalities['total']} personalities:")
            for p in personalities['personalities']:
                print(f"  - {p['personality_name']} ({p['archetype']})")
        else:
            print(f"✗ Failed to list personalities: {list_response.status_code}")
        
        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    print("\n🧪 Starting Personality Memory Isolation Tests")
    print("Make sure the AI Service is running on http://localhost:8000")
    print()
    
    asyncio.run(test_personality_memory_isolation())

