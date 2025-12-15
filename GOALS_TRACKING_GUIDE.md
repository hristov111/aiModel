# Goals & Progress Tracking System Guide

## 🎯 Overview

The **Goals & Progress Tracking System** transforms your AI from a reactive chatbot into a proactive life companion that helps users achieve their dreams. It automatically detects goals from natural language, tracks progress over time, provides check-ins, and celebrates achievements.

---

## ✨ Key Features

### 1. **Automatic Goal Detection**
- Detects new goal declarations from natural conversation
- Identifies explicit goals ("I want to learn Spanish") and implicit ones ("I'm planning to...")
- Extracts goal category, motivation, and deadlines automatically

### 2. **Intelligent Progress Tracking**
- Monitors mentions of existing goals in conversations
- Detects positive progress, setbacks, and completions
- Tracks sentiment and emotional context of progress updates
- Maintains progress notes with timestamps

### 3. **Comprehensive Analytics**
- Goal completion rates
- Progress by category
- Deadline tracking and overdue alerts
- Recent activity history
- Category breakdowns

### 4. **Proactive Check-Ins**
- Identifies goals that need attention
- Configurable check-in frequency (daily, weekly, monthly)
- Automatic reminders for stale goals

### 5. **AI-Powered Support**
- AI adapts responses based on goal context
- Celebrates achievements enthusiastically
- Offers encouragement during setbacks
- Provides strategic advice for different goal types

### 6. **Multi-Goal Management**
- Track unlimited goals simultaneously
- Organize by categories: learning, health, career, financial, personal, creative, social
- Milestone tracking within each goal
- Status management: active, completed, paused, abandoned

---

## 🏗️ Architecture

### Database Schema

#### Goals Table
```
goals
├── id (UUID, PK)
├── user_id (UUID, FK → users.id)
├── title (String, 255 chars)
├── description (Text, optional)
├── category (String: learning, health, career, etc.)
├── status (String: active, completed, paused, abandoned)
├── progress_percentage (Float, 0-100)
├── created_at (DateTime)
├── updated_at (DateTime)
├── target_date (DateTime, optional)
├── completed_at (DateTime, optional)
├── last_mentioned_at (DateTime)
├── mention_count (Integer)
├── check_in_frequency (String: daily, weekly, biweekly, monthly, never)
├── last_check_in (DateTime)
├── milestones (JSONB array)
├── progress_notes (JSONB array)
├── motivation (Text)
├── obstacles (JSONB array)
└── metadata (JSONB)
```

#### Goal Progress Table
```
goal_progress
├── id (UUID, PK)
├── goal_id (UUID, FK → goals.id)
├── user_id (UUID, FK → users.id)
├── progress_type (String: mention, update, milestone, setback, completion)
├── content (Text)
├── progress_delta (Float, can be negative)
├── sentiment (String: positive, negative, neutral)
├── emotion (String, from emotion detection)
├── conversation_id (UUID, optional)
├── detected_automatically (Boolean)
├── created_at (DateTime)
└── metadata (JSONB)
```

### Core Components

1. **`GoalDetector`** (`app/services/goal_detector.py`)
   - Pattern-based goal detection
   - Progress sentiment analysis
   - Category classification
   - Completion detection

2. **`GoalService`** (`app/services/goal_service.py`)
   - CRUD operations for goals
   - Progress recording
   - Analytics generation
   - Check-in management

3. **`PromptBuilder` Integration**
   - Injects goal context into AI prompts
   - Provides goal-aware response guidance
   - Adapts tone based on progress type

4. **`ChatService` Integration**
   - Automatic goal detection per message
   - Progress tracking in real-time
   - Seamless integration with emotion and personality systems

---

## 📡 API Endpoints

### Create a Goal

```http
POST /goals
Content-Type: application/json
X-User-Id: user123

{
  "title": "Learn Spanish",
  "description": "Become conversational in Spanish for my trip to Spain",
  "category": "learning",
  "target_date": "2025-12-31T00:00:00",
  "motivation": "I want to connect with locals and understand the culture",
  "check_in_frequency": "weekly"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Learn Spanish",
  "description": "Become conversational in Spanish",
  "category": "learning",
  "status": "active",
  "progress_percentage": 0.0,
  "target_date": "2025-12-31T00:00:00",
  "created_at": "2024-01-15T10:00:00",
  "mention_count": 0,
  "check_in_frequency": "weekly",
  "milestones": [],
  "progress_notes": [],
  "motivation": "For my trip to Spain",
  "obstacles": [],
  "message": "Goal created successfully"
}
```

