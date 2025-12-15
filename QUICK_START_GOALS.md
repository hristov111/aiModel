# Quick Start: Goals & Progress Tracking 🎯

Get started with the Goals & Progress Tracking system in 5 minutes!

---

## 🚀 Setup

### 1. Run the Migration
```bash
cd "/home/bean12/Desktop/AI Service"
alembic upgrade head
```

This creates the `goals` and `goal_progress` tables.

### 2. Restart the Service
```bash
# If using Docker
docker-compose restart

# If running locally
uvicorn app.main:app --reload
```

---

## 💬 Try It Out

### Option 1: Natural Language (Recommended)

Just chat naturally about your goals:

```
User: "I want to learn Spanish by the end of this year"

AI: "🎉 That's a fantastic goal! Learning Spanish is an amazing journey. 
     I've noted your goal to learn Spanish. 
     
     Would you like me to help you create a study plan? 
     What's motivating you to learn Spanish?"
```

**What happened behind the scenes:**
- ✅ AI detected the goal "learn Spanish"
- ✅ Created goal with category "learning"
- ✅ Set target date to 2025-12-31
- ✅ Started tracking mentions

---

### Option 2: Direct API

Create a goal programmatically:

```bash
curl -X POST http://localhost:8000/goals \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "title": "Learn Spanish",
    "description": "Become conversational in Spanish",
    "category": "learning",
    "target_date": "2025-12-31T00:00:00",
    "motivation": "Planning a trip to Spain",
    "check_in_frequency": "weekly"
  }'
```

---

## 📊 Track Progress

### Natural Language Updates

```
User: "I practiced Spanish for 30 minutes today! Completed 5 lessons."

AI: "👏 Excellent work! Consistency is key when learning a language. 
     How are you feeling about your progress so far?"
```

**What happened:**
- ✅ AI detected mention of "Learn Spanish" goal
- ✅ Recorded positive progress update
- ✅ Sentiment: positive
- ✅ Updated last_mentioned_at

### Manual Progress Logging

```bash
curl -X POST http://localhost:8000/goals/{goal_id}/progress \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "content": "Completed 5 lessons and practiced for 30 minutes",
    "progress_type": "update",
    "progress_delta": 10.0,
    "sentiment": "positive"
  }'
```

---

## 🎉 Celebrate Completions

```
User: "I just had my first full conversation in Spanish with a native speaker!"

AI: "🏆 THAT'S INCREDIBLE! What an amazing milestone! 
     You should be so proud of yourself. How did it feel? 
     Tell me all about it!"
```

**What happened:**
- ✅ AI detected milestone achievement
- ✅ Recorded as major progress
- ✅ Celebrated enthusiastically
- ✅ Asked follow-up questions

---

## 📈 View Your Progress

### Get All Your Goals

```bash
curl http://localhost:8000/goals \
  -H "X-User-Id: user123"
```

**Response:**
```json
{
  "goals": [
    {
      "id": "...",
      "title": "Learn Spanish",
      "category": "learning",
      "status": "active",
      "progress_percentage": 35.0,
      "mention_count": 12,
      ...
    }
  ],
  "total": 5,
  "active": 4,
  "completed": 1
}
```

### Get Analytics

```bash
curl http://localhost:8000/goals/analytics/summary \
  -H "X-User-Id: user123"
```

**Shows:**
- Total goals, active, completed
- Completion rate (%)
- Progress by category
- Average progress
- Recent activity
- Overdue goals

---

## 🔧 Common Scenarios

### Scenario 1: Starting a New Goal

**User says:** "I'm planning to run a marathon next year"

**AI responds:**
- Detects goal: "Run a marathon"
- Category: health
- Offers support and advice
- Asks about training plan

**API equivalent:**
```bash
POST /goals
{
  "title": "Run a marathon",
  "category": "health",
  "target_date": "2026-06-01T00:00:00"
}
```

---

### Scenario 2: Reporting Progress

**User says:** "Ran 5 miles this morning, feeling great!"

**AI responds:**
- Detects mention of marathon goal
- Records positive progress
- Celebrates consistency
- Asks about training experience

**API equivalent:**
```bash
POST /goals/{goal_id}/progress
{
  "content": "Ran 5 miles",
  "progress_type": "update",
  "sentiment": "positive",
  "progress_delta": 5.0
}
```

