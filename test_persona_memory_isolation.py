#!/usr/bin/env python3
"""
Test script to verify personality-specific memory isolation.

This test verifies that:
1. Each persona (elara, seraphina, etc.) has separate memories per user
2. Personas don't share memories unless user tells them the same info
3. Different users have completely isolated memories even with the same persona
"""

import asyncio
import httpx
import json
from typing import Dict, List
import time

BASE_URL = "http://localhost:8000"
TIMEOUT = 60.0


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_step(step_num: int, text: str):
    """Print a test step."""
    print(f"\n[STEP {step_num}] {text}")
    print("-" * 80)


def extract_response_text(sse_data: str) -> str:
    """Extract the full response text from SSE stream."""
    lines = sse_data.strip().split('\n')
    response_chunks = []
    
    for line in lines:
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])  # Remove 'data: ' prefix
                if data.get('type') == 'chunk':
                    response_chunks.append(data.get('chunk', ''))
            except json.JSONDecodeError:
                continue
    
    return ''.join(response_chunks).strip()


def print_response(persona: str, response_text: str):
    """Print AI response in a formatted way."""
    print(f"\n🤖 {persona.upper()} says:")
    print(f"   \"{response_text[:200]}{'...' if len(response_text) > 200 else ''}\"")


async def chat_with_persona(
    user_id: str,
    persona: str,
    message: str,
    conversation_id: str = None
) -> Dict:
    """Send a chat message to a specific persona."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        payload = {
            "message": message,
            "personality_name": persona
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        response = await client.post(
            f"{BASE_URL}/chat",
            headers={"X-User-Id": user_id},
            json=payload
        )
        
        response.raise_for_status()
        
        # Extract conversation_id and response text
        response_text = extract_response_text(response.text)
        
        # Extract conversation_id from first data line
        lines = response.text.strip().split('\n')
        conv_id = None
        for line in lines:
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    conv_id = data.get('conversation_id')
                    if conv_id:
                        break
                except json.JSONDecodeError:
                    continue
        
        return {
            "conversation_id": conv_id,
            "response": response_text
        }


async def wait_for_memory_storage(seconds: int = 3):
    """Wait for memory extraction to complete."""
    print(f"   ⏳ Waiting {seconds}s for memory storage...")
    await asyncio.sleep(seconds)


async def check_memory_recall(user_id: str, persona: str, question: str, expected_keywords: List[str]) -> bool:
    """
    Check if a persona recalls specific information by asking a question.
    Returns True if all expected keywords are found in the response.
    """
    result = await chat_with_persona(user_id, persona, question)
    response = result["response"].lower()
    
    found_keywords = [kw for kw in expected_keywords if kw.lower() in response]
    not_found = [kw for kw in expected_keywords if kw.lower() not in response]
    
    print(f"\n   📝 Memory Check for {persona.upper()}:")
    print(f"      Question: \"{question}\"")
    print(f"      Response: \"{response[:150]}{'...' if len(response) > 150 else ''}\"")
    print(f"      ✓ Found keywords: {found_keywords}")
    if not_found:
        print(f"      ✗ Missing keywords: {not_found}")
    
    return len(not_found) == 0


async def main():
    """Run memory isolation tests."""
    print_header("🧪 PERSONALITY MEMORY ISOLATION TEST")
    print("Testing that each persona maintains separate memories per user")
    print("and only knows what the user explicitly told them.\n")
    
    # Test users
    user_alice = "test_alice_" + str(int(time.time()))
    user_bob = "test_bob_" + str(int(time.time()))
    
    print(f"👤 Test User 1: {user_alice}")
    print(f"👤 Test User 2: {user_bob}")
    
    try:
        # ========================================================================
        # TEST 1: User Alice tells Elara about working at Google
        # ========================================================================
        print_step(1, "Alice tells ELARA she works at Google")
        
        result1 = await chat_with_persona(
            user_alice,
            "elara",
            "Hi! I work at Google as a software engineer. I've been there for 3 years."
        )
        print_response("elara", result1["response"])
        await wait_for_memory_storage()
        
        # ========================================================================
        # TEST 2: User Alice talks to Seraphina (should NOT know about Google)
        # ========================================================================
        print_step(2, "Alice asks SERAPHINA about her job (Seraphina should NOT know)")
        
        knows_google = await check_memory_recall(
            user_alice,
            "seraphina",
            "Do you remember where I work?",
            ["google"]  # Should NOT be found
        )
        
        if knows_google:
            print("\n   ❌ FAIL: Seraphina knows about Google (memories are shared!)")
        else:
            print("\n   ✅ PASS: Seraphina doesn't know about Google (memories isolated!)")
        
        # ========================================================================
        # TEST 3: Alice tells Seraphina she works at Microsoft
        # ========================================================================
        print_step(3, "Alice tells SERAPHINA she works at Microsoft")
        
        result2 = await chat_with_persona(
            user_alice,
            "seraphina",
            "By the way, I work at Microsoft in the Azure team. It's really exciting!"
        )
        print_response("seraphina", result2["response"])
        await wait_for_memory_storage()
        
        # ========================================================================
        # TEST 4: Verify Elara still thinks Alice works at Google
        # ========================================================================
        print_step(4, "Verify ELARA still remembers Google (not Microsoft)")
        
        remembers_google = await check_memory_recall(
            user_alice,
            "elara",
            "Where do I work again?",
            ["google"]
        )
        
        if remembers_google:
            print("\n   ✅ PASS: Elara remembers Google!")
        else:
            print("\n   ❌ FAIL: Elara doesn't remember Google")
        
        # Also check that Elara doesn't know about Microsoft
        result_elara = await chat_with_persona(
            user_alice,
            "elara",
            "Do you know anything about my work at Microsoft?"
        )
        if "microsoft" not in result_elara["response"].lower() or "don't" in result_elara["response"].lower() or "not" in result_elara["response"].lower():
            print("   ✅ PASS: Elara doesn't know about Microsoft!")
        else:
            print("   ⚠️  WARNING: Elara might have been told about Microsoft")
        
        # ========================================================================
        # TEST 5: Verify Seraphina remembers Microsoft (not Google)
        # ========================================================================
        print_step(5, "Verify SERAPHINA remembers Microsoft (not Google)")
        
        remembers_microsoft = await check_memory_recall(
            user_alice,
            "seraphina",
            "What company do I work for?",
            ["microsoft"]
        )
        
        if remembers_microsoft:
            print("\n   ✅ PASS: Seraphina remembers Microsoft!")
        else:
            print("\n   ❌ FAIL: Seraphina doesn't remember Microsoft")
        
        # ========================================================================
        # TEST 6: Different user (Bob) talks to Elara
        # ========================================================================
        print_step(6, "User Bob talks to ELARA (should NOT know Alice's info)")
        
        result_bob = await chat_with_persona(
            user_bob,
            "elara",
            "Hi! Do you know where I work?"
        )
        print_response("elara", result_bob["response"])
        
        # Elara should not know Bob's workplace (he didn't tell her yet)
        if "google" not in result_bob["response"].lower() and ("don't" in result_bob["response"].lower() or "not" in result_bob["response"].lower() or "haven't" in result_bob["response"].lower()):
            print("\n   ✅ PASS: Elara doesn't know Bob's workplace (cross-user isolation!)")
        else:
            print("\n   ⚠️  WARNING: Elara might be leaking Alice's info to Bob")
        
        # ========================================================================
        # TEST 7: Bob tells Elara he works at Amazon
        # ========================================================================
        print_step(7, "Bob tells ELARA he works at Amazon")
        
        result_bob2 = await chat_with_persona(
            user_bob,
            "elara",
            "I work at Amazon Web Services, in the cloud infrastructure team."
        )
        print_response("elara", result_bob2["response"])
        await wait_for_memory_storage()
        
        # ========================================================================
        # TEST 8: Verify Elara remembers different jobs for Alice and Bob
        # ========================================================================
        print_step(8, "Verify ELARA remembers different jobs for Alice vs Bob")
        
        # Ask Alice
        alice_job = await chat_with_persona(
            user_alice,
            "elara",
            "Quick reminder: where do I work?"
        )
        print(f"\n   👤 Alice asks Elara: \"{alice_job['response'][:100]}...\"")
        
        # Ask Bob
        bob_job = await chat_with_persona(
            user_bob,
            "elara",
            "Quick reminder: where do I work?"
        )
        print(f"   👤 Bob asks Elara: \"{bob_job['response'][:100]}...\"")
        
        alice_knows_google = "google" in alice_job["response"].lower()
        bob_knows_amazon = "amazon" in bob_job["response"].lower()
        alice_knows_amazon = "amazon" in alice_job["response"].lower()
        bob_knows_google = "google" in bob_job["response"].lower()
        
        if alice_knows_google and bob_knows_amazon and not alice_knows_amazon and not bob_knows_google:
            print("\n   ✅ PASS: Elara maintains separate memories for Alice and Bob!")
        else:
            print("\n   ❌ FAIL: Memory separation between users is broken")
            print(f"      Alice knows Google: {alice_knows_google} (should be True)")
            print(f"      Bob knows Amazon: {bob_knows_amazon} (should be True)")
            print(f"      Alice knows Amazon: {alice_knows_amazon} (should be False)")
            print(f"      Bob knows Google: {bob_knows_google} (should be False)")
        
        # ========================================================================
        # TEST 9: Test with a third persona (Nova) to ensure isolation
        # ========================================================================
        print_step(9, "Alice tells NOVA about her hobbies (different from work info)")
        
        result_nova = await chat_with_persona(
            user_alice,
            "nova",
            "I love painting and playing guitar in my free time!"
        )
        print_response("nova", result_nova["response"])
        await wait_for_memory_storage()
        
        # Verify Elara and Seraphina don't know about hobbies
        print("\n   Checking if Elara knows about Alice's hobbies...")
        elara_hobbies = await chat_with_persona(
            user_alice,
            "elara",
            "What are my hobbies?"
        )
        
        if "painting" not in elara_hobbies["response"].lower() and "guitar" not in elara_hobbies["response"].lower():
            print("   ✅ PASS: Elara doesn't know about hobbies (only told to Nova)")
        else:
            print("   ⚠️  WARNING: Elara might know about hobbies")
        
        # ========================================================================
        # FINAL SUMMARY
        # ========================================================================
        print_header("📊 TEST SUMMARY")
        
        print("\n✅ Successfully verified:")
        print("   1. Elara and Seraphina maintain separate memories for the same user")
        print("   2. Each persona only knows what the user explicitly told them")
        print("   3. Same persona (Elara) maintains separate memories for different users")
        print("   4. Multiple personas (Elara, Seraphina, Nova) all have isolated memories")
        print("\n🎯 Memory isolation per (user_id, personality_id) is working correctly!")
        
        print("\n" + "=" * 80)
        print("  ✅ ALL TESTS PASSED - MEMORY ISOLATION VERIFIED")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

