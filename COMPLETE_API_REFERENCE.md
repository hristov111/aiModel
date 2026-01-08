# Complete API Reference Guide
## AI Companion Service - All Endpoints Explained

**Base URL:** `http://localhost:8000`  
**Production URL:** `https://yourdomain.com` (when deployed)

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [Chat & Conversations](#chat--conversations)
3. [Memory Management](#memory-management)
4. [User Preferences](#user-preferences)
5. [Emotion Tracking](#emotion-tracking)
6. [Personality System](#personality-system)
7. [Goals & Progress](#goals--progress)
8. [Content Safety](#content-safety)
9. [System Health](#system-health)

---

## 🔐 Authentication

All endpoints (except `/health`, `/`, and token creation) require authentication using ONE of these methods:

### Method 1: JWT Token (Recommended for Production)
```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Method 2: API Key
```bash
X-API-Key: user_alice_abc123def456
```

### Method 3: User ID (Development Only)
```bash
X-User-Id: alice
```

---

## 1. Authentication Endpoints

### 1.1 Create JWT Token

**Purpose:** Generate a JWT token for a user. This also creates the user in the database if they don't exist.

**URL:** `POST http://localhost:8000/auth/token`

**Authentication:** None required

**Request Body:**
```json
{
  "user_id": "alice",
  "expires_in_hours": 24
}
```

**Parameters:**
- `user_id` (string, required): Unique identifier for the user
- `expires_in_hours` (integer, optional): Token validity duration (default: 24, max: 168)

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWxpY2UiLCJleHAiOjE3MDk4NTYwMDB9.abcd1234",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_id": "alice"
}
```

**Full Example:**
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "expires_in_hours": 24
  }'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/auth/token",
    json={
        "user_id": "alice",
        "expires_in_hours": 24
    }
)

token_data = response.json()
access_token = token_data["access_token"]
print(f"Token: {access_token}")
```

---

### 1.2 Validate JWT Token

**Purpose:** Check if a JWT token is still valid.

**URL:** `POST http://localhost:8000/auth/validate`

**Authentication:** None required

**Request Body:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (Valid Token):**
```json
{
  "valid": true,
  "user_id": "alice",
  "expires_at": "2024-03-08T12:00:00Z",
  "error": null
}
```

**Response (Invalid Token):**
```json
{
  "valid": false,
  "user_id": null,
  "expires_at": null,
  "error": "Invalid or expired token"
}
```

**Full Example:**
```bash
curl -X POST http://localhost:8000/auth/validate \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

---

## 2. Chat & Conversations

### 2.1 Chat (Stream Response)

**Purpose:** Send a message to the AI and receive a streaming response. This is the main endpoint for conversing with the AI. The AI will remember context from previous messages and recall long-term memories.

**URL:** `POST http://localhost:8000/chat`

**Authentication:** Required

**Rate Limit:** 30 requests per minute

**Request Body:**
```json
{
  "message": "Hello! My name is Alice and I love programming in Python.",
  "conversation_id": null
}
```

**Parameters:**
- `message` (string, required): The user's message to the AI
- `conversation_id` (string/UUID, optional): If null, starts a new conversation. If provided, continues an existing conversation.

**Response Format:** Server-Sent Events (SSE) stream

**Event Types:**

1. **Thinking Events** - AI's processing steps:
```
data: {"type": "thinking", "step": "retrieving_memories", "detail": "Found 5 relevant memories"}

data: {"type": "thinking", "step": "detecting_emotion", "detail": "Emotion: joyful (0.85 confidence)"}

data: {"type": "thinking", "step": "generating_response", "detail": "Using casual communication style"}
```

2. **Chunk Events** - Response text pieces:
```
data: {"type": "chunk", "content": "Hello Alice"}

data: {"type": "chunk", "content": "! It's great"}

data: {"type": "chunk", "content": " to meet you."}
```

3. **Done Event** - Completion with conversation ID:
```
data: {"type": "done", "conversation_id": "550e8400-e29b-41d4-a716-446655440000"}
```

4. **Error Event** - If something goes wrong:
```
data: {"type": "error", "error": "Connection to LLM failed", "detail": "Timeout after 30s"}
```

**Full Example (curl):**
```bash
# Start a new conversation
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello! My name is Alice and I love programming in Python."
  }'

# Continue an existing conversation
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What do you remember about me?",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Python Example (Streaming):**
```python
import httpx
import json

async def chat_with_ai(message, conversation_id=None, token=None):
    """Stream chat responses from the AI."""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {"message": message}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    async with httpx.AsyncClient() as client:
        async with client.stream(
            'POST',
            'http://localhost:8000/chat',
            json=payload,
            headers=headers,
            timeout=60.0
        ) as response:
            conversation_id = None
            
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    
                    if data['type'] == 'thinking':
                        print(f"[Thinking: {data['step']}] {data.get('detail', '')}")
                    
                    elif data['type'] == 'chunk':
                        print(data['content'], end='', flush=True)
                    
                    elif data['type'] == 'done':
                        conversation_id = data['conversation_id']
                        print(f"\n\n[Conversation ID: {conversation_id}]")
                    
                    elif data['type'] == 'error':
                        print(f"\nError: {data['error']}")
            
            return conversation_id

# Usage
import asyncio
conv_id = asyncio.run(chat_with_ai("Hello!", token="YOUR_TOKEN"))
```

**JavaScript Example:**
```javascript
async function chatWithAI(message, conversationId = null, token) {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: message,
      conversation_id: conversationId
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let conversationId = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        if (data.type === 'thinking') {
          console.log(`[${data.step}] ${data.detail || ''}`);
        } else if (data.type === 'chunk') {
          process.stdout.write(data.content);
        } else if (data.type === 'done') {
          conversationId = data.conversation_id;
          console.log(`\n[Conversation ID: ${conversationId}]`);
        } else if (data.type === 'error') {
          console.error(`Error: ${data.error}`);
        }
      }
    }
  }

  return conversationId;
}

// Usage
chatWithAI("Hello!", null, "YOUR_TOKEN");
```

---

### 2.2 Reset Conversation

**Purpose:** Clear the short-term conversation buffer (recent messages) but keep long-term memories. Use this to start fresh while the AI still remembers important facts about the user.

**URL:** `POST http://localhost:8000/conversation/reset`

**Authentication:** Required

**Request Body:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Conversation reset successfully",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Full Example:**
```bash
curl -X POST http://localhost:8000/conversation/reset \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/conversation/reset",
    headers={"Authorization": f"Bearer {token}"},
    json={"conversation_id": "550e8400-e29b-41d4-a716-446655440000"}
)

result = response.json()
print(f"Reset: {result['message']}")
```

---

### 2.3 List Conversations

**Purpose:** Get a list of all conversations for the authenticated user.

**URL:** `GET http://localhost:8000/conversations`

**Authentication:** Required

**Response:**
```json
{
  "conversations": [
    {
      "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2024-03-01T10:30:00Z",
      "updated_at": "2024-03-01T11:45:00Z",
      "message_count": 15,
      "last_message": "Thanks for the help!"
    },
    {
      "conversation_id": "660e8400-e29b-41d4-a716-446655440001",
      "created_at": "2024-03-02T14:20:00Z",
      "updated_at": "2024-03-02T14:35:00Z",
      "message_count": 8,
      "last_message": "What's the weather like?"
    }
  ],
  "total": 2
}
```

**Full Example:**
```bash
curl -X GET http://localhost:8000/conversations \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Python Example:**
```python
import requests

response = requests.get(
    "http://localhost:8000/conversations",
    headers={"Authorization": f"Bearer {token}"}
)

conversations = response.json()
for conv in conversations['conversations']:
    print(f"ID: {conv['conversation_id']}, Messages: {conv['message_count']}")
```

---

## 3. Memory Management

### 3.1 Clear All Memories

**Purpose:** Delete ALL memories (both short-term conversation buffer AND long-term stored memories) for a specific conversation. This is a destructive operation and cannot be undone.

**URL:** `POST http://localhost:8000/memory/clear`

**Authentication:** Required

**Request Body:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Memories cleared successfully",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "memories_cleared": 24
}
```

**Full Example:**
```bash
curl -X POST http://localhost:8000/memory/clear \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/memory/clear",
    headers={"Authorization": f"Bearer {token}"},
    json={"conversation_id": "550e8400-e29b-41d4-a716-446655440000"}
)

result = response.json()
print(f"Cleared {result['memories_cleared']} memories")
```

---

## 4. User Preferences

### 4.1 Set User Preferences

**Purpose:** Set communication style preferences. The AI will adapt its responses to match the selected style.

**URL:** `POST http://localhost:8000/preferences`

**Authentication:** Required

**Request Body:**
```json
{
  "communication_style": "casual",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Parameters:**
- `communication_style` (string, required): One of:
  - `"formal"` - Professional, structured communication
  - `"casual"` - Friendly, relaxed conversation
  - `"technical"` - Detailed, technical explanations
  - `"friendly"` - Warm, encouraging tone
- `conversation_id` (string/UUID, optional): Associate preferences with a conversation

**Response:**
```json
{
  "user_id": "alice",
  "communication_style": "casual",
  "preferences": {
    "style": "casual",
    "formality_level": 0.3,
    "detail_level": 0.6
  },
  "updated_at": "2024-03-01T10:30:00Z"
}
```

**Full Example:**
```bash
curl -X POST http://localhost:8000/preferences \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "communication_style": "technical",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/preferences",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "communication_style": "casual",
        "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
    }
)

