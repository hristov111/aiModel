# Frontend Functionality Recreation Guide

This document describes the complete frontend logic and functionality for the AI Chat application. Use this to recreate the frontend from scratch focusing only on functionality, not styling.

---

## Overview

The frontend is a **single-page chat application** that:
- Sends messages to the backend API via POST requests
- Receives **streaming responses** using Server-Sent Events (SSE)
- Displays a **real-time thinking process** in a side panel
- Handles **age verification** prompts for sensitive content
- Supports multiple **authentication methods** (X-User-Id, API Key, JWT)
- Persists **conversation state** and settings in localStorage

---

## File Structure

Create these files:

```
frontend/
├── chat.html          # Main HTML structure
├── chat.js            # Core application logic
├── chat.css           # Styling (not covered in this guide)
└── config.js          # Configuration and localStorage management
```

---

## 1. Configuration System (config.js)

### Purpose
Manage application settings and persist them in localStorage.

### Configuration Object

```javascript
const CONFIG = {
    // Default API configuration
    DEFAULT_API_URL: 'http://localhost:8000',
    DEFAULT_USER_ID: null,
    
    // Storage keys for localStorage
    STORAGE_KEYS: {
        API_URL: 'ai_chat_api_url',
        USER_ID: 'ai_chat_user_id',
        API_KEY: 'ai_chat_api_key',
        JWT_TOKEN: 'ai_chat_jwt_token',
        CONVERSATION_ID: 'ai_chat_conversation_id',
        THINKING_VISIBLE: 'ai_chat_thinking_visible'
    },
    
    // UI settings
    AUTO_SCROLL: true,
    SHOW_TIMESTAMPS: true,
    MAX_MESSAGE_LENGTH: 4000,
    
    // Thinking panel settings
    THINKING_PANEL_DEFAULT_VISIBLE: true,
    SHOW_DETAILED_THINKING: true,
    
    // Message formatting
    TIMESTAMP_FORMAT: {
        hour: '2-digit',
        minute: '2-digit'
    }
};
```

### Helper Functions

#### getConfig(key)
Retrieves a configuration value from localStorage or returns default.

**Logic:**
1. Look up the storage key name using `CONFIG.STORAGE_KEYS[key]`
2. Try to get value from `localStorage.getItem(storageKey)`
3. If found, return it
4. Otherwise, return default values:
   - 'API_URL' → `CONFIG.DEFAULT_API_URL`
   - 'USER_ID' → `CONFIG.DEFAULT_USER_ID`
   - 'THINKING_VISIBLE' → `'true'` or `'false'` based on default
   - Other keys → `null`

#### setConfig(key, value)
Saves a configuration value to localStorage.

**Logic:**
1. Look up the storage key name
2. If `value` is `null` or `undefined`, remove the item from localStorage
3. Otherwise, save it using `localStorage.setItem(storageKey, value)`

#### clearConfig()
Clears all stored configuration.

**Logic:**
- Loop through all values in `CONFIG.STORAGE_KEYS`
- Remove each one from localStorage

---

## 2. HTML Structure (chat.html)

### Required Elements

Create HTML with these specific element IDs (the JavaScript depends on them):

#### Header Section
- `<h1>` - Title: "🤖 AI Chat Assistant"
- `<button id="toggleThinking">` - Toggle thinking panel visibility
- `<button id="clearChat">` - Clear conversation
- `<button id="settingsBtn">` - Open settings modal

#### Settings Modal
- `<div id="settingsModal" class="modal">` - Modal container
- `<button id="closeSettings">` - Close modal button
- `<input id="apiUrl">` - API URL input
- `<input id="userId">` - User ID input
- `<input id="apiKey" type="password">` - API Key input
- `<input id="jwtToken" type="password">` - JWT Token input
- `<button id="saveSettings">` - Save settings button

#### Chat Area
- `<div id="chatMessages">` - Messages container
- `<textarea id="messageInput">` - Message input field
- `<button id="sendBtn">` - Send message button
  - Must contain: `<span id="sendBtnText">Send</span>`

#### Thinking Panel
- `<div id="thinkingPanel">` - Thinking panel container
- `<button id="closeThinking">` - Close thinking panel
- `<div id="thinkingSteps">` - Thinking steps container

