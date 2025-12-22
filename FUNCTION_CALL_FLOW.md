# 🔄 Complete Function Call Flow Documentation

## Overview

This document traces **every function call** when a user sends a message, showing what each function does and where it's called from.

---

## 📨 Message Journey: Start to Finish

### **Entry Point: User Sends Message**

```
User Browser → POST http://localhost:8000/chat
```

---

## 🎯 Phase 1: API Layer (routes.py)

### **1. `chat_endpoint()`**
- **File**: `app/api/routes.py`
- **Line**: 52-111
- **Called By**: FastAPI router (user HTTP request)
- **What It Does**: 
  - Receives POST request
  - Authenticates user via `get_current_user_id()`
  - Validates conversation ownership
  - Creates streaming response
- **Calls Next**: `chat_service.stream_chat()`

```python
@router.post("/chat")
async def chat_endpoint(
    request: Request,
    chat_request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    user_id: str = Depends(get_current_user_id)
):
    # Validates and starts streaming
    return StreamingResponse(generate_stream(), media_type="text/event-stream")
```

**Next Function** ⬇️

---

## 🧠 Phase 2: Main Orchestrator (chat_service.py)

### **2. `stream_chat()`**
- **File**: `app/services/chat_service.py`
- **Line**: 71-562
- **Called By**: `chat_endpoint()` in routes.py
- **What It Does**: 
  - **MAIN ORCHESTRATOR** - controls entire message flow
  - Manages conversation lifecycle
  - Coordinates all services
  - Yields streaming events to user
- **Parameters**:
  - `user_message`: The user's text
  - `conversation_id`: Optional (creates new if None)
  - `user_id`: External user ID (e.g., "myuser123")
  - `db_session`: Database connection
- **Returns**: AsyncIterator of streaming events

```python
async def stream_chat(
    self,
    user_message: str,
    conversation_id: UUID = None,
    user_id: str = None,
    db_session = None
) -> AsyncIterator[Dict[str, Any]]:
    # Orchestrates everything...
```

---

### **Inside `stream_chat()` - Step by Step**

#### **Step 2.1: Initialize Journey Logger**
- **Line**: 76-78
- **Calls**: `JourneyLogger.__init__()`
- **What It Does**: Creates logger for detailed step tracking
- **Output**: Logs to `message_journey.log`

```python
request_id = str(uuid4())
journey = JourneyLogger(request_id, user_id or "anonymous")
journey.log_start(user_message)
```

**Next** ⬇️

#### **Step 2.2: Create/Get Conversation**
- **Line**: 83-102
- **Calls**: `uuid4()` (if new conversation)
- **What It Does**: Generates or validates conversation ID
- **Database**: Creates `ConversationModel` record

```python
if not conversation_id:
    conversation_id = uuid4()
    journey.log_conversation_created(conversation_id)
```

**Next** ⬇️

#### **Step 2.3: Resolve User**
- **Line**: 105-116
- **Calls**: `get_user_db_id()` from `app.core.auth`
- **What It Does**: Converts external user ID to internal database UUID
- **Database**: Queries `UserModel` table

```python
if user_id:
    user_db_id = await get_user_db_id(db_session, user_id)
    journey.log_user_resolved(str(user_db_id))
```

**Next** ⬇️

#### **Step 2.4: Store User Message**
- **Line**: 144-148
- **Calls**: `conversation_buffer.add_message()`
- **What It Does**: Adds message to short-term memory (in-memory cache)
- **File**: `app/services/short_term_memory.py`

```python
self.conversation_buffer.add_message(
    conversation_id=conversation_id,
    role="user",
    content=user_message
)
```

**Next** ⬇️

#### **Step 2.5: Check User Preferences**
- **Line**: 160-183
- **Calls**: `preference_service.detect_and_update_preferences()`
- **What It Does**: Analyzes message for communication preferences
- **File**: `app/services/user_preference_service.py`
- **Database**: Updates `PreferenceModel` table

```python
if self.preference_service and user_id:
    updated_prefs = await self.preference_service.detect_and_update_preferences(
        external_user_id=user_id,
        message=user_message,
        context=context_messages
    )
```

**Next** ⬇️