prefs = response.json()
print(f"Style set to: {prefs['communication_style']}")
```

---

### 4.2 Get User Preferences

**Purpose:** Retrieve the current communication preferences for the user.

**URL:** `GET http://localhost:8000/preferences`

**Authentication:** Required

**Response:**
```json
{
  "user_id": "alice",
  "communication_style": "casual",
  "preferences": {
    "style": "casual",
    "formality_level": 0.3,
    "detail_level": 0.6
  },
  "created_at": "2024-03-01T10:00:00Z",
  "updated_at": "2024-03-01T10:30:00Z"
}
```

**Full Example:**
```bash
curl -X GET http://localhost:8000/preferences \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Python Example:**
```python
import requests

response = requests.get(
    "http://localhost:8000/preferences",
    headers={"Authorization": f"Bearer {token}"}
)

prefs = response.json()
print(f"Current style: {prefs['communication_style']}")
```

---

## 5. Emotion Tracking

### 5.1 Get Emotion History

**Purpose:** Retrieve the history of emotions detected in conversations. The AI automatically detects emotions in user messages.

**URL:** `GET http://localhost:8000/emotions/history`

**Authentication:** Required

**Query Parameters:**
- `conversation_id` (UUID, optional): Filter by specific conversation
- `limit` (integer, optional): Number of results (default: 50)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response:**
```json
{
  "emotions": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
      "emotion": "joyful",
      "confidence": 0.85,
      "message": "I just got promoted!",
      "detected_at": "2024-03-01T10:30:00Z"
    },
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
      "emotion": "anxious",
      "confidence": 0.72,
      "message": "I'm worried about the presentation tomorrow",
      "detected_at": "2024-03-01T11:15:00Z"
    }
  ],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

**Full Example:**
```bash
# Get all emotions
curl -X GET "http://localhost:8000/emotions/history" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get emotions for specific conversation with pagination
curl -X GET "http://localhost:8000/emotions/history?conversation_id=550e8400-e29b-41d4-a716-446655440000&limit=20&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Python Example:**
```python
import requests

response = requests.get(
    "http://localhost:8000/emotions/history",
    headers={"Authorization": f"Bearer {token}"},
    params={
        "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
        "limit": 20
    }
)

data = response.json()
for emotion in data['emotions']:
    print(f"{emotion['detected_at']}: {emotion['emotion']} ({emotion['confidence']:.2f})")
```

