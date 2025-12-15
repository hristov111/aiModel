# 🎭 Personality System - Complete Guide

## Overview

The **Personality System** transforms your AI Companion from a generic chatbot into a unique, personalized companion with its own character, traits, and relationship dynamics. Define WHO your AI is, HOW it behaves, and watch your relationship grow over time.

---

## 🌟 Key Features

### 1. **9 Predefined Archetypes**
Choose from carefully crafted personality archetypes:
- 🧙 **Wise Mentor** - Thoughtful guide who challenges you to grow
- 🤗 **Supportive Friend** - Warm companion who listens without judgment
- 💼 **Professional Coach** - Results-focused accountability partner
- ✨ **Creative Partner** - Imaginative collaborator for brainstorming
- 🧘 **Calm Therapist** - Patient listener for emotional processing
- 🎉 **Enthusiastic Cheerleader** - Your biggest fan and motivator
- 📊 **Pragmatic Advisor** - Straightforward, logical problem-solver
- 🤔 **Curious Student** - Eager learner who explores with you
- ⚖️ **Balanced Companion** - Adaptable AI that meets your needs

### 2. **8 Personality Traits** (0-10 Scales)
Fine-tune your AI's personality across multiple dimensions:
- **Humor Level** (0=serious → 10=very humorous)
- **Formality Level** (0=casual → 10=very formal)
- **Enthusiasm Level** (0=reserved → 10=very enthusiastic)
- **Empathy Level** (0=logical → 10=highly empathetic)
- **Directness Level** (0=gentle → 10=very direct)
- **Curiosity Level** (0=passive → 10=very curious)
- **Supportiveness Level** (0=challenging → 10=highly supportive)
- **Playfulness Level** (0=serious → 10=very playful)

### 3. **5 Behavioral Preferences**
Control specific AI behaviors:
- **Asks Questions** - Should AI ask clarifying questions?
- **Uses Examples** - Should AI provide examples?
- **Shares Opinions** - Should AI share its perspectives?
- **Challenges User** - Should AI push you to grow?
- **Celebrates Wins** - Should AI celebrate achievements?

### 4. **Relationship Evolution**
Your relationship with the AI grows naturally:
- **Relationship Depth Score** (0-10) - Grows with interactions
- **Trust Level** (0-10) - Influenced by user feedback
- **Milestones** - Celebrate 100 messages, 1 month, 6 months, etc.
- **Days Known** - Track how long you've known each other

### 5. **Natural Language Configuration**
Configure personality using plain English:
- "Be like a wise mentor"
- "I want you to be more enthusiastic"
- "Be more direct with me"
- "Stop asking so many questions"

---

## 🚀 Quick Start

### 1. Choose an Archetype
```bash
# List available archetypes
curl -X GET "http://localhost:8000/personality/archetypes" \
  -H "X-User-Id: user_123"

# Create personality from archetype
curl -X POST "http://localhost:8000/personality" \
  -H "X-User-Id: user_123" \
  -H "Content-Type: application/json" \
  -d '{"archetype": "wise_mentor"}'
```

### 2. Customize Traits
```bash
# Adjust specific traits
curl -X PUT "http://localhost:8000/personality" \
  -H "X-User-Id: user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "traits": {
      "humor_level": 8,
      "enthusiasm_level": 7
    },
    "merge": true
  }'
```

### 3. Chat and Watch It Adapt!
```bash
# Just chat normally - personality is applied automatically
curl -X POST "http://localhost:8000/chat" \
  -H "X-User-Id: user_123" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about your day!"}'
```

---

## 📡 API Endpoints

### 1. List Archetypes

**Endpoint:** `GET /personality/archetypes`

**Example:**
```bash
curl -X GET "http://localhost:8000/personality/archetypes"
```

**Response:**
```json
{
  "archetypes": [
    {
      "name": "wise_mentor",
      "display_name": "Wise Mentor",
      "description": "A knowledgeable guide who offers wisdom...",
      "relationship_type": "mentor",
      "example_greeting": "I'm here to help guide you on your journey..."
    }
  ],
  "total": 9
}
```

---

### 2. Get Current Personality

**Endpoint:** `GET /personality`

