# 🚀 Quick Start: Emotion Detection

Get emotion detection running in 5 minutes!

---

## Step 1: Install Dependencies (if not already installed)

```bash
cd "/home/bean12/Desktop/AI Service"
pip install -r requirements.txt
```

---

## Step 2: Run Database Migration

```bash
# Apply the new emotion_history table
alembic upgrade head

# Verify migration
alembic current
# Should show: 003_emotion_detection
```

---

## Step 3: Start the Service

```bash
# Local development
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# OR with Docker
docker-compose down
docker-compose up -d --build
```

---

## Step 4: Test Emotion Detection

### Test 1: Happy Emotion
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "X-User-Id: test_user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am so happy today! 😊 Everything is going great!"
  }'
```

### Test 2: Check Emotion Was Detected
```bash
curl -X GET "http://localhost:8000/emotions/history?limit=1" \
  -H "X-User-Id: test_user_123"
```

**Expected Response:**
```json
{
  "emotions": [
    {
      "emotion": "happy",
      "confidence": 0.85,
      "intensity": "high",
      "indicators": ["emoji", "keyword", "phrase"],
      "message_snippet": "I am so happy today! 😊 Everything is going great!",
      "detected_at": "2024-01-15T10:30:00",
      "conversation_id": "..."
    }
  ],
  "total_count": 1,
  "period_days": 30,
  "message": "Emotion history retrieved successfully"
}
```

---

## Step 5: Test Different Emotions

```bash
# Test Sad
curl -X POST "http://localhost:8000/chat" \
  -H "X-User-Id: test_user_123" \
  -H "Content-Type: application/json" \
  -d '{"message": "I am feeling really sad 😢"}'

# Test Frustrated
curl -X POST "http://localhost:8000/chat" \
  -H "X-User-Id: test_user_123" \
  -H "Content-Type: application/json" \
  -d '{"message": "This is so frustrating! 😤 Been stuck for hours!"}'

# Test Excited
curl -X POST "http://localhost:8000/chat" \
  -H "X-User-Id: test_user_123" \
  -H "Content-Type: application/json" \
  -d '{"message": "OMG I just got the job! 🎉 So excited!"}'
```

---

## Step 6: View Emotion Analytics

### Get Statistics
```bash
curl -X GET "http://localhost:8000/emotions/statistics?days=30" \
  -H "X-User-Id: test_user_123"
```

### Get Trends
```bash
curl -X GET "http://localhost:8000/emotions/trends?days=30" \
  -H "X-User-Id: test_user_123"
```

---

## Step 7: Explore API Documentation

Open your browser:
```
http://localhost:8000/docs
```

Look for the new emotion endpoints:
- GET `/emotions/history`
- GET `/emotions/statistics`
- GET `/emotions/trends`
- DELETE `/emotions/history`

---

## ✅ Verification Checklist

- [ ] Migration successful (`alembic current` shows `003_emotion_detection`)
- [ ] Service started without errors
- [ ] Sent test message with emotion
- [ ] Emotion detected and stored
- [ ] Can retrieve emotion history
- [ ] Statistics endpoint returns data
- [ ] AI response is empathetic to emotion

---

## 🎭 What's Happening Behind the Scenes?

```
Your Message
    ↓
[Emotion Detector Analyzes]
    - Keywords: "happy", "sad", "frustrated"
    - Emojis: 😊, 😢, 😤
    - Phrases: "I'm so happy", "feeling sad"
    ↓
[If Detected (confidence > 0.3)]
    - Store in database
    - Calculate intensity
    - Track indicators
    ↓
[Build Empathetic Prompt]
    - Inject emotion context
    - Add response strategy
    - Consider emotion history
    ↓
[LLM Responds]
    - Tone matches emotion
    - Empathetic language
    - Context-aware support
```

---

## 🔥 Try These Examples

### Example 1: Supportive Response to Sadness
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "X-User-Id: demo_user" \
  -H "Content-Type: application/json" \
  -d '{"message": "I just lost my job 😢 Feeling really down"}'
```

**AI will:**
- Detect "sad" with high confidence
- Respond with gentle, supportive tone
- Offer comfort without dismissing feelings
- Avoid being overly cheerful

### Example 2: Celebrating Excitement
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "X-User-Id: demo_user" \
  -H "Content-Type: application/json" \
  -d '{"message": "Just got engaged! 💍 Best day ever! 🎉"}'
```

**AI will:**
- Detect "excited" with high confidence
- Match their energetic tone
- Use exclamation points
- Celebrate with them

### Example 3: Patient with Frustration
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "X-User-Id: demo_user" \
  -H "Content-Type: application/json" \
  -d '{"message": "Been debugging for 6 hours 😤 Nothing works!"}'
```

**AI will:**
- Detect "frustrated" with high confidence
- Be patient and understanding
- Break down solutions step-by-step
- Acknowledge frustration is normal

---

## 📚 Next Steps

1. **Read Full Documentation:** `EMOTION_DETECTION_GUIDE.md`
2. **Review Implementation:** `EMOTION_DETECTION_SUMMARY.md`
3. **Check Changelog:** See version 2.2.0 in `CHANGELOG.md`
4. **Explore Code:**
   - Detection logic: `app/services/emotion_detector.py`
   - Service layer: `app/services/emotion_service.py`
   - Prompt engineering: `app/services/prompt_builder.py`

---

## 🐛 Troubleshooting

### Migration Failed
```bash
# Check current version
alembic current

# If stuck, try:
alembic downgrade -1
alembic upgrade head
```

### No Emotions Detected
- Check message length (must be > 3 chars)
- Verify emotion indicators (keywords, emojis, phrases)
- Lower confidence threshold if needed (in `emotion_detector.py`)

### Import Errors
```bash
# Ensure all packages installed
pip install -r requirements.txt

# Check for missing packages
pip list | grep -E "fastapi|sqlalchemy|pydantic"
```

---

## 🎉 Success!

You now have **Advanced Emotion Detection** running!

Your AI can:
✅ Detect 12+ emotions automatically  
✅ Track emotional trends over time  
✅ Respond with empathy and context  
✅ Adapt to user's emotional state  
✅ Identify users who need support  

**Your AI Companion is emotionally intelligent!** 🎭💙

---

For detailed documentation, see `EMOTION_DETECTION_GUIDE.md`

For technical overview, see `EMOTION_DETECTION_SUMMARY.md`