---

### 5.2 Get Emotion Statistics

**Purpose:** Get aggregated statistics about detected emotions (counts, averages, most common emotions).

**URL:** `GET http://localhost:8000/emotions/statistics`

**Authentication:** Required

**Query Parameters:**
- `conversation_id` (UUID, optional): Filter by specific conversation

**Response:**
```json
{
  "total_emotions": 45,
  "emotion_counts": {
    "joyful": 15,
    "neutral": 12,
    "anxious": 8,
    "excited": 6,
    "sad": 4
  },
  "average_confidence": 0.78,
  "most_common_emotion": "joyful",
  "date_range": {
    "from": "2024-03-01T00:00:00Z",
    "to": "2024-03-07T23:59:59Z"
  }
}
```

**Full Example:**
```bash
curl -X GET "http://localhost:8000/emotions/statistics" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# For specific conversation
curl -X GET "http://localhost:8000/emotions/statistics?conversation_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Python Example:**
```python
import requests

response = requests.get(
    "http://localhost:8000/emotions/statistics",
    headers={"Authorization": f"Bearer {token}"}
)

stats = response.json()
print(f"Total emotions: {stats['total_emotions']}")
print(f"Most common: {stats['most_common_emotion']}")
print(f"Emotion breakdown: {stats['emotion_counts']}")
```

---

### 5.3 Get Emotion Trends

**Purpose:** Get emotion trends over time (daily averages, changes).

**URL:** `GET http://localhost:8000/emotions/trends`

**Authentication:** Required

**Query Parameters:**
- `conversation_id` (UUID, optional): Filter by specific conversation
- `days` (integer, optional): Number of days to look back (default: 7)

**Response:**
```json
{
  "trends": [
    {
      "date": "2024-03-01",
      "emotions": {
        "joyful": 3,
        "neutral": 2,
        "anxious": 1
      },
      "average_confidence": 0.82,
      "total_messages": 6
    },
    {
      "date": "2024-03-02",
      "emotions": {
        "excited": 4,
        "joyful": 2
      },
      "average_confidence": 0.79,
      "total_messages": 6
    }
  ],
  "days_analyzed": 7,
  "overall_trend": "improving"
}
```

**Full Example:**
```bash
curl -X GET "http://localhost:8000/emotions/trends?days=7" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Python Example:**
```python
import requests

response = requests.get(
    "http://localhost:8000/emotions/trends",
    headers={"Authorization": f"Bearer {token}"},
    params={"days": 14}
)

trends = response.json()
for day in trends['trends']:
    print(f"{day['date']}: {day['emotions']}")
```

---

### 5.4 Clear Emotion History

**Purpose:** Delete emotion history for the user or a specific conversation.

**URL:** `DELETE http://localhost:8000/emotions/history`

**Authentication:** Required

**Query Parameters:**
- `conversation_id` (UUID, optional): If provided, only clears emotions for that conversation

**Response:**
```json
{
  "success": true,
  "message": "Emotion history cleared successfully",
  "emotions_cleared": 45
}
```

**Full Example:**
```bash
# Clear all emotion history
curl -X DELETE "http://localhost:8000/emotions/history" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Clear for specific conversation
curl -X DELETE "http://localhost:8000/emotions/history?conversation_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Python Example:**
```python
import requests

response = requests.delete(
    "http://localhost:8000/emotions/history",
    headers={"Authorization": f"Bearer {token}"},
    params={"conversation_id": "550e8400-e29b-41d4-a716-446655440000"}
)