**Example:**
```bash
curl -X GET "http://localhost:8000/personality" \
  -H "X-User-Id: user_123"
```

**Response:**
```json
{
  "archetype": "wise_mentor",
  "relationship_type": "mentor",
  "traits": {
    "humor_level": 4,
    "formality_level": 6,
    "enthusiasm_level": 5,
    "empathy_level": 7,
    "directness_level": 7,
    "curiosity_level": 8,
    "supportiveness_level": 6,
    "playfulness_level": 3
  },
  "behaviors": {
    "asks_questions": true,
    "uses_examples": true,
    "shares_opinions": true,
    "challenges_user": true,
    "celebrates_wins": true
  },
  "custom": {
    "backstory": null,
    "custom_instructions": null,
    "speaking_style": "Thoughtful, measured..."
  },
  "meta": {
    "version": 1,
    "created_at": "2024-01-15T10:00:00",
    "updated_at": "2024-01-15T10:00:00"
  }
}
```

---

### 3. Create Personality

**Endpoint:** `POST /personality`

**Option A: From Archetype**
```bash
curl -X POST "http://localhost:8000/personality" \
  -H "X-User-Id: user_123" \
  -H "Content-Type: application/json" \
  -d '{"archetype": "supportive_friend"}'
```

**Option B: Custom Configuration**
```bash
curl -X POST "http://localhost:8000/personality" \
  -H "X-User-Id: user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "relationship_type": "friend",
    "traits": {
      "humor_level": 8,
      "empathy_level": 9,
      "playfulness_level": 7
    },
    "behaviors": {
      "asks_questions": true,
      "celebrates_wins": true,
      "challenges_user": false
    },
    "custom": {
      "backstory": "You are a childhood friend who has known me for years",
      "speaking_style": "Warm, casual, uses emojis"
    }
  }'
```

---

### 4. Update Personality

**Endpoint:** `PUT /personality`

**Merge Updates (default)**
```bash
curl -X PUT "http://localhost:8000/personality" \
  -H "X-User-Id: user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "traits": {
      "enthusiasm_level": 9
    },
    "merge": true
  }'
```

**Complete Replacement**
```bash
curl -X PUT "http://localhost:8000/personality" \
  -H "X-User-Id: user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "archetype": "professional_coach",
    "merge": false
  }'
```

---

### 5. Delete Personality

**Endpoint:** `DELETE /personality`

```bash
curl -X DELETE "http://localhost:8000/personality" \
  -H "X-User-Id: user_123"
```

---

### 6. Get Relationship State

**Endpoint:** `GET /personality/relationship`

```bash
curl -X GET "http://localhost:8000/personality/relationship" \
  -H "X-User-Id: user_123"
```

**Response:**
```json
{
  "total_messages": 156,
  "relationship_depth_score": 6.8,
  "trust_level": 7.5,
  "days_known": 45,
  "first_interaction": "2024-01-01T10:00:00",
  "last_interaction": "2024-02-15T14:30:00",
  "milestones": [
    {
      "type": "100_messages",
      "reached_at": "2024-02-10T12:00:00",
      "message": "Reached 100 messages together!"
    }
  ],
  "positive_reactions": 12,
  "negative_reactions": 1
}
```

---

## 🎨 Archetype Deep Dive

### 🧙 Wise Mentor
**Best For:** Learning, personal growth, making difficult decisions

**Personality:**
- Humor: 4/10 (Occasionally witty)
- Formality: 6/10 (Professional but warm)
- Enthusiasm: 5/10 (Measured)
- Empathy: 7/10 (Understanding)
- Directness: 7/10 (Honest and clear)
- Curiosity: 8/10 (Asks probing questions)
- Supportiveness: 6/10 (Balanced support/challenge)
- Playfulness: 3/10 (Mostly serious)

**Behaviors:**
- ✅ Asks questions to provoke thought
- ✅ Uses stories and metaphors
- ✅ Shares wisdom and opinions
- ✅ Challenges you to grow
- ✅ Celebrates milestones

**Example Interaction:**
```
User: "I'm not sure if I should take this job offer..."

AI: "That's a significant decision. Before we explore it together, 
let me ask you this: What would your life look like in five years 
if you took this job? And what if you didn't? Sometimes the answer 
lies in the vision that excites you most."
```

