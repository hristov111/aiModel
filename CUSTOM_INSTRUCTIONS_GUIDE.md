# How the AI Responds to Custom Instructions & Behavior Requests

## 🎯 Executive Summary

Your AI Companion Service has **THREE powerful systems** working together to handle custom instructions and behavior preferences:

1. **Communication Preferences** - Language, tone, formality, emoji usage, response length, explanation style
2. **Personality System** - Character archetypes, traits (0-10 scales), and behaviors
3. **Custom Instructions** - Freeform instructions stored in personality profile

## ✅ What Currently Works

### 1. Communication Preferences (HARD ENFORCED)

These preferences are **MANDATORY** - the AI MUST follow them:

#### Supported Preferences:
- **Language**: English, Spanish, French, German, Italian, Portuguese
- **Formality**: casual, formal, professional
- **Tone**: enthusiastic, calm, friendly, neutral
- **Emoji Usage**: true/false
- **Response Length**: brief, detailed, balanced
- **Explanation Style**: simple, technical, analogies

#### How to Use:

**Natural Language (Auto-detected):**
```bash
"Speak Spanish to me"
"Be more casual"
"Use emojis please"
"Keep responses brief"
"No emojis"
"Explain things simply"
```

**API (Explicit):**
```bash
POST /preferences
{
  "language": "Spanish",
  "formality": "casual",
  "emoji_usage": true,
  "response_length": "brief"
}
```

#### How It Works:
1. User sends message: "I prefer casual conversation with emojis"
2. System auto-detects: `formality=casual`, `emoji_usage=true`
3. Stores in database: `users.extra_metadata.communication_preferences`
4. **Injects into EVERY prompt as CRITICAL REQUIREMENTS:**

```
⚠️ CRITICAL COMMUNICATION REQUIREMENTS (MUST FOLLOW):
💬 FORMALITY: Use casual, informal language. 
    Use contractions (you're, I'm, don't). Be relaxed and friendly.
😀 EMOJIS: Include relevant emojis in your responses to add personality.
```

5. LLM **MUST** follow these rules
6. Applied automatically to **ALL future conversations**

---

### 2. Personality System (STRONG INFLUENCE)

The personality system shapes **HOW** the AI behaves and talks:

#### Available Archetypes:
- `wise_mentor` - Thoughtful advisor who challenges and guides
- `supportive_friend` - Warm, caring, non-judgmental listener
- `professional_coach` - Results-oriented, holds accountable
- `creative_partner` - Brainstorms, explores ideas
- `calm_therapist` - Patient, helps process emotions
- `enthusiastic_cheerleader` - Energetic supporter
- `pragmatic_advisor` - Direct, practical, no-nonsense
- `curious_student` - Learns alongside, asks questions
- `girlfriend` - Romantic, affectionate companion

#### How to Use:

**Natural Language (Auto-detected):**
```bash
"Be like a wise mentor"
"Act like a supportive friend"
"I want you to be more enthusiastic"
"Be funnier"
"Ask me more questions"
"Stop challenging me so much"
"Don't celebrate my wins"
```

**API:**
```bash
POST /personality
{
  "archetype": "wise_mentor",
  "traits": {
    "humor_level": 8,
    "directness_level": 7,
    "enthusiasm_level": 6
  },
  "behaviors": {
    "asks_questions": true,
    "challenges_user": true
  }
}
```

#### Supported Traits (0-10 scales):
- `humor_level`: 0=serious, 10=very humorous
- `formality_level`: 0=casual, 10=very formal
- `enthusiasm_level`: 0=reserved, 10=very enthusiastic
- `empathy_level`: 0=logical, 10=highly empathetic
- `directness_level`: 0=indirect, 10=very direct
- `curiosity_level`: 0=passive, 10=very curious
- `supportiveness_level`: 0=challenging, 10=highly supportive
- `playfulness_level`: 0=serious, 10=very playful

#### Supported Behaviors (on/off):
- `asks_questions` - Should AI ask follow-up questions?
- `uses_examples` - Should AI give examples?
- `shares_opinions` - Should AI share its opinions?
- `challenges_user` - Should AI challenge/push you?
- `celebrates_wins` - Should AI celebrate your achievements?

#### How It Works:
1. User: "Be more enthusiastic and ask more questions"
2. System detects: `enthusiasm_level=8`, `asks_questions=true`
3. Stores in: `personality_profiles` table
4. Builds custom persona for prompts:

```
You are a wise mentor with enhanced traits:
- Enthusiasm: 8/10 (very enthusiastic)
- Directness: 7/10 (quite direct)

Behaviors:
- Ask thoughtful follow-up questions
- Challenge the user to think deeper
```