#### Status Bar
- `<span id="connectionStatus">` - Connection status indicator
- `<span id="statusText">` - Status text
- `<span id="conversationId">` - Display conversation ID

### Initial Welcome Message

The `chatMessages` div should initially contain:

```html
<div class="welcome-message">
    <h2>Welcome! 👋</h2>
    <p>Start chatting to see the AI's thinking process in real-time.</p>
    <p class="hint">💡 Click the "Thinking" button to toggle the thinking panel visibility.</p>
</div>
```

### Scripts Loading Order

```html
<script src="/static/config.js"></script>
<script src="/static/chat.js"></script>
```

---

## 3. Main Application Class (chat.js)

### Class Structure

```javascript
class ChatApp {
    constructor() {
        // Initialize state
        // Get DOM references
        // Call init()
    }
    
    init() {
        // Load settings from localStorage
        // Attach event listeners
        // Set initial UI state
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});
```

### State Management

The app maintains these state variables:

```javascript
this.conversationId = getConfig('CONVERSATION_ID');
this.isProcessing = false;  // Prevents multiple simultaneous messages
this.currentThinkingSteps = [];  // Array of thinking steps
this.currentMessageElement = null;  // Reference to assistant message being streamed
```

### DOM Element References

Cache all DOM elements in `this.elements` object:

```javascript
this.elements = {
    chatMessages: document.getElementById('chatMessages'),
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    thinkingPanel: document.getElementById('thinkingPanel'),
    thinkingSteps: document.getElementById('thinkingSteps'),
    toggleThinking: document.getElementById('toggleThinking'),
    closeThinking: document.getElementById('closeThinking'),
    clearChat: document.getElementById('clearChat'),
    settingsBtn: document.getElementById('settingsBtn'),
    settingsModal: document.getElementById('settingsModal'),
    closeSettings: document.getElementById('closeSettings'),
    saveSettings: document.getElementById('saveSettings'),
    connectionStatus: document.getElementById('connectionStatus'),
    statusText: document.getElementById('statusText'),
    conversationIdDisplay: document.getElementById('conversationId'),
    apiUrl: document.getElementById('apiUrl'),
    userId: document.getElementById('userId'),
    apiKey: document.getElementById('apiKey'),
    jwtToken: document.getElementById('jwtToken')
};
```

---

## 4. Core Functionality

### 4.1 Initialization (init method)

**Logic:**
1. Call `loadSettings()` to populate settings inputs from localStorage
2. Call `attachEventListeners()` to bind all event handlers
3. Call `updateConnectionStatus('disconnected')` to show initial status
4. Call `updateConversationDisplay()` to show conversation ID
5. Check if thinking panel should be hidden:
   - Get `THINKING_VISIBLE` from config
   - If `'false'`, add `'hidden'` class to thinking panel

### 4.2 Settings Management

#### loadSettings()
**Logic:**
1. Set `apiUrl` input value to `getConfig('API_URL')`
2. Set `userId` input value to `getConfig('USER_ID')`
3. Set `apiKey` input value to `getConfig('API_KEY')` or empty string
4. Set `jwtToken` input value to `getConfig('JWT_TOKEN')` or empty string

#### saveSettings()
**Logic:**
1. Call `setConfig('API_URL', apiUrl.value)`
2. Call `setConfig('USER_ID', userId.value)`
3. Call `setConfig('API_KEY', apiKey.value)`
4. Call `setConfig('JWT_TOKEN', jwtToken.value)`
5. Call `hideSettings()`
6. Call `showNotification('Settings saved successfully!', 'success')`

#### showSettings() / hideSettings()
**Logic:**
- Show: Add `'show'` class to `settingsModal`
- Hide: Remove `'show'` class from `settingsModal`

### 4.3 Event Listeners (attachEventListeners method)

Bind these event handlers:

```javascript
// Send message
sendBtn.addEventListener('click', () => this.sendMessage());
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
    }
});

// Thinking panel toggle
toggleThinking.addEventListener('click', () => this.toggleThinkingPanel());
closeThinking.addEventListener('click', () => this.toggleThinkingPanel());

// Clear chat
clearChat.addEventListener('click', () => this.clearChat());

// Settings modal
settingsBtn.addEventListener('click', () => this.showSettings());
closeSettings.addEventListener('click', () => this.hideSettings());
saveSettings.addEventListener('click', () => this.saveSettings());

// Close modal on outside click
settingsModal.addEventListener('click', (e) => {
    if (e.target === settingsModal) {
        this.hideSettings();
    }
});
```