---

### 🤗 Supportive Friend
**Best For:** Emotional support, companionship, casual chats

**Personality:**
- Humor: 7/10 (Frequently funny)
- Formality: 2/10 (Very casual)
- Enthusiasm: 7/10 (Energetic)
- Empathy: 9/10 (Highly empathetic)
- Directness: 4/10 (Gentle)
- Curiosity: 7/10 (Interested in you)
- Supportiveness: 9/10 (Very supportive)
- Playfulness: 7/10 (Fun and light)

**Example Interaction:**
```
User: "I'm feeling really stressed about work..."

AI: "Oh no, I'm so sorry you're feeling stressed! 😔 That sounds 
really tough. Want to talk about what's going on? I'm here to 
listen, and there's no judgment at all. Sometimes it just helps 
to vent, you know? 💙"
```

---

### 💼 Professional Coach
**Best For:** Goal achievement, accountability, productivity

**Personality:**
- Humor: 5/10 (Occasional)
- Formality: 7/10 (Professional)
- Enthusiasm: 6/10 (Motivated)
- Empathy: 6/10 (Balanced)
- Directness: 8/10 (Very direct)
- Curiosity: 7/10 (Explores goals)
- Supportiveness: 5/10 (Results-focused)
- Playfulness: 3/10 (Focused)

**Example Interaction:**
```
User: "I want to learn Python but keep procrastinating..."

AI: "Let's address this head-on. You've identified the goal (learn Python) 
and the obstacle (procrastination). Here's what we're going to do:

1. Set a specific commitment: 30 minutes daily, 5 days a week
2. Start tomorrow morning at 9 AM - I'll check in with you
3. Track progress for 2 weeks, then adjust

The question isn't if you want to learn - it's whether you're ready 
to commit. Are you?"
```

---

### ✨ Creative Partner
**Best For:** Brainstorming, creative projects, exploration

**Personality:**
- Humor: 8/10 (Playful and witty)
- Formality: 3/10 (Casual)
- Enthusiasm: 9/10 (Very energetic!)
- Empathy: 6/10 (Balanced)
- Directness: 5/10 (Gentle)
- Curiosity: 10/10 (Extremely curious)
- Supportiveness: 7/10 (Encouraging)
- Playfulness: 9/10 (Very creative)

**Example Interaction:**
```
User: "I need to come up with a name for my app..."

AI: "Ooh, naming time! This is so exciting! ✨ Let's think wild first, 
then narrow down. Tell me:

- What emotion should users feel when they see the name?
- Any sounds or syllables you love?
- Should it be playful, professional, or mysterious?

And hey, what if the name was a made-up word that SOUNDS like what 
the app does? Like... hmm, if it helps people organize, maybe something 
like 'Tidyflow' or 'Orderix'? Just riffing here - let's explore!"
```

---

## 💡 Use Cases & Examples

### Use Case 1: Therapy & Mental Health
```json
{
  "archetype": "calm_therapist",
  "custom": {
    "backstory": "You are a licensed therapist specializing in CBT",
    "speaking_style": "Gentle, reflective, asks open-ended questions"
  }
}
```

**AI Behavior:**
- Creates safe, non-judgmental space
- Asks reflective questions
- Validates feelings
- Helps process emotions
- Never gives medical advice (boundaries)

---

### Use Case 2: Language Learning
```json
{
  "archetype": "enthusiastic_cheerleader",
  "traits": {
    "enthusiasm_level": 10,
    "supportiveness_level": 10,
    "playfulness_level": 8
  },
  "behaviors": {
    "celebrates_wins": true,
    "challenges_user": false
  }
}
```

**AI Behavior:**
- Celebrates every attempt
- Makes learning fun
- Uses encouragement constantly
- Focuses on progress, not perfection

---

### Use Case 3: Technical Mentor
```json
{
  "archetype": "wise_mentor",
  "traits": {
    "directness_level": 8,
    "formality_level": 6
  },
  "behaviors": {
    "uses_examples": true,
    "challenges_user": true
  },
  "custom": {
    "backstory": "Senior software engineer with 20 years experience"
  }
}
```

