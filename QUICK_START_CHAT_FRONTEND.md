# Quick Start - Chat Frontend

## 🚀 Get Started in 3 Steps

### Step 1: Start the Backend

```bash
cd "/home/bean12/Desktop/AI Service"
uvicorn app.main:app --reload
```

### Step 2: Open the Chat Interface

Open your browser and go to:
```
http://localhost:8000/chat
```

### Step 3: Configure & Chat

1. Click the **⚙️** button (top right)
2. Set your **User ID** (e.g., `user123`)
3. Click **Save Settings**
4. Start chatting!

## 🧠 What You'll See

### Thinking Panel (Right Side)

Watch the AI process your message in real-time:

- 🚀 **Processing Start** - Beginning analysis
- 😊 **Emotion Detected** - Your emotional state (e.g., "happy 85%")
- 🎭 **Personality Applied** - AI's personality traits
- 🎯 **Goals Tracked** - Your active goals (if any)
- 🧠 **Memories Retrieved** - Relevant past conversations
- 📝 **Context Assembled** - Building the response
- ⚡ **Generating Response** - Creating the answer

### Chat Area (Left Side)

- Your messages appear in **blue bubbles** on the right
- AI responses appear in **white bubbles** on the left
- Responses stream in real-time as they're generated

## 💡 Tips

- **Toggle Thinking Panel**: Click "👁️ Thinking" to show/hide
- **Clear Chat**: Click "🗑️ Clear" to start a new conversation
- **Send Message**: Press Enter (Shift+Enter for new line)
- **Persistent**: Your conversation is saved automatically

## 🔧 Optional: Authentication

If your backend requires authentication:

1. **API Key**: Add in Settings → API Key field
2. **JWT Token**: Generate via:
   ```bash
   curl -X POST http://localhost:8000/auth/token \
     -H "Content-Type: application/json" \
     -d '{"user_id": "user123"}'
   ```
   Then paste the `access_token` in Settings → JWT Token

## 📖 Full Documentation

See [CHAT_FRONTEND.md](CHAT_FRONTEND.md) for complete documentation.

## ✅ Verify It's Working

You should see:
- ✅ Green dot in status bar (bottom left) when connected
- ✅ Thinking steps appearing in real-time
- ✅ AI responses streaming character by character
- ✅ Conversation ID displayed (bottom right)

## 🐛 Troubleshooting

**Not connecting?**
- Ensure backend is running on port 8000
- Check API URL in Settings matches your backend

**No thinking steps?**
- Click "👁️ Thinking" to show the panel
- Check browser console (F12) for errors

**Can't send messages?**
- Verify User ID is set in Settings
- Check message isn't empty

---

**That's it! Enjoy watching your AI think! 🤖💭**

