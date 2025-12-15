# User Communication Preferences Guide

## 🎯 Overview

The AI Companion Service now supports **hard-enforced communication preferences**! Tell the AI how you want it to talk to you, and it will **consistently** follow your preferences in every conversation.

## ✨ Features

### Auto-Detection
- ✅ AI automatically detects preference requests from your messages
- ✅ "I prefer casual conversation" → Stored automatically
- ✅ "Use emojis please" → Applied immediately
- ✅ "Be more formal" → Updated preferences

### Hard Enforcement
- ✅ Preferences are **REQUIRED instructions**, not suggestions
- ✅ Consistent behavior across all conversations
- ✅ Takes precedence over default behavior

### Change Anytime
- ✅ Update preferences whenever you want
- ✅ New preferences override old ones
- ✅ Clear all preferences to reset to defaults

## 📋 Supported Preferences

### 1. Language
Choose which language the AI speaks:
- **English** (default)
- **Spanish**
- **French**
- **German**
- **Italian**
- **Portuguese**

```bash
# Via natural language
"Speak Spanish to me"
"Talk in French"

# Via API
{"language": "Spanish"}
```

### 2. Formality
Control how formal or casual the AI sounds:
- **casual** - Relaxed, uses contractions, friendly
- **formal** - Polite, no contractions, respectful
- **professional** - Business tone, corporate language

```bash
# Natural language
"Be more casual"
"Speak formally please"
"Use professional language"

# API
{"formality": "casual"}
```

### 3. Tone
Set the emotional tone:
- **enthusiastic** - Energetic, excited, positive
- **calm** - Measured, steady, composed
- **friendly** - Warm, welcoming, kind
- **neutral** - Objective, unemotional

```bash
# Natural language
"Be enthusiastic!"
"Keep it calm"
"Be friendly"

# API
{"tone": "enthusiastic"}
```

### 4. Emoji Usage
Control emoji use:
- **true** - Include emojis
- **false** - No emojis

```bash
# Natural language
"Use emojis"
"No emojis please"
"I like emojis"

# API
{"emoji_usage": true}
```

### 5. Response Length
Control how long responses are:
- **brief** - Short, concise (2-3 sentences)
- **detailed** - Long, thorough explanations
- **balanced** - Medium length (default)

```bash
# Natural language
"Keep it brief"
"Be more detailed"
"Give balanced responses"

# API
{"response_length": "brief"}
```

### 6. Explanation Style
Choose how concepts are explained:
- **simple** - Easy terms, no jargon (ELI5 style)
- **technical** - Technical terminology, precise
- **analogies** - Use metaphors and comparisons

```bash
# Natural language
"Explain simply"
"Get technical"
"Use analogies"

# API
{"explanation_style": "simple"}
```

## 🚀 Usage

### Method 1: Natural Language (Auto-Detection)

Just tell the AI your preferences in conversation:

```bash
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: alice" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I prefer you to speak Spanish in a casual, enthusiastic way with emojis"
  }'
```

**The AI automatically:**
1. Detects the preferences
2. Stores them to your profile
3. Applies them immediately
4. Uses them in ALL future conversations

### Method 2: API Endpoint (Explicit)

Set preferences directly via API:

```bash
# Set preferences
curl -X POST http://localhost:8000/preferences \
  -H "X-User-Id: alice" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "Spanish",
    "formality": "casual",
    "tone": "enthusiastic",
    "emoji_usage": true,
    "response_length": "balanced",
    "explanation_style": "simple"
  }'
```

### View Current Preferences

```bash
curl http://localhost:8000/preferences \
  -H "X-User-Id: alice"
```

**Response:**
```json
{
  "preferences": {
    "language": "Spanish",
    "formality": "casual",
    "tone": "enthusiastic",
    "emoji_usage": true,
    "response_length": "balanced",
    "explanation_style": "simple",
    "last_updated": "2024-01-15T10:30:00"
  },
  "message": "Preferences retrieved successfully"
}
```

### Update Specific Preferences

```bash
# Only update tone (keeps other preferences)
curl -X POST http://localhost:8000/preferences \
  -H "X-User-Id: alice" \
  -H "Content-Type: application/json" \
  -d '{"tone": "calm"}'
```

### Clear All Preferences

```bash
curl -X DELETE http://localhost:8000/preferences \
  -H "X-User-Id: alice"
```

## 📝 Examples

### Example 1: Professional User

```bash
# Set preferences
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: bob" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Please be professional and formal. No emojis. Give detailed responses."
  }'

# All future responses will be:
# - Professional business tone
# - Formal language
# - No emojis
# - Detailed explanations
```

### Example 2: Casual Learner

```bash
# Set preferences
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: carol" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Talk casually to me, use emojis, and explain things simply with analogies"
  }'

# All future responses will be:
# - Casual, friendly tone
# - Includes emojis 😊
# - Simple explanations
# - Uses analogies and metaphors
```

