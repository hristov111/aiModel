#!/usr/bin/env python3
"""Test showing the difference between requests with and without personality_name."""

import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000"


async def test_comparison():
    """Compare requests with and without personality_name."""
    print("🧪 Comparison Test: With vs Without personality_name\n")
    print("=" * 70)
    
    user1 = f"test_without_{int(time.time())}"
    user2 = f"test_with_{int(time.time())}"
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Test 1: WITHOUT personality_name (your current situation)
        print("\n❌ Test 1: WITHOUT personality_name")
        print("-" * 70)
        
        conv_id1 = None
        for i in range(3):
            print(f"   Message {i+1}...")
            payload = {"message": f"Test message {i+1}: My name is TestUser{i+1}"}
            if conv_id1:
                payload["conversation_id"] = conv_id1
            
            resp = await client.post(
                f"{BASE_URL}/chat",
                headers={"X-User-Id": user1},
                json=payload
            )
            
            # Extract conversation_id
            for line in resp.text.split('\n'):
                if '"conversation_id"' in line:
                    import json
                    try:
                        data = json.loads(line.split('data: ')[1])
                        conv_id1 = data.get('conversation_id')
                        break
                    except:
                        pass
        
        print(f"   Conversation ID: {conv_id1}")
        
        # Wait for memory extraction
        await asyncio.sleep(12)
        
        # Check database
        print("\n   Checking database...")
        import subprocess
        result1 = subprocess.run([
            "docker", "exec", "ai_companion_db_dev", "psql", "-U", "postgres", 
            "-d", "ai_companion", "-t", "-c",
            f"SELECT COUNT(*), personality_id FROM memories WHERE conversation_id = '{conv_id1}' GROUP BY personality_id;"
        ], capture_output=True, text=True)
        
        if result1.stdout.strip():
            print(f"   Memories stored: {result1.stdout.strip()}")
            if "| " in result1.stdout and result1.stdout.split("|")[1].strip() == "":
                print("   ⚠️  personality_id is NULL - memories won't be retrieved!")
        else:
            print("   ⚠️  No memories stored")
        
        # Test 2: WITH personality_name (correct way)
        print("\n\n✅ Test 2: WITH personality_name")
        print("-" * 70)
        
        conv_id2 = None
        for i in range(3):
            print(f"   Message {i+1}...")
            payload = {
                "message": f"Test message {i+1}: I love coding{i+1}",
                "personality_name": "elara"  # ← This is the key!
            }
            if conv_id2:
                payload["conversation_id"] = conv_id2
            
            resp = await client.post(
                f"{BASE_URL}/chat",
                headers={"X-User-Id": user2},
                json=payload
            )
            
            # Extract conversation_id
            for line in resp.text.split('\n'):
                if '"conversation_id"' in line:
                    import json
                    try:
                        data = json.loads(line.split('data: ')[1])
                        conv_id2 = data.get('conversation_id')
                        break
                    except:
                        pass
        
        print(f"   Conversation ID: {conv_id2}")
        
        # Wait for memory extraction
        await asyncio.sleep(12)
        
        # Check database
        print("\n   Checking database...")
        result2 = subprocess.run([
            "docker", "exec", "ai_companion_db_dev", "psql", "-U", "postgres", 
            "-d", "ai_companion", "-t", "-c",
            f"SELECT COUNT(*), pp.personality_name FROM memories m LEFT JOIN personality_profiles pp ON m.personality_id = pp.id WHERE m.conversation_id = '{conv_id2}' GROUP BY pp.personality_name;"
        ], capture_output=True, text=True)
        
        if result2.stdout.strip():
            print(f"   Memories stored: {result2.stdout.strip()}")
            if "elara" in result2.stdout.lower():
                print("   ✅ personality_id is SET - memories WILL be retrieved!")
        else:
            print("   ⚠️  No memories stored")
        
        print("\n" + "=" * 70)
        print("📊 Summary:")
        print("   WITHOUT personality_name → personality_id = NULL → ❌ Can't retrieve")
        print("   WITH personality_name → personality_id = UUID → ✅ Can retrieve")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_comparison())

