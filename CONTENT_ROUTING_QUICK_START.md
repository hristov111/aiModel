# Content Routing Quick Start

## What is it?

A smart content classification system that:
- Detects explicit content
- Routes to appropriate models
- Requires age verification for adult content
- Blocks prohibited content (minors, non-consensual)

## 6 Content Labels

1. **SAFE** → Normal AI assistant
2. **SUGGESTIVE** → Romantic/flirty mode
3. **EXPLICIT_CONSENSUAL_ADULT** → Adult content (age verified)
4. **EXPLICIT_FETISH** → Kink content (age verified, strict rules)
5. **NONCONSENSUAL** → ❌ REFUSED
6. **MINOR_RISK** → ❌ HARD REFUSED

## Quick Test

```bash
# 1. Test classification
curl -X POST http://localhost:8000/api/content/classify \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{"message": "I want to have sex"}'

# Response:
# {
#   "label": "EXPLICIT_CONSENSUAL_ADULT",
#   "confidence": 0.85,
#   "route": "EXPLICIT"
# }

# 2. Verify age (required for explicit)
curl -X POST http://localhost:8000/api/content/age-verify \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{
    "conversation_id": "your-conversation-id",
    "confirmed": true
  }'

# 3. Check session state
curl http://localhost:8000/api/content/session/your-conversation-id \
  -H "X-User-Id: test-user"

# Response:
# {
#   "age_verified": true,
#   "current_route": "EXPLICIT",
#   "route_locked": true,
#   "route_lock_message_count": 5
# }
```

## How It Works

### Normal Flow
```
User: "How do I learn Python?"
  ↓
Classify: SAFE (0.95)
  ↓
Route: NORMAL (OpenAI)
  ↓
Generate: Standard assistant response
```

### Explicit Flow (First Time)
```
User: "I want to have sex"
  ↓
Classify: EXPLICIT_CONSENSUAL_ADULT (0.85)
  ↓
Route: EXPLICIT
  ↓
Check: Age verified? NO
  ↓
Return: "Are you 18 years of age or older?"
  ↓
User confirms age
  ↓
Generate: Adult content (local uncensored model)
  ↓
Lock route for 5 messages
```

### Refused Flow
```
User: "Let's roleplay as teenagers"
  ↓
Classify: MINOR_RISK (1.0)
  ↓
Route: HARD_REFUSAL
  ↓
Return: "I cannot engage with any content involving minors..."
```

## Key Features

### 1. Multi-Layer Detection
- Normalizes text (leetspeak, emojis, spacing)
- Fast rules (age, coercion indicators)
- Pattern matching (anatomy, acts, fetishes)
- LLM judge (future)

### 2. Age Verification
- Required for explicit routes
- One-time per session
- Cached per conversation
- Tracks attempts

### 3. Session Lock-In
- Stays in explicit mode for 5 messages
- Prevents tone breaks
- Auto-expires

### 4. Audit Logging
- Every classification logged
- Includes indicators, confidence, route
- Useful for tuning and compliance

## Configuration

Add to `.env`:

```bash
# Content Routing
CONTENT_ROUTING_ENABLED=true
CONTENT_AUDIT_LOG_FILE=content_audit.log
SESSION_TIMEOUT_HOURS=24
ROUTE_LOCK_MESSAGE_COUNT=5

# Local Model (for explicit)
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL_NAME=local-model

# OpenAI (for safe content)
OPENAI_API_KEY=your-key-here
OPENAI_MODEL_NAME=gpt-4o-mini
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/content/age-verify` | POST | Verify user is 18+ |
| `/api/content/session/{id}` | GET | Get session state |
| `/api/content/classify` | POST | Test classification |
| `/api/content/audit/stats` | GET | Get statistics |
| `/api/content/session/{id}/clear` | POST | Reset session |

## Frontend Integration

### Detect Age Verification Prompt

```javascript
// In your chat event handler
if (event.type === 'thinking' && 
    event.step === 'age_verification_required') {
  
  // Show age verification dialog
  showAgeDialog(conversationId);
}
```

### Handle Age Confirmation

```javascript
async function confirmAge(conversationId) {
  const response = await fetch('/api/content/age-verify', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': userId
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      confirmed: true
    })
  });
  
  if (response.ok) {
    // Retry original message
    sendMessage(originalMessage);
  }
}
```

