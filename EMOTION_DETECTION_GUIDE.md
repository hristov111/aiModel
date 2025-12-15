# 🎭 Emotion Detection & Empathetic AI Guide

## Overview

The **Advanced Emotion Detection** feature gives your AI Companion emotional intelligence! It automatically detects 12+ emotions from user messages with confidence scoring, tracks emotional trends over time, and adapts its communication style to be empathetic and context-aware.

---

## 🌟 Key Features

### 1. **Multi-Method Emotion Detection**
- **Keyword Matching**: Detects emotional words (e.g., "sad", "excited", "frustrated")
- **Emoji Analysis**: Recognizes emotional emojis (😢, 😊, 😡, 🎉)
- **Phrase Pattern Matching**: Identifies emotional phrases (e.g., "I'm so happy", "can't stop crying")
- **Confidence Scoring**: Every detection has a 0-1 confidence score
- **Intensity Levels**: Categorizes emotions as low, medium, or high intensity

### 2. **12+ Supported Emotions**
| Emotion | Description | Response Strategy |
|---------|-------------|-------------------|
| **😊 Happy** | Joy, contentment, pleasure | Warm, positive reinforcement |
| **🎉 Excited** | Enthusiasm, anticipation, thrill | Energetic, celebratory |
| **😢 Sad** | Sadness, grief, heartbreak | Gentle, supportive empathy |
| **😡 Angry** | Anger, rage, frustration | Calm, de-escalating |
| **😤 Frustrated** | Irritation, being stuck | Patient, solution-focused |
| **😰 Anxious** | Worry, nervousness, fear | Reassuring, calming |
| **😕 Confused** | Bewilderment, uncertainty | Clear, patient explanations |
| **🙏 Grateful** | Thankfulness, appreciation | Warm, humble acceptance |
| **😞 Disappointed** | Letdown, unmet expectations | Encouraging, supportive |
| **💪 Proud** | Achievement, accomplishment | Celebratory, affirming |
| **😔 Lonely** | Isolation, feeling alone | Warm, companionable |
| **🌟 Hopeful** | Optimism, looking forward | Encouraging, optimistic |

### 3. **Historical Emotion Tracking**
- Stores every detected emotion with metadata
- Tracks emotion trends over days/weeks/months
- Analyzes sentiment patterns (positive/negative/neutral)
- Identifies if user needs extra support

### 4. **Context-Aware Empathy**
The AI adapts its responses based on:
- **Current Emotion**: Matches tone to user's immediate emotional state
- **Emotion History**: Considers recent emotional patterns
- **Trend Analysis**: Recognizes if emotions are improving or declining
- **Attention Flags**: Identifies when user may need extra support

---

## 🚀 How It Works

### Emotion Detection Flow

```
User Message
    ↓
[Emotion Detector]
    ├── Keyword Analysis (weight: 0.4)
    ├── Emoji Recognition (weight: 0.5)
    └── Phrase Matching (weight: 0.6)
    ↓
[Confidence Calculation]
    ↓
[Store in Database]
    ↓
[Emotion Service]
    ├── Recent Emotions
    ├── Trend Analysis
    └── Context Building
    ↓
[Prompt Builder]
    ├── Inject Current Emotion
    ├── Add Trend Context
    └── Build Empathetic Instructions
    ↓
[LLM Response]
    └── Emotionally-Aware Reply
```

### Example Detection

**User Input:**
```
"I'm so frustrated 😤 I've been trying to fix this bug for hours and nothing works!"
```

**Detection Results:**
```json
{
  "emotion": "frustrated",
  "confidence": 0.92,
  "intensity": "high",
  "indicators": ["keyword", "emoji", "phrase"]
}
```

**AI Response Adaptation:**
```
The AI will:
✓ Be patient and understanding
✓ Break solutions into clear steps
✓ Acknowledge frustration is normal
✓ Offer structured, actionable help
```

---

## 📡 API Endpoints

### 1. Get Emotion History

**Endpoint:** `GET /emotions/history`

**Query Parameters:**
- `limit` (optional): Max emotions to return (default: 20, max: 100)
- `days` (optional): Look back period in days (default: 30)

**Example Request:**
```bash
curl -X GET "https://your-api.com/emotions/history?limit=10&days=7" \
  -H "X-User-Id: user_12345"
```

