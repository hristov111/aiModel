# Message Flow Tracking: "I don't like chocolate"

## 📍 Where Does Your Message Go?

When you send "I don't like chocolate", here's the **complete journey**:

```
┌─────────────────────────────────────────────────────────────┐
│  YOU: "I don't like chocolate"                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  1️⃣  FASTAPI ROUTE            │
        │  /chat endpoint receives it   │
        └───────────┬───────────────────┘
                    │
                    ▼
        ┌───────────────────────────────┐
        │  2️⃣  CHAT SERVICE             │
        │  stream_chat() processes it   │
        └───────────┬───────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────────┐   ┌───────────────────┐
│  3️⃣  SHORT-TERM  │   │  4️⃣  ANALYSIS     │
│  MEMORY           │   │  (Parallel)       │
│                   │   │                   │
│  Stored in:       │   │  - Personality    │
│  - RAM buffer     │   │  - Emotion        │
│  - conversation   │   │  - Preferences    │
│    history        │   └───────────────────┘
│                   │
│  🔍 LOG:          │
│  "Added user      │
│   message to      │
│   conversation"   │
└───────────────────┘
        │
        │ (After 3+ messages)
        ▼
┌─────────────────────────────────────────────┐
│  5️⃣  BACKGROUND: MEMORY EXTRACTION          │
│  (Runs AFTER you get your response)         │
│                                              │
│  Step A: Extract Facts                      │
│  ├─ Pattern matching: "I...like/dislike"   │
│  ├─ LLM extraction (if enabled)             │
│  └─ Result: "User dislikes chocolate"       │
│                                              │
│  🔍 LOG:                                     │
│  "📝 MEMORY EXTRACTION: Extracted 1 facts"  │
│  "  └─ Fact 1: 'User dislikes chocolate'"  │
│                                              │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│  6️⃣  VECTOR STORE: store_memory()           │
│  (PostgreSQL + pgvector)                     │
│                                               │
│  Step A: Create embedding                    │
│  ├─ "User dislikes chocolate" → [0.2, ...]  │
│  └─ 384-dimensional vector                   │
│                                               │
│  Step B: Check for contradictions            │
│  └─ _check_and_consolidate()                │
│                                               │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│  7️⃣  CONTRADICTION DETECTION                │
│  (This is the KEY part!)                     │
│                                               │
│  Step A: Find similar memories               │
│  ├─ Search for memories about "chocolate"   │
│  ├─ Similarity threshold: ≥ 0.4              │
│  └─ Found: "User likes chocolate" (sim=0.82)│
│                                               │
│  🔍 LOG:                                      │
│  "🔍 CONTRADICTION CHECK: Found 1 similar    │
│   memories for 'User dislikes chocolate'"   │
│  "  └─ Similar memory (sim=0.82):            │
│     'User likes chocolate'"                  │
│                                               │
│  Step B: Check if contradictory              │
│  ├─ Compare: "likes" vs "dislikes"          │
│  ├─ Method: LLM or pattern matching         │
│  └─ Result: YES, contradictory!              │
│                                               │
│  🔍 LOG:                                      │
│  "🤔 Checking if contradictory:              │
│     Old='User likes chocolate' vs            │
│     New='User dislikes chocolate'"           │
│  "⚠️  CONTRADICTION DETECTED!"               │
│                                               │
│  Step C: Supersede old memory                │
│  ├─ Mark old memory: is_active = False      │
│  ├─ Set: superseded_by = new_memory_id      │
│  └─ Keep new memory: is_active = True       │
│                                               │
│  🔍 LOG:                                      │
│  "🔄 SUPERSEDING: Old memory abc123          │
│     'User likes chocolate' →                 │
│     Replaced by new memory xyz789            │
│     'User dislikes chocolate'"               │
│  "✅ Old memory marked as inactive"          │
│                                               │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│  8️⃣  DATABASE: Final State                   │
│  (PostgreSQL)                                 │
│                                               │
│  memories table:                              │
│  ┌────┬─────────────────┬──────────┬────────┐│
│  │ ID │ Content         │is_active│supers..││
│  ├────┼─────────────────┼──────────┼────────┤│
│  │abc │User likes...    │ FALSE ❌│ xyz789 ││
│  │xyz │User dislikes... │ TRUE  ✅│ NULL   ││
│  └────┴─────────────────┴──────────┴────────┘│
│                                               │
│  Only ACTIVE memories are used in prompts!   │
│                                               │
└──────────────────────────────────────────────┘
```

---

## 🔍 How to Watch This in Real-Time

### 1. Send Messages to Trigger Memory Extraction

Memory extraction requires **at least 3 messages** in a conversation:

