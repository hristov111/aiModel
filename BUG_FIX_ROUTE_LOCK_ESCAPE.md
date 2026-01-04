# Bug Fix: Route Lock Escape for Normal Questions

## Problem

When a user starts an explicit conversation and the route is locked to `EXPLICIT` mode for 5 messages, they could not switch back to normal conversation even when asking a completely safe question.

### Example Scenario

1. User: "Tell me something sexy" → Classified as `SUGGESTIVE`, routed to `ROMANCE` or `EXPLICIT`
2. System locks route to `EXPLICIT` for 5 messages
3. User: "What's the weather like?" → Still routed to `EXPLICIT` mode (bug!)
4. User expects normal conversation but gets explicit context

### Root Cause

The `SessionManager` locks routes for 5 messages when explicit content is detected. The original logic in `chat_service.py`:

- **Checked if route was locked BEFORE classification**
- **Skipped content classification entirely if locked**
- **Used a mock classification based on the locked route**

This meant safe content could never break out of explicit mode until the 5-message counter naturally decremented.

```python
# OLD BUGGY CODE
if session_manager.is_route_locked(conversation_id):
    route = session_manager.get_current_route(conversation_id)
    # Create mock classification - never checks actual content!
    classification = ClassificationResult(...)
    logger.info("Route locked - skipping classification")
else:
    # Only classify if NOT locked
    classification = classifier.classify(user_message)
```

## Solution

**Always classify content**, even when route is locked. Then:

1. If new content is ALSO explicit → stay locked (continue explicit conversation)
2. If new content is SAFE → **break the lock** immediately (user wants normal chat)

### Implementation

```python
# NEW FIXED CODE
# ALWAYS classify content (even if route is locked)
classification = classifier.classify(user_message)
route = router.route(classification)

# Check if route is locked and should stay locked
if session_manager.is_route_locked(conversation_id):
    locked_route = session_manager.get_current_route(conversation_id)
    
    # If new content is also explicit, stay locked
    if route in (ModelRoute.EXPLICIT, ModelRoute.FETISH, ModelRoute.ROMANCE):
        route = locked_route  # Keep the locked route
        logger.info("Continuing explicit conversation")
    else:
        # New content is SAFE - break the lock!
        logger.info("Breaking route lock: user switched to SAFE content")
        session.route_lock_message_count = 0  # Clear the lock
```

## Benefits

✅ **Flexible conversation flow**: Users can naturally switch from explicit to normal topics
✅ **Still maintains context**: Explicit conversations continue naturally if user keeps the explicit context
✅ **Better UX**: System respects user intent immediately
✅ **Safe by default**: Any safe question breaks out of explicit mode

## Testing

### Test Case 1: Breaking the Lock
```
User: "Tell me something sexy"
→ Classified: SUGGESTIVE, Route: ROMANCE, Lock: 5 messages

User: "What's the weather?"
→ Classified: SAFE, Route: NORMAL, Lock: BROKEN ✅
```

### Test Case 2: Staying Locked
```
User: "Tell me something sexy"
→ Classified: SUGGESTIVE, Route: ROMANCE, Lock: 5 messages

User: "Tell me more"
→ Classified: SUGGESTIVE, Route: ROMANCE, Lock: 4 messages remaining ✅
```

## Files Modified

- `app/services/chat_service.py` (lines 580-612)
  - Moved classification BEFORE lock check
  - Added logic to break lock on SAFE content
  - Removed mock classification for locked routes

## Related Systems

- **SessionManager** (`app/services/session_manager.py`): Manages route locking
- **ContentClassifier** (`app/services/content_classifier.py`): Multi-layer classification
- **ContentRouter** (`app/services/content_router.py`): Routes content to appropriate models

## Notes

- The 5-message lock was originally designed to prevent rapid switching between explicit/safe modes
- This fix maintains the intent while allowing natural conversation flow
- The lock counter (`route_lock_message_count`) is explicitly set to 0 to break the lock
- Session state persists across messages in the same conversation

## Date

Fixed: January 3, 2026