result = response.json()
print(f"Cleared {result['emotions_cleared']} emotion records")
```

---

## 6. Personality System

### 6.1 List Available Personality Archetypes

**Purpose:** Get a list of all available personality archetypes that can be assigned to the AI.

**URL:** `GET http://localhost:8000/personality/archetypes`

**Authentication:** Not required

**Response:**
```json
{
  "archetypes": [
    {
      "id": "mentor",
      "name": "Mentor",
      "description": "Wise, guiding presence that helps you learn and grow",
      "traits": {
        "formality": 0.7,
        "empathy": 0.8,
        "directness": 0.6,
        "enthusiasm": 0.5
      }
    },
    {
      "id": "friend",
      "name": "Friend",
      "description": "Casual, supportive companion for everyday conversations",
      "traits": {
        "formality": 0.3,
        "empathy": 0.9,
        "directness": 0.5,
        "enthusiasm": 0.7
      }
    },
    {
      "id": "professional",
      "name": "Professional",
      "description": "Business-focused, efficient assistant",
      "traits": {
        "formality": 0.9,
        "empathy": 0.5,
        "directness": 0.8,
        "enthusiasm": 0.4
      }
    },
    {
      "id": "creative",
      "name": "Creative",
      "description": "Imaginative, inspiring collaborator",
      "traits": {
        "formality": 0.4,
        "empathy": 0.7,
        "directness": 0.4,
        "enthusiasm": 0.9
      }
    },
    {
      "id": "analytical",
      "name": "Analytical",
      "description": "Logical, detail-oriented problem solver",
      "traits": {
        "formality": 0.7,
        "empathy": 0.4,
        "directness": 0.9,
        "enthusiasm": 0.3
      }
    }
  ],
  "total": 5
}
```

**Full Example:**
```bash
curl -X GET http://localhost:8000/personality/archetypes
```

**Python Example:**
```python
import requests

response = requests.get("http://localhost:8000/personality/archetypes")
archetypes = response.json()

for archetype in archetypes['archetypes']:
    print(f"{archetype['name']}: {archetype['description']}")
```

---

### 6.2 Create/Set AI Personality

**Purpose:** Set the AI's personality archetype for the user. This affects how the AI communicates and responds.

**URL:** `POST http://localhost:8000/personality`

**Authentication:** Required

**Request Body:**
```json
{
  "archetype": "mentor",
  "custom_traits": {
    "formality": 0.7,
    "enthusiasm": 0.8,
    "empathy": 0.9
  },
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Parameters:**
- `archetype` (string, required): One of: `"mentor"`, `"friend"`, `"professional"`, `"creative"`, `"analytical"`
- `custom_traits` (object, optional): Override default traits (values 0.0 - 1.0):
  - `formality`: How formal/casual (0 = very casual, 1 = very formal)
  - `empathy`: How empathetic (0 = logical only, 1 = highly empathetic)
  - `directness`: How direct (0 = gentle/indirect, 1 = very direct)
  - `enthusiasm`: How enthusiastic (0 = reserved, 1 = very enthusiastic)
- `conversation_id` (string/UUID, optional): Associate with specific conversation

**Response:**
```json
{
  "personality_id": "990e8400-e29b-41d4-a716-446655440004",
  "user_id": "alice",
  "archetype": "mentor",
  "traits": {
    "formality": 0.7,
    "empathy": 0.9,
    "directness": 0.6,
    "enthusiasm": 0.8
  },
  "created_at": "2024-03-01T10:30:00Z",
  "is_active": true
}
```

**Full Example:**
```bash
# Use default archetype traits
curl -X POST http://localhost:8000/personality \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "archetype": "mentor"
  }'

# With custom traits
curl -X POST http://localhost:8000/personality \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "archetype": "friend",
    "custom_traits": {
      "formality": 0.2,
      "enthusiasm": 0.9
    }
  }'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/personality",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "archetype": "mentor",
        "custom_traits": {
            "empathy": 0.9,
            "enthusiasm": 0.7
        }
    }
)

personality = response.json()
print(f"Personality set: {personality['archetype']}")
print(f"Traits: {personality['traits']}")
```

---

### 6.3 Get Current Personality

**Purpose:** Retrieve the currently active AI personality for the user.

**URL:** `GET http://localhost:8000/personality`

**Authentication:** Required

**Response:**
```json
{
  "personality_id": "990e8400-e29b-41d4-a716-446655440004",
  "user_id": "alice",
  "archetype": "mentor",
  "traits": {
    "formality": 0.7,
    "empathy": 0.9,
    "directness": 0.6,
    "enthusiasm": 0.8
  },
  "created_at": "2024-03-01T10:30:00Z",
  "updated_at": "2024-03-01T10:30:00Z",
  "is_active": true
}
```

**Full Example:**
```bash
curl -X GET http://localhost:8000/personality \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Python Example:**
```python
import requests

response = requests.get(
    "http://localhost:8000/personality",
    headers={"Authorization": f"Bearer {token}"}
)

personality = response.json()
print(f"Current archetype: {personality['archetype']}")
print(f"Traits: {personality['traits']}")
```

---

### 6.4 Update Personality

**Purpose:** Update the existing AI personality (change archetype or adjust traits).

**URL:** `PUT http://localhost:8000/personality`

**Authentication:** Required