### 4.4 Connection Status Display

#### updateConnectionStatus(status)

**Logic:**
1. Reset `connectionStatus` element class to `'status-dot'`
2. Based on status value:
   - **'connected'**: 
     - Add class `'status-connected'`
     - Set `statusText` to `'Connected'`
   - **'processing'**:
     - Add class `'status-processing'`
     - Set `statusText` to `'Processing...'`
   - **'disconnected'** (default):
     - Add class `'status-disconnected'`
     - Set `statusText` to `'Disconnected'`

### 4.5 Conversation Display

#### updateConversationDisplay()

**Logic:**
1. If `conversationId` exists:
   - Get first 8 characters: `conversationId.substring(0, 8)`
   - Set `conversationIdDisplay` text to `'Conversation: {first8}...'`
2. Otherwise:
   - Set text to `'No conversation'`

### 4.6 Clear Chat

#### clearChat()

**Logic:**
1. Show confirmation: `confirm('Clear all messages? This will start a new conversation.')`
2. If user cancels, return early
3. Clear conversation ID:
   - Set `this.conversationId = null`
   - Call `setConfig('CONVERSATION_ID', null)`
4. Clear UI:
   - Set `chatMessages.innerHTML` to welcome message HTML
   - Call `clearThinkingSteps()`
5. Update display: `updateConversationDisplay()`

### 4.7 Thinking Panel

#### toggleThinkingPanel()

**Logic:**
1. Toggle `'hidden'` class on `thinkingPanel`
2. Get result: `isHidden` (true if hidden, false if visible)
3. Save preference: `setConfig('THINKING_VISIBLE', isHidden ? 'false' : 'true')`

#### clearThinkingSteps()

**Logic:**
- Set `thinkingSteps.innerHTML` to placeholder message:

```html
<div class="thinking-placeholder">
    <p>Thinking steps will appear here when the AI processes your message.</p>
</div>
```

---

## 5. Message Sending Logic

### sendMessage() Method

**Complete Logic:**

```javascript
async sendMessage() {
    // 1. Get and validate input
    const message = messageInput.value.trim();
    
    if (!message || this.isProcessing) {
        return;  // Ignore empty or if already processing
    }
    
    if (message.length > CONFIG.MAX_MESSAGE_LENGTH) {
        this.showNotification(`Message too long (max ${CONFIG.MAX_MESSAGE_LENGTH} characters)`, 'error');
        return;
    }
    
    // 2. Clear input field
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // 3. Add user message to chat
    this.addMessage('user', message);
    
    // 4. Clear previous thinking steps
    this.clearThinkingSteps();
    
    // 5. Disable send button
    this.isProcessing = true;
    sendBtn.disabled = true;
    sendBtn.querySelector('#sendBtnText').textContent = 'Sending...';
    
    // 6. Update status
    this.updateConnectionStatus('processing');
    
    // 7. Create assistant message placeholder
    this.currentMessageElement = this.createMessageElement('assistant', '');
    chatMessages.appendChild(this.currentMessageElement);
    
    // 8. Add typing indicator
    const typingIndicator = this.createTypingIndicator();
    this.currentMessageElement.querySelector('.message-content').appendChild(typingIndicator);
    
    this.scrollToBottom();
    
    // 9. Send to API
    await this.streamChat(message);
}
```

---

## 6. API Communication (Streaming)

### streamChat(message) Method

This is the most critical method. It handles:
- Authentication header selection
- POST request to `/chat` endpoint
- SSE stream parsing
- Real-time UI updates

**Complete Logic:**