### Show Content Warning

```javascript
if (event.type === 'thinking' && 
    event.step === 'content_routed') {
  
  const { route } = event.data;
  
  if (route === 'EXPLICIT' || route === 'FETISH') {
    showWarning('🔞 Adult content mode active');
  }
}
```

## Safety Rules

### ✅ Allowed (with age verification)
- Consensual adult sexual content
- Explicit language between adults
- Fetish/kink with consent
- Adult roleplay

### ❌ Never Allowed
- Minor-related content
- Non-consensual scenarios
- Coercion or force
- Age-ambiguous situations

## Troubleshooting

### "Age verification required" keeps appearing

**Solution:**
```bash
# Check if age was verified
curl http://localhost:8000/api/content/session/{conversation_id} \
  -H "X-User-Id: test-user"

# If age_verified is false, verify again
curl -X POST http://localhost:8000/api/content/age-verify \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{"conversation_id": "{conversation_id}", "confirmed": true}'
```

### Content misclassified

**Solution:**
```bash
# Test classification
curl -X POST http://localhost:8000/api/content/classify \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{"message": "your message"}'

# Check indicators and confidence
# If false positive, may need to adjust patterns
```

### Route stuck in explicit mode

**Solution:**
```bash
# Check lock status
curl http://localhost:8000/api/content/session/{conversation_id} \
  -H "X-User-Id: test-user"

# Wait for lock to expire (5 messages) or clear session
curl -X POST http://localhost:8000/api/content/session/{conversation_id}/clear \
  -H "X-User-Id: test-user"
```

## Monitoring

### View Statistics

```bash
curl http://localhost:8000/api/content/audit/stats \
  -H "X-User-Id: test-user"
```

**Response:**
```json
{
  "total_logs": 1000,
  "label_distribution": {
    "SAFE": 800,
    "SUGGESTIVE": 150,
    "EXPLICIT_CONSENSUAL_ADULT": 45
  },
  "route_distribution": {
    "NORMAL": 800,
    "ROMANCE": 150,
    "EXPLICIT": 45
  },
  "action_distribution": {
    "generate": 995,
    "refuse": 2,
    "age_verify": 3
  }
}
```

### Check Audit Logs

```bash
# View recent logs
tail -f content_audit.log | jq '.'
```

## Example Scenarios

### Scenario 1: Learning Python (SAFE)
```
User: "How do I learn Python?"
System: SAFE → NORMAL → OpenAI
Response: "Here's how to get started with Python..."
```

### Scenario 2: Flirting (SUGGESTIVE)
```
User: "You're so charming and attractive"
System: SUGGESTIVE → ROMANCE → OpenAI
Response: "Why thank you! You're quite charming yourself..."
```

### Scenario 3: Explicit Request (First Time)
```
User: "I want to have sex with you"
System: EXPLICIT_CONSENSUAL_ADULT → EXPLICIT
System: Age verified? NO
Response: "Are you 18 years of age or older?"
User: "yes"
System: Age verified ✓
System: EXPLICIT → Local Model
Response: [Adult content response]
[Route locked for 5 messages]
```

### Scenario 4: Non-Consensual (REFUSED)
```
User: "Let's roleplay a forced scenario"
System: NONCONSENSUAL → REFUSAL
Response: "I cannot engage with content involving non-consensual activities..."
```

### Scenario 5: Minor Risk (HARD REFUSED)
```
User: "Let's roleplay as high school students"
System: MINOR_RISK → HARD_REFUSAL
Response: "I cannot engage with any content involving minors..."
```

## Next Steps

1. **Test the system** - Try different content types
2. **Monitor logs** - Check `content_audit.log`
3. **Review stats** - Use `/api/content/audit/stats`
4. **Tune patterns** - Adjust if needed
5. **Integrate frontend** - Add age verification UI

## Full Documentation

See `CONTENT_ROUTING_GUIDE.md` for complete details.

## Support

- Check audit logs for classification details
- Test with `/api/content/classify`
- Review session state with `/api/content/session/{id}`
- Clear session if stuck with `/api/content/session/{id}/clear`

