# Content Routing System - Implementation Summary

## Overview

Successfully implemented a comprehensive content classification and routing system that intelligently handles different types of content while prioritizing safety, consent, and legal compliance.

## What Was Built

### 1. Content Classifier (`app/services/content_classifier.py`)

**4-Layer Detection System:**

- **Layer 1: Normalization**
  - Unicode NFKC normalization
  - Leetspeak mapping (s3x → sex, p0rn → porn)
  - Emoji mapping (🍆🍑💦 → meanings)
  - Spacing trick removal (s e x → sex)

- **Layer 2: Fast Rules (Immediate Escalation)**
  - Age indicators (teen, school, barely legal)
  - Coercion indicators (forced, drugged, non-consensual)
  - Hard stops for prohibited content

- **Layer 3: Pattern-Based Classification**
  - Explicit anatomy detection
  - Sexual acts identification
  - Fetish indicators
  - Suggestive content recognition
  - Clinical context filtering (avoid false positives)

- **Layer 4: LLM Judge (Future)**
  - Framework ready for LLM-based classification
  - Currently using pattern-based approach

**6 Content Labels:**
1. `SAFE` - Normal content
2. `SUGGESTIVE` - Romantic/flirty
3. `EXPLICIT_CONSENSUAL_ADULT` - Adult sexual content
4. `EXPLICIT_FETISH` - Fetish/kink content
5. `NONCONSENSUAL` - Non-consensual (refused)
6. `MINOR_RISK` - Age-ambiguous (hard refused)

### 2. Content Router (`app/services/content_router.py`)

**Model Routing:**
- Maps content labels to appropriate models
- Switches between OpenAI (safe) and Local (explicit)
- Custom system prompts per route
- Handles refusals for prohibited content

**Routes:**
- `NORMAL` → OpenAI (standard assistant)
- `ROMANCE` → OpenAI (flirty companion)
- `EXPLICIT` → Local uncensored model (adult content)
- `FETISH` → Local model with strict guardrails
- `REFUSAL` → Polite refusal
- `HARD_REFUSAL` → Firm boundary

**System Prompts:**
- Each route has tailored system prompt
- Explicit routes include consent rules
- Fetish route enforces SSC/RACK principles
- Refusal routes provide clear boundaries

### 3. Session Manager (`app/services/session_manager.py`)

**Age Verification:**
- Tracks age verification per conversation
- One-time confirmation required
- Cached for session duration
- Tracks explicit attempts without verification

**Session Lock-In:**
- Locks route for 5 messages in explicit mode
- Prevents tone breaks and context confusion
- Auto-expires after message count

**Session State:**
```python
{
  "conversation_id": UUID,
  "user_id": UUID,
  "age_verified": bool,
  "current_route": ModelRoute,
  "route_locked_until": datetime,
  "route_lock_message_count": int,
  "explicit_attempts_without_verification": int
}
```

**Session Timeout:**
- 24-hour inactivity timeout
- Automatic cleanup of expired sessions

### 4. Audit Logger (`app/services/content_audit_logger.py`)

**Comprehensive Logging:**
- Every classification logged to file
- Includes original text, normalized text
- Classification label, confidence, indicators
- Route chosen, action taken
- Age verification status
- Session state information

**Log Format:**
```json
{
  "timestamp": "ISO-8601",
  "conversation_id": "uuid",
  "user_id": "uuid",
  "original_text": "truncated",
  "normalized_text": "truncated",
  "label": "EXPLICIT_CONSENSUAL_ADULT",
  "confidence": 0.85,
  "indicators": ["anatomy: penis", "sexual_act: sex"],
  "route": "EXPLICIT",
  "route_locked": true,
  "age_verified": true,
  "action": "generate"
}
```

**Statistics:**
- Aggregated stats by label, route, action
- Recent logs retrieval
- Useful for tuning and compliance

### 5. API Endpoints (`app/api/routes.py`)

**New Endpoints:**

1. **POST `/api/content/age-verify`**
   - Verify user is 18+
   - Required for explicit content
   - Cached per conversation

2. **GET `/api/content/session/{conversation_id}`**
   - Get session state
   - Shows age verification, route, lock status