**Request Body:**
```json
{
  "archetype": "friend",
  "custom_traits": {
    "formality": 0.3,
    "enthusiasm": 0.9
  }
}
```

**Response:** Same as Create Personality

**Full Example:**
```bash
curl -X PUT http://localhost:8000/personality \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "archetype": "creative",
    "custom_traits": {
      "enthusiasm": 0.95
    }
  }'
```

---

### 6.5 Get Relationship State

**Purpose:** Get metrics about the relationship between user and AI (total messages, trust level, milestones, etc.).

**URL:** `GET http://localhost:8000/personality/relationship`

**Authentication:** Required

**Response:**
```json
{
  "total_messages": 156,
  "relationship_depth": 0.75,
  "trust_level": 0.82,
  "days_known": 14,
  "milestones_reached": [
    "first_conversation",
    "10_messages",
    "50_messages",
    "100_messages",
    "one_week"
  ],
  "positive_reactions": 45,
  "negative_reactions": 3,
  "topics_discussed": [
    "programming",
    "career",
    "health",
    "hobbies"
  ]
}
```

**Full Example:**
```bash
curl -X GET http://localhost:8000/personality/relationship \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Python Example:**
```python
import requests

response = requests.get(
    "http://localhost:8000/personality/relationship",
    headers={"Authorization": f"Bearer {token}"}
)

relationship = response.json()
print(f"Messages: {relationship['total_messages']}")
print(f"Trust level: {relationship['trust_level']}")
print(f"Milestones: {relationship['milestones_reached']}")
```

---

## 7. Goals & Progress Tracking

### 7.1 Create Goal

**Purpose:** Create a new goal for tracking progress.

**URL:** `POST http://localhost:8000/goals`

**Authentication:** Required

**Rate Limit:** 50 requests per minute

**Request Body:**
```json
{
  "title": "Learn Python Programming",
  "description": "Complete a Python course and build 3 projects",
  "category": "learning",
  "target_date": "2024-12-31",
  "motivation": "To advance my career as a software developer",
  "check_in_frequency": "weekly"
}
```

**Parameters:**
- `title` (string, required): Goal title
- `description` (string, optional): Detailed description
- `category` (string, required): One of:
  - `"learning"` - Educational goals
  - `"health"` - Health and fitness
  - `"career"` - Professional development
  - `"financial"` - Money and savings
  - `"personal"` - Personal development
  - `"creative"` - Creative projects
  - `"social"` - Social and relationships
- `target_date` (string, optional): ISO format date (e.g., "2024-12-31")
- `motivation` (string, optional): Why you want to achieve this
- `check_in_frequency` (string, optional): One of:
  - `"daily"` - Check in every day
  - `"weekly"` - Check in every week
  - `"biweekly"` - Check in every 2 weeks
  - `"monthly"` - Check in every month
  - `"never"` - No automatic check-ins

**Response:**
```json
{
  "goal_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "user_id": "alice",
  "title": "Learn Python Programming",
  "description": "Complete a Python course and build 3 projects",
  "category": "learning",
  "status": "active",
  "progress_percentage": 0,
  "target_date": "2024-12-31T00:00:00Z",
  "motivation": "To advance my career as a software developer",
  "check_in_frequency": "weekly",
  "next_check_in": "2024-03-08T00:00:00Z",
  "created_at": "2024-03-01T10:30:00Z",
  "updated_at": "2024-03-01T10:30:00Z"
}
```

**Full Example:**
```bash
curl -X POST http://localhost:8000/goals \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Exercise 3 times per week",
    "description": "Go to the gym or do home workouts",
    "category": "health",
    "target_date": "2024-06-30",
    "check_in_frequency": "weekly"
  }'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/goals",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "title": "Learn Python Programming",
        "description": "Complete a Python course and build 3 projects",
        "category": "learning",
        "target_date": "2024-12-31",
        "motivation": "To advance my career",
        "check_in_frequency": "weekly"
    }
)

goal = response.json()
print(f"Goal created: {goal['goal_id']}")
print(f"Title: {goal['title']}")
```

---

### 7.2 List Goals

**Purpose:** Get all goals for the user, with optional filtering.

**URL:** `GET http://localhost:8000/goals`

**Authentication:** Required

**Query Parameters:**
- `status` (string, optional): Filter by status (`"active"`, `"completed"`, `"abandoned"`)
- `category` (string, optional): Filter by category

**Response:**
```json
{
  "goals": [
    {
      "goal_id": "aa0e8400-e29b-41d4-a716-446655440005",
      "title": "Learn Python Programming",
      "category": "learning",
      "status": "active",
      "progress_percentage": 35,
      "target_date": "2024-12-31T00:00:00Z",
      "created_at": "2024-03-01T10:30:00Z"
    },
    {
      "goal_id": "bb0e8400-e29b-41d4-a716-446655440006",
      "title": "Exercise 3 times per week",
      "category": "health",
      "status": "active",
      "progress_percentage": 60,
      "target_date": "2024-06-30T00:00:00Z",
      "created_at": "2024-03-01T11:00:00Z"
    }
  ],
  "total": 2
}
```

