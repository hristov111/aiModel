# Explicit Conversation Context Fix - Complete

## Problem

When a user sent an explicit message, the system would classify it as EXPLICIT and route to the explicit model. However, on subsequent messages that weren't explicitly sexual (but were contextually part of the same conversation), the system would:

1. Re-classify each message independently
2. Often classify follow-up messages as SAFE
3. Switch back to NORMAL route
4. Break the conversational flow

**Example**:
- User: "I want to have sex with you" → Classified as EXPLICIT, routes to explicit model
- AI: *responds in explicit mode*
- User: "keep going" → Classified as SAFE, routes back to normal model ❌
- Result: Context is lost, conversation broken

## Solution

Implemented **route locking** that was already in the codebase but wasn't being properly utilized.

### Key Changes

**File**: `app/services/chat_service.py`

1. **Added import**: `ClassificationResult` to create mock classifications
2. **Reordered logic**: Get session BEFORE classification (line ~551)
3. **Check route lock first**: Before classifying content, check if route is locked
4. **Skip classification if locked**: Use the locked route directly for next 5 messages

### How It Works Now

```python
# 1. Get session first
session = session_manager.get_session(conversation_id, user_db_id)

# 2. Check if route is locked (continuing explicit conversation)
if session_manager.is_route_locked(conversation_id):
    route = session_manager.get_current_route(conversation_id)
    # Skip classification - use locked route
    classification = ClassificationResult(
        label=ContentLabel.EXPLICIT_CONSENSUAL_ADULT,
        confidence=1.0,
        reasoning="Route locked - continuing explicit conversation context"
    )
else:
    # Normal flow: classify and route
    classification = classifier.classify(user_message)
    route = router.route(classification)
```

### Route Lock Behavior

From `app/services/session_manager.py`:
- **Lock Duration**: 5 messages (`ROUTE_LOCK_MESSAGE_COUNT = 5`)
- **Applies to**: EXPLICIT and FETISH routes
- **Behavior**:
  - Message 1: "explicit message" → Classifies as EXPLICIT → Locks for 5 messages
  - Messages 2-6: ANY message → Skip classification → Stay in EXPLICIT mode
  - Message 7+: Lock expires → Resume normal classification

## Flow Diagram

### Before Fix:
```
User: "explicit message"
  → Classify: EXPLICIT → Route: EXPLICIT → Lock: 5 messages
  
User: "continue" (not explicit text)
  → Classify: SAFE → Route: NORMAL ❌
  (Context broken)
```

### After Fix:
```
User: "explicit message"
  → Classify: EXPLICIT → Route: EXPLICIT → Lock: 5 messages
  
User: "continue" (not explicit text)
  → Check Lock: YES → Route: EXPLICIT (skip classification) ✅
  (Context maintained)
  
User: "keep going" (not explicit text)
  → Check Lock: YES → Route: EXPLICIT (4 messages left) ✅
  
... (continues for 5 total messages)

User: 6th message
  → Check Lock: NO → Classify: SAFE → Route: NORMAL
  (Lock expired, back to normal)
```

## Benefits

✅ **Contextual Understanding**: Follow-up messages stay in explicit mode
✅ **Natural Conversation**: No jarring context switches
✅ **Configurable**: `ROUTE_LOCK_MESSAGE_COUNT` can be adjusted
✅ **Safe**: Still requires age verification before explicit content
✅ **Auditable**: Mock classification maintains audit trail

## Testing

### Test Case 1: Explicit Conversation Lock
```bash
# Terminal test
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want explicit content"}'

# Check logs - should see:
# "Route locked to EXPLICIT for 5 messages"

# Send follow-up (non-explicit)
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"message": "continue", "conversation_id": "<from previous>"}'

# Check logs - should see:
# "Route locked to EXPLICIT (4 messages remaining) - skipping classification"
```

### Test Case 2: Lock Expiration
Send 6 messages in same conversation:
- Message 1: Explicit → Lock set
- Messages 2-5: Lock active (4, 3, 2, 1 remaining)
- Message 6: Lock expired → Normal classification resumes

## Configuration

In `app/services/session_manager.py`:

```python
class SessionManager:
    # Adjust this value to change lock duration
    ROUTE_LOCK_MESSAGE_COUNT = 5  # Default: 5 messages
```

**Increase** to maintain explicit context longer
**Decrease** to return to normal mode faster

## Additional Notes

- Lock only applies to EXPLICIT and FETISH routes
- ROMANCE route does not lock (allows natural flow between flirty and normal)
- Lock is per-conversation (different conversations have independent locks)
- Lock resets if user sends another explicit message
- Age verification is still enforced before entering explicit mode

---

**Status**: ✅ Fixed and Deployed
**Date**: 2024-12-24
**Version**: Development (docker-compose.dev.yml)