---

## ⚡ Phase 3: PARALLEL DETECTION (Optimized!)

This is where **3x speedup** happens - all run **simultaneously**!

### **3. Parallel Detection Block**
- **Line**: 185-380
- **Called By**: `stream_chat()`
- **What It Does**: Runs 4 async tasks in parallel using `asyncio.gather()`

```python
(
    personality_config_detected,
    detected_emotion,
    (personality_config, relationship_state),
    user_preferences
) = await asyncio.gather(
    detect_personality(),      # Task 1
    detect_emotion(),          # Task 2
    load_personality(),        # Task 3
    load_preferences(),        # Task 4
    return_exceptions=True
)
```

#### **Task 1: `detect_personality()` (nested function)**
- **Line**: 203-233
- **Calls**: 
  - `personality_detector.detect()`
  - `personality_service.update_personality()`
- **What It Does**: 
  - Detects if user wants to change AI personality
  - Updates personality in database if detected
- **Files**: 
  - `app/services/personality_detector.py`
  - `app/services/personality_service.py`
- **Database**: Updates `PersonalityProfileModel`

```python
async def detect_personality():
    personality_config_detected = await self.personality_detector.detect(
        user_message,
        context=context_for_detection
    )
    if personality_config_detected:
        await self.personality_service.update_personality(...)
    return personality_config_detected
```

#### **Task 2: `detect_emotion()` (nested function)**
- **Line**: 238-266
- **Calls**: `emotion_service.detect_and_store()`
- **What It Does**: 
  - Detects emotion from message (happy, sad, angry, etc.)
  - Stores emotion in database
- **File**: `app/services/emotion_service.py`
- **Database**: Inserts into `EmotionHistoryModel`

```python
async def detect_emotion():
    emotion = await self.emotion_service.detect_and_store(
        user_id=user_db_id,
        message=user_message,
        conversation_id=conversation_id,
        context=context_messages
    )
    return {'emotion': emotion.emotion, 'confidence': emotion.confidence, ...}
```

#### **Task 3: `load_personality()` (nested function)**
- **Line**: 271-290
- **Calls**: 
  - `personality_service.get_personality()`
  - `personality_service.get_relationship_state()`
  - `personality_service.update_relationship_metrics()`
- **What It Does**: Loads existing personality configuration
- **Database**: Queries `PersonalityProfileModel`, `RelationshipStateModel`

```python
async def load_personality():
    personality_config = await self.personality_service.get_personality(user_db_id)
    relationship_state = await self.personality_service.get_relationship_state(user_db_id)
    await self.personality_service.update_relationship_metrics(
        user_id=user_db_id,
        message_sent=True
    )
    return personality_config, relationship_state
```

#### **Task 4: `load_preferences()` (nested function)**
- **Line**: 295-305
- **Calls**: `preference_service.get_user_preferences()`
- **What It Does**: Loads user's communication preferences
- **Database**: Queries `PreferenceModel`

```python
async def load_preferences():
    return await self.preference_service.get_user_preferences(user_id)
```

**Next** ⬇️

---

## 🔍 Phase 4: Memory Retrieval

### **4. `retrieve_relevant_memories()`**
- **File**: `app/services/long_term_memory.py`
- **Line**: 43-65
- **Called By**: `stream_chat()` line 402
- **What It Does**: 
  - Searches for relevant past memories
  - Uses semantic similarity (vector search)
- **Calls Next**: `retrieval.retrieve_relevant()`

```python
relevant_memories = await self.long_term_memory.retrieve_relevant_memories(
    conversation_id=conversation_id,
    query_text=user_message
)
```

#### **4.1: `retrieve_relevant()` (called by above)**
- **File**: `app/services/memory_retrieval.py`
- **Line**: 47-89
- **Called By**: `retrieve_relevant_memories()`
- **What It Does**: 
  - Generates embedding for user message
  - Searches vector database
  - Returns top K similar memories
- **Calls Next**: 
  - `embedder.embed()`
  - `vector_store.search_similar()`

```python
query_embedding = await self.embedder.embed(query_text)
memories = await self.vector_store.search_similar(
    conversation_id=conversation_id,
    query_embedding=query_embedding,
    top_k=top_k
)
```