**Example Response:**
```json
{
  "emotions": [
    {
      "emotion": "happy",
      "confidence": 0.85,
      "intensity": "high",
      "indicators": ["emoji", "keyword"],
      "message_snippet": "I'm so excited about this! 😊",
      "detected_at": "2024-01-15T10:30:00",
      "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    {
      "emotion": "frustrated",
      "confidence": 0.78,
      "intensity": "medium",
      "indicators": ["keyword", "phrase"],
      "message_snippet": "This is taking longer than expected...",
      "detected_at": "2024-01-15T09:15:00",
      "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "total_count": 2,
  "period_days": 7,
  "message": "Emotion history retrieved successfully"
}
```

---

### 2. Get Emotion Statistics

**Endpoint:** `GET /emotions/statistics`

**Query Parameters:**
- `days` (optional): Analysis period in days (default: 30)

**Example Request:**
```bash
curl -X GET "https://your-api.com/emotions/statistics?days=30" \
  -H "X-User-Id: user_12345"
```

**Example Response:**
```json
{
  "total_emotions_detected": 47,
  "period_days": 30,
  "emotions": [
    {
      "emotion": "happy",
      "count": 18,
      "percentage": 38.3,
      "avg_confidence": 0.82
    },
    {
      "emotion": "excited",
      "count": 12,
      "percentage": 25.5,
      "avg_confidence": 0.88
    },
    {
      "emotion": "frustrated",
      "count": 8,
      "percentage": 17.0,
      "avg_confidence": 0.75
    }
  ],
  "sentiment_breakdown": {
    "positive": {
      "count": 35,
      "percentage": 74.5
    },
    "negative": {
      "count": 10,
      "percentage": 21.3
    },
    "neutral": {
      "count": 2,
      "percentage": 4.2
    }
  },
  "message": "Emotion statistics retrieved successfully"
}
```

---

### 3. Get Emotion Trends

**Endpoint:** `GET /emotions/trends`

**Query Parameters:**
- `days` (optional): Analysis period in days (default: 30)

**Example Request:**
```bash
curl -X GET "https://your-api.com/emotions/trends?days=30" \
  -H "X-User-Id: user_12345"
```

**Example Response:**
```json
{
  "dominant_emotion": "happy",
  "emotion_distribution": {
    "happy": 0.42,
    "excited": 0.28,
    "grateful": 0.15,
    "frustrated": 0.10,
    "confused": 0.05
  },
  "recent_trend": "improving",
  "needs_attention": false,
  "message": "Emotion trends analyzed successfully"
}
```

**Trend Interpretation:**
- `"improving"`: User's emotional state is getting better (fewer negative emotions)
- `"stable"`: Consistent emotional patterns
- `"declining"`: More negative emotions recently
- `"insufficient_data"`: Not enough data to determine trend

**Needs Attention Flag:**
- `true`: User has shown 3+ negative emotions in last 5 interactions
- `false`: Emotional state appears stable

---

### 4. Clear Emotion History

**Endpoint:** `DELETE /emotions/history`

**Query Parameters:**
- `conversation_id` (optional): Clear emotions for specific conversation only

**Example Request:**
```bash
# Clear all emotions
curl -X DELETE "https://your-api.com/emotions/history" \
  -H "X-User-Id: user_12345"

# Clear emotions for specific conversation
curl -X DELETE "https://your-api.com/emotions/history?conversation_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "X-User-Id: user_12345"
```

**Example Response:**
```json
{
  "success": true,
  "message": "Emotion history cleared successfully",
  "emotions_cleared": 47
}
```

---

## 🎨 Emotion-Aware Prompt Engineering

### How Emotions Modify AI Behavior

When an emotion is detected, the AI's system prompt is dynamically modified:

#### Example: Sad User

**System Prompt Addition:**
```
💭 EMOTIONAL CONTEXT & RESPONSE GUIDANCE:
📊 DETECTED EMOTION: Sad (confidence: 85%, intensity: high)
  The user is feeling sad. Be gentle, supportive, and empathetic.
  Acknowledge their feelings without dismissing them.
  Offer comfort and show that you understand.
  Avoid being overly cheerful - meet them where they are emotionally.

📈 EMOTION PATTERN: User has been mostly sad recently (trend: declining)
  ⚠️ ATTENTION: User has shown multiple negative emotions recently.
  Be extra supportive and check in on their wellbeing if appropriate.
  ⚠️ Their emotional state may be declining. Be extra sensitive and supportive.
```

#### Example: Excited User

