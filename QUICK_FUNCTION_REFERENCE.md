# 🚀 Quick Function Reference Guide

## 📍 Top 10 Most Important Functions

### **1. `stream_chat()` - The Main Boss** 👑
- **Location**: `app/services/chat_service.py:71`
- **What**: Orchestrates EVERYTHING
- **Called By**: API endpoint
- **Duration**: ~50 seconds total

### **2. `chat_endpoint()` - The Entry Point** 🚪
- **Location**: `app/api/routes.py:52`
- **What**: Receives HTTP requests
- **Called By**: User's browser
- **Duration**: <1ms (just routing)

### **3. `llm_client.stream_chat()` - The VPS Call** 🤖
- **Location**: `app/services/llm_client.py:81`
- **What**: **SENDS REQUEST TO VPS** with X-API-Key
- **Called By**: `stream_chat()` in chat_service
- **Duration**: ~24 seconds (biggest bottleneck!)

### **4. `retrieve_relevant_memories()` - Memory Search** 🧠
- **Location**: `app/services/long_term_memory.py:43`
- **What**: Searches past conversations
- **Called By**: `stream_chat()`
- **Duration**: ~50ms

### **5. `detect_and_store()` - Emotion Detection** 😊
- **Location**: `app/services/emotion_service.py:67`
- **What**: Detects user's emotion
- **Called By**: `stream_chat()` (parallel)
- **Duration**: ~24s (uses LLM)

### **6. `personality_detector.detect()` - Personality** 🎭
- **Location**: `app/services/personality_detector.py:288`
- **What**: Detects personality preferences
- **Called By**: `stream_chat()` (parallel)
- **Duration**: ~24s (uses LLM)

### **7. `build_chat_messages()` - Prompt Builder** 📝
- **Location**: `app/services/prompt_builder.py:49`
- **What**: Creates final prompt for LLM
- **Called By**: `stream_chat()`
- **Duration**: ~5ms

### **8. `_background_analysis()` - Background Tasks** 🔄
- **Location**: `app/services/chat_service.py:588`
- **What**: Goals + memory extraction (user doesn't wait)
- **Called By**: `stream_chat()` via asyncio.create_task()
- **Duration**: ~2-5s (happens after response)

### **9. `search_similar()` - Vector Search** 🔍
- **Location**: `app/repositories/vector_store.py:211`
- **What**: pgvector similarity search
- **Called By**: `retrieve_relevant_memories()`
- **Duration**: ~30ms

### **10. `detect_and_track_goals()` - Goal Tracking** 🎯
- **Location**: `app/services/goal_service.py:156`
- **What**: Tracks user goals
- **Called By**: `_background_analysis()`
- **Duration**: ~1-2s (background)

---

## ⚡ Critical Path (What User Waits For)

```
1. stream_chat() starts
2. ⚡ Parallel detection (~24s)
   ├─ Personality
   ├─ Emotion  
   └─ Load config
3. Retrieve memories (~50ms)
4. Build prompt (~5ms)
5. 🤖 VPS LLM call (~24s) ← BIGGEST WAIT
6. Stream response to user
───────────────────────────
TOTAL: ~50 seconds
```

---

## 🔄 Background Path (User Doesn't Wait)

```
7. _background_analysis()
   ├─ Goal detection (~1s)
   └─ Memory extraction (~2s)
───────────────────────────
User already has response! ✅
```

---

## 🗺️ Mini Call Map

```
User
 ↓
routes.py → chat_endpoint()
 ↓
chat_service.py → stream_chat() ← MAIN
 ↓
├─ Parallel Block (3x faster!)
│  ├─ personality_detector.detect()
│  ├─ emotion_service.detect_and_store()
│  └─ personality_service.get_personality()
│
├─ long_term_memory.retrieve_relevant_memories()
│  └─ vector_store.search_similar()
│
├─ prompt_builder.build_chat_messages()
│
├─ llm_client.stream_chat() ← VPS REQUEST
│  └─ POST http://66.42.93.128/llm/v1
│      with X-API-Key header
│
└─ _background_analysis() ← Fire & forget
   ├─ goal_service.detect_and_track_goals()
   └─ long_term_memory.extract_and_store_memories()
```

---

## 🎯 Where X-API-Key is Used

**Function**: `llm_client.stream_chat()`  
**File**: `app/services/llm_client.py:81`  
**Line**: 98-104

```python
stream = await self.client.chat.completions.create(
    model=self.model_name,
    messages=messages,
    temperature=self.temperature,
    max_tokens=self.max_tokens,
    stream=True
)
# X-API-Key sent automatically via default_headers
```

**Set in**: `llm_client.py:76-78`
```python
default_headers = {}
if settings.vps_api_key:
    default_headers["X-API-Key"] = settings.vps_api_key
```

---

## 🐛 Quick Debug Guide

### Problem: Slow Response
**Check**: `message_journey.log` for timing
```bash
tail -f message_journey.log | grep "total:"
```

### Problem: VPS Error
**Check**: `llm_client.stream_chat()` in `app.log`
```bash
grep "HTTP Request.*66.42" app.log | tail -5
```

### Problem: No Memories
**Check**: `retrieve_relevant_memories()` in `app.log`
```bash
grep "Retrieved.*memories" app.log | tail -5
```

### Problem: Database Error
**Check**: Any function with DB access
```bash
grep -i "database\|connection refused" app.log | tail -10
```

---

## 📊 Function Speed Reference

| Speed | Functions |
|-------|-----------|
| **<1ms** | chat_endpoint, routing |
| **5-10ms** | build_chat_messages, in-memory ops |
| **30-50ms** | database queries, vector search |
| **1-2s** | goal detection, memory extraction |
| **20-30s** | LLM calls (personality, emotion, chat) |

---

## 🎓 Learning Path

To understand the code:

1. **Start Here**: `FUNCTION_CALL_FLOW.md` (full details)
2. **Read**: `stream_chat()` in `chat_service.py:71`
3. **Trace**: Follow one message through journey log
4. **Debug**: Use `tail -f message_journey.log`
5. **Optimize**: Focus on LLM call functions

---

**See Full Documentation**: `FUNCTION_CALL_FLOW.md`