#### **4.2: `search_similar()` (called by above)**
- **File**: `app/repositories/vector_store.py`
- **Line**: 211-263
- **Called By**: `retrieve_relevant()`
- **What It Does**: 
  - Queries PostgreSQL with pgvector
  - Uses cosine similarity
  - Returns matching memories
- **Database**: Queries `MemoryModel` with vector search

```python
query = select(MemoryModel).where(
    MemoryModel.conversation_id == conversation_id,
    (1 - MemoryModel.embedding.cosine_distance(query_embedding)) >= similarity_threshold
).order_by(
    MemoryModel.embedding.cosine_distance(query_embedding)
).limit(top_k)
```

**Next** ⬇️

---

## 📝 Phase 5: Prompt Building

### **5. `build_chat_messages()`**
- **File**: `app/services/prompt_builder.py`
- **Line**: 49-139
- **Called By**: `stream_chat()` line 449
- **What It Does**: 
  - Builds system prompt with context
  - Includes memories, personality, emotions
  - Formats messages for LLM
- **Returns**: List of message dicts

```python
messages = self.prompt_builder.build_chat_messages(
    system_prompt=system_prompt,
    recent_messages=history_messages,
    current_user_message=user_message
)
```

#### **5.1: `build_system_prompt()` (called internally)**
- **File**: `app/services/prompt_builder.py`
- **Line**: 15-47
- **Called By**: `build_chat_messages()`
- **What It Does**: 
  - Creates detailed system prompt
  - Adds personality traits
  - Adds emotion context
  - Adds memories
  - Adds user preferences

```python
system_prompt = self.prompt_builder.build_system_prompt(
    persona=settings.system_persona,
    relevant_memories=relevant_memories,
    user_preferences=user_preferences,
    personality_config=personality_config,
    emotion_context=detected_emotion
)
```

**Next** ⬇️

---

## 🤖 Phase 6: LLM Request (THE CRITICAL PART!)

### **6. `stream_chat()` (LLM Client)**
- **File**: `app/services/llm_client.py`
- **Line**: 81-123
- **Called By**: `stream_chat()` in chat_service.py line 513
- **What It Does**: 
  - **SENDS REQUEST TO VPS** with X-API-Key header
  - Streams response token by token
  - Handles errors (connection, timeout)
- **HTTP Request**: POST to `http://66.42.93.128/llm/v1/chat/completions`

```python
async for chunk in self.llm_client.stream_chat(messages):
    # Each chunk is a piece of the response
    yield {"type": "chunk", "chunk": chunk, ...}
```

#### **6.1: Request Details**
- **Method**: POST
- **URL**: `http://66.42.93.128/llm/v1/chat/completions`
- **Headers**: 
  - `Content-Type: application/json`
  - `X-API-Key: {VPS_API_KEY from .env}`
- **Body**:
```json
{
  "model": "qwen2.5-7b-instruct",
  "messages": [...],
  "temperature": 0.7,
  "max_tokens": 150,
  "stream": true
}
```

#### **6.2: Response Handling**
```python
async for chunk in stream:
    if chunk.choices and len(chunk.choices) > 0:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content  # ← Streams to user immediately
```

**Next** ⬇️

---

## 🔄 Phase 7: Background Tasks (After User Gets Response)

### **7. `_background_analysis()`**
- **File**: `app/services/chat_service.py`
- **Line**: 588-630
- **Called By**: `stream_chat()` line 545 via `asyncio.create_task()`
- **What It Does**: 
  - Runs **after** user receives response
  - Non-blocking, fire-and-forget
  - Handles goal tracking and memory extraction

```python
asyncio.create_task(
    self._background_analysis(
        user_message=user_message,
        user_db_id=user_db_id,
        conversation_id=conversation_id,
        detected_emotion=detected_emotion
    )
)
```

#### **7.1: Goal Detection (in background)**
- **Calls**: `goal_service.detect_and_track_goals()`
- **File**: `app/services/goal_service.py`
- **What It Does**: 
  - Detects if user mentions goals
  - Tracks progress on existing goals
- **Database**: Updates `GoalModel`, `GoalProgressModel`