```javascript
async streamChat(message) {
    // 1. Get configuration
    const apiUrl = getConfig('API_URL');
    const userId = getConfig('USER_ID');
    const apiKey = getConfig('API_KEY');
    const jwtToken = getConfig('JWT_TOKEN');
    
    // 2. Check authentication
    if (!userId && !apiKey && !jwtToken) {
        this.showNotification('Please configure authentication in settings', 'error');
        this.resetSendButton();
        return;
    }
    
    // 3. Prepare headers
    const headers = {
        'Content-Type': 'application/json'
    };
    
    // 4. Add authentication (priority: JWT > API Key > X-User-Id)
    if (jwtToken) {
        headers['Authorization'] = `Bearer ${jwtToken}`;
        console.log('🔐 Using JWT authentication');
    } else if (apiKey) {
        headers['X-API-Key'] = apiKey;
        console.log('🔑 Using API Key authentication');
    } else if (userId) {
        headers['X-User-Id'] = userId;
        console.log('⚠️ Using X-User-Id (dev mode)');
    }
    
    // 5. Prepare request body
    const body = {
        message: message
    };
    
    if (this.conversationId) {
        body.conversation_id = this.conversationId;
    }
    
    try {
        // 6. Make POST request
        const response = await fetch(`${apiUrl}/chat`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(body)
        });
        
        // 7. Check response status
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        this.updateConnectionStatus('connected');
        
        // 8. Read SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let assistantMessage = '';
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            
            // 9. Process complete SSE messages
            const lines = buffer.split('\n');
            buffer = lines.pop();  // Keep incomplete line in buffer
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.substring(6);
                    
                    try {
                        const event = JSON.parse(data);
                        
                        // 10. Handle different event types
                        switch (event.type) {
                            case 'thinking':
                                this.handleThinkingEvent(event);
                                break;
                                
                            case 'chunk':
                                assistantMessage += event.chunk;
                                this.updateAssistantMessage(assistantMessage);
                                
                                // Update conversation ID if present
                                if (event.conversation_id && !this.conversationId) {
                                    this.conversationId = event.conversation_id;
                                    setConfig('CONVERSATION_ID', this.conversationId);
                                    this.updateConversationDisplay();
                                }
                                break;
                                
                            case 'done':
                                // Update conversation ID
                                if (event.conversation_id) {
                                    this.conversationId = event.conversation_id;
                                    setConfig('CONVERSATION_ID', this.conversationId);
                                    this.updateConversationDisplay();
                                }
                                break;
                                
                            case 'age_verification_required':
                                this.handleAgeVerificationRequired(event);
                                break;
                                
                            case 'error':
                                this.showNotification(event.error || 'An error occurred', 'error');
                                break;
                        }
                    } catch (e) {
                        console.error('Failed to parse SSE data:', e, data);
                    }
                }
            }
        }
        
        // 11. Finalize message
        if (assistantMessage) {
            this.finalizeAssistantMessage(assistantMessage);
        }
        
    } catch (error) {
        console.error('Chat error:', error);
        this.showNotification(`Connection error: ${error.message}`, 'error');
        
        // Remove typing indicator
        if (this.currentMessageElement) {
            this.currentMessageElement.remove();
            this.currentMessageElement = null;
        }
    } finally {
        this.resetSendButton();
        this.updateConnectionStatus('disconnected');
    }
}
```

### Key SSE Event Types

The backend sends these event types:

1. **`thinking`** - Processing steps (shown in thinking panel)
   - `event.type` = `'thinking'`
   - `event.step` = step name (e.g., 'processing_start', 'checking_personality')
   - `event.data` = step details (varies by step)

2. **`chunk`** - Response text chunks (streamed to user)
   - `event.type` = `'chunk'`
   - `event.chunk` = text fragment
   - `event.conversation_id` = conversation UUID

3. **`done`** - Stream complete
   - `event.type` = `'done'`
   - `event.conversation_id` = final conversation UUID

4. **`age_verification_required`** - Content requires age verification
   - `event.type` = `'age_verification_required'`
   - `event.conversation_id` = conversation UUID

5. **`error`** - Error occurred
   - `event.type` = `'error'`
   - `event.error` = error message

---

## 7. Message Display Logic

### createMessageElement(role, content)

**Logic:**
1. Create `div` with class `'message'` and `role` (e.g., `'message user'`)
2. Create inner `div` with class `'message-content'`
3. Set `textContent` to `content`
4. Append content div to message div
5. Return message div

### addMessage(role, content)

**Logic:**
1. Call `createMessageElement(role, content)`
2. If `CONFIG.SHOW_TIMESTAMPS` is true:
   - Create `div` with class `'message-time'`
   - Set text to: `new Date().toLocaleTimeString('en-US', CONFIG.TIMESTAMP_FORMAT)`
   - Append to message content div