```bash
# Message 1
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: testuser" \
  -d '{"message": "I like chocolate", "conversation_id": null}'

# Message 2  
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: testuser" \
  -d '{"message": "How are you?", "conversation_id": "SAME_ID_FROM_RESPONSE"}'

# Message 3 - triggers extraction!
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id": testuser" \
  -d '{"message": "Actually, I do not like chocolate", "conversation_id": "SAME_ID"}'
```

### 2. Watch the Logs

```bash
# Watch in real-time
tail -f app.log | grep -E "📝|🔍|⚠️|🔄|✅"

# Or after the fact
tail -200 app.log | grep -E "MEMORY EXTRACTION|CONTRADICTION|SUPERSEDING"
```

### 3. Check the Database

```bash
# See all memories for a user
docker exec ai_companion_db psql -U postgres -d ai_companion -c "
SELECT 
    id,
    content,
    is_active,
    superseded_by,
    created_at
FROM memories
WHERE user_id = (SELECT id FROM users WHERE external_user_id = 'testuser')
ORDER BY created_at DESC
LIMIT 5;"
```

---

## 📊 Log Output Example

When everything works, you'll see:

```log
2025-12-18 16:30:00 - app.services.memory_extraction - INFO - 📝 MEMORY EXTRACTION: Extracted 1 facts from conversation
2025-12-18 16:30:00 - app.services.memory_extraction - INFO -   └─ Fact 1: 'User dislikes chocolate'

2025-12-18 16:30:00 - app.repositories.vector_store - INFO - 🔍 CONTRADICTION CHECK: Found 1 similar memories for 'User dislikes chocolate'
2025-12-18 16:30:00 - app.repositories.vector_store - INFO -   └─ Similar memory (sim=0.82): 'User likes chocolate'

2025-12-18 16:30:00 - app.repositories.vector_store - INFO - 🤔 Checking if contradictory: Old='User likes chocolate' vs New='User dislikes chocolate'

2025-12-18 16:30:00 - app.repositories.vector_store - INFO - ⚠️  CONTRADICTION DETECTED! Old: 'User likes chocolate' New: 'User dislikes chocolate' (similarity: 0.82)

2025-12-18 16:30:00 - app.repositories.vector_store - INFO - 🔄 SUPERSEDING: Old memory abc-123 'User likes chocolate' → Replaced by new memory xyz-789 'User dislikes chocolate'

2025-12-18 16:30:00 - app.repositories.vector_store - INFO - ✅ Old memory marked as inactive (superseded)
```

---

## 🎯 Key Points

1. **Short-term Memory (RAM)**:
   - Stores message immediately
   - Used for current conversation
   - Not persistent

2. **Long-term Memory (PostgreSQL)**:
   - Extracted after 3+ messages
   - Persistent across conversations
   - Searchable with vector similarity

3. **Contradiction Detection**:
   - Automatic
   - Uses embeddings + semantic check
   - Old memories are superseded, not deleted

4. **Active vs Inactive**:
   - Only `is_active=True` memories are used
   - Superseded memories kept for history
   - Can be restored if needed

---

## 🚀 Quick Test Script

```bash
#!/bin/bash
cd "/home/bean12/Desktop/AI Service"

USER="choctest$(date +%s)"
echo "Testing with user: $USER"

# Create conversation with 3+ messages
CONV_ID=$(curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER" \
  -d '{"message": "I like chocolate"}' | grep -o '"conversation_id":"[^"]*"' | cut -d'"' -f4)

echo "Conversation ID: $CONV_ID"

sleep 5

curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER" \
  -d "{\"message\": \"How are you?\", \"conversation_id\": \"$CONV_ID\"}" > /dev/null

sleep 5

curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER" \
  -d "{\"message\": \"Actually, I do not like chocolate\", \"conversation_id\": \"$CONV_ID\"}" > /dev/null

echo ""
echo "Waiting for background processing..."
sleep 10

echo ""
echo "📋 Check logs:"
tail -200 app.log | grep -E "📝|🔍|⚠️|🔄" | tail -20
```

---

## 🐛 Troubleshooting

### Problem: No logs showing up

**Cause**: Memory extraction needs 3+ messages in SAME conversation

**Solution**: Make sure you're using the same `conversation_id` for all messages

### Problem: Contradiction not detected

**Cause 1**: Similarity too low (< 0.4)
- Memories not similar enough to compare
- Solution: Check embedding quality

**Cause 2**: Not recognized as contradiction
- LLM or pattern matcher didn't detect opposition
- Solution: Check `_is_contradictory` method logs

### Problem: Old memory still showing up

**Cause**: Query is retrieving inactive memories

**Solution**: Ensure queries filter `is_active=True`
```python
WHERE is_active = True  # Add this!
```

---

**Now you can track every step of "I don't like chocolate"!** 🍫