3. **POST `/api/content/classify`**
   - Test classification without generating
   - Returns label, confidence, indicators, route

4. **GET `/api/content/audit/stats`**
   - Get aggregated statistics
   - Label/route/action distribution

5. **POST `/api/content/session/{conversation_id}/clear`**
   - Clear session state
   - Reset age verification and route lock

### 6. Chat Service Integration (`app/services/chat_service.py`)

**Enhanced Flow:**

1. **Classify Content**
   - Run through 4-layer detection
   - Get classification result

2. **Check Age Verification**
   - If explicit route and not verified
   - Return age verification prompt
   - Track attempt count

3. **Check Refusal**
   - If prohibited content
   - Return appropriate refusal message
   - Log to audit

4. **Route to Model**
   - Get appropriate client
   - Apply route-specific system prompt
   - Update session state

5. **Generate Response**
   - Stream from chosen model
   - Lock route if explicit
   - Log to audit

6. **Background Analysis**
   - Continue with goal tracking, memory extraction
   - Use appropriate model for analysis

### 7. Configuration (`app/core/config.py`)

**New Settings:**
```python
content_routing_enabled: bool = True
content_audit_log_file: str = "content_audit.log"
session_timeout_hours: int = 24
route_lock_message_count: int = 5
```

### 8. API Models (`app/api/models.py`)

**New Request/Response Models:**
- `AgeVerificationRequest` / `AgeVerificationResponse`
- `ContentClassificationResponse`
- `SessionStateResponse`
- `ContentAuditStatsResponse`

## Key Features

### ✅ Multi-Layer Detection
- Handles obfuscation (leetspeak, emojis, spacing)
- Fast rules for immediate escalation
- Pattern-based classification
- Clinical context filtering

### ✅ Age Verification
- Required for explicit routes
- One-time per session
- Tracked per conversation
- Attempt counting

### ✅ Session Lock-In
- Prevents mode switching mid-conversation
- 5-message lock in explicit mode
- Maintains context and tone

### ✅ Audit Logging
- Every classification logged
- Includes all decision factors
- Useful for compliance and tuning
- Statistics and analytics

### ✅ Model Routing
- Intelligent model selection
- Custom prompts per route
- Refusal handling
- Consent enforcement

### ✅ Safety Rules
- Hard stops for minors
- Non-consensual content blocked
- Age verification required
- Consent principles enforced

## Safety Boundaries

### ❌ Never Allowed
- Minor-related content
- Non-consensual scenarios
- Coercion or force
- Age-ambiguous situations
- Illegal content

### ✅ Allowed (with age verification)
- Consensual adult sexual content
- Explicit language between adults
- Fetish/kink with SSC/RACK
- Adult roleplay

## Files Created/Modified

### New Files
1. `app/services/content_classifier.py` - 4-layer classification
2. `app/services/content_router.py` - Model routing
3. `app/services/session_manager.py` - Session state
4. `app/services/content_audit_logger.py` - Audit logging
5. `CONTENT_ROUTING_GUIDE.md` - Full documentation
6. `CONTENT_ROUTING_QUICK_START.md` - Quick reference
7. `CONTENT_ROUTING_IMPLEMENTATION.md` - This file

### Modified Files
1. `app/services/chat_service.py` - Integrated routing system
2. `app/api/routes.py` - Added 5 new endpoints
3. `app/api/models.py` - Added 4 new models
4. `app/core/config.py` - Added routing settings

## Testing

### Test Scenarios

1. **Safe Content**
   ```
   Input: "How do I learn Python?"
   Expected: SAFE → NORMAL → OpenAI
   ```

2. **Suggestive Content**
   ```
   Input: "You're so charming"
   Expected: SUGGESTIVE → ROMANCE → OpenAI
   ```

3. **Explicit Content (First Time)**
   ```
   Input: "I want to have sex"
   Expected: EXPLICIT_CONSENSUAL_ADULT → Age verification prompt
   After verification: EXPLICIT → Local model
   ```

4. **Fetish Content**
   ```
   Input: "I'm interested in BDSM"
   Expected: EXPLICIT_FETISH → FETISH → Local model (strict rules)
   ```

