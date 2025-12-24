# Content Routing System Guide

## Overview

This AI service implements a comprehensive content classification and routing system that intelligently handles different types of content, from safe conversations to explicit adult content. The system prioritizes safety, consent, and legal compliance while allowing appropriate content for verified adults.

## Architecture

### 4-Layer Detection System

#### Layer 1: Normalization
- **Unicode normalization (NFKC)** - Handles special characters
- **Leetspeak mapping** - Converts "s3x" → "sex", "p0rn" → "porn"
- **Emoji mapping** - Translates 🍆🍑💦 to their meanings
- **Spacing tricks** - Removes "s e x" → "sex"

#### Layer 2: Fast Rules (Immediate Escalation)
- **Age indicators** - Detects mentions of minors, schools, "barely legal"
- **Coercion indicators** - Identifies non-consensual language
- **Hard stops** - Immediately blocks prohibited content

#### Layer 3: Pattern-Based Classification
- **Explicit anatomy** - Recognizes anatomical terms
- **Sexual acts** - Identifies sexual content
- **Fetish indicators** - Detects BDSM, kink content
- **Suggestive content** - Finds romantic/flirty language

#### Layer 4: LLM Judge (Future)
- Optional LLM-based classification for borderline cases
- Currently using pattern-based classification

## Content Labels

### 6 Risk Levels

1. **SAFE** - Normal, appropriate content
2. **SUGGESTIVE** - Romantic, flirty content
3. **EXPLICIT_CONSENSUAL_ADULT** - Adult sexual content (consensual)
4. **EXPLICIT_FETISH** - Fetish/kink content (with guardrails)
5. **NONCONSENSUAL** - Non-consensual content (REFUSED)
6. **MINOR_RISK** - Age-ambiguous content (HARD REFUSED)

## Model Routing

### Route Mapping

| Content Label | Route | Model | Behavior |
|--------------|-------|-------|----------|
| SAFE | NORMAL | OpenAI | Standard assistant |
| SUGGESTIVE | ROMANCE | OpenAI | Flirty, romantic |
| EXPLICIT_CONSENSUAL_ADULT | EXPLICIT | Local (uncensored) | Adult content allowed |
| EXPLICIT_FETISH | FETISH | Local (uncensored) | Kink with strict rules |
| NONCONSENSUAL | REFUSAL | OpenAI | Refuses request |
| MINOR_RISK | HARD_REFUSAL | OpenAI | Hard refusal |

### System Prompts

Each route has a custom system prompt:

- **NORMAL**: Helpful AI assistant
- **ROMANCE**: Warm, flirtatious companion
- **EXPLICIT**: Adult companion with consent rules
- **FETISH**: Kink-aware with SSC/RACK principles
- **REFUSAL**: Polite refusal message
- **HARD_REFUSAL**: Firm boundary statement

## Age Verification

### Requirements

- **Explicit routes require age verification**
- **One-time confirmation per session**
- **Cached per conversation**
- **Tracks verification attempts**

### Flow

1. User sends explicit content
2. System detects → routes to EXPLICIT
3. Checks age verification status
4. If not verified:
   - Returns age verification prompt
   - Tracks attempt count
   - Waits for confirmation
5. User confirms age (18+)
6. Session marked as verified
7. Explicit content allowed

### API Endpoint

```bash
POST /api/content/age-verify
{
  "conversation_id": "uuid",
  "confirmed": true
}
```

## Session Management

### Session Lock-In

Once a conversation enters explicit mode, it stays there for **5 messages** to prevent:
- Tone breaks
- Context confusion
- Accidental mode switching

### Session State

```python
{
  "conversation_id": "uuid",
  "age_verified": true,
  "current_route": "EXPLICIT",
  "route_locked": true,
  "route_lock_message_count": 3
}
```

### Session Timeout

Sessions expire after **24 hours** of inactivity.

## Audit Logging

### What's Logged

Every classification is logged with:
- Original text (truncated)
- Normalized text
- Classification label & confidence
- Indicators that triggered classification
- Route chosen
- Action taken (generate/refuse/age_verify)
- Age verification status
- Session state

### Log Format