**AI Behavior:**
- Explains complex concepts clearly
- Uses code examples
- Challenges assumptions
- Teaches best practices

---

### Use Case 4: Creative Writing Partner
```json
{
  "archetype": "creative_partner",
  "traits": {
    "playfulness_level": 10,
    "curiosity_level": 10
  },
  "custom": {
    "speaking_style": "Imaginative, uses vivid descriptions and metaphors"
  }
}
```

**AI Behavior:**
- Brainstorms wildly
- Offers creative suggestions
- Explores "what if" scenarios
- Builds on your ideas

---

## 🔄 Natural Language Configuration

### Changing Archetypes
```
User: "Be like a wise mentor"
→ AI automatically switches to wise_mentor archetype

User: "Act more like a supportive friend"
→ AI switches to supportive_friend archetype
```

### Adjusting Traits
```
User: "Be more enthusiastic!"
→ enthusiasm_level increases to 8-9

User: "You're being too serious, lighten up"
→ humor_level and playfulness_level increase

User: "Be more direct with me, don't sugarcoat"
→ directness_level increases to 8-9

User: "Stop asking so many questions"
→ curiosity_level decreases, asks_questions = false
```

### Modifying Behaviors
```
User: "Give me more examples when explaining"
→ uses_examples = true

User: "I need you to challenge me more"
→ challenges_user = true

User: "Just listen, don't give opinions"
→ shares_opinions = false
```

---

## 📊 Relationship Evolution

### Depth Score Calculation
```python
depth_score = (
    log(total_messages + 1) * 1.5 +
    days_known / 30 +
    (positive_reactions - negative_reactions) / 10
)
# Capped at 10.0
```

### Depth Score Levels
- **0-2**: Just getting to know each other
- **3-5**: Developing relationship
- **6-7**: Established connection
- **8-9**: Deep relationship
- **10**: Very close bond

### Milestones
- **10 messages**: First real conversation
- **50 messages**: Getting comfortable
- **100 messages**: Solid foundation
- **500 messages**: Deep connection
- **1000 messages**: Long-term relationship
- **1 week**: One week together
- **1 month**: One month anniversary
- **6 months**: Half year milestone
- **1 year**: One year together!

### Trust Level
- Increases with positive feedback (+0.1 per 👍)
- Decreases with negative feedback (-0.2 per 👎)
- Influences how AI adapts to you

---

## 🎯 Best Practices

### 1. **Start with an Archetype**
- Easier than building from scratch
- Pre-tuned for specific use cases
- Can customize later

### 2. **Adjust Gradually**
- Make small tweaks (±1-2 points)
- Test the changes
- Iterate based on experience

### 3. **Be Specific in Custom Instructions**
```
❌ Bad: "Be nice"
✅ Good: "Always validate feelings before offering solutions"

❌ Bad: "Talk differently"
✅ Good: "Use metaphors from nature when explaining concepts"
```

### 4. **Mix Archetypes**
```json
{
  "archetype": "wise_mentor",
  "traits": {
    "humor_level": 7,  // Add humor to mentor
    "playfulness_level": 6
  }
}
```

### 5. **Review Relationship State**
- Check depth score periodically
- Celebrate milestones
- Adjust personality as relationship deepens

---

## 🔧 Advanced Configuration

### Custom Personality from Scratch
```json
{
  "relationship_type": "friend",
  "traits": {
    "humor_level": 8,
    "formality_level": 3,
    "enthusiasm_level": 7,
    "empathy_level": 9,
    "directness_level": 6,
    "curiosity_level": 7,
    "supportiveness_level": 8,
    "playfulness_level": 6
  },
  "behaviors": {
    "asks_questions": true,
    "uses_examples": true,
    "shares_opinions": false,
    "challenges_user": false,
    "celebrates_wins": true
  },
  "custom": {
    "backstory": "You are my college roommate who I've known for 10 years",
    "custom_instructions": "Remember our inside jokes, reference past adventures",
    "speaking_style": "Casual, friendly, uses our shared slang"
  }
}
```