### Example 3: Changing Your Mind

```bash
# Day 1: Set casual
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: dave" \
  -d '{"message": "Be casual with me"}'

# Day 2: Change to formal
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: dave" \
  -d '{"message": "Actually, be more formal from now on"}'

# ✅ The AI immediately switches to formal language
```

## 🔍 How It Works

### Behind the Scenes

1. **Message Received** → "I prefer casual language"
   
2. **Preference Extraction** → Detects: `{formality: "casual"}`
   
3. **Storage** → Saved to `users.metadata.communication_preferences`
   
4. **Prompt Building** → Adds HARD ENFORCEMENT rules:
   ```
   ⚠️ CRITICAL COMMUNICATION REQUIREMENTS (MUST FOLLOW):
   💬 FORMALITY: Use casual, informal language. 
   Use contractions (you're, I'm, don't). Be relaxed and friendly.
   ```
   
5. **LLM Response** → MUST follow the rules

6. **Future Chats** → Preferences automatically applied

### Enforcement Level

**Before (Soft):**
```
Relevant memories:
- User prefers casual conversation

Instructions:
- Be helpful and conversational
```
→ LLM might ignore the preference

**After (HARD):**
```
⚠️ CRITICAL COMMUNICATION REQUIREMENTS (MUST FOLLOW):
💬 FORMALITY: Use casual, informal language. 
Use contractions (you're, I'm, don't).
```
→ LLM MUST follow this

## 🎯 Detection Patterns

The system detects these phrases:

**Language:**
- "speak spanish"
- "talk in french"
- "use german"
- "en español"

**Formality:**
- "be casual"
- "speak formally"
- "don't be so formal"
- "professional manner"

**Tone:**
- "be enthusiastic"
- "keep it calm"
- "be friendly"
- "stay neutral"

**Emojis:**
- "use emojis"
- "no emojis"
- "I like emojis"

**Length:**
- "keep it brief"
- "be more detailed"
- "short answers"

**Style:**
- "explain simply"
- "get technical"
- "use analogies"

## 💡 Best Practices

### ✅ DO:
- Be specific: "I prefer casual Spanish with emojis"
- Update anytime: "Actually, be more formal now"
- Mix methods: Natural language + API
- Test preferences: Ask "How would you describe yourself?"

### ❌ DON'T:
- Don't expect instant language fluency (depends on LLM model)
- Don't set conflicting preferences ("casual" + "formal")
- Don't expect perfect consistency (LLM-dependent)

## 🔧 Technical Details

### Storage

Preferences are stored in the `users` table:

```sql
SELECT metadata->'communication_preferences' 
FROM users 
WHERE external_user_id = 'alice';
```

### Data Structure

```json
{
  "communication_preferences": {
    "language": "Spanish",
    "formality": "casual",
    "tone": "enthusiastic",
    "emoji_usage": true,
    "response_length": "balanced",
    "explanation_style": "simple",
    "last_updated": "2024-01-15T10:30:00.000Z"
  }
}
```

### Priority

1. **User Preferences** (highest priority)
2. Conversation context
3. Relevant memories
4. Default system persona

## 🎓 Advanced Usage

### Python Client

```python
class AIClient:
    def __init__(self, user_id):
        self.user_id = user_id
        self.base_url = "http://localhost:8000"
    
    def set_preferences(self, **prefs):
        """Set communication preferences."""
        response = requests.post(
            f"{self.base_url}/preferences",
            headers={"X-User-Id": self.user_id},
            json=prefs
        )
        return response.json()
    
    def chat(self, message):
        """Chat with preferences applied."""
        response = requests.post(
            f"{self.base_url}/chat",
            headers={"X-User-Id": self.user_id},
            json={"message": message}
        )
        return response

# Usage
client = AIClient("alice")
client.set_preferences(
    language="Spanish",
    tone="friendly",
    emoji_usage=True
)
client.chat("Hello!")  # Responds in Spanish with friendly tone and emojis
```

## 🆘 Troubleshooting

**Preferences not applied?**
- Check: `GET /preferences` to verify they're stored
- Wait: First message after setting may not apply (next one will)
- Model: Some LLM models follow instructions better than others

**AI not following preferences?**
- Check LM Studio model quality
- Try more explicit: "You MUST speak Spanish"
- Use API endpoint for guaranteed storage

**Want to reset?**
- `DELETE /preferences` clears all
- Or chat: "Forget my preferences"

## 📚 See Also

- [AUTHENTICATION.md](AUTHENTICATION.md) - User authentication
- [README.md](README.md) - Main documentation
- [API_EXAMPLES.md](API_EXAMPLES.md) - More examples

---

**Version**: 2.1.0  
**Feature**: Adaptive Communication with Hard Preference Enforcement