3. Remove welcome message if present:
   - Query for `.welcome-message` in `chatMessages`
   - If found, remove it
4. Append message element to `chatMessages`
5. Call `scrollToBottom()`

### createTypingIndicator()

**Logic:**
- Create and return this HTML structure:

```html
<div class="typing-indicator">
    <div class="typing-dots">
        <span></span>
        <span></span>
        <span></span>
    </div>
</div>
```

### updateAssistantMessage(content)

**Logic:**
1. If `currentMessageElement` is null, return
2. Get the `.message-content` div inside it
3. Remove typing indicator if present (query for `.typing-indicator`)
4. Set `textContent` to `content`
5. Call `scrollToBottom()`

### finalizeAssistantMessage(content)

**Logic:**
1. If `currentMessageElement` is null, return
2. Get the `.message-content` div
3. Set `textContent` to `content`
4. If `CONFIG.SHOW_TIMESTAMPS` is true:
   - Create `div` with class `'message-time'`
   - Add timestamp
   - Append to content div
5. Set `currentMessageElement = null`
6. Call `scrollToBottom()`

### resetSendButton()

**Logic:**
1. Set `isProcessing = false`
2. Set `sendBtn.disabled = false`
3. Set send button text back to `'Send'`

### scrollToBottom()

**Logic:**
- If `CONFIG.AUTO_SCROLL` is true:
  - Set `chatMessages.scrollTop = chatMessages.scrollHeight`

---

## 8. Thinking Panel Logic

### handleThinkingEvent(event)

**Logic:**
1. Extract `step` from `event.step`
2. Extract `data` from `event.data`
3. Call `addThinkingStep(step, data)`

### addThinkingStep(step, data)

**Logic:**
1. Remove placeholder if present:
   - Query for `.thinking-placeholder` in `thinkingSteps`
   - If found, remove it

2. Create step element (`div` with class `'thinking-step processing'`)

3. Get step information by calling `getStepInfo(step, data)`

4. Set innerHTML:
```html
<div class="step-header">
    <span class="step-icon">{stepInfo.icon}</span>
    <span class="step-title">{stepInfo.title}</span>
</div>
<div class="step-details">{stepInfo.details}</div>
<!-- If stepInfo.data exists: -->
<div class="step-data">{stepInfo.data}</div>
```

5. Append to `thinkingSteps`

6. Scroll to bottom: `thinkingSteps.scrollTop = thinkingSteps.scrollHeight`

7. After 500ms:
   - Remove `'processing'` class
   - Add `'complete'` class

### getStepInfo(step, data)

**Returns object with:**
```javascript
{
    icon: '🔄',       // Emoji icon
    title: 'Step Name',
    details: 'Description',
    data: null  // Optional formatted data
}
```

**Step Type Mapping:**

| Step | Icon | Title | Details Logic |
|------|------|-------|---------------|
| `processing_start` | 🚀 | Starting Processing | From `data.message` |
| `message_stored` | 💾 | Message Stored | From `data.message` |
| `checking_preferences` | 🔍 | Analyzing Preferences | From `data.message` |
| `preferences_updated` | ✅ | Preferences Analyzed | From `data.message` |
| `checking_personality` | 🔍 | Checking Personality Config | From `data.message` |
| `personality_detected` | 🎭 | Personality Updated | `Archetype: {data.archetype}` + traits list |
| `personality_loaded` | 🎭 | Personality Applied | `Using {archetype} personality (depth: {depth}/10)` |
| `analyzing_emotion` | 🔍 | Analyzing Emotion | From `data.message` |
| `emotion_detected` | 😊 | Emotion Detected | `{emotion} (confidence: {conf}%, intensity: {intensity})` |
| `analyzing_goals` | 🔍 | Analyzing Goals | From `data.message` |
| `goals_tracked` | 🎯 | Goals Tracked | `{count} active goals, {new} new, {updates} updated` |
| `retrieving_memories` | 🔍 | Searching Memories | From `data.message` |
| `memories_retrieved` | 🧠 | Memories Retrieved | `Found {count} relevant memories` |
| `building_context` | 🔧 | Building Context | `Assembling {count} messages` |
| `prompt_built` | 📝 | Context Assembled | List: `{memories} memories, {messages} messages, etc.` |
| `generating_response` | ⚡ | Generating Response | From `data.message` |
| `extracting_memories` | 💾 | Extracting Memories | `Background task running...` |
| (default) | 🔄 | Formatted step name | From `data.message` |