### Get All Goals

```http
GET /goals?status=active&include_completed=false
X-User-Id: user123
```

**Query Parameters:**
- `status` (optional): Filter by status (active, completed, paused, abandoned)
- `category` (optional): Filter by category
- `include_completed` (boolean): Include completed goals

**Response:**
```json
{
  "goals": [
    {
      "id": "...",
      "title": "Learn Spanish",
      "status": "active",
      "progress_percentage": 35.0,
      ...
    }
  ],
  "total": 5,
  "active": 4,
  "completed": 1,
  "message": "Goals retrieved successfully"
}
```

### Get a Specific Goal

```http
GET /goals/{goal_id}
X-User-Id: user123
```

### Update a Goal

```http
PUT /goals/{goal_id}
Content-Type: application/json
X-User-Id: user123

{
  "progress_percentage": 45.0,
  "status": "active"
}
```

### Delete a Goal (Set to Abandoned)

```http
DELETE /goals/{goal_id}
X-User-Id: user123
```

### Log Progress Manually

```http
POST /goals/{goal_id}/progress
Content-Type: application/json
X-User-Id: user123

{
  "content": "Completed 5 lessons today and practiced speaking for 30 minutes!",
  "progress_type": "update",
  "progress_delta": 10.0,
  "sentiment": "positive"
}
```

**Progress Types:**
- `mention` - Simply mentioned the goal
- `update` - Made progress
- `milestone` - Reached a milestone
- `setback` - Faced an obstacle
- `completion` - Completed the goal

### Get Progress History

```http
GET /goals/{goal_id}/progress?limit=50
X-User-Id: user123
```

**Response:**
```json
{
  "goal_id": "123e4567-...",
  "entries": [
    {
      "id": "...",
      "type": "update",
      "content": "Practiced for 30 minutes",
      "sentiment": "positive",
      "emotion": "excited",
      "progress_delta": 5.0,
      "created_at": "2024-02-20T14:30:00"
    }
  ],
  "total": 12,
  "message": "Progress history retrieved successfully"
}
```

### Get Goal Analytics

```http
GET /goals/analytics/summary
X-User-Id: user123
```

**Response:**
```json
{
  "total_goals": 10,
  "active_goals": 6,
  "completed_goals": 3,
  "paused_goals": 1,
  "abandoned_goals": 0,
  "completion_rate": 30.0,
  "by_category": {
    "learning": {
      "total": 4,
      "active": 3,
      "completed": 1
    },
    "health": {
      "total": 3,
      "active": 2,
      "completed": 1
    }
  },
  "average_progress": 42.5,
  "goals_with_deadlines": 5,
  "overdue_goals": 1,
  "recent_activity": [
    {
      "goal_id": "...",
      "type": "update",
      "sentiment": "positive",
      "date": "2024-02-20T14:30:00"
    }
  ],
  "message": "Analytics retrieved successfully"
}
```

### Get Goals Needing Check-In

```http
GET /goals/checkin/needed?days=7
X-User-Id: user123
```

Returns goals that haven't been mentioned or checked on in the specified number of days.

---

## 🤖 AI Integration

### Automatic Goal Detection in Chat

The AI automatically detects goals from natural language:

**User:** "I want to learn Spanish by the end of this year"
**AI Response:** 
- ✅ Automatically creates goal: "Learn Spanish"
- Category: learning
- Target date: 2025-12-31
- 🎉 Acknowledges and shows enthusiasm
- Offers to help plan

### Progress Tracking in Conversations

**User:** "I practiced Spanish for 30 minutes today!"
**AI Response:**
- ✅ Detects mention of "Learn Spanish" goal
- Records positive progress update
- Increments mention count
- Updates last_mentioned_at
- 👏 Celebrates the effort
- Asks follow-up questions

### Completion Celebration