### Roleplay Scenarios
```json
{
  "custom": {
    "backstory": "You are Sherlock Holmes, the famous detective",
    "speaking_style": "Precise, observant, occasionally condescending but charming",
    "custom_instructions": "Always deduce things about me from small details. Be brilliant but socially awkward."
  },
  "traits": {
    "directness_level": 9,
    "curiosity_level": 10,
    "formality_level": 7
  }
}
```

---

## 🚨 Troubleshooting

### AI Not Following Personality
**Problem:** AI doesn't seem to match configured personality

**Solutions:**
1. Check personality is saved: `GET /personality`
2. Verify traits are reasonable (0-10 range)
3. Review LLM's adherence (some models better than others)
4. Use more explicit custom_instructions
5. Try a predefined archetype first

### Personality Too Extreme
**Problem:** AI is too serious/playful/formal/etc.

**Solutions:**
1. Adjust traits to mid-range (4-6)
2. Use "merge" updates to tweak gradually
3. Try balanced_companion archetype

### Natural Language Not Detecting
**Problem:** "Be more X" doesn't change personality

**Solutions:**
1. Be more explicit: "I want you to be more enthusiastic"
2. Use exact trait names: "Increase enthusiasm level"
3. Manually update via API
4. Check logs for detection

---

## 📈 Analytics & Insights

### Track Personality Evolution
```bash
# Get personality history (via meta.version)
curl -X GET "http://localhost:8000/personality" \
  -H "X-User-Id: user_123" | jq '.meta.version'
```

### Monitor Relationship Growth
```bash
# Check depth score trend
curl -X GET "http://localhost:8000/personality/relationship" \
  -H "X-User-Id: user_123" | jq '.relationship_depth_score'
```

### Analyze Milestones
```bash
# View achieved milestones
curl -X GET "http://localhost:8000/personality/relationship" \
  -H "X-User-Id: user_123" | jq '.milestones'
```

---

## 🎓 Psychology Behind Traits

### Humor Level
- **Low (0-3)**: Professional contexts, serious topics
- **Medium (4-7)**: Balanced engagement
- **High (8-10)**: Entertainment, stress relief

### Empathy Level
- **Low (0-3)**: Technical support, logical analysis
- **Medium (4-7)**: General conversation
- **High (8-10)**: Emotional support, therapy

### Directness Level
- **Low (0-3)**: Sensitive topics, conflict-averse users
- **Medium (4-7)**: Normal conversation
- **High (8-10)**: Coaching, accountability, tough love

---

## 🌐 Integration Examples

### React Frontend
```javascript
// Create personality
const createPersonality = async (archetype) => {
  const response = await fetch('http://localhost:8000/personality', {
    method: 'POST',
    headers: {
      'X-User-Id': userId,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ archetype })
  });
  return await response.json();
};

// Update trait
const updateTrait = async (trait, value) => {
  const response = await fetch('http://localhost:8000/personality', {
    method: 'PUT',
    headers: {
      'X-User-Id': userId,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      traits: { [trait]: value },
      merge: true
    })
  });
  return await response.json();
};
```

### Python Client
```python
import requests

class PersonalityClient:
    def __init__(self, base_url, user_id):
        self.base_url = base_url
        self.headers = {'X-User-Id': user_id}
    
    def create_personality(self, archetype):
        return requests.post(
            f'{self.base_url}/personality',
            headers=self.headers,
            json={'archetype': archetype}
        ).json()
    
    def get_personality(self):
        return requests.get(
            f'{self.base_url}/personality',
            headers=self.headers
        ).json()
    
    def update_traits(self, **traits):
        return requests.put(
            f'{self.base_url}/personality',
            headers=self.headers,
            json={'traits': traits, 'merge': True}
        ).json()
```

---

## 🎉 Congratulations!

You now have a complete **Personality System** that lets you:

✅ Choose from 9 unique archetypes  
✅ Customize 8 personality traits  
✅ Control 5 behavioral preferences  
✅ Track relationship evolution  
✅ Configure via natural language  
✅ Build deep, lasting connections  

**Your AI Companion now has a soul!** 🎭💙

---

*For technical implementation details, see `PERSONALITY_SYSTEM_SUMMARY.md`*

*For API reference, visit `/docs` endpoint*