```json
{
  "timestamp": "2025-12-24T10:30:00Z",
  "conversation_id": "uuid",
  "user_id": "uuid",
  "label": "EXPLICIT_CONSENSUAL_ADULT",
  "confidence": 0.85,
  "indicators": ["anatomy: penis", "sexual_act: sex"],
  "route": "EXPLICIT",
  "route_locked": true,
  "age_verified": true,
  "action": "generate"
}
```

### Use Cases

- Platform reviews
- User complaints
- False positive/negative tuning
- Compliance audits

## API Endpoints

### 1. Age Verification

```bash
POST /api/content/age-verify
Content-Type: application/json
X-User-Id: your-user-id

{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "confirmed": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Age verified successfully",
  "age_verified": true
}
```

### 2. Get Session State

```bash
GET /api/content/session/{conversation_id}
X-User-Id: your-user-id
```

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "age_verified": true,
  "current_route": "EXPLICIT",
  "route_locked": true,
  "route_lock_message_count": 3
}
```

### 3. Classify Content

```bash
POST /api/content/classify
Content-Type: application/json
X-User-Id: your-user-id

{
  "message": "Your message here"
}
```

**Response:**
```json
{
  "label": "EXPLICIT_CONSENSUAL_ADULT",
  "confidence": 0.85,
  "indicators": ["anatomy: penis", "sexual_act: sex"],
  "route": "EXPLICIT"
}
```

### 4. Get Audit Statistics

```bash
GET /api/content/audit/stats
X-User-Id: your-user-id
```

**Response:**
```json
{
  "total_logs": 1000,
  "label_distribution": {
    "SAFE": 800,
    "SUGGESTIVE": 150,
    "EXPLICIT_CONSENSUAL_ADULT": 45,
    "EXPLICIT_FETISH": 3,
    "NONCONSENSUAL": 1,
    "MINOR_RISK": 1
  },
  "route_distribution": {
    "NORMAL": 800,
    "ROMANCE": 150,
    "EXPLICIT": 45,
    "FETISH": 3,
    "REFUSAL": 1,
    "HARD_REFUSAL": 1
  },
  "action_distribution": {
    "generate": 995,
    "refuse": 2,
    "age_verify": 3
  }
}
```

### 5. Clear Session

```bash
POST /api/content/session/{conversation_id}/clear
X-User-Id: your-user-id
```

**Response:**
```json
{
  "success": true,
  "message": "Session cleared successfully"
}
```

## Configuration

### Environment Variables

```bash
# Content Routing
CONTENT_ROUTING_ENABLED=true
CONTENT_AUDIT_LOG_FILE=content_audit.log
SESSION_TIMEOUT_HOURS=24
ROUTE_LOCK_MESSAGE_COUNT=5

# LM Studio (for explicit content)
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL_NAME=local-model
LM_STUDIO_TEMPERATURE=0.8
LM_STUDIO_MAX_TOKENS=2000

# OpenAI (for safe content)
OPENAI_API_KEY=your-key-here
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
```

## Safety Rules

### Hard Boundaries (NEVER ALLOWED)

1. **Minor-related content** - Any age-ambiguous scenarios
2. **Non-consensual content** - Coercion, force, assault
3. **Illegal content** - Anything illegal in any jurisdiction

### Explicit Content Rules

When explicit content is allowed:

✅ **Allowed:**
- Consensual adult sexual content
- Explicit anatomical language
- Fetish/kink with SSC/RACK principles
- Roleplay between adults

❌ **Not Allowed:**
- Non-consensual acts
- Age ambiguity
- Permanent harm
- Extreme degradation
- Power imbalance exploitation

## Testing

### Test Cases

```python
# Test 1: Safe content
message = "How do I learn Python?"
# Expected: SAFE → NORMAL route

# Test 2: Suggestive content
message = "You're so charming and attractive"
# Expected: SUGGESTIVE → ROMANCE route

# Test 3: Explicit content (age verified)
message = "I want to have sex with you"
# Expected: EXPLICIT_CONSENSUAL_ADULT → EXPLICIT route

# Test 4: Fetish content (age verified)
message = "I'm interested in BDSM roleplay"
# Expected: EXPLICIT_FETISH → FETISH route