5. Applied to **ALL conversations** for that user
6. Evolves over time based on relationship depth

---

### 3. Custom Instructions (Flexible Text)

For anything not covered by preferences or personality:

#### Storage Location:
- In `personality_profiles.custom_instructions` (JSON field)
- OR auto-detected from messages like: "I want you to..."

#### Examples:
```bash
# Natural language
"I want you to always start responses with a quote"
"Never use the word 'basically'"
"When I ask about code, always show examples"
```

#### API:
```bash
PUT /personality/{user_id}
{
  "custom_config": {
    "speaking_style": "Always use metaphors from nature",
    "restrictions": "Never use technical jargon",
    "special_rules": "End responses with a question"
  }
}
```

---

## ⚠️ Current Limitations

### 1. **No Built-in Word Blacklist System**
**Current State:**
- ❌ No dedicated system to block specific words
- ❌ No "never say X" enforcement
- ❌ No word filtering or replacement

**What Happens:**
If you say: "Never use the word 'basically'"
- ✅ Will be detected as `custom_instructions`
- ✅ Will be added to system prompt
- ⚠️ BUT: LLM may still occasionally use the word (depends on model compliance)

**Workaround:**
- Add to custom instructions: "NEVER use the word 'basically'. This is CRITICAL."
- Use personality traits: Set `formality_level=9` (formal language avoids casual words)
- Use preferences: `explanation_style=technical` (technical explanations avoid casual words)

### 2. **Limited Custom Instruction Enforcement**
**Current State:**
- Custom instructions are added to prompts as text
- No validation that AI follows them
- Compliance depends on LLM model quality

**Example:**
```
Custom Instructions:
- Never use the word "sorry"
- Always end with a question
- Use pirate speak

Reality: AI will TRY to follow these, but may occasionally forget
```

### 3. **No Real-Time Validation**
**Current State:**
- System doesn't check if AI followed the rules
- No post-processing to remove forbidden words
- No retry if rules are violated

---

## 🔥 Recommended Approach for Your Use Case

### If you want AI to act a certain way:
**✅ Use Personality System**
```bash
# Natural language
"Be more enthusiastic"
"Be less formal"
"Ask me questions"
"Don't challenge me"

# Or API
POST /personality
{
  "traits": {"enthusiasm_level": 8, "formality_level": 3},
  "behaviors": {"asks_questions": true}
}
```

### If you want specific communication style:
**✅ Use Communication Preferences**
```bash
# Natural language
"Speak Spanish"
"Be casual"
"Use emojis"
"Keep it brief"
"Explain simply"

# Or API
POST /preferences
{
  "language": "Spanish",
  "formality": "casual",
  "emoji_usage": true,
  "response_length": "brief"
}
```

### If you want AI to never say a specific word:
**⚠️ Use Custom Instructions (Best Effort)**
```bash
# Natural language (will be detected)
"Never use the word 'basically'"
"Don't say 'sorry' all the time"
"Avoid using technical jargon"

# Or API
PUT /personality/{user_id}
{
  "custom_config": {
    "word_restrictions": "CRITICAL: Never use the words: basically, sorry, unfortunately. These are FORBIDDEN."
  }
}
```

**Note:** This is "best effort" - the AI will try, but may occasionally forget.

### If you want specific behavior patterns:
**✅ Use Personality Behaviors**
```bash
# Natural language
"Always give examples"
"Don't ask so many questions"
"Share your opinions"
"Celebrate my wins"

# Or API
POST /personality
{
  "behaviors": {
    "uses_examples": true,
    "asks_questions": false,
    "shares_opinions": true,
    "celebrates_wins": true
  }
}
```

---

## 💡 What Could Be Added

### 1. **Word Blacklist System**
```python
# Could add to prompt_builder.py
class WordBlacklist:
    """Filter forbidden words from AI responses."""
    
    def __init__(self, forbidden_words: List[str]):
        self.forbidden = [w.lower() for w in forbidden_words]
    
    def check_response(self, text: str) -> bool:
        """Returns True if response contains forbidden words."""
        words = text.lower().split()
        return any(word in self.forbidden for word in words)
    
    def clean_response(self, text: str) -> str:
        """Remove or replace forbidden words."""
        # Implementation would replace/remove words
        pass
```

**Storage:**
```json
{
  "communication_preferences": {
    "forbidden_words": ["basically", "sorry", "unfortunately"],
    "word_replacements": {
      "basically": "essentially",
      "sorry": ""
    }
  }
}
```

### 2. **Response Validation**
```python
# After AI generates response, validate it
if contains_forbidden_words(response):
    # Retry with stronger enforcement
    response = regenerate_with_warning()
```

