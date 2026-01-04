# API Examples

Complete examples for testing the AI Companion Service API.

## Base URL

```
http://localhost:8000
```

## 1. Chat (Streaming)

### Simple Chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: alice" \
  -d '{
    "message": "Hello! My name is Alice and I love Python programming."
  }'
```

### Continue Conversation
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: alice" \
  -d '{
    "message": "What do you remember about me?",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Create JWT (recommended) and use it

```bash
# 1) Create token (also creates the user if missing)
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id":"alice","expires_in_hours":24}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 2) Use token
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"Hello from JWT!"}'
```

### Python Client (Streaming)
```python
import httpx
import json
import asyncio

async def chat_stream(message, conversation_id=None):
    async with httpx.AsyncClient() as client:
        payload = {"message": message}
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        async with client.stream(
            'POST',
            'http://localhost:8000/chat',
            json=payload,
            headers={"X-User-Id": "alice"},
            timeout=60.0
        ) as response:
            print("Assistant: ", end='', flush=True)
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    if 'chunk' in data and data['chunk']:
                        print(data['chunk'], end='', flush=True)
                    if data.get('done'):
                        print(f"\n[Conversation ID: {data.get('conversation_id')}]")

# Run
asyncio.run(chat_stream("Tell me about AI"))
```

### JavaScript Client (Fetch API)
```javascript
async function chatStream(message, conversationId = null) {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-User-Id': 'alice' },
    body: JSON.stringify({ 
      message, 
      conversation_id: conversationId 
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.chunk) {
          process.stdout.write(data.chunk);
        }
        if (data.done) {
          console.log(`\n[Conversation ID: ${data.conversation_id}]`);
        }
      }
    }
  }
}

// Usage
chatStream("What is machine learning?");
```

## 2. Reset Conversation

```bash
curl -X POST http://localhost:8000/conversation/reset \
  -H "Content-Type: application/json" \
  -H "X-User-Id: alice" \
  -d '{
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Python
```python
import httpx

async def reset_conversation(conversation_id):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://localhost:8000/conversation/reset',
            json={"conversation_id": conversation_id},
            headers={"X-User-Id": "alice"}
        )
        return response.json()
```

## 3. Clear Memories

```bash
curl -X POST http://localhost:8000/memory/clear \
  -H "Content-Type: application/json" \
  -H "X-User-Id: alice" \
  -d '{
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Python
```python
import httpx

async def clear_memories(conversation_id):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://localhost:8000/memory/clear',
            json={"conversation_id": conversation_id},
            headers={"X-User-Id": "alice"}
        )
        return response.json()
```

## 4. Health Check

```bash
curl http://localhost:8000/health
```

### Python
```python
import httpx

async def check_health():
    async with httpx.AsyncClient() as client:
        response = await client.get('http://localhost:8000/health')
        return response.json()
```

## Complete Python CLI Example

```python
#!/usr/bin/env python3
"""Simple CLI client for AI Companion Service."""

import asyncio
import httpx
import json
from uuid import UUID

class AICompanionClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.conversation_id = None
        self.headers = {"X-User-Id": "alice"}  # dev auth example
    
    async def chat(self, message: str) -> str:
        """Send a chat message and get streaming response."""
        async with httpx.AsyncClient() as client:
            payload = {"message": message}
            if self.conversation_id:
                payload["conversation_id"] = str(self.conversation_id)
            
            response_text = []
            async with client.stream(
                'POST',
                f'{self.base_url}/chat',
                json=payload,
                headers=self.headers,
                timeout=60.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if 'chunk' in data and data['chunk']:
                            print(data['chunk'], end='', flush=True)
                            response_text.append(data['chunk'])
                        if data.get('done'):
                            self.conversation_id = data.get('conversation_id')
                            print()
            
            return ''.join(response_text)
    
    async def reset(self):
        """Reset the conversation."""
        if not self.conversation_id:
            print("No active conversation")
            return
        
        async with httpx.AsyncClient() as client:
            await client.post(
                f'{self.base_url}/conversation/reset',
                json={"conversation_id": str(self.conversation_id)},
                headers=self.headers
            )
        print("Conversation reset")
    
    async def clear(self):
        """Clear all memories."""
        if not self.conversation_id:
            print("No active conversation")
            return
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{self.base_url}/memory/clear',
                json={"conversation_id": str(self.conversation_id)},
                headers=self.headers
            )
        data = response.json()
        print(f"Cleared {data['memories_cleared']} memories")

async def main():
    """Interactive CLI."""
    client = AICompanionClient()
    
    print("AI Companion CLI")
    print("Commands: /reset, /clear, /quit")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input == "/quit":
                break
            elif user_input == "/reset":
                await client.reset()
            elif user_input == "/clear":
                await client.clear()
            else:
                print("AI: ", end='', flush=True)
                await client.chat(user_input)
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError: {e}")
    
    print("\nGoodbye!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Rate Limiting

The API has rate limiting enabled (default: 30 requests/minute).

If you exceed the limit, you'll receive:
```json
{
  "error": "Rate limit exceeded: 30 per 1 minute"
}
```

## Error Responses

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Server Error
```json
{
  "error": "LLMConnectionError",
  "detail": "Failed to connect to LM Studio"
}
```

## Testing Memory System

### Test Long-Term Memory
```bash
# 1. Introduce yourself
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: bob" \
  -d '{"message": "Hi! My name is Bob and I love hiking and photography."}'

# 2. Continue conversation (note the conversation_id from response)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: bob" \
  -d '{
    "message": "I also enjoy cooking Italian food.",
    "conversation_id": "YOUR_CONVERSATION_ID"
  }'

# 3. Test memory recall
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: bob" \
  -d '{
    "message": "What do you know about my interests?",
    "conversation_id": "YOUR_CONVERSATION_ID"
  }'
```

### Test Short-Term Reset
```bash
# Reset conversation but keep long-term memories
curl -X POST http://localhost:8000/conversation/reset \
  -H "Content-Type: application/json" \
  -H "X-User-Id: bob" \
  -d '{"conversation_id": "YOUR_CONVERSATION_ID"}'

# Memory should still be recalled
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: bob" \
  -d '{
    "message": "Do you remember anything about me?",
    "conversation_id": "YOUR_CONVERSATION_ID"
  }'
```

## Production Usage Tips

1. **Store conversation IDs**: Keep track of conversation_id for each user session
2. **Handle streaming**: Implement proper SSE parsing in your client
3. **Error handling**: Always handle connection errors and timeouts
4. **Rate limiting**: Implement client-side rate limiting for better UX
5. **Security**: Use HTTPS in production and implement authentication

## Postman Collection

Import this JSON to Postman:

```json
{
  "info": {
    "name": "AI Companion Service",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Chat",
      "request": {
        "method": "POST",
        "header": [],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"message\": \"Hello!\",\n  \"conversation_id\": null\n}",
          "options": {
            "raw": {
              "language": "json"
            }
          }
        },
        "url": {
          "raw": "http://localhost:8000/chat",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["chat"]
        }
      }
    },
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": {
          "raw": "http://localhost:8000/health",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["health"]
        }
      }
    }
  ]
}
```