```python
if self.goal_service:
    goal_tracking_result = await self.goal_service.detect_and_track_goals(
        user_id=user_db_id,
        message=user_message,
        conversation_id=conversation_id,
        detected_emotion=detected_emotion.get('emotion')
    )
```

#### **7.2: Memory Extraction (in background)**
- **Calls**: `long_term_memory.extract_and_store_memories()`
- **File**: `app/services/long_term_memory.py`
- **Line**: 67-86
- **What It Does**: 
  - Analyzes conversation for important facts
  - Stores in long-term memory database
- **Database**: Inserts into `MemoryModel`

```python
count = await self.long_term_memory.extract_and_store_memories(
    conversation_id=conversation_id,
    messages=recent_messages
)
```

**Next** ⬇️

---

## ✅ Phase 8: Completion

### **8. Journey Complete**
- **Line**: 556 in chat_service.py
- **Calls**: `journey.log_complete()`
- **What It Does**: Logs final timing and success
- **Output**: Final log entry in `message_journey.log`

```python
journey.log_complete(time.time() - journey.start_time)
```

---

## 🗺️ Complete Call Tree Visualization

```
User Browser
    │
    ├─ POST /chat
    │
    ├─► chat_endpoint() [routes.py:52]
         │
         ├─► get_current_user_id() [auth.py]
         │
         ├─► stream_chat() [chat_service.py:71] ◄─ MAIN ORCHESTRATOR
              │
              ├─► JourneyLogger() [journey_logger.py]
              │
              ├─► get_user_db_id() [auth.py]
              │
              ├─► conversation_buffer.add_message() [short_term_memory.py]
              │
              ├─► preference_service.detect_and_update_preferences() [user_preference_service.py]
              │
              ├─► ⚡ PARALLEL BLOCK (asyncio.gather)
              │    ├─► personality_detector.detect() [personality_detector.py]
              │    │    └─► llm_client.chat() [llm_client.py] - LLM call
              │    │
              │    ├─► emotion_service.detect_and_store() [emotion_service.py]
              │    │    ├─► emotion_detector.detect() [emotion_detector.py]
              │    │    │    └─► llm_client.chat() - LLM call
              │    │    └─► db.add(EmotionHistoryModel)
              │    │
              │    ├─► personality_service.get_personality() [personality_service.py]
              │    │    └─► db.query(PersonalityProfileModel)
              │    │
              │    └─► preference_service.get_user_preferences() [user_preference_service.py]
              │         └─► db.query(PreferenceModel)
              │
              ├─► long_term_memory.retrieve_relevant_memories() [long_term_memory.py]
              │    └─► retrieval.retrieve_relevant() [memory_retrieval.py]
              │         ├─► embedder.embed() [embeddings.py]
              │         └─► vector_store.search_similar() [vector_store.py]
              │              └─► db.query(MemoryModel) - pgvector search
              │
              ├─► prompt_builder.build_chat_messages() [prompt_builder.py]
              │    └─► build_system_prompt()
              │
              ├─► 🤖 llm_client.stream_chat() [llm_client.py:81]
              │    └─► HTTP POST http://66.42.93.128/llm/v1/chat/completions
              │         Headers: X-API-Key: {VPS_API_KEY}
              │         ↓
              │         Response: Streaming tokens
              │
              ├─► conversation_buffer.add_message() (assistant)
              │
              └─► 🔄 _background_analysis() [chat_service.py:588]
                   ├─► goal_service.detect_and_track_goals() [goal_service.py]
                   │    ├─► goal_detector.detect() [goal_detector.py]
                   │    └─► db.add(GoalModel, GoalProgressModel)
                   │
                   └─► long_term_memory.extract_and_store_memories()
                        ├─► memory_extractor.extract() [memory_extraction.py]
                        ├─► memory_categorizer.categorize() [memory_categorizer.py]
                        ├─► embedder.embed()
                        └─► vector_store.store() [vector_store.py]
                             └─► db.add(MemoryModel)
```

---

## 📊 Function Reference Table