**Full Example:**
```bash
# Get all goals
curl -X GET http://localhost:8000/goals \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Filter by status
curl -X GET "http://localhost:8000/goals?status=active" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Filter by category
curl -X GET "http://localhost:8000/goals?category=health" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Python Example:**
```python
import requests

response = requests.get(
    "http://localhost:8000/goals",
    headers={"Authorization": f"Bearer {token}"},
    params={"status": "active"}
)

goals = response.json()
for goal in goals['goals']:
    print(f"{goal['title']}: {goal['progress_percentage']}%")
```

---

### 7.3 Get Goal Details

**Purpose:** Get detailed information about a specific goal.

**URL:** `GET http://localhost:8000/goals/{goal_id}`

**Authentication:** Required

**Response:**
```json
{
  "goal_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "user_id": "alice",
  "title": "Learn Python Programming",
  "description": "Complete a Python course and build 3 projects",
  "category": "learning",
  "status": "active",
  "progress_percentage": 35,
  "target_date": "2024-12-31T00:00:00Z",
  "motivation": "To advance my career as a software developer",
  "check_in_frequency": "weekly",
  "next_check_in": "2024-03-08T00:00:00Z",
  "created_at": "2024-03-01T10:30:00Z",
  "updated_at": "2024-03-05T14:20:00Z",
  "completed_at": null,
  "progress_entries": 5
}
```

**Full Example:**
```bash
curl -X GET http://localhost:8000/goals/aa0e8400-e29b-41d4-a716-446655440005 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Python Example:**
```python
import requests

goal_id = "aa0e8400-e29b-41d4-a716-446655440005"
response = requests.get(
    f"http://localhost:8000/goals/{goal_id}",
    headers={"Authorization": f"Bearer {token}"}
)

goal = response.json()
print(f"Goal: {goal['title']}")
print(f"Progress: {goal['progress_percentage']}%")
print(f"Status: {goal['status']}")
```

---

### 7.4 Update Goal

**Purpose:** Update a goal's details.

**URL:** `PUT http://localhost:8000/goals/{goal_id}`

**Authentication:** Required

**Request Body:**
```json
{
  "title": "Master Python Programming",
  "description": "Complete a Python course and build 5 projects",
  "target_date": "2024-12-31",
  "status": "active",
  "check_in_frequency": "biweekly"
}
```

**Response:** Same as Get Goal Details

**Full Example:**
```bash
curl -X PUT http://localhost:8000/goals/aa0e8400-e29b-41d4-a716-446655440005 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Master Python Programming",
    "status": "active"
  }'
```

---

### 7.5 Delete Goal

**Purpose:** Delete a goal permanently.

**URL:** `DELETE http://localhost:8000/goals/{goal_id}`

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Goal deleted successfully",
  "goal_id": "aa0e8400-e29b-41d4-a716-446655440005"
}
```

**Full Example:**
```bash
curl -X DELETE http://localhost:8000/goals/aa0e8400-e29b-41d4-a716-446655440005 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 7.6 Add Progress Update

**Purpose:** Log progress on a goal.

**URL:** `POST http://localhost:8000/goals/{goal_id}/progress`

**Authentication:** Required

**Request Body:**
```json
{
  "progress_percentage": 50,
  "notes": "Completed chapters 1-5 of the Python course. Built my first simple calculator app!",
  "mood": "motivated"
}
```

**Parameters:**
- `progress_percentage` (integer, required): Current progress (0-100)
- `notes` (string, optional): Description of what was accomplished
- `mood` (string, optional): How you feel about the progress

**Response:**
```json
{
  "progress_id": "cc0e8400-e29b-41d4-a716-446655440007",
  "goal_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "progress_percentage": 50,
  "notes": "Completed chapters 1-5 of the Python course. Built my first simple calculator app!",
  "mood": "motivated",
  "created_at": "2024-03-05T14:20:00Z"
}
```

**Full Example:**
```bash
curl -X POST http://localhost:8000/goals/aa0e8400-e29b-41d4-a716-446655440005/progress \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "progress_percentage": 50,
    "notes": "Completed 5 chapters today!",
    "mood": "motivated"
  }'
```

**Python Example:**
```python
import requests

goal_id = "aa0e8400-e29b-41d4-a716-446655440005"
response = requests.post(
    f"http://localhost:8000/goals/{goal_id}/progress",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "progress_percentage": 50,
        "notes": "Completed chapters 1-5 of the Python course",
        "mood": "motivated"
    }
)

progress = response.json()
print(f"Progress logged: {progress['progress_percentage']}%")
```

---

### 7.7 Get Progress History

**Purpose:** Get all progress updates for a specific goal.

**URL:** `GET http://localhost:8000/goals/{goal_id}/progress`

**Authentication:** Required

**Response:**
```json
{
  "goal_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "progress_entries": [
    {
      "progress_id": "cc0e8400-e29b-41d4-a716-446655440007",
      "progress_percentage": 50,
      "notes": "Completed chapters 1-5",
      "mood": "motivated",
      "created_at": "2024-03-05T14:20:00Z"
    },
    {
      "progress_id": "dd0e8400-e29b-41d4-a716-446655440008",
      "progress_percentage": 35,
      "notes": "Started the course",
      "mood": "excited",
      "created_at": "2024-03-01T10:30:00Z"
    }
  ],
  "total": 2
}
```

