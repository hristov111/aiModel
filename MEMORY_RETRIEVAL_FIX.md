# Memory Retrieval Fix Guide

## 🔴 Problem

Memories are **NOT being retrieved** because they're stored without `personality_id`.

## 🔍 Root Cause

Your frontend is **NOT sending** the `personality_name` parameter in chat requests.

### Current Database State:
```sql
SELECT personality_name, COUNT(*) FROM memories 
LEFT JOIN personality_profiles ON memories.personality_id = personality_profiles.id
GROUP BY personality_name;

personality_name | count
-----------------+-------
                 |  13   ← NULL personality_id (can't be retrieved!)
elara            |   2   ← Has personality_id (can be retrieved!)
```

## ✅ Solution

**Add `personality_name` to EVERY chat request from your frontend.**

### Before (Not Working):
```javascript
const response = await fetch('/chat', {
  method: 'POST',
  headers: {
    'X-User-Id': userId,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: userMessage,
    system_prompt: systemPromptFromSupabase  // ← Missing personality_name!
  })
});
```

### After (Working):
```javascript
const response = await fetch('/chat', {
  method: 'POST',
  headers: {
    'X-User-Id': userId,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: userMessage,
    personality_name: currentPersonality,  // ← ADD THIS! (e.g., "elara", "seraphina")
    system_prompt: systemPromptFromSupabase
  })
});
```

## 📝 Implementation Steps

### 1. Update Your Frontend Code

Find where you make the `/chat` API call and add `personality_name`:

```javascript
// Example: When user chats with a specific character
function sendMessageToCharacter(message, characterName) {
  const payload = {
    message: message,
    personality_name: characterName.toLowerCase(),  // "Elara" → "elara"
    system_prompt: getSystemPromptFor(characterName)
  };
  
  // Include conversation_id if continuing conversation
  if (currentConversationId) {
    payload.conversation_id = currentConversationId;
  }
  
  return fetch('/chat', {
    method: 'POST',
    headers: {
      'X-User-Id': getCurrentUserId(),
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });
}
```

### 2. Character Name Mapping

The 8 personality names (must match database):
```javascript
const CHARACTER_NAMES = {
  'Elara': 'elara',
  'Seraphina': 'seraphina',
  'Isla': 'isla',
  'Lyra': 'lyra',
  'Aria': 'aria',
  'Nova': 'nova',
  'Juniper': 'juniper',
  'Sloane': 'sloane'
};

// Use it:
const personality_name = CHARACTER_NAMES[selectedCharacter];
```

### 3. Maintain Conversation Continuity

```javascript
// Per-character conversation tracking
let conversationsByCharacter = {
  'elara': null,
  'seraphina': null,
  // ... etc
};

async function sendMessage(message, character) {
  const personality = character.toLowerCase();
  
  const payload = {
    message: message,
    personality_name: personality,
    system_prompt: await fetchSystemPromptFromSupabase(character)
  };
  
  // Reuse conversation if exists
  if (conversationsByCharacter[personality]) {
    payload.conversation_id = conversationsByCharacter[personality];
  }
  
  const response = await fetch('/chat', {
    method: 'POST',
    headers: {
      'X-User-Id': userId,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });
  
  // Save conversation_id for next message
  const data = await response.json();
  if (data.conversation_id) {
    conversationsByCharacter[personality] = data.conversation_id;
  }
  
  return response;
}

// Reset when user explicitly starts new conversation
function startNewConversation(character) {
  const personality = character.toLowerCase();
  conversationsByCharacter[personality] = null;
}
```

## 🧪 Testing

### Test 1: Verify personality_name is being sent

Open browser dev tools → Network tab → Send a message → Check request payload:

```json
{
  "message": "Hello",
  "personality_name": "elara",  // ← Should be present!
  "system_prompt": "You are Elara..."
}
```

### Test 2: Verify memories are stored with personality_id

After sending 3+ messages in same conversation, check database:

```bash
docker exec ai_companion_db_dev psql -U postgres -d ai_companion -c "
SELECT 
    pp.personality_name,
    m.content,
    m.created_at
FROM memories m
LEFT JOIN personality_profiles pp ON m.personality_id = pp.id
ORDER BY m.created_at DESC
LIMIT 5;
"
```

**Should see:**
```
personality_name | content          | created_at
-----------------+------------------+------------
elara            | User likes...    | 2026-01-08...
elara            | User works at... | 2026-01-08...
```

### Test 3: Verify memory retrieval works

Send 3+ messages, then ask: "What did I tell you about myself?"

**Expected:** AI should recall the information.

## 🎯 Quick Fix Checklist

- [ ] Add `personality_name` to chat request payload
- [ ] Map character display names to lowercase personality names
- [ ] Reuse `conversation_id` across messages with same character
- [ ] Test in browser dev tools (check Network tab)
- [ ] Verify database shows `personality_name` is not NULL
- [ ] Test memory recall after 3+ messages

## ❓ Debugging

### If memories still aren't being retrieved:

1. **Check if personality_name is being sent:**
   ```bash
   # Monitor API requests
   docker logs ai_companion_service_dev -f | grep personality_name
   ```

2. **Check if memories have personality_id:**
   ```bash
   docker exec ai_companion_db_dev psql -U postgres -d ai_companion -c "
   SELECT COUNT(*), 
          CASE WHEN personality_id IS NULL THEN 'NULL' ELSE 'SET' END as status
   FROM memories 
   GROUP BY status;
   "
   ```

3. **Check conversation continuity:**
   ```bash
   # Should see multiple messages with same conversation_id
   docker logs ai_companion_service_dev -f | grep "conversation:"
   ```

## 📚 Reference

- **API Endpoint:** `POST /chat`
- **Required Headers:** `X-User-Id`
- **Required Payload:**
  - `message` (string): User's message
  - `personality_name` (string): Character name in lowercase
- **Optional Payload:**
  - `conversation_id` (UUID): To continue existing conversation
  - `system_prompt` (string): Custom system prompt from Supabase

## 🎉 Expected Result

Once fixed:
- ✅ Memories stored with `personality_id`
- ✅ Memories retrieved per personality
- ✅ Each character remembers only what you told them
- ✅ Perfect memory isolation between characters

---

**Bottom Line:** Your backend is working perfectly. The issue is that the frontend isn't sending `personality_name`, so memories are stored without `personality_id` and can't be retrieved. Add one field to your API calls and everything will work!

