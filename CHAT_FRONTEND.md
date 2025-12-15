# Chat Frontend - AI Thinking Visualization

A real-time chat interface that visualizes the AI's internal thinking process, including emotion detection, memory retrieval, personality application, and goal tracking.

## 🚀 Quick Start

### 1. Start the Backend

```bash
# From the project root
uvicorn app.main:app --reload
```

The backend will start on `http://localhost:8000`

### 2. Access the Chat Interface

Open your browser and navigate to:

```
http://localhost:8000/chat
```

### 3. Configure Settings

1. Click the **⚙️ Settings** button in the header
2. Configure your connection:
   - **API URL**: `http://localhost:8000` (default)
   - **User ID**: Your unique user identifier (e.g., `user123`)
   - **API Key** (optional): If you have an API key
   - **JWT Token** (optional): If you have a JWT bearer token
3. Click **Save Settings**

### 4. Start Chatting!

- Type your message in the input box
- Press **Enter** to send (or **Shift+Enter** for new line)
- Watch the AI think in real-time in the thinking panel!

## 📋 Features

### Real-Time Thinking Visualization

The thinking panel shows each step of the AI's processing:

- 🚀 **Processing Start** - Initial message processing
- 😊 **Emotion Detection** - Detected emotion with confidence and intensity
- 🎭 **Personality Application** - Active personality traits and archetype
- 🎯 **Goals Tracking** - Active goals and progress updates
- 🧠 **Memory Retrieval** - Relevant memories from past conversations
- 📝 **Context Assembly** - Building the complete prompt
- ⚡ **Response Generation** - Streaming the AI's response

### Chat Interface

- **Message History**: Persistent conversation across page reloads
- **Streaming Responses**: See the AI's response as it's generated
- **Typing Indicator**: Visual feedback while AI is thinking
- **Timestamps**: Optional timestamps on messages
- **Auto-scroll**: Automatically scrolls to latest messages

### Thinking Panel

- **Collapsible**: Toggle visibility with the "Thinking" button
- **Detailed Information**: See confidence scores, memory counts, goal progress
- **Step-by-Step**: Watch each processing step complete in real-time
- **Color-Coded**: Different colors for processing, complete, and error states

### Settings & Configuration

- **Persistent Storage**: Settings saved in browser localStorage
- **Flexible Authentication**: Support for User ID, API Key, or JWT tokens
- **Conversation Persistence**: Continue conversations across sessions

## 🎨 User Interface

### Header Controls

- **🤖 AI Chat Assistant**: Application title
- **👁️ Thinking**: Toggle thinking panel visibility
- **🗑️ Clear**: Clear conversation and start fresh
- **⚙️**: Open settings modal

### Status Bar

- **Connection Status**: Shows connected/disconnected/processing state
- **Conversation ID**: Current conversation identifier

### Responsive Design

- **Desktop**: Side-by-side chat and thinking panel
- **Tablet/Mobile**: Thinking panel overlays on top when opened

## 🔧 Configuration

### Default Settings

Edit `frontend/config.js` to change defaults:

```javascript
const CONFIG = {
    DEFAULT_API_URL: 'http://localhost:8000',
    DEFAULT_USER_ID: 'user123',
    AUTO_SCROLL: true,
    SHOW_TIMESTAMPS: true,
    MAX_MESSAGE_LENGTH: 4000,
    THINKING_PANEL_DEFAULT_VISIBLE: true
};
```

### Environment-Specific Configuration

For different environments (dev, staging, production), you can:

1. Modify `config.js` before deployment
2. Or use the Settings UI to configure per-user

## 📊 Understanding the Thinking Process

### Emotion Detection

When you send a message, the AI analyzes your emotional state:

```
😊 Emotion Detected
happy (confidence: 85%, intensity: high)
```

This helps the AI respond with appropriate empathy and tone.

### Personality Application

The AI applies its configured personality traits:

```
🎭 Personality Applied
Using Supportive Friend personality (depth: 6.8/10)
empathy_level: 8/10, humor_level: 6/10
```

### Goals Tracking

If you have active goals, the AI tracks them:

```
🎯 Goals Tracked
2 active goals
Learn Spanish (learning): 35%
Exercise Daily (health): 60%
```

### Memory Retrieval

The AI retrieves relevant memories from past conversations:

```
🧠 Memories Retrieved
Found 5 relevant memories
[0.92] User mentioned wanting to visit Spain
[0.87] User struggles with morning routines
```

### Context Assembly

All context is assembled before generating a response:

```
📝 Context Assembled
Using 8 messages with preferences, personality, emotion
```

## 🔐 Authentication

The chat interface supports three authentication methods:

### 1. User ID (Required)