**System Prompt Addition:**
```
💭 EMOTIONAL CONTEXT & RESPONSE GUIDANCE:
📊 DETECTED EMOTION: Excited (confidence: 92%, intensity: high)
  The user is excited! Share their enthusiasm!
  Be energetic and celebratory in your response.
  Amplify their excitement - this is a great moment for them!
  Use exclamation points and positive language to match their energy.
```

---

## 🔧 Configuration & Customization

### Emotion Detection Thresholds

Located in `app/services/emotion_detector.py`:

```python
# Minimum confidence threshold (adjust for sensitivity)
CONFIDENCE_THRESHOLD = 0.3  # Lower = more detections, higher = more precise

# Detection weights (adjust for accuracy)
KEYWORD_WEIGHT = 0.4   # How much keywords contribute
EMOJI_WEIGHT = 0.5     # How much emojis contribute
PHRASE_WEIGHT = 0.6    # How much phrases contribute (highest)
```

### Adding New Emotions

To add a new emotion, update `EMOTIONS` dict in `emotion_detector.py`:

```python
'your_emotion': {
    'keywords': {
        'word1': 0.8,  # weight 0-1
        'word2': 0.9
    },
    'emojis': {
        '😎': 0.8,
        '🆒': 0.7
    },
    'phrases': [
        (r"regex pattern", 0.9),  # (pattern, weight)
    ],
    'response_tone': 'your_custom_tone'
}
```

### Customizing Response Strategies

In `prompt_builder.py`, modify `_build_emotion_instructions()`:

```python
emotion_strategies = {
    'your_emotion': {
        'approach': 'your_approach',
        'instructions': [
            "Custom instruction 1",
            "Custom instruction 2",
            # ...
        ]
    }
}
```

---

## 📊 Database Schema

### emotion_history Table

```sql
CREATE TABLE emotion_history (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    emotion VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,  -- 0.0 to 1.0
    intensity VARCHAR(20) NOT NULL,  -- 'low', 'medium', 'high'
    indicators JSONB,  -- ['keyword', 'emoji', 'phrase']
    message_snippet TEXT,  -- First 100 chars of message
    detected_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for fast querying
CREATE INDEX ix_emotion_history_user_id ON emotion_history(user_id);
CREATE INDEX ix_emotion_history_detected_at ON emotion_history(detected_at);
CREATE INDEX ix_emotion_history_emotion ON emotion_history(emotion);
```

### Migration

Run the migration to add emotion tracking:

```bash
# Apply migration
alembic upgrade head

# Verify
alembic current
# Should show: 003_emotion_detection
```

---

## 🎯 Use Cases

### 1. Mental Health & Wellbeing Apps
- Track user mood over time
- Identify concerning trends early
- Provide empathetic support during difficult times
- Celebrate positive emotional shifts

### 2. Customer Support Bots
- Detect frustrated customers and escalate appropriately
- Adapt tone to customer's emotional state
- Provide extra patience when users are confused
- Celebrate successful resolutions

### 3. Educational AI Tutors
- Recognize when students are frustrated with material
- Provide encouragement when students are discouraged
- Celebrate achievements and breakthroughs
- Adjust explanation style based on confusion levels

### 4. Personal AI Companions
- Build deeper emotional connections
- Remember emotional context across conversations
- Provide consistent emotional support
- Adapt personality to user's communication style

### 5. Team Collaboration Tools
- Monitor team morale and sentiment
- Identify team members who may need support
- Recognize and celebrate team wins
- Improve communication based on emotional context

---

## 🔒 Privacy & Security

### Data Privacy
- Emotion data is **user-isolated** (multi-tenant safe)
- Only stores first 100 chars of message (snippets)
- Full messages are never stored in emotion_history
- All emotion data respects user data deletion requests

### User Control
- Users can **view** their emotion history anytime
- Users can **delete** their emotion history
- Users can clear emotions per conversation
- Emotion detection can be disabled per user (future feature)

### GDPR Compliance
- Emotion data is personal data - treat accordingly
- Include emotion data in data export requests
- Delete emotion data when user requests account deletion
- Anonymize or aggregate for analytics

---

## 🧪 Testing Emotion Detection

### Test Different Emotions

```bash
# Test happy detection
curl -X POST "https://your-api.com/chat" \
  -H "X-User-Id: test_user" \
  -H "Content-Type: application/json" \
  -d '{"message": "I am so happy today! 😊 Everything is going great!"}'

# Test sad detection
curl -X POST "https://your-api.com/chat" \
  -H "X-User-Id: test_user" \
  -H "Content-Type: application/json" \
  -d '{"message": "I am feeling really sad 😢 Nothing seems to be working out"}'

# Test frustrated detection
curl -X POST "https://your-api.com/chat" \
  -H "X-User-Id: test_user" \
  -H "Content-Type: application/json" \
  -d '{"message": "This is so frustrating! 😤 I have been stuck on this for hours"}'
```