**User:** "I just finished my first Spanish conversation with a native speaker!"
**AI Response:**
- ✅ Detects major milestone
- Records completion if appropriate
- 🏆 Celebrates enthusiastically
- Asks about feelings and next steps

### Setback Support

**User:** "I'm struggling with Spanish verb conjugations. It's too hard."
**AI Response:**
- ✅ Detects setback sentiment
- Records obstacle
- 💪 Provides empathetic support
- Offers problem-solving strategies
- Encourages persistence

---

## 🧩 Integration with Other Systems

### Emotion Detection Integration
- Progress updates include detected emotions
- AI adapts encouragement based on emotional state
- Tracks emotional trends per goal

### Personality System Integration
- Goal coaching style matches AI personality archetype
- "Professional Coach" → Strategic advice
- "Enthusiastic Cheerleader" → High energy encouragement
- "Calm Therapist" → Gentle, supportive guidance

### Preference System Integration
- Respects communication preferences while coaching
- Adapts response length and style
- Honors emoji usage preferences

---

## 📊 Use Cases

### Learning Goals
**Example:** "Learn Python programming"
- AI tracks study sessions
- Celebrates completed projects
- Helps debug issues
- Recommends resources
- Monitors progress toward certification

### Health & Fitness Goals
**Example:** "Lose 20 pounds by summer"
- Tracks workout mentions
- Celebrates consistency
- Provides encouragement during plateaus
- Reminds about rest and self-care
- Monitors progress toward target

### Career Goals
**Example:** "Get promoted to senior engineer"
- Tracks skill development
- Celebrates achievements
- Provides strategic advice
- Helps prepare for interviews
- Monitors timeline

### Creative Goals
**Example:** "Write a novel"
- Tracks writing sessions
- Celebrates word count milestones
- Helps with motivation
- Provides creative encouragement
- Monitors progress toward completion

---

## 🎨 Goal Categories

### Supported Categories
1. **learning** - Education, skills, courses, languages
2. **health** - Fitness, diet, mental health, wellness
3. **career** - Job, promotion, skills, networking
4. **financial** - Savings, investments, debt reduction
5. **personal** - Relationships, hobbies, travel, organization
6. **creative** - Writing, art, music, design, photography
7. **social** - Making friends, networking, community

Each category gets tailored AI coaching style and advice.

---

## 🔧 Configuration

### Check-In Frequencies
- `daily` - AI checks in daily
- `weekly` - AI checks in weekly (recommended)
- `biweekly` - AI checks in every 2 weeks
- `monthly` - AI checks in monthly
- `never` - No automatic check-ins

### Progress Delta Guidelines
- Small progress: +5 to +10
- Milestone: +15 to +25
- Major achievement: +30 to +50
- Setback: -5 to -15
- Completion: Set progress to 100%

---

## 💡 Best Practices

### For Users
1. **Be Natural** - Just talk about your goals normally, the AI will detect them
2. **Update Regularly** - Mention your progress in conversations
3. **Be Honest** - Share struggles and setbacks, AI will help
4. **Celebrate Wins** - Tell the AI about achievements, no matter how small
5. **Set Realistic Deadlines** - Optional but helps with tracking

### For Developers
1. **Tune Detection Thresholds** - Adjust confidence scores in `GoalDetector`
2. **Customize Categories** - Add domain-specific categories as needed
3. **Monitor Performance** - Track automatic vs manual goal creation
4. **Enhance Patterns** - Add new detection patterns based on user language
5. **Integrate Analytics** - Use goal data for user insights

---

## 🚀 Quick Start

### 1. Run Migration
```bash
alembic upgrade head
```

### 2. Create a Goal via API
```bash
curl -X POST http://localhost:8000/goals \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "title": "Run a marathon",
    "category": "health",
    "target_date": "2025-12-31T00:00:00",
    "check_in_frequency": "weekly"
  }'
```

### 3. Chat Naturally
```
User: "I started training for a marathon today!"
AI: "🎉 That's amazing! I see you've set a goal to run a marathon. 
     How did your first training session go?"
```

### 4. Check Analytics
```bash
curl http://localhost:8000/goals/analytics/summary \
  -H "X-User-Id: user123"
```

