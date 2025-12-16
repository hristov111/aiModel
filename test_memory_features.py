#!/usr/bin/env python3
"""
Comprehensive test for memory features with JWT authentication.
"""

import requests
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000"
USER_ID = "myuser123"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJteXVzZXIxMjMiLCJpYXQiOjE3NjU4Nzg0OTUsImV4cCI6MTc2NTk2NDg5NSwidHlwZSI6ImFjY2Vzc190b2tlbiJ9.mMNINFA46SWHNlDeznMNH2d_gGI647J9RmFqoPhkspI"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}"
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def print_section(msg):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def test_health():
    """Test 1: Health check"""
    print_section("TEST 1: Health Check")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        data = response.json()
        print_success(f"API is {data['status']}")
        print_info(f"  Version: {data.get('version', 'unknown')}")
        print_info(f"  Database: {data.get('database', False)}")
        print_info(f"  LLM: {data.get('llm', False)}")
        return True
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def test_chat_with_memory_extraction(message):
    """Test 2: Send message and extract memories"""
    print_section(f"TEST 2: Chat with Memory Extraction")
    print_info(f"Sending: '{message}'")
    
    try:
        payload = {
            "message": message,
            "user_id": USER_ID
        }
        
        response = requests.post(
            f"{API_URL}/chat",
            headers=HEADERS,
            json=payload,
            stream=True,
            timeout=30
        )
        
        thinking_steps = []
        response_chunks = []
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('type') == 'thinking':
                            thinking_steps.append(data)
                            step = data.get('step', 'unknown')
                            step_data = data.get('data', {})
                            
                            if step == 'memories_retrieved':
                                count = step_data.get('count', 0)
                                memories = step_data.get('memories', [])
                                if count > 0:
                                    print_success(f"Retrieved {count} memories:")
                                    for mem in memories:
                                        print(f"    - {mem.get('content', '')[:60]}...")
                                        print(f"      Similarity: {mem.get('similarity_score', 0):.3f}")
                                else:
                                    print_error("No memories retrieved!")
                                    
                            elif step == 'goals_tracked':
                                goals = step_data.get('goals', [])
                                print_info(f"Tracking {len(goals)} goals")
                                
                            elif step == 'personality_loaded':
                                archetype = step_data.get('archetype', 'none')
                                print_info(f"Personality: {archetype}")
                                
                        elif data.get('type') == 'chunk':
                            response_chunks.append(data.get('chunk', ''))
                    except json.JSONDecodeError:
                        pass
        
        full_response = ''.join(response_chunks)
        if response_chunks:
            print_success(f"Got response: {full_response[:100]}...")
        
        return {
            'thinking_steps': thinking_steps,
            'response': full_response,
            'success': len(response_chunks) > 0
        }
    except Exception as e:
        print_error(f"Chat request failed: {e}")
        return {'success': False, 'error': str(e)}

def test_user_preferences():
    """Test 3: Get user preferences"""
    print_section("TEST 3: User Preferences")
    try:
        response = requests.get(
            f"{API_URL}/user/preferences",
            headers=HEADERS,
            params={"user_id": USER_ID},
            timeout=5
        )
        
        if response.status_code == 200:
            prefs = response.json()
            print_success(f"Retrieved {len(prefs.get('preferences', []))} preferences")
            for pref in prefs.get('preferences', [])[:5]:
                print(f"  - {pref.get('name', 'unknown')}: {pref.get('value', 'N/A')}")
            return True
        else:
            print_error(f"Status {response.status_code}: {response.text[:100]}")
            return False
    except Exception as e:
        print_error(f"Preferences request failed: {e}")
        return False

def test_goals():
    """Test 4: Get user goals"""
    print_section("TEST 4: User Goals")
    try:
        response = requests.get(
            f"{API_URL}/user/goals",
            headers=HEADERS,
            params={"user_id": USER_ID},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            goals = data.get('goals', [])
            print_success(f"Found {len(goals)} goals")
            for goal in goals:
                print(f"  - {goal.get('title', 'Untitled')}")
                print(f"    Status: {goal.get('status', 'unknown')}, Progress: {goal.get('progress_percentage', 0)}%")
            return True
        else:
            print_error(f"Status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Goals request failed: {e}")
        return False

def test_personality():
    """Test 5: Get personality profile"""
    print_section("TEST 5: Personality Profile")
    try:
        response = requests.get(
            f"{API_URL}/user/personality",
            headers=HEADERS,
            params={"user_id": USER_ID},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Personality archetype: {data.get('archetype', 'none')}")
            print_info(f"Relationship: {data.get('relationship_type', 'unknown')}")
            traits = data.get('traits', {})
            if traits:
                print_info("Traits:")
                for trait, value in list(traits.items())[:5]:
                    print(f"    {trait}: {value}/10")
            return True
        else:
            print_error(f"Status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Personality request failed: {e}")
        return False

def main():
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Memory Features Comprehensive Test{Colors.RESET}")
    print(f"{Colors.BOLD}User: {USER_ID}{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    results = {}
    
    # Test 1: Health
    results['health'] = test_health()
    
    if not results['health']:
        print_error("\nServer not available. Exiting.")
        return
    
    # Test 2: Chat with memory that should match existing memories
    result = test_chat_with_memory_extraction("Hi! What do you know about me?")
    results['chat_memory_retrieval'] = result.get('success', False)
    
    # Test 3: Chat with new information
    result = test_chat_with_memory_extraction("By the way, I also enjoy reading science fiction books!")
    results['chat_new_memory'] = result.get('success', False)
    
    # Test 4: Preferences
    results['preferences'] = test_user_preferences()
    
    # Test 5: Goals
    results['goals'] = test_goals()
    
    # Test 6: Personality
    results['personality'] = test_personality()
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed_test else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n{Colors.BOLD}Result: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All features working!{Colors.RESET}\n")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ Some features need attention{Colors.RESET}\n")

if __name__ == "__main__":
    main()