**For personality steps with traits:**
- Format traits as: `trait: value/10, trait: value/10, ...` (show first 3)
- Add to `data` field

**For goals_tracked with goals array:**
- Format as: `{title} ({category}): {progress}%` (one per line)

**For memories_retrieved with memories array:**
- Format as: `[type][importance] content` (one per line, separated by blank line)

---

## 9. Age Verification Logic

### handleAgeVerificationRequired(event)

This handles the age verification flow for sensitive content.

**Complete Logic:**

```javascript
async handleAgeVerificationRequired(event) {
    console.log('🔞 Age verification required:', event);
    
    // 1. Store conversation ID
    if (event.conversation_id) {
        this.conversationId = event.conversation_id;
        setConfig('CONVERSATION_ID', this.conversationId);
        this.updateConversationDisplay();
    }
    
    // 2. Show confirmation dialog
    const confirmed = confirm(
        'Age Verification Required\n\n' +
        'This content requires age verification. You must be 18 years or older to continue.\n\n' +
        'Click OK to confirm you are 18+, or Cancel to decline.'
    );
    
    console.log('✅ User confirmed:', confirmed);
    
    if (confirmed) {
        try {
            // 3. Get authentication info
            const apiUrl = getConfig('API_URL');
            const userId = getConfig('USER_ID');
            const apiKey = getConfig('API_KEY');
            const jwtToken = getConfig('JWT_TOKEN');
            
            // 4. Prepare headers
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (jwtToken) {
                headers['Authorization'] = `Bearer ${jwtToken}`;
            } else if (apiKey) {
                headers['X-API-Key'] = apiKey;
            } else if (userId) {
                headers['X-User-Id'] = userId;
            }
            
            // 5. Call age verification API
            const response = await fetch(`${apiUrl}/content/age-verify`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    conversation_id: this.conversationId,
                    confirmed: true
                })
            });
            
            // 6. Check response
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to verify age: ${response.statusText} - ${errorText}`);
            }
            
            const result = await response.json();
            
            // 7. Handle result
            if (result.age_verified) {
                this.showNotification('Age verified! You can now send your message again.', 'success');
                
                const message = 'Age verified successfully. Please send your message again to continue.';
                if (this.currentMessageElement) {
                    this.finalizeAssistantMessage(message);
                } else {
                    this.addMessage('assistant', message);
                }
            } else {
                this.showNotification('Age verification failed', 'error');
                if (this.currentMessageElement) {
                    this.currentMessageElement.remove();
                    this.currentMessageElement = null;
                }
            }
            
        } catch (error) {
            console.error('❌ Age verification error:', error);
            this.showNotification(`Age verification error: ${error.message}`, 'error');
            if (this.currentMessageElement) {
                this.currentMessageElement.remove();
                this.currentMessageElement = null;
            }
        }
    } else {
        // 8. User declined
        console.log('❌ User declined age verification');
        this.showNotification('Age verification declined. Content cannot be displayed.', 'error');
        
        const message = 'Age verification is required to access this content. Please confirm you are 18+ years old to continue.';
        if (this.currentMessageElement) {
            this.finalizeAssistantMessage(message);
        } else {
            this.addMessage('assistant', message);
        }
    }
}
```

---

## 10. Notification System

### showNotification(message, type = 'info')

**Logic:**
1. Create a `div` element
2. Style it based on `type`:
   - `'error'` → red background (`#ef4444`)
   - `'success'` → green background (`#10b981`)
   - `'info'` (default) → blue background (`#3b82f6`)
3. Position it fixed at top-right (e.g., `top: 20px, right: 20px`)
4. Set white text color
5. Set `textContent` to `message`
6. Append to `document.body`
7. After 3 seconds (3000ms):
   - Add fade-out animation
   - After animation (300ms), remove element