# Test 5: Non-consensual (REFUSED)
message = "Let's roleplay a forced scenario"
# Expected: NONCONSENSUAL → REFUSAL

# Test 6: Minor risk (HARD REFUSED)
message = "Let's roleplay as teenagers"
# Expected: MINOR_RISK → HARD_REFUSAL
```

### Testing Script

```bash
# Test classification
curl -X POST http://localhost:8000/api/content/classify \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{"message": "Your test message"}'

# Test age verification
curl -X POST http://localhost:8000/api/content/age-verify \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{"conversation_id": "uuid", "confirmed": true}'

# Get session state
curl http://localhost:8000/api/content/session/{conversation_id} \
  -H "X-User-Id: test-user"
```

## Frontend Integration

### Age Verification Flow

```javascript
// Detect age verification prompt
if (event.type === 'thinking' && event.step === 'age_verification_required') {
  // Show age verification UI
  showAgeVerificationDialog(conversationId);
}

// Handle age confirmation
async function confirmAge(conversationId, confirmed) {
  const response = await fetch('/api/content/age-verify', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': userId
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      confirmed: confirmed
    })
  });
  
  const result = await response.json();
  if (result.age_verified) {
    // Retry original message
    sendMessage(originalMessage);
  }
}
```

### Content Warning Display

```javascript
// Show content routing info
if (event.type === 'thinking' && event.step === 'content_routed') {
  const { label, route, confidence } = event.data;
  
  if (route === 'EXPLICIT' || route === 'FETISH') {
    showContentWarning('Adult content mode active');
  }
}
```

## Monitoring

### Key Metrics

1. **Classification accuracy** - Review audit logs
2. **False positives** - Safe content marked explicit
3. **False negatives** - Explicit content marked safe
4. **Age verification rate** - How many users verify
5. **Refusal rate** - How often content is refused

### Dashboard Queries

```python
# Get audit stats
stats = audit_logger.get_stats()

# Recent classifications
recent = audit_logger.get_recent_logs(limit=100)

# Filter by label
explicit_logs = [log for log in recent if log['label'] == 'EXPLICIT_CONSENSUAL_ADULT']

# Refusal analysis
refusals = [log for log in recent if log['action'] == 'refuse']
```

## Troubleshooting

### Issue: Age verification not working

**Solution:**
- Check session state: `GET /api/content/session/{conversation_id}`
- Verify conversation ownership
- Clear session and retry: `POST /api/content/session/{conversation_id}/clear`

### Issue: Content misclassified

**Solution:**
- Check audit logs for indicators
- Review normalization layer
- Adjust pattern thresholds
- Add to clinical context if false positive

### Issue: Route locked unexpectedly

**Solution:**
- Check `route_lock_message_count` in session state
- Wait for lock to expire (5 messages)
- Or clear session to reset

## Best Practices

1. **Always log classifications** - Essential for tuning
2. **Monitor false positives** - Especially clinical/medical content
3. **Review refusals** - Ensure legitimate refusals
4. **Test edge cases** - Leetspeak, emojis, spacing tricks
5. **Update patterns** - Add new indicators as discovered
6. **Respect boundaries** - Never compromise on MINOR_RISK or NONCONSENSUAL

## Future Enhancements

1. **LLM-based classification** - Layer 4 for borderline cases
2. **User feedback** - Allow users to report misclassifications
3. **Adaptive thresholds** - Learn from user patterns
4. **Multi-language support** - Extend to other languages
5. **Image classification** - Handle image content
6. **Real-time monitoring** - Dashboard for live metrics

## Support

For issues or questions:
- Check audit logs: `/api/content/audit/stats`
- Review session state: `/api/content/session/{conversation_id}`
- Test classification: `/api/content/classify`
- Clear session if stuck: `/api/content/session/{conversation_id}/clear`

## Legal Compliance

This system is designed to:
- ✅ Prevent minor-related content
- ✅ Block non-consensual content
- ✅ Require age verification for adult content
- ✅ Log all decisions for audit
- ✅ Respect user boundaries

**Note:** This is a technical implementation. Consult legal counsel for compliance with local laws and regulations.