| Function | File | Line | Called By | Purpose | DB Access |
|----------|------|------|-----------|---------|-----------|
| `chat_endpoint()` | routes.py | 52 | FastAPI | Entry point | No |
| `stream_chat()` | chat_service.py | 71 | chat_endpoint | Main orchestrator | Yes |
| `add_message()` | short_term_memory.py | ~45 | stream_chat | Store in buffer | No (in-memory) |
| `detect_and_update_preferences()` | user_preference_service.py | ~58 | stream_chat | Detect preferences | Yes (PreferenceModel) |
| `detect()` (personality) | personality_detector.py | ~288 | stream_chat | Detect personality | No |
| `detect_and_store()` (emotion) | emotion_service.py | ~67 | stream_chat | Detect emotion | Yes (EmotionHistoryModel) |
| `get_personality()` | personality_service.py | ~98 | stream_chat | Load personality | Yes (PersonalityProfileModel) |
| `retrieve_relevant_memories()` | long_term_memory.py | 43 | stream_chat | Get memories | Yes (MemoryModel + vector) |
| `build_chat_messages()` | prompt_builder.py | 49 | stream_chat | Build prompt | No |
| `stream_chat()` (LLM) | llm_client.py | 81 | stream_chat | **VPS REQUEST** | No (HTTP) |
| `_background_analysis()` | chat_service.py | 588 | stream_chat (async) | Background tasks | Yes (various) |
| `detect_and_track_goals()` | goal_service.py | ~156 | _background_analysis | Track goals | Yes (GoalModel) |
| `extract_and_store_memories()` | long_term_memory.py | 67 | _background_analysis | Save memories | Yes (MemoryModel) |

---

## ⏱️ Timing Breakdown (Typical Message)

| Phase | Functions | Time | Notes |
|-------|-----------|------|-------|
| **API Layer** | chat_endpoint | <1ms | Fast routing |
| **Setup** | conversation, user resolution | ~10ms | DB queries |
| **Parallel Detection** | personality, emotion, prefs | ~24s | **LLM calls (slow!)** |
| **Memory Retrieval** | vector search | ~50ms | DB query |
| **Prompt Building** | build_chat_messages | ~5ms | In-memory |
| **LLM Response** | stream_chat (VPS) | ~24s | **Network + inference** |
| **Background** | goals, memories | ~2-5s | **User doesn't wait** |
| **TOTAL USER WAIT** | | **~50s** | Before optimization: ~96s |

---

## 🔑 Key Takeaways

1. **`stream_chat()` is the heart** - everything flows through it
2. **Parallel detection** = 3x speedup (run simultaneously)
3. **VPS LLM call** = biggest bottleneck (~24s)
4. **Background tasks** = user doesn't wait for them
5. **X-API-Key** = sent in every VPS request
6. **Journey log** = tracks every step for debugging

---

## 🐛 Debugging Reference

### Where to Look for Problems

| Symptom | Check Function | File | What to Look For |
|---------|----------------|------|------------------|
| Message not sending | `chat_endpoint()` | routes.py | HTTP 500 errors |
| Slow response | `stream_chat()` | chat_service.py | Journey log timings |
| VPS auth error | `llm_client.stream_chat()` | llm_client.py | 401/403 errors, X-API-Key |
| No memories | `retrieve_relevant_memories()` | long_term_memory.py | Empty results, DB connection |
| Emotion not detected | `detect_and_store()` | emotion_service.py | Confidence scores |
| Database errors | Any DB query | Various | Connection refused |

### Debug Commands

```bash
# Watch function calls in real-time
tail -f message_journey.log

# Check for errors in specific functions
grep "ERROR" app.log | grep "chat_service"
grep "ERROR" app.log | grep "llm_client"

# Verify VPS requests
grep "HTTP Request.*66.42" app.log

# Check database queries
grep "SELECT\|INSERT\|UPDATE" app.log
```

---

## 📚 Related Documentation

- **VPS API Setup**: `VPS_API_AUTH_SETUP.md`
- **Performance**: `OPTIMIZATION_SUMMARY.md`
- **Architecture**: `README.md`
- **Security**: `SECURITY_CHECKLIST.md`

---

**Last Updated**: December 18, 2025  
**Application Version**: 4.0.0  
**Author**: AI Development Team

