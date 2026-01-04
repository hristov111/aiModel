# Authentication Guide

The AI Companion Service now supports multi-user authentication to isolate conversations and memories per user.

## Authentication Methods

The service supports three authentication methods (in order of preference):

### 1. Authorization Bearer Token (JWT - Recommended)

This is the recommended approach for any real deployment.

#### Create a token (also creates the user in the DB if missing)

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "expires_in_hours": 24}'
```

#### Use the token

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{"message": "Hello!"}'
```

### 2. X-User-Id Header (Development/Testing only)

**⚠️ WARNING**: This is for development only. NOT secure for production.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: alice" \
  -d '{"message": "Hello!"}'
```

To disable this mechanism (recommended for production), set:

```env
ALLOW_X_USER_ID_AUTH=false
```

### 3. X-API-Key Header (Simple API Keys)

Simple API key authentication. Format: `user_<user_id>_<random>`

```bash
# Use API key
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: user_alice_a1b2c3d4e5f6" \
  -d '{"message": "Hello!"}'
```

## User Isolation

### Database Schema

```
users
├── id (UUID) - Internal database ID
├── external_user_id (string) - Your user ID from auth system
├── email
├── display_name
└── created_at

conversations
├── id (UUID)
├── user_id (FK → users.id) ← Enforces ownership
├── title
├── created_at
└── updated_at

memories
├── id (UUID)
├── conversation_id (FK → conversations.id) ← Inherits user isolation
├── content
├── embedding (vector)
└── ...
```

### How It Works

1. **Authentication**: User provides credentials via header
2. **User Lookup**: System finds or creates user record
3. **Conversation Check**: For existing conversations, verifies ownership
4. **Memory Isolation**: All queries filter by user_id automatically

## API Changes

### All Endpoints Now Require Authentication

**Before:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

**After:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: alice" \
  -d '{"message": "Hello"}'
```

### New Endpoint: List Conversations

Get all conversations for authenticated user:

```bash
curl http://localhost:8000/conversations \
  -H "X-User-Id: alice"
```

**Response:**
```json
{
  "conversations": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Chat about AI",
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T11:45:00",
      "message_count": 12
    }
  ],
  "total": 1
}
```

## Configuration

In `.env`:

```env
# Authentication
REQUIRE_AUTHENTICATION=true  # Set to false to disable auth (dev only)
ALLOW_X_USER_ID_AUTH=true   # Dev-only; set false in production
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

## Migration

If upgrading from the original version:

```bash
# Run migration to add users table
alembic upgrade head

# All existing conversations will be assigned to "default_user"
# Each user will only see their own conversations going forward
```

## Examples

### Python Client

```python
import httpx
import json

class AICompanionClient:
    def __init__(self, base_url="http://localhost:8000", user_id="alice"):
        self.base_url = base_url
        self.user_id = user_id
    
    async def chat(self, message, conversation_id=None):
        """Send chat message."""
        async with httpx.AsyncClient() as client:
            payload = {"message": message}
            if conversation_id:
                payload["conversation_id"] = conversation_id
            
            async with client.stream(
                'POST',
                f'{self.base_url}/chat',
                json=payload,
                headers={"X-User-Id": self.user_id},
                timeout=60.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if 'chunk' in data and data['chunk']:
                            print(data['chunk'], end='', flush=True)
                        if data.get('done'):
                            return data.get('conversation_id')
    
    async def list_conversations(self):
        """List all conversations."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{self.base_url}/conversations',
                headers={"X-User-Id": self.user_id}
            )
            return response.json()

# Usage
client = AICompanionClient(user_id="alice")
conv_id = await client.chat("Tell me about AI")
conversations = await client.list_conversations()
```

### JavaScript Client

```javascript
class AICompanionClient {
  constructor(baseUrl = 'http://localhost:8000', userId = 'alice') {
    this.baseUrl = baseUrl;
    this.userId = userId;
  }
  
  async chat(message, conversationId = null) {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': this.userId
      },
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
            return data.conversation_id;
          }
        }
      }
    }
  }
  
  async listConversations() {
    const response = await fetch(`${this.baseUrl}/conversations`, {
      headers: { 'X-User-Id': this.userId }
    });
    return response.json();
  }
}

// Usage
const client = new AICompanionClient('http://localhost:8000', 'alice');
const convId = await client.chat('Hello!');
const conversations = await client.listConversations();
```

## Security Best Practices

### Development
- ✅ Use `X-User-Id` header for quick testing
- ✅ Set `REQUIRE_AUTHENTICATION=false` to disable temporarily

### Production
- ❌ **NEVER** use `X-User-Id` in production
- ✅ Use JWT (`/auth/token` for development; protect it behind real login in production)
- ✅ Use HTTPS only
- ✅ Rotate JWT secret keys regularly
- ✅ Add rate limiting per user
- ✅ Implement proper user registration/login
- ✅ Hash API keys in database
- ✅ Add API key expiration

## Troubleshooting

### 401 Unauthorized
- Ensure you're providing an authentication header
- Check header name (case-sensitive)
- Verify user_id format
- If using JWT, ensure the token was minted by the currently running service (JWT secret mismatch will fail)

### 404 Conversation Not Found
- Conversation belongs to different user
- Check conversation_id is correct
- Verify user ownership

### Users Not Isolated
- Ensure migration 002 ran successfully
- Check `REQUIRE_AUTHENTICATION=true` in .env
- Verify authentication middleware is active

## Testing Multi-User Isolation

```bash
# User Alice creates conversation
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: alice" \
  -H "Content-Type: application/json" \
  -d '{"message": "My name is Alice and I love Python"}' \
  | tee /dev/tty | grep -o '"conversation_id":"[^"]*"' | cut -d'"' -f4 > conv_id.txt

CONV_ID=$(cat conv_id.txt)

# User Bob tries to access Alice's conversation (should fail)
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: bob" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What's in this conversation?\", \"conversation_id\": \"$CONV_ID\"}"
# Expected: 404 Not Found

# Alice can access her own conversation
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: alice" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What do you remember about me?\", \"conversation_id\": \"$CONV_ID\"}"
# Expected: Stream with memory recall
```

## Summary

- ✅ Multi-user support with user isolation
- ✅ Three authentication methods (dev, API key, JWT)
- ✅ Conversation ownership verification
- ✅ Automatic user creation on first access
- ✅ List conversations per user
- ✅ Backwards compatible migration
- ✅ Ready for production JWT implementation