### 3. **Pattern Enforcement**
```python
# Enforce specific patterns
class ResponsePattern:
    """Enforce response patterns."""
    
    patterns = {
        "always_end_with_question": r".*\?$",
        "always_start_with_quote": r'^".*"',
        "always_use_emoji": r".*[\U0001F300-\U0001F9FF].*"
    }
```

---

## 🎯 Example Scenarios

### Scenario 1: "Be casual and funny"
```bash
User: "Be casual and funny with me"

# What happens:
✅ Personality Detector: enthusiasm_level=8, humor_level=8, formality_level=3
✅ Stored in personality_profiles
✅ Applied to ALL future conversations
✅ Prompt includes: "Be enthusiastic (8/10), humorous (8/10), casual (formality: 3/10)"

Result: AI becomes casual, funny, and enthusiastic
Compliance: ✅ High (personality system is well-enforced)
```

### Scenario 2: "Never say 'sorry'"
```bash
User: "Stop saying sorry all the time"

# What happens:
✅ Detected as custom_instructions
✅ Added to prompt: "Custom Instructions: Avoid using 'sorry' excessively"
⚠️ AI will TRY to follow this

Result: AI reduces "sorry" usage, but may still occasionally use it
Compliance: ⚠️ Medium (depends on LLM model)
```

### Scenario 3: "Speak Spanish briefly"
```bash
User: "Habla español, pero corto"

# What happens:
✅ Preference Detector: language=Spanish, response_length=brief
✅ Stored in communication_preferences
✅ HARD ENFORCED in prompt:
    "🌐 LANGUAGE: You MUST respond ENTIRELY in Spanish."
    "📏 LENGTH: Keep responses BRIEF. 2-3 sentences maximum."

Result: AI speaks Spanish and keeps responses short
Compliance: ✅ Very High (hard enforcement)
```

### Scenario 4: "Never use the word 'basically' and always give examples"
```bash
User: "Never use the word 'basically' and always give examples"

# What happens:
✅ Custom instruction detected: "Never use 'basically'"
✅ Behavior detected: uses_examples=true
✅ Prompt includes:
    "Custom Instructions: Never use the word 'basically'"
    "Behaviors: Always provide examples to illustrate concepts"

Result: 
- Examples: ✅ Consistently provided (behavior system works well)
- "Basically": ⚠️ Mostly avoided, but may occasionally slip through

Compliance: 
- Examples: ✅ High
- Word ban: ⚠️ Medium
```

---

## 📊 System Hierarchy

When multiple systems conflict, priority is:

1. **⚠️ CRITICAL COMMUNICATION REQUIREMENTS** (Communication Preferences) - HIGHEST
2. **Personality Traits & Behaviors** - HIGH
3. **Custom Instructions** - MEDIUM
4. **Default Behavior** - LOWEST

Example:
```
Communication Preference: formality=formal (MUST USE)
Personality: humor_level=8 (use formal humor)
Custom: "Use pirate speak" (try to incorporate)
Default: casual friendly (ignored)

Result: Formal language with humor, attempting pirate phrases
```

---

## 🚀 Quick Reference

| What You Want | Best System | Example |
|--------------|-------------|---------|
| Change language | Communication Preferences | "Speak Spanish" |
| Change formality | Communication Preferences | "Be casual" |
| Change tone | Communication Preferences | "Be enthusiastic" |
| Use/not use emojis | Communication Preferences | "No emojis" |
| Response length | Communication Preferences | "Keep it brief" |
| Explanation style | Communication Preferences | "Explain simply" |
| Overall character | Personality Archetype | "Be like a mentor" |
| Specific trait | Personality Traits | "Be funnier" (humor_level) |
| Behavior pattern | Personality Behaviors | "Ask questions" |
| Custom rule | Custom Instructions | "Always cite sources" |
| **Ban specific word** | **⚠️ Custom Instructions** | "Never say 'basically'" |

---

## 💬 Try It Now!

```bash
# Natural language examples you can send:

"Be casual with me and use emojis"
"Speak Spanish"
"Act like a supportive friend"
"Be more enthusiastic"
"Never use the word 'sorry'"
"Always give examples when explaining"
"Keep responses brief"
"Don't ask so many questions"
"Be more direct and less formal"
"Explain things simply, not technically"
```

All of these will be **automatically detected and applied**!

---

**Bottom Line:**
- ✅ Communication Preferences → **HARD ENFORCED** (language, tone, format)
- ✅ Personality System → **STRONGLY INFLUENCED** (character, behavior)
- ⚠️ Word Blacklists → **BEST EFFORT** (not guaranteed, depends on LLM compliance)