---

### Scenario 3: Facing Obstacles

**User says:** "I'm struggling with my marathon training. My knee hurts."

**AI responds:**
- Detects setback
- Shows empathy
- Offers support
- Suggests solutions (rest, cross-training, doctor)
- Records obstacle

**API equivalent:**
```bash
POST /goals/{goal_id}/progress
{
  "content": "Knee pain during training",
  "progress_type": "setback",
  "sentiment": "negative"
}
```

---

### Scenario 4: Completing a Goal

**User says:** "I just finished the marathon! 4 hours 23 minutes!"

**AI responds:**
- Detects completion
- Celebrates enthusiastically 🏆
- Asks how they feel
- Marks goal as completed
- Updates progress to 100%

**API equivalent:**
```bash
PUT /goals/{goal_id}
{
  "status": "completed",
  "progress_percentage": 100.0
}
```

---

## 🎨 Goal Categories

Choose the right category for better AI coaching:

| Category | Examples | AI Coaching Style |
|----------|----------|-------------------|
| **learning** | Learn Spanish, Master Python | Educational tips, practice encouragement |
| **health** | Lose weight, Run marathon | Consistency praise, rest reminders |
| **career** | Get promoted, Learn new skill | Strategic advice, confidence building |
| **financial** | Save $10k, Pay off debt | Milestone tracking, budget support |
| **personal** | Organize home, Travel to Japan | Lifestyle advice, planning help |
| **creative** | Write a novel, Learn guitar | Creative encouragement, inspiration |
| **social** | Make new friends, Join club | Social tips, confidence building |

---

## 💡 Tips for Best Results

### 1. **Be Specific**
❌ "Get better at coding"
✅ "Learn Python and build 3 projects"

### 2. **Set Deadlines (Optional but Helpful)**
✅ "Learn Spanish by December 2025"
- Helps AI prioritize check-ins
- Tracks urgency
- Provides deadline reminders

### 3. **Share Your Why (Motivation)**
✅ "I want to learn Spanish for my trip to Spain"
- AI provides more relevant encouragement
- Stored as motivation field
- Referenced in future conversations

### 4. **Update Regularly**
- Mention your goals in conversations
- Share wins AND struggles
- Be honest about progress

### 5. **Celebrate Small Wins**
- Every step forward counts
- AI will celebrate with you
- Builds momentum and motivation

---

## 🔍 Check Your Goals

### View Active Goals
```bash
curl "http://localhost:8000/goals?status=active" \
  -H "X-User-Id: user123"
```

### Get Goals Needing Check-In
```bash
curl "http://localhost:8000/goals/checkin/needed?days=7" \
  -H "X-User-Id: user123"
```

Returns goals you haven't mentioned in 7+ days.

### Get Progress History
```bash
curl "http://localhost:8000/goals/{goal_id}/progress" \
  -H "X-User-Id: user123"
```

See all updates, milestones, and setbacks for a goal.

---

## 🎯 Next Steps

1. **Set Your First Goal** - Just chat naturally about something you want to achieve
2. **Check Your Goals** - Use `GET /goals` to see what's tracked
3. **Update Progress** - Tell the AI about your progress (or log it via API)
4. **Review Analytics** - Use `GET /goals/analytics/summary` to see your stats
5. **Stay Consistent** - Regular updates = better AI coaching

---

## 🐛 Troubleshooting

### Goal Not Detected?
Try being more explicit:
- ❌ "Spanish would be cool"
- ✅ "I want to learn Spanish"

### Progress Not Tracked?
Make sure you mention the goal by name:
- ❌ "I practiced today"
- ✅ "I practiced Spanish today"

### Need More Control?
Use the API directly:
- Create goals explicitly with `POST /goals`
- Log progress manually with `POST /goals/{id}/progress`
- Update fields directly with `PUT /goals/{id}`

---

## 📚 Learn More

- **Full Guide:** See `GOALS_TRACKING_GUIDE.md`
- **API Docs:** Visit `http://localhost:8000/docs`
- **Examples:** Check `API_EXAMPLES.md`

---

## 🎉 You're Ready!

Your AI is now a proactive life coach! Start chatting about your goals and watch the magic happen. 🚀

**Remember:** The more you share, the better the AI can support you on your journey! 💪