**Full Example:**
```bash
curl -X GET http://localhost:8000/goals/aa0e8400-e29b-41d4-a716-446655440005/progress \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 7.8 Get Goals Analytics

**Purpose:** Get aggregated analytics across all goals.

**URL:** `GET http://localhost:8000/goals/analytics`

**Authentication:** Required

**Response:**
```json
{
  "total_goals": 5,
  "active_goals": 3,
  "completed_goals": 2,
  "abandoned_goals": 0,
  "completion_rate": 0.4,
  "average_progress": 52.5,
  "goals_by_category": {
    "learning": 2,
    "health": 2,
    "career": 1
  },
  "goals_with_target_date": 4,
  "overdue_goals": 1,
  "on_track_goals": 2
}
```

**Full Example:**
```bash
curl -X GET http://localhost:8000/goals/analytics \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Python Example:**
```python
import requests

response = requests.get(
    "http://localhost:8000/goals/analytics",
    headers={"Authorization": f"Bearer {token}"}
)

analytics = response.json()
print(f"Total goals: {analytics['total_goals']}")
print(f"Completion rate: {analytics['completion_rate'] * 100}%")
print(f"Category breakdown: {analytics['goals_by_category']}")
```

---

### 7.9 Get Check-In Goals

**Purpose:** Get goals that are due for a check-in based on their frequency setting.

**URL:** `POST http://localhost:8000/goals/checkin`

**Authentication:** Required

**Response:**
```json
{
  "goals_due": [
    {
      "goal_id": "aa0e8400-e29b-41d4-a716-446655440005",
      "title": "Learn Python Programming",
      "category": "learning",
      "progress_percentage": 50,
      "last_check_in": "2024-03-01T10:30:00Z",
      "next_check_in": "2024-03-08T00:00:00Z",
      "days_since_last_update": 7
    }
  ],
  "total": 1
}
```

**Full Example:**
```bash
curl -X POST http://localhost:8000/goals/checkin \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/goals/checkin",
    headers={"Authorization": f"Bearer {token}"}
)

checkin = response.json()
for goal in checkin['goals_due']:
    print(f"Check-in needed: {goal['title']}")
```

---

## 8. Content Safety

### 8.1 Age Verification

**Purpose:** Verify user's age and set content restriction level.

**URL:** `POST http://localhost:8000/age-verification`

**Authentication:** Required

**Request Body:**
```json
{
  "birth_year": 1990,
  "agreed_to_terms": true
}
```

**Response:**
```json
{
  "verified": true,
  "age": 34,
  "content_level": "adult",
  "message": "Age verification successful"
}
```

**Full Example:**
```bash
curl -X POST http://localhost:8000/age-verification \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "birth_year": 1990,
    "agreed_to_terms": true
  }'
```

---

### 8.2 Get Content Classification

**Purpose:** Check the safety rating of a message.

**URL:** `GET http://localhost:8000/content/classification`

**Authentication:** Required

**Query Parameters:**
- `message` (string, required): The message to classify

**Response:**
```json
{
  "classification": "safe",
  "confidence": 0.95,
  "allowed": true
}
```

**Full Example:**
```bash
curl -X GET "http://localhost:8000/content/classification?message=Hello%20there" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 8.3 Get Session State

**Purpose:** Get current session configuration including age verification and content level.

**URL:** `GET http://localhost:8000/session/state`

**Authentication:** Required

**Response:**
```json
{
  "user_id": "alice",
  "age_verified": true,
  "content_level": "adult",
  "session_created": "2024-03-01T10:00:00Z"
}
```

**Full Example:**
```bash
curl -X GET http://localhost:8000/session/state \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 8.4 Get Content Audit Stats

**Purpose:** Get content moderation statistics (admin only).

**URL:** `GET http://localhost:8000/content/audit/stats`

**Authentication:** Required (admin)

**Response:**
```json
{
  "total_messages_audited": 1234,
  "flagged_messages": 15,
  "blocked_messages": 3,
  "safe_messages": 1216
}
```

**Full Example:**
```bash
curl -X GET http://localhost:8000/content/audit/stats \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

---

## 9. System Health

### 9.1 Health Check

**Purpose:** Check if the service is running and healthy.

**URL:** `GET http://localhost:8000/health`

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "version": "4.0.0",
  "database": true,
  "llm": true,
  "timestamp": "2024-03-01T10:30:00Z"
}
```

**Full Example:**
```bash
curl -X GET http://localhost:8000/health
```

**Python Example:**
```python
import requests

response = requests.get("http://localhost:8000/health")
health = response.json()
print(f"Status: {health['status']}")
print(f"Database: {'✓' if health['database'] else '✗'}")
print(f"LLM: {'✓' if health['llm'] else '✗'}")
```

---

### 9.2 Root Endpoint

**Purpose:** Get service information and available features.

**URL:** `GET http://localhost:8000/`

**Authentication:** Not required

**Response:**
```json
{
  "service": "AI Companion Service",
  "version": "4.0.0",
  "features": {
    "multi_user": true,
    "adaptive_communication": true,
    "emotion_detection": true,
    "personality_system": true,
    "goal_tracking": true,
    "content_safety": true,
    "memory_system": true
  },
  "documentation": "http://localhost:8000/docs"
}
```