### View Detection Results

```bash
# Check if emotions were detected
curl -X GET "https://your-api.com/emotions/history?limit=3" \
  -H "X-User-Id: test_user"
```

---

## 📈 Analytics & Insights

### Aggregate Emotion Data

For product analytics, you can query emotion trends:

```python
from sqlalchemy import func, select
from app.models.database import EmotionHistoryModel

# Most common emotions across all users
query = (
    select(
        EmotionHistoryModel.emotion,
        func.count(EmotionHistoryModel.id).label('count')
    )
    .group_by(EmotionHistoryModel.emotion)
    .order_by(func.count(EmotionHistoryModel.id).desc())
)

# Average sentiment over time
# ... (implement date-based aggregation)
```

### Dashboard Metrics

Track these KPIs:
- **Average Sentiment Score**: Positive/(Positive+Negative)
- **Emotion Diversity**: Number of unique emotions per user
- **Trend Direction**: % of users with improving vs declining trends
- **Attention Rate**: % of users flagged as "needs attention"
- **Response Time**: Time between emotion detection and response

---

## 🚀 Performance Considerations

### Detection Speed
- Emotion detection is **asynchronous** (non-blocking)
- Detection time: ~5-15ms per message
- No impact on chat response latency

### Database Load
- Indexed queries for fast retrieval
- Emotion history capped at configurable limits
- Old emotions can be auto-archived

### Scalability
- Emotion detection is stateless (horizontal scaling)
- Database sharding by user_id supported
- Can process millions of emotions per day

---

## 🛠️ Troubleshooting

### Emotion Not Detected

**Problem:** Expected emotion wasn't detected

**Solutions:**
1. Check confidence threshold (may be too high)
2. Verify keywords/phrases are in detector patterns
3. Look at detection weights (may need adjustment)
4. Check if message is too short (< 3 chars skipped)

### Wrong Emotion Detected

**Problem:** Detected emotion doesn't match actual emotion

**Solutions:**
1. Review detection patterns for conflicts
2. Adjust pattern weights to prioritize accuracy
3. Add more specific phrase patterns
4. Consider context (sarcasm may confuse detector)

### AI Not Adapting to Emotion

**Problem:** AI response doesn't reflect detected emotion

**Solutions:**
1. Verify emotion is passing to prompt builder
2. Check system prompt includes emotion instructions
3. Ensure emotion_service is in dependencies
4. Review LLM's adherence to system instructions

---

## 🎓 Best Practices

### 1. **Balance Detection Sensitivity**
- Too sensitive = false positives (detecting emotions that aren't there)
- Too strict = missed emotions (failing to detect real emotions)
- Tune confidence threshold based on your use case

### 2. **Respect User Privacy**
- Always get consent for emotion tracking
- Be transparent about what you're detecting
- Give users control over their emotion data

### 3. **Don't Over-Rely on Detection**
- Emotion detection is probabilistic, not perfect
- Use as guidance, not absolute truth
- Combine with other signals (user feedback, conversation context)

### 4. **Handle Edge Cases**
- Sarcasm is hard to detect
- Mixed emotions may conflict
- Cultural differences in emotional expression
- Users may mask emotions

### 5. **Monitor & Improve**
- Track detection accuracy metrics
- Collect user feedback on empathy quality
- Continuously update detection patterns
- A/B test different response strategies

---

## 📚 Additional Resources

- **Code:** `app/services/emotion_detector.py` - Emotion detection logic
- **Code:** `app/services/emotion_service.py` - Emotion storage and retrieval
- **Code:** `app/services/prompt_builder.py` - Emotion-aware prompt construction
- **Migration:** `migrations/versions/003_add_emotion_detection.py`
- **API:** `app/api/routes.py` - Emotion endpoints
- **Models:** `app/api/models.py` - Emotion API models

---

## 🎉 Congratulations!

You now have a fully-featured emotion detection system! Your AI Companion can:

✅ Detect 12+ emotions with confidence scoring  
✅ Track emotional trends over time  
✅ Adapt responses based on emotional context  
✅ Provide empathetic, context-aware support  
✅ Analyze sentiment patterns and needs  

**Your AI is now emotionally intelligent!** 🎭💙

---

*For questions or support, please refer to the main project documentation.*

