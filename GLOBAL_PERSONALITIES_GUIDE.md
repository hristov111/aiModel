# Global Personalities Guide

## Overview

The system now supports **8 pre-defined global character personalities** that all users can chat with. Each character maintains separate memories for each user.

## Available Characters

| Name | Archetype | Description |
|------|-----------|-------------|
| **elara** | wise_mentor | Art enthusiast from Paris |
| **seraphina** | supportive_friend | Warm and caring companion |
| **isla** | calm_therapist | Patient and understanding listener |
| **lyra** | creative_partner | Imaginative creative collaborator |
| **aria** | enthusiastic_cheerleader | Energetic and encouraging supporter |
| **nova** | pragmatic_advisor | Practical and straightforward advisor |
| **juniper** | curious_student | Eager and inquisitive learner |
| **sloane** | professional_coach | Results-focused professional coach |

## How It Works

### Memory Isolation Per User

Each character maintains **separate memories for each user**:

```
User Alice chats with Elara → Memories: (alice_id, elara_id)
User Bob chats with Elara   → Memories: (bob_id, elara_id)
User Alice chats with Nova  → Memories: (alice_id, nova_id)
```

**Result:**
- Elara remembers different things about Alice and Bob
- Alice's conversations with Elara and Nova are completely separate

## Frontend Integration

### Updated Chat Request

Your frontend needs to include the `personality_name` field:

```json
{
  "message": "Hello, I'm working on a new art project",
  "personality_name": "elara",
  "system_prompt": "You are Elara, a 28-year-old art enthusiast from Paris...",
  "conversation_id": "uuid-if-continuing"
}
```

### API Endpoint

```
POST http://localhost:8000/chat
Headers:
  X-User-Id: <user_id>
  Content-Type: application/json

Body:
{
  "message": "user message here",
  "personality_name": "elara",  // ← Required for memory isolation
  "system_prompt": "...",       // ← From your Supabase
  "conversation_id": "..."      // ← Optional, for continuing conversation
}
```

### Example Frontend Code

```javascript
async function sendMessage(userId, characterName, message, systemPrompt) {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {
      'X-User-Id': userId,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      personality_name: characterName.toLowerCase(), // 'elara', 'seraphina', etc.
      system_prompt: systemPrompt, // Fetch this from your Supabase
    }),
  });

  return response;
}

// Usage
const character = 'elara';
const systemPrompt = await fetchFromSupabase(character); // Your Supabase fetch
await sendMessage('alice123', character, 'Hello!', systemPrompt);
```

## What Happens Behind the Scenes

1. **Frontend sends request** with `personality_name: "elara"`
2. **Backend finds** the global "elara" personality record
3. **Backend retrieves** memories for (current_user, elara_id)
4. **Backend uses** your system_prompt from Supabase (not modified)
5. **Backend generates** AI response with context
6. **Backend stores** new memories with (current_user, elara_id)

## Key Features

✅ **System prompt from Supabase** - Backend uses it exactly as provided  
✅ **Memory isolation per user** - Each user has separate memories with each character  
✅ **Memory isolation per character** - Each character remembers different things  
✅ **No extra setup** - 8 characters already created and ready to use  
✅ **Automatic fallback** - If personality_name not provided, works as before  

## Testing

You can verify memory isolation:

```bash
# User Alice talks to Elara
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: alice" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I work at Google",
    "personality_name": "elara",
    "system_prompt": "You are Elara..."
  }'

# User Bob talks to Elara
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: bob" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I work at Microsoft",
    "personality_name": "elara",
    "system_prompt": "You are Elara..."
  }'

# Verify: Elara should remember different jobs for Alice and Bob!
```

## Migration Applied

The system has been updated with migration `008_global_personalities`:
- ✅ Created system user
- ✅ Created 8 global personality records
- ✅ Updated services to fetch global personalities
- ✅ Memory isolation works per (user_id, personality_id)

## Character Name Matching

Character names are **case-insensitive**:
- `"elara"`, `"Elara"`, `"ELARA"` → all work
- Backend normalizes to lowercase for matching

## Next Steps

1. **Update your frontend** to include `personality_name` in chat requests
2. **Keep fetching system_prompt** from Supabase as you do now
3. **Test** with multiple users chatting with the same character
4. **Verify** memory isolation is working correctly

## Troubleshooting

**Issue:** "Personality not found"
- **Solution:** Check that `personality_name` matches one of the 8 characters (elara, seraphina, isla, lyra, aria, nova, juniper, sloane)

**Issue:** "Memories are shared between users"
- **Solution:** Verify that `X-User-Id` header is different for each user

**Issue:** "Character doesn't use Supabase persona"
- **Solution:** Make sure you're sending `system_prompt` in the request body

## Database Schema

```
users
├── id: uuid
└── external_user_id: "system" (for global personalities)

personality_profiles (8 global records)
├── id: uuid
├── user_id: system_user_id
├── personality_name: "elara", "seraphina", etc.
└── archetype: "wise_mentor", etc.

memories (per user + personality)
├── id: uuid
├── user_id: actual_user_id (alice, bob, etc.)
├── personality_id: elara_id, seraphina_id, etc.
└── content: "User works at Google"
```

This ensures that:
- Global personalities exist once in the database
- Each user's memories are isolated per personality
- Multiple users can chat with the same character safely