Every request must include a User ID to identify the user.

### 2. API Key (Optional)

If your backend requires API key authentication:
- Set in Settings modal
- Sent as `X-API-Key` header

### 3. JWT Token (Optional)

For token-based authentication:
- Set in Settings modal
- Sent as `Authorization: Bearer <token>` header

### Creating a JWT Token

Use the backend API to create a token:

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "expires_in_hours": 24}'
```

Then paste the `access_token` into the JWT Token field in Settings.

## 🐛 Troubleshooting

### "Not connected" Status

**Problem**: Status bar shows "Not connected"

**Solutions**:
1. Ensure backend is running: `uvicorn app.main:app --reload`
2. Check API URL in Settings matches your backend
3. Verify User ID is set in Settings

### No Thinking Steps Appearing

**Problem**: Thinking panel is empty during processing

**Solutions**:
1. Check that thinking panel is visible (click "Thinking" button)
2. Verify backend is updated with thinking step emission
3. Check browser console for errors (F12)

### Authentication Errors

**Problem**: Getting 401/403 errors

**Solutions**:
1. Verify User ID is set in Settings
2. If using API Key, ensure it's valid
3. If using JWT Token, check it hasn't expired
4. Try creating a new token via `/auth/token` endpoint

### Messages Not Sending

**Problem**: Send button doesn't work

**Solutions**:
1. Check message isn't empty
2. Verify message length is under 4000 characters
3. Ensure not already processing a message
4. Check browser console for errors

### CORS Errors

**Problem**: Browser shows CORS policy errors

**Solutions**:
1. Ensure backend CORS settings allow your origin
2. Check `app/core/config.py` - `CORS_ORIGINS` setting
3. For development, backend should allow `*` or your specific origin

## 📱 Browser Compatibility

Tested and working on:
- ✅ Chrome/Chromium 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

Requires:
- JavaScript enabled
- LocalStorage support
- EventSource (SSE) support

## 🎯 Tips for Best Experience

1. **Keep Thinking Panel Open**: Watch the AI's process to understand its reasoning
2. **Set Your User ID**: Use a consistent User ID to maintain conversation history
3. **Try Different Emotions**: See how the AI detects and responds to different emotional states
4. **Set Goals**: Use the goals API to track your progress and see the AI reference them
5. **Configure Personality**: Customize the AI's personality via the API and see it applied

## 🔄 Conversation Management

### Starting a New Conversation

Click the **🗑️ Clear** button to:
- Clear all messages
- Reset conversation ID
- Start fresh with a new conversation

### Continuing a Conversation

Conversations are automatically saved:
- Conversation ID stored in localStorage
- Reload the page to continue where you left off
- All messages and context preserved

### Multiple Conversations

To manage multiple conversations:
1. Note your current conversation ID (shown in status bar)
2. Clear to start a new conversation
3. To return to previous conversation, you'd need to manually set the conversation ID (advanced)

## 🚀 Advanced Usage

### Monitoring Network Traffic

Open browser DevTools (F12) → Network tab to see:
- SSE stream from `/chat` endpoint
- Individual event messages
- Thinking steps and response chunks

### Customizing the Interface

Edit the frontend files:
- `frontend/chat.html` - Structure
- `frontend/chat.css` - Styling
- `frontend/chat.js` - Behavior
- `frontend/config.js` - Configuration

Changes take effect on page reload (no build step needed).

### API Integration

The frontend uses Server-Sent Events (SSE) to stream responses:

```javascript
// Example event structure
{
  "type": "thinking",
  "step": "emotion_detected",
  "data": {
    "emotion": "happy",
    "confidence": 0.85,
    "intensity": "high"
  },
  "conversation_id": "...",
  "timestamp": "2024-..."
}
```

## 📚 Related Documentation

- [API Examples](API_EXAMPLES.md) - Backend API usage
- [Emotion Detection Guide](EMOTION_DETECTION_GUIDE.md) - Emotion detection features
- [Personality System Guide](PERSONALITY_SYSTEM_GUIDE.md) - Personality configuration
- [Goals Tracking Guide](GOALS_TRACKING_GUIDE.md) - Goal tracking features

## 🤝 Support

If you encounter issues:
1. Check the browser console for errors (F12)
2. Check the backend logs for errors
3. Verify all settings are correct
4. Try clearing localStorage and reconfiguring

## 🎉 Enjoy!

You now have a powerful chat interface that lets you see exactly how your AI assistant thinks and processes information. Use this to:
- Debug and improve your AI's behavior
- Understand how different features work together
- Verify that emotion detection, personality, and goals are working correctly
- Build trust by seeing the AI's reasoning process

Happy chatting! 🤖💬