**Inline CSS Example:**
```javascript
notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    background-color: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
    color: white;
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    z-index: 10000;
`;
```

---

## 11. API Endpoints Reference

### POST /chat
**Purpose:** Send a message and receive streaming response

**Request:**
```json
{
    "message": "Hello!",
    "conversation_id": "uuid-string-or-null"
}
```

**Headers:**
- `Content-Type: application/json`
- One of:
  - `Authorization: Bearer {jwt_token}`
  - `X-API-Key: {api_key}`
  - `X-User-Id: {user_id}` (dev only)

**Response:** Server-Sent Events stream

### POST /content/age-verify
**Purpose:** Confirm age verification for sensitive content

**Request:**
```json
{
    "conversation_id": "uuid-string",
    "confirmed": true
}
```

**Headers:** Same as `/chat`

**Response:**
```json
{
    "age_verified": true
}
```

---

## 12. Implementation Checklist

When recreating this frontend, implement in this order:

### Phase 1: Configuration
- [ ] Create `config.js` with CONFIG object
- [ ] Implement `getConfig()` function
- [ ] Implement `setConfig()` function
- [ ] Implement `clearConfig()` function

### Phase 2: HTML Structure
- [ ] Create HTML with all required element IDs
- [ ] Add initial welcome message
- [ ] Include config.js and chat.js scripts

### Phase 3: Core App Class
- [ ] Create `ChatApp` class with constructor
- [ ] Initialize state variables
- [ ] Cache DOM element references
- [ ] Implement `init()` method

### Phase 4: Settings & UI
- [ ] Implement `loadSettings()` / `saveSettings()`
- [ ] Implement `showSettings()` / `hideSettings()`
- [ ] Implement `updateConnectionStatus()`
- [ ] Implement `updateConversationDisplay()`
- [ ] Implement `toggleThinkingPanel()`
- [ ] Implement `clearChat()`

### Phase 5: Event Handlers
- [ ] Attach send message events (button + Enter key)
- [ ] Attach thinking panel events
- [ ] Attach settings modal events
- [ ] Attach clear chat event

### Phase 6: Message Display
- [ ] Implement `createMessageElement()`
- [ ] Implement `addMessage()`
- [ ] Implement `createTypingIndicator()`
- [ ] Implement `updateAssistantMessage()`
- [ ] Implement `finalizeAssistantMessage()`
- [ ] Implement `scrollToBottom()`
- [ ] Implement `resetSendButton()`

### Phase 7: Chat Logic
- [ ] Implement `sendMessage()` method
- [ ] Implement message validation
- [ ] Implement UI state management during send

### Phase 8: API Communication
- [ ] Implement `streamChat()` method
- [ ] Implement authentication header logic
- [ ] Implement fetch() request
- [ ] Implement SSE stream reading
- [ ] Implement line-by-line parsing
- [ ] Implement event type switching

### Phase 9: Thinking Panel
- [ ] Implement `handleThinkingEvent()`
- [ ] Implement `addThinkingStep()`
- [ ] Implement `getStepInfo()` with all step types
- [ ] Implement `clearThinkingSteps()`

### Phase 10: Age Verification
- [ ] Implement `handleAgeVerificationRequired()`
- [ ] Implement confirmation dialog
- [ ] Implement API call to `/content/age-verify`
- [ ] Implement success/failure handling

### Phase 11: Notifications
- [ ] Implement `showNotification()`
- [ ] Implement auto-dismiss after 3 seconds

### Phase 12: Initialization
- [ ] Add DOMContentLoaded event listener
- [ ] Instantiate ChatApp class

---

## 13. Testing the Frontend

### Manual Tests

1. **Settings Persistence:**
   - Open settings, enter values, save
   - Refresh page
   - Open settings again - values should persist

2. **Message Sending:**
   - Type a message, click Send
   - Verify user message appears
   - Verify typing indicator shows
   - Verify response streams in

3. **Thinking Panel:**
   - Send a message
   - Open thinking panel
   - Verify steps appear in real-time
   - Close and reopen - should persist state

4. **Conversation Continuity:**
   - Send first message, note conversation ID
   - Send second message
   - Verify same conversation ID is used

5. **Clear Chat:**
   - Send messages
   - Click Clear
   - Verify welcome message returns
   - Verify new conversation starts

6. **Authentication:**
   - Test with X-User-Id header
   - Test with API Key
   - Test with JWT token
   - Verify priority: JWT > API Key > User ID

7. **Age Verification:**
   - Send message that triggers verification
   - Test accepting
   - Test declining
   - Verify conversation continues correctly

8. **Error Handling:**
   - Turn off backend
   - Try sending message
   - Verify error notification appears
   - Verify UI resets properly

---

## 14. Key Implementation Notes

### Critical Details

1. **SSE Parsing:**
   - Lines may be incomplete in stream chunks
   - Always maintain a buffer for incomplete lines
   - Only parse lines that start with `'data: '`

2. **Authentication Priority:**
   - JWT Token (highest)
   - API Key (medium)
   - X-User-Id (lowest, dev only)
   - Never send X-User-Id when using JWT

3. **State Management:**
   - `isProcessing` prevents double-sends
   - `currentMessageElement` tracks the assistant message being streamed
   - `conversationId` must persist across page reloads

4. **Conversation ID Handling:**
   - First message: send `conversation_id: null`
   - Backend returns ID in response
   - Save to localStorage
   - Use in all subsequent messages

5. **Typing Indicator:**
   - Add when message starts
   - Remove when first chunk arrives
   - Important for UX feedback

6. **Scroll Behavior:**
   - Auto-scroll after each chunk
   - Keeps latest content visible
   - Use `scrollTop = scrollHeight` pattern

7. **Error Recovery:**
   - Always reset send button in `finally` block
   - Remove message element on error
   - Show user-friendly error notifications

8. **Age Verification Flow:**
   - Store conversation ID immediately
   - Show modal before API call
   - User must resend message after verification
   - Conversation continues with same ID

---

## 15. Backend API Contract

### Expected SSE Events

The backend will send these events in this typical order:

```
data: {"type": "thinking", "step": "processing_start", "data": {...}}
data: {"type": "thinking", "step": "message_stored", "data": {...}}
data: {"type": "thinking", "step": "checking_personality", "data": {...}}
data: {"type": "thinking", "step": "personality_loaded", "data": {...}}
data: {"type": "thinking", "step": "analyzing_emotion", "data": {...}}
data: {"type": "thinking", "step": "emotion_detected", "data": {...}}
data: {"type": "thinking", "step": "retrieving_memories", "data": {...}}
data: {"type": "thinking", "step": "memories_retrieved", "data": {...}}
data: {"type": "thinking", "step": "building_context", "data": {...}}
data: {"type": "thinking", "step": "prompt_built", "data": {...}}
data: {"type": "thinking", "step": "generating_response", "data": {...}}
data: {"type": "chunk", "chunk": "Hello", "conversation_id": "..."}
data: {"type": "chunk", "chunk": " there", "conversation_id": "..."}
data: {"type": "chunk", "chunk": "!", "conversation_id": "..."}
data: {"type": "done", "conversation_id": "..."}
```

### Age Verification Flow

```
data: {"type": "age_verification_required", "conversation_id": "..."}
```

User must then:
1. Accept/decline prompt
2. If accepted, POST to `/content/age-verify`
3. Resend original message with same conversation_id

---

## 16. Summary

This frontend is a **stateful single-page application** that:

✅ Manages settings in localStorage  
✅ Handles three authentication methods with priority  
✅ Streams responses via SSE with real-time parsing  
✅ Displays AI thinking process in side panel  
✅ Handles age verification for sensitive content  
✅ Maintains conversation continuity across page reloads  
✅ Provides visual feedback (typing indicators, status dots)  
✅ Shows notifications for errors and success  
✅ Auto-scrolls to keep latest content visible  

The key complexity is in the **SSE stream parsing** and **state management** across authentication, conversation flow, and UI updates.

---

## Questions to Ask When Implementing

1. What port is the backend running on? (Update `DEFAULT_API_URL`)
2. Should the thinking panel be visible by default? (Update `THINKING_PANEL_DEFAULT_VISIBLE`)
3. What's the maximum message length? (Update `MAX_MESSAGE_LENGTH`)
4. Should timestamps be shown? (Update `SHOW_TIMESTAMPS`)
5. Should auto-scroll be enabled? (Update `AUTO_SCROLL`)

---

**End of Frontend Functionality Guide**


