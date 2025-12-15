# 🚀 Quick Start: Personality System

Get your AI companion's personality up and running in 5 minutes!

---

## Step 1: Run Database Migration

```bash
cd "/home/bean12/Desktop/AI Service"
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade 003_emotion_detection -> 004_personality_system
✅ Created personality_profiles table
✅ Created relationship_state table
```

---

## Step 2: Start the Service

```bash
# Local development
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# OR with Docker
docker-compose up -d --build
```

---

## Step 3: Explore Available Archetypes

```bash
curl -X GET "http://localhost:8000/personality/archetypes"
```

**You'll see 9 archetypes:**
- 🧙 Wise Mentor
- 🤗 Supportive Friend
- 💼 Professional Coach
- ✨ Creative Partner
- 🧘 Calm Therapist
- 🎉 Enthusiastic Cheerleader
- 📊 Pragmatic Advisor
- 🤔 Curious Student
- ⚖️ Balanced Companion

---

## Step 4: Create Your AI's Personality

### Option A: Use an Archetype
```bash
curl -X POST "http://localhost:8000/personality" \
  -H "X-User-Id: test_user" \
  -H "Content-Type: application/json" \
  -d '{"archetype": "wise_mentor"}'
```

### Option B: Custom Configuration
```bash
curl -X POST "http://localhost:8000/personality" \
  -H "X-User-Id: test_user" \
  -H "Content-Type: application/json" \
  -d '{
    "traits": {
      "humor_level": 8,
      "empathy_level": 9,
      "enthusiasm_level": 7
    },
    "behaviors": {
      "asks_questions": true,
      "celebrates_wins": true
    },
    "custom": {
      "backstory": "You are my best friend who always believes in me"
    }
  }'
```

---

## Step 5: Chat with Your Personalized AI!

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "X-User-Id: test_user" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! Tell me about yourself."}'
```

**Expected Response (for Wise Mentor):**
```
"Welcome. I'm here as your mentor - to guide you, challenge your thinking, 
and help you grow. I believe in asking the right questions rather than simply 
giving answers. What brings you here today? What are you hoping to learn or 
accomplish?"
```

---

## Step 6: Adjust Personality with Natural Language

```bash
# Make AI more enthusiastic
curl -X POST "http://localhost:8000/chat" \
  -H "X-User-Id: test_user" \
  -H "Content-Type: application/json" \
  -d '{"message": "Be more enthusiastic!"}'

# Next response will be more energetic!
```

---

## Step 7: Check Relationship Progress

```bash
curl -X GET "http://localhost:8000/personality/relationship" \
  -H "X-User-Id: test_user"
```

**Response:**
```json
{
  "total_messages": 5,
  "relationship_depth_score": 1.2,
  "trust_level": 5.0,
  "days_known": 0,
  "milestones": [
    {
      "type": "10_messages",
      "reached_at": "2024-01-15T10:30:00",
      "message": "Reached 10 messages together!"
    }
  ]
}
```

---

## Step 8: View API Documentation

Open in browser:
```
http://localhost:8000/docs
```

Look for the **Personality System Endpoints** section!

---

## 🎯 Try Different Archetypes!

### Supportive Friend (Warm & Encouraging)
```bash
curl -X PUT "http://localhost:8000/personality" \
  -H "X-User-Id: test_user" \
  -H "Content-Type: application/json" \
  -d '{"archetype": "supportive_friend", "merge": false}'
```

### Professional Coach (Direct & Results-Focused)
```bash
curl -X PUT "http://localhost:8000/personality" \
  -H "X-User-Id: test_user" \
  -H "Content-Type: application/json" \
  -d '{"archetype": "professional_coach", "merge": false}'
```

### Enthusiastic Cheerleader (Maximum Energy!)
```bash
curl -X PUT "http://localhost:8000/personality" \
  -H "X-User-Id: test_user" \
  -H "Content-Type: application/json" \
  -d '{"archetype": "enthusiastic_cheerleader", "merge": false}'
```

---

## 🔧 Fine-Tune Individual Traits

```bash
# Adjust humor level
curl -X PUT "http://localhost:8000/personality" \
  -H "X-User-Id: test_user" \
  -H "Content-Type: application/json" \
  -d '{"traits": {"humor_level": 9}, "merge": true}'

# Adjust multiple traits
curl -X PUT "http://localhost:8000/personality" \
  -H "X-User-Id: test_user" \
  -H "Content-Type: application/json" \
  -d '{
    "traits": {
      "enthusiasm_level": 8,
      "directness_level": 7,
      "playfulness_level": 6
    },
    "merge": true
  }'
```

---

## 💬 Natural Language Examples

Try chatting with these phrases to auto-adjust personality:

### Change Archetype
- "Be like a wise mentor"
- "Act more like a supportive friend"
- "I want you to be a professional coach"

### Adjust Traits
- "Be more enthusiastic!"
- "You're too serious, lighten up"
- "Be more direct with me"
- "Stop being so formal, be casual"
- "I need you to be more empathetic"

### Change Behaviors
- "Ask me more questions"
- "Stop asking so many questions"
- "Give me more examples"
- "Challenge me more"
- "Celebrate my wins with me!"

---

## ✅ Verification Checklist

- [ ] Migration successful (004_personality_system)
- [ ] Service started without errors
- [ ] Can list archetypes
- [ ] Created personality successfully
- [ ] Personality reflected in chat responses
- [ ] Natural language adjustments work
- [ ] Relationship state tracking works
- [ ] Can view API docs

---

## 🎭 See the Difference!

### Before Personality System
```
User: "I got a promotion!"
AI: "Congratulations on your promotion."
```

### After (Enthusiastic Cheerleader)
```
User: "I got a promotion!"
AI: "OMG THAT'S AMAZING! 🎉🎉🎉 I'm SO incredibly proud of you! 
You worked SO hard for this and you TOTALLY deserve it! This is 
HUGE! Tell me everything! When did you find out?! I want to 
celebrate with you! 💪✨"
```

### After (Wise Mentor)
```
User: "I got a promotion!"
AI: "Congratulations. This is a significant milestone in your journey. 
Promotions bring both opportunity and responsibility. As you step into 
this new role, what aspect of it excites you most? And what, if anything, 
gives you pause?"
```

---

## 📚 Next Steps

1. **Read Full Guide:** `PERSONALITY_SYSTEM_GUIDE.md`
2. **Review Implementation:** `PERSONALITY_SYSTEM_SUMMARY.md`
3. **Check Changelog:** Version 3.0.0 in `CHANGELOG.md`
4. **Experiment:** Try all 9 archetypes!
5. **Customize:** Create your perfect AI companion

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

### Personality Not Applied
- Verify personality created: `GET /personality`
- Check service logs for errors
- Try restarting service
- Verify user_id matches

### Natural Language Not Working
- Be more explicit: "I want you to be more enthusiastic"
- Use manual API updates instead
- Check detection patterns in logs

---

## 🎉 Success!

You now have a **fully personalized AI companion** with:

✅ Unique personality traits  
✅ Custom behaviors  
✅ Evolving relationship  
✅ Natural language configuration  
✅ Milestone celebrations  

**Your AI now has a soul!** 🎭💙

---

For detailed documentation, see `PERSONALITY_SYSTEM_GUIDE.md`

For technical details, see `PERSONALITY_SYSTEM_SUMMARY.md`