---

## 🔍 Technical Details

### Goal Detection Algorithm

1. **Pattern Matching**
   - Explicit patterns: "my goal is to", "i want to", "i'm planning to"
   - Implicit patterns: "starting", "decided to", "working on"
   - Confidence scoring: 0.9 for explicit, 0.6 for implicit

2. **Category Classification**
   - Keyword matching across predefined categories
   - Scoring system for multi-category indicators
   - Default to "personal" if ambiguous

3. **Progress Sentiment Analysis**
   - Positive indicators: "made progress", "finished", "achieved"
   - Negative indicators: "struggling", "stuck", "frustrated"
   - Neutral indicators: "still working", "currently practicing"

4. **Completion Detection**
   - Pattern: "finished", "completed", "reached my goal"
   - Auto-completes goal (status → completed, progress → 100%)

### Performance Considerations

- Goal detection runs asynchronously
- Progress recording is non-blocking
- Analytics queries are optimized with indexes
- Check-in queries use date-based filtering

---

## 📈 Metrics & KPIs

### System Metrics
- Goals created per user
- Average completion rate
- Time to completion
- Active vs abandoned rate
- Check-in engagement rate

### User Engagement
- Goal mentions per conversation
- Progress updates frequency
- Manual vs automatic tracking ratio
- Category distribution

---

## 🐛 Troubleshooting

### Goal Not Detected
**Problem:** User mentions a goal but it's not created
**Solution:**
- Check confidence threshold in `GoalDetector.detect_goal()`
- Add custom patterns for domain-specific language
- Verify message processing in `ChatService`

### Progress Not Tracking
**Problem:** Goal mentions don't record progress
**Solution:**
- Verify goal keywords match in `_extract_keywords()`
- Check match_score threshold (default 0.3)
- Ensure user_id consistency

### Analytics Slow
**Problem:** `/goals/analytics/summary` is slow
**Solution:**
- Verify database indexes are created
- Limit active goals query to recent entries
- Add caching layer for frequently accessed analytics

---

## 🔮 Future Enhancements

### Planned Features
1. **Smart Milestones** - AI suggests milestone checkpoints
2. **Goal Recommendations** - AI suggests related goals
3. **Collaboration** - Share goals with friends
4. **Gamification** - Points, badges, streaks
5. **Habit Tracking** - Daily/weekly habit formation
6. **Goal Templates** - Pre-built goal structures
7. **Visual Progress** - Charts and graphs
8. **Reminders** - Push notifications for check-ins
9. **Goal Dependencies** - Track prerequisite goals
10. **Time Tracking** - Automatic time spent per goal

---

## 📚 API Reference Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/goals` | POST | Create a goal |
| `/goals` | GET | List all goals |
| `/goals/{id}` | GET | Get specific goal |
| `/goals/{id}` | PUT | Update goal |
| `/goals/{id}` | DELETE | Delete goal (abandon) |
| `/goals/{id}/progress` | POST | Log progress |
| `/goals/{id}/progress` | GET | Get progress history |
| `/goals/analytics/summary` | GET | Get analytics |
| `/goals/checkin/needed` | GET | Get stale goals |

---

## 🤝 Contributing

When adding new goal detection patterns:
1. Add patterns to `GOAL_PATTERNS` in `goal_detector.py`
2. Test with real user messages
3. Adjust confidence thresholds
4. Document the pattern purpose

When adding new categories:
1. Add to `CATEGORY_PATTERNS` in `goal_detector.py`
2. Add category-specific guidance in `_build_goal_instructions()`
3. Update API documentation

---

## 📄 License

Part of the AI Companion Service. See main project LICENSE.

---

## 🎯 Summary

The Goals & Progress Tracking System provides:
- ✅ Automatic goal detection from natural language
- ✅ Intelligent progress tracking and sentiment analysis
- ✅ Comprehensive analytics and insights
- ✅ Proactive check-ins and reminders
- ✅ AI-powered coaching and encouragement
- ✅ Seamless integration with emotion and personality systems
- ✅ Multi-category support for diverse life goals
- ✅ Complete REST API for external integrations

Transform your AI from a chatbot into a life coach! 🚀

