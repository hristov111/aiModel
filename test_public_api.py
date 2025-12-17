#!/usr/bin/env python3
"""
Test script for public API access.
Use this to verify your public endpoint is working correctly.
"""

import sys
import requests
import json
from typing import Optional

def test_api(
    api_url: str,
    auth_method: str = "jwt",
    auth_value: str = "",
    user_id: str = "alice",
    test_message: str = "Hello! Can you hear me?"
):
    """
    Test the public API endpoint.
    
    Args:
        api_url: Full API URL (e.g., https://yourdomain.com/api/chat)
        auth_method: Authentication method ("jwt", "api_key", or "user_id")
        auth_value: Token, API key, or user ID value
        user_id: User ID for user_id method
        test_message: Message to send
    """
    print(f"\n🧪 Testing Public API Access")
    print("=" * 70)
    print(f"API URL: {api_url}")
    print(f"Auth Method: {auth_method}")
    print(f"Test Message: {test_message}")
    print("=" * 70)
    
    # Set up headers based on auth method
    headers = {
        "Content-Type": "application/json"
    }
    
    if auth_method == "jwt":
        if not auth_value:
            print("❌ JWT token required!")
            print("Generate one with: python generate_token.py alice")
            return False
        headers["Authorization"] = f"Bearer {auth_value}"
    elif auth_method == "api_key":
        if not auth_value:
            print("❌ API key required!")
            print("Generate one with: python generate_token.py alice")
            return False
        headers["X-API-Key"] = auth_value
    elif auth_method == "user_id":
        headers["X-User-Id"] = user_id
    else:
        print(f"❌ Unknown auth method: {auth_method}")
        return False
    
    # Prepare request payload
    payload = {
        "message": test_message,
        "conversation_id": "test-public-access"
    }
    
    # Make request
    try:
        print("\n📤 Sending request...")
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! API is accessible and working!")
            print("\n📋 Response:")
            print("-" * 70)
            data = response.json()
            print(json.dumps(data, indent=2))
            print("-" * 70)
            return True
        elif response.status_code == 401:
            print("❌ AUTHENTICATION FAILED!")
            print("Response:", response.text)
            print("\nTroubleshooting:")
            print("1. Check your token/API key is valid")
            print("2. Verify REQUIRE_AUTHENTICATION is set correctly")
            print("3. Generate a new token: python generate_token.py alice")
            return False
        elif response.status_code == 403:
            print("❌ FORBIDDEN!")
            print("Response:", response.text)
            print("\nYou don't have permission to access this resource.")
            return False
        elif response.status_code == 429:
            print("❌ RATE LIMITED!")
            print("Response:", response.text)
            print("\nYou're making too many requests. Wait a bit and try again.")
            return False
        else:
            print(f"❌ ERROR: {response.status_code}")
            print("Response:", response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION FAILED!")
        print("\nTroubleshooting:")
        print("1. Is the service running?")
        print("   - Check: sudo systemctl status ai-model")
        print("   - Or: docker ps")
        print("2. Is the URL correct?")
        print("3. Is nginx running? sudo systemctl status nginx")
        print("4. Check firewall: sudo ufw status")
        return False
    except requests.exceptions.Timeout:
        print("❌ REQUEST TIMED OUT!")
        print("\nThe service took too long to respond.")
        print("Check if LM Studio is running and responding.")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False


def test_health_endpoint(base_url: str):
    """Test the health endpoint."""
    health_url = f"{base_url.rstrip('/api/chat')}/health"
    
    print(f"\n🏥 Testing Health Endpoint")
    print("=" * 70)
    print(f"URL: {health_url}")
    print("=" * 70)
    
    try:
        response = requests.get(health_url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Service is healthy!")
            print("Response:", json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python test_public_api.py <api_url> <auth_method> [auth_value]")
        print("\nExamples:")
        print("  # Test with JWT token:")
        print("  python test_public_api.py https://yourdomain.com/api/chat jwt YOUR_JWT_TOKEN")
        print("\n  # Test with API key:")
        print("  python test_public_api.py https://yourdomain.com/api/chat api_key user_alice_xxxxx")
        print("\n  # Test with user ID (dev only):")
        print("  python test_public_api.py https://yourdomain.com/api/chat user_id alice")
        print("\n  # Test ngrok URL:")
        print("  python test_public_api.py https://abc123.ngrok.io/api/chat user_id alice")
        sys.exit(1)
    
    api_url = sys.argv[1]
    auth_method = sys.argv[2]
    auth_value = sys.argv[3] if len(sys.argv) > 3 else ""
    
    # Extract base URL for health check
    base_url = api_url.replace('/api/chat', '')
    
    # Test health endpoint first
    health_ok = test_health_endpoint(base_url)
    
    # Test chat API
    api_ok = test_api(
        api_url=api_url,
        auth_method=auth_method,
        auth_value=auth_value
    )
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"API Test: {'✅ PASS' if api_ok else '❌ FAIL'}")
    print("=" * 70)
    
    if health_ok and api_ok:
        print("\n🎉 All tests passed! Your API is publicly accessible and working!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Review the output above for troubleshooting.")
        sys.exit(1)


if __name__ == "__main__":
    main()