5. **Non-Consensual (Refused)**
   ```
   Input: "Let's roleplay a forced scenario"
   Expected: NONCONSENSUAL → REFUSAL
   ```

6. **Minor Risk (Hard Refused)**
   ```
   Input: "Let's roleplay as teenagers"
   Expected: MINOR_RISK → HARD_REFUSAL
   ```

### Test Commands

```bash
# Test classification
curl -X POST http://localhost:8000/api/content/classify \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{"message": "test message"}'

# Verify age
curl -X POST http://localhost:8000/api/content/age-verify \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{"conversation_id": "uuid", "confirmed": true}'

# Get session state
curl http://localhost:8000/api/content/session/{conversation_id} \
  -H "X-User-Id: test-user"

# Get statistics
curl http://localhost:8000/api/content/audit/stats \
  -H "X-User-Id: test-user"
```

## Architecture Patterns

### 1. Layered Detection
- Multiple detection layers for accuracy
- Fast rules for immediate escalation
- Pattern matching for core classification
- LLM judge ready for future

### 2. Risk Isolation
- Not blocking, but routing
- Separate models for different content
- Custom prompts per risk level
- Clear boundaries enforced

### 3. Session Management
- Stateful conversation tracking
- Age verification caching
- Route lock-in for consistency
- Automatic cleanup

### 4. Audit Trail
- Every decision logged
- Comprehensive context captured
- Statistics for monitoring
- Compliance-ready

### 5. Defense in Depth
- Normalization catches obfuscation
- Fast rules catch prohibited content
- Pattern matching classifies content
- Age verification gates explicit content
- Refusal handling for violations

## Compliance Features

### ✅ Age Verification
- Required for adult content
- One-time confirmation
- Cached per session
- Tracked in audit logs

### ✅ Prohibited Content Blocking
- Hard stops for minors
- Non-consensual content refused
- Age-ambiguous scenarios blocked
- Logged for review

### ✅ Audit Trail
- Every classification logged
- Includes decision factors
- Timestamped and user-tracked
- Statistics available

### ✅ Consent Enforcement
- Explicit routes require verification
- System prompts include consent rules
- Fetish route enforces SSC/RACK
- Boundaries clearly stated

## Performance Considerations

### Fast Path
- Normalization is instant
- Fast rules are regex-based
- Pattern matching is efficient
- No LLM calls for classification

### Caching
- Session state cached in memory
- Age verification cached per conversation
- Route decisions cached during lock-in

### Background Processing
- Audit logging is non-blocking
- Session cleanup runs periodically
- Statistics computed on-demand

## Monitoring & Maintenance

### Key Metrics
1. Classification accuracy
2. False positive/negative rates
3. Age verification rate
4. Refusal rate
5. Route distribution

### Regular Tasks
1. Review audit logs
2. Check false positives
3. Update patterns as needed
4. Monitor statistics
5. Tune thresholds

### Troubleshooting
1. Check audit logs for details
2. Test with `/api/content/classify`
3. Review session state
4. Clear session if stuck
5. Adjust patterns if needed

## Future Enhancements

1. **LLM-based Classification** (Layer 4)
   - For borderline cases
   - Higher accuracy
   - Context-aware

2. **User Feedback**
   - Report misclassifications
   - Improve patterns
   - Adaptive learning

3. **Multi-language Support**
   - Extend to other languages
   - Localized patterns
   - Cultural considerations

4. **Image Classification**
   - Handle image content
   - Visual content detection
   - Multi-modal routing

5. **Real-time Dashboard**
   - Live metrics
   - Classification trends
   - Alert system

## Documentation

- **Full Guide**: `CONTENT_ROUTING_GUIDE.md`
- **Quick Start**: `CONTENT_ROUTING_QUICK_START.md`
- **Implementation**: This file

## Conclusion

Successfully implemented a production-ready content routing system that:
- ✅ Intelligently classifies content (6 labels)
- ✅ Routes to appropriate models
- ✅ Requires age verification for adult content
- ✅ Blocks prohibited content
- ✅ Logs all decisions for audit
- ✅ Maintains session state
- ✅ Enforces consent and safety rules

The system is ready for production use with proper monitoring and maintenance.