**Full Example:**
```bash
curl -X GET http://localhost:8000/
```

---

## 📚 Complete Workflow Examples

### Example 1: Complete Chat Session

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Step 1: Create JWT token
token_response = requests.post(
    f"{BASE_URL}/auth/token",
    json={"user_id": "alice", "expires_in_hours": 24}
)
token = token_response.json()["access_token"]
print(f"Token created: {token[:20]}...")

# Step 2: Set personality
personality_response = requests.post(
    f"{BASE_URL}/personality",
    headers={"Authorization": f"Bearer {token}"},
    json={"archetype": "mentor"}
)
print(f"Personality: {personality_response.json()['archetype']}")

# Step 3: Set preferences
prefs_response = requests.post(
    f"{BASE_URL}/preferences",
    headers={"Authorization": f"Bearer {token}"},
    json={"communication_style": "technical"}
)
print(f"Style: {prefs_response.json()['communication_style']}")

# Step 4: Start chatting
import httpx
import asyncio

async def chat():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            'POST',
            f'{BASE_URL}/chat',
            json={"message": "Teach me about Python decorators"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60.0
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    if data['type'] == 'chunk':
                        print(data['content'], end='', flush=True)
                    elif data['type'] == 'done':
                        return data['conversation_id']

conversation_id = asyncio.run(chat())
print(f"\n\nConversation ID: {conversation_id}")
```

---

### Example 2: Goal Tracking Workflow

```python
import requests

BASE_URL = "http://localhost:8000"
token = "YOUR_TOKEN_HERE"
headers = {"Authorization": f"Bearer {token}"}

# Create a goal
goal_response = requests.post(
    f"{BASE_URL}/goals",
    headers=headers,
    json={
        "title": "Learn FastAPI",
        "description": "Build 3 API projects",
        "category": "learning",
        "target_date": "2024-06-30",
        "check_in_frequency": "weekly"
    }
)
goal = goal_response.json()
goal_id = goal["goal_id"]
print(f"Goal created: {goal['title']}")

# Add progress
progress_response = requests.post(
    f"{BASE_URL}/goals/{goal_id}/progress",
    headers=headers,
    json={
        "progress_percentage": 25,
        "notes": "Completed the tutorial section",
        "mood": "motivated"
    }
)
print(f"Progress: {progress_response.json()['progress_percentage']}%")

# Get analytics
analytics_response = requests.get(
    f"{BASE_URL}/goals/analytics",
    headers=headers
)
analytics = analytics_response.json()
print(f"Total goals: {analytics['total_goals']}")
print(f"Completion rate: {analytics['completion_rate'] * 100}%")
```

---

### Example 3: Emotion Tracking

```python
import requests

BASE_URL = "http://localhost:8000"
token = "YOUR_TOKEN_HERE"
headers = {"Authorization": f"Bearer {token}"}

# Chat and emotions are detected automatically
# ... chat with the AI ...

# Get emotion history
emotions_response = requests.get(
    f"{BASE_URL}/emotions/history",
    headers=headers,
    params={"limit": 10}
)
emotions = emotions_response.json()

for emotion in emotions['emotions']:
    print(f"{emotion['detected_at']}: {emotion['emotion']} ({emotion['confidence']:.2f})")

# Get statistics
stats_response = requests.get(
    f"{BASE_URL}/emotions/statistics",
    headers=headers
)
stats = stats_response.json()
print(f"\nMost common emotion: {stats['most_common_emotion']}")
print(f"Emotion counts: {stats['emotion_counts']}")
```

---

## 🔧 Error Handling

All endpoints return standard HTTP status codes:

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required/failed
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

**Error Response Format:**
```json
{
  "detail": "Error message here"
}
```

**Validation Error (422):**
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

---

## 📝 Notes for AI Integration

1. **Always use JWT tokens** for production (not X-User-Id header)
2. **Store conversation IDs** to continue conversations
3. **Handle SSE streams** properly for chat endpoint
4. **Implement retry logic** for rate limiting (429 errors)
5. **Set appropriate timeouts** (60s+ for chat streaming)
6. **Check health endpoint** before making requests
7. **Use async clients** (httpx, aiohttp) for better performance
8. **Handle errors gracefully** - parse error messages
9. **Respect rate limits** - default is 30 req/min for chat
10. **Store tokens securely** - never expose in logs or UI

---

## 🎯 Quick Start for AI

```python
# 1. Get token
token_resp = requests.post("http://localhost:8000/auth/token", 
                          json={"user_id": "user123"})
TOKEN = token_resp.json()["access_token"]

# 2. Chat
import httpx
async with httpx.AsyncClient() as client:
    async with client.stream('POST', 'http://localhost:8000/chat',
                            json={"message": "Hello!"},
                            headers={"Authorization": f"Bearer {TOKEN}"},
                            timeout=60.0) as resp:
        async for line in resp.aiter_lines():
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if data['type'] == 'chunk':
                    print(data['content'], end='')
```

---

**Last Updated:** January 2026  
**Service Version:** 4.0.0  
**API Documentation:** http://localhost:8000/docs


