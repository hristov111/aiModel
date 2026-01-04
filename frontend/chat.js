/**
 * AI Chat Frontend - Main JavaScript
 * Handles SSE connections, message display, and thinking visualization
 */

class ChatApp {
    constructor() {
        // State
        this.conversationId = getConfig('CONVERSATION_ID');
        this.isProcessing = false;
        this.currentThinkingSteps = [];
        this.currentMessageElement = null;
        
        // DOM elements
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
            // Settings inputs
            apiUrl: document.getElementById('apiUrl'),
            userId: document.getElementById('userId'),
            apiKey: document.getElementById('apiKey'),
            jwtToken: document.getElementById('jwtToken')
        };
        
        this.init();
    }
    
    init() {
        this.loadSettings();
        this.attachEventListeners();
        this.updateConnectionStatus('disconnected');
        this.updateConversationDisplay();
        
        // Initialize thinking panel visibility
        const thinkingVisible = getConfig('THINKING_VISIBLE') === 'true';
        if (!thinkingVisible) {
            this.elements.thinkingPanel.classList.add('hidden');
        }
    }
    
    loadSettings() {
        this.elements.apiUrl.value = getConfig('API_URL');
        this.elements.userId.value = getConfig('USER_ID');
        this.elements.apiKey.value = getConfig('API_KEY') || '';
        this.elements.jwtToken.value = getConfig('JWT_TOKEN') || '';
    }
    
    attachEventListeners() {
        // Send message
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Thinking panel
        this.elements.toggleThinking.addEventListener('click', () => this.toggleThinkingPanel());
        this.elements.closeThinking.addEventListener('click', () => this.toggleThinkingPanel());
        
        // Clear chat
        this.elements.clearChat.addEventListener('click', () => this.clearChat());
        
        // Settings modal
        this.elements.settingsBtn.addEventListener('click', () => this.showSettings());
        this.elements.closeSettings.addEventListener('click', () => this.hideSettings());
        this.elements.saveSettings.addEventListener('click', () => this.saveSettings());
        
        // Close modal on outside click
        this.elements.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.elements.settingsModal) {
                this.hideSettings();
            }
        });
    }
    
    toggleThinkingPanel() {
        const isHidden = this.elements.thinkingPanel.classList.toggle('hidden');
        setConfig('THINKING_VISIBLE', !isHidden ? 'true' : 'false');
    }
    
    showSettings() {
        this.elements.settingsModal.classList.add('show');
    }
    
    hideSettings() {
        this.elements.settingsModal.classList.remove('show');
    }
    
    saveSettings() {
        setConfig('API_URL', this.elements.apiUrl.value);
        setConfig('USER_ID', this.elements.userId.value);
        setConfig('API_KEY', this.elements.apiKey.value);
        setConfig('JWT_TOKEN', this.elements.jwtToken.value);
        this.hideSettings();
        this.showNotification('Settings saved successfully!', 'success');
    }
    
    clearChat() {
        if (!confirm('Clear all messages? This will start a new conversation.')) {
            return;
        }
        
        // Clear conversation ID
        this.conversationId = null;
        setConfig('CONVERSATION_ID', null);
        
        // Clear messages
        this.elements.chatMessages.innerHTML = `
            <div class="welcome-message">
                <h2>Welcome! 👋</h2>
                <p>Start chatting to see the AI's thinking process in real-time.</p>
                <p class="hint">💡 Click the "Thinking" button to toggle the thinking panel visibility.</p>
            </div>
        `;
        
        // Clear thinking steps
        this.clearThinkingSteps();
        
        this.updateConversationDisplay();
    }
    
    updateConnectionStatus(status) {
        this.elements.connectionStatus.className = 'status-dot';
        
        switch (status) {
            case 'connected':
                this.elements.connectionStatus.classList.add('status-connected');
                this.elements.statusText.textContent = 'Connected';
                break;
            case 'processing':
                this.elements.connectionStatus.classList.add('status-processing');
                this.elements.statusText.textContent = 'Processing...';
                break;
            case 'disconnected':
            default:
                this.elements.connectionStatus.classList.add('status-disconnected');
                this.elements.statusText.textContent = 'Disconnected';
                break;
        }
    }
    
    updateConversationDisplay() {
        if (this.conversationId) {
            this.elements.conversationIdDisplay.textContent = 
                `Conversation: ${this.conversationId.substring(0, 8)}...`;
        } else {
            this.elements.conversationIdDisplay.textContent = 'No conversation';
        }
    }
    
    async sendMessage() {
        const message = this.elements.messageInput.value.trim();
        
        if (!message || this.isProcessing) {
            return;
        }
        
        if (message.length > CONFIG.MAX_MESSAGE_LENGTH) {
            this.showNotification(`Message too long (max ${CONFIG.MAX_MESSAGE_LENGTH} characters)`, 'error');
            return;
        }
        
        // Clear input
        this.elements.messageInput.value = '';
        this.elements.messageInput.style.height = 'auto';
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Clear previous thinking steps
        this.clearThinkingSteps();
        
        // Disable send button
        this.isProcessing = true;
        this.elements.sendBtn.disabled = true;
        this.elements.sendBtn.querySelector('#sendBtnText').textContent = 'Sending...';
        
        // Update status
        this.updateConnectionStatus('processing');
        
        // Create assistant message placeholder
        this.currentMessageElement = this.createMessageElement('assistant', '');
        this.elements.chatMessages.appendChild(this.currentMessageElement);
        
        // Add typing indicator
        const typingIndicator = this.createTypingIndicator();
        this.currentMessageElement.querySelector('.message-content').appendChild(typingIndicator);
        
        this.scrollToBottom();
        
        // Send to API
        await this.streamChat(message);
    }
    
    async streamChat(message) {
        const apiUrl = getConfig('API_URL');
        const userId = getConfig('USER_ID');
        const apiKey = getConfig('API_KEY');
        const jwtToken = getConfig('JWT_TOKEN');
        
        // Check if we have any form of authentication
        if (!userId && !apiKey && !jwtToken) {
            this.showNotification('Please configure authentication in settings (User ID, API Key, or JWT Token)', 'error');
            this.resetSendButton();
            return;
        }
        
        // Prepare headers
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Priority: JWT Token > API Key > X-User-Id (dev mode)
        if (jwtToken) {
            headers['Authorization'] = `Bearer ${jwtToken}`;
            // Don't send X-User-Id when using JWT - the token contains the user ID
            console.log('🔐 Using JWT authentication');
        } else if (apiKey) {
            headers['X-API-Key'] = apiKey;
            console.log('🔑 Using API Key authentication');
        } else if (userId) {
            // Only use X-User-Id header in development without JWT/API key
            headers['X-User-Id'] = userId;
            console.log('⚠️ Using X-User-Id (dev mode)');
        }
        
        // Prepare request body
        const body = {
            message: message
        };
        
        if (this.conversationId) {
            body.conversation_id = this.conversationId;
        }
        
        try {
            const response = await fetch(`${apiUrl}/chat`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(body)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.updateConnectionStatus('connected');
            
            // Read SSE stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let assistantMessage = '';
            
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                
                // Process complete SSE messages
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep incomplete line in buffer
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.substring(6);
                        
                        try {
                            const event = JSON.parse(data);
                            
                            // Handle different event types
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
                                    // Handle age verification required
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
            
            // Finalize message
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
    
    handleThinkingEvent(event) {
        const step = event.step;
        const data = event.data;
        
        // Add thinking step to panel
        this.addThinkingStep(step, data);
    }
    
    async handleAgeVerificationRequired(event) {
        console.log('🔞 Age verification required:', event);
        
        // Store conversation ID
        if (event.conversation_id) {
            this.conversationId = event.conversation_id;
            setConfig('CONVERSATION_ID', this.conversationId);
            this.updateConversationDisplay();
        }
        
        console.log('📝 Conversation ID:', this.conversationId);
        
        // Show confirmation dialog
        const confirmed = confirm(
            'Age Verification Required\n\n' +
            'This content requires age verification. You must be 18 years or older to continue.\n\n' +
            'Click OK to confirm you are 18+, or Cancel to decline.'
        );
        
        console.log('✅ User confirmed:', confirmed);
        
        if (confirmed) {
            try {
                // Call age verification API
                const apiUrl = getConfig('API_URL');
                const userId = getConfig('USER_ID');
                const apiKey = getConfig('API_KEY');
                const jwtToken = getConfig('JWT_TOKEN');
                
                console.log('🔧 API URL:', apiUrl);
                console.log('👤 User ID:', userId);
                
                const headers = {
                    'Content-Type': 'application/json'
                };
                
                // Add authentication
                if (jwtToken) {
                    headers['Authorization'] = `Bearer ${jwtToken}`;
                    console.log('🔐 Using JWT token');
                } else if (apiKey) {
                    headers['X-API-Key'] = apiKey;
                    console.log('🔑 Using API Key');
                } else if (userId) {
                    headers['X-User-Id'] = userId;
                    console.log('👤 Using X-User-Id');
                }
                
                console.log('📤 Calling age verification API...');
                
                const response = await fetch(`${apiUrl}/content/age-verify`, {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify({
                        conversation_id: this.conversationId,
                        confirmed: true
                    })
                });
                
                console.log('📥 Response status:', response.status);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('❌ API error:', errorText);
                    throw new Error(`Failed to verify age: ${response.statusText} - ${errorText}`);
                }
                
                const result = await response.json();
                console.log('✅ Age verification result:', result);
                
                if (result.age_verified) {
                    this.showNotification('Age verified! You can now send your message again.', 'success');
                    
                    // Show message in assistant area
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
            // User declined
            console.log('❌ User declined age verification');
            this.showNotification('Age verification declined. Content cannot be displayed.', 'error');
            
            // Show message in assistant area
            const message = 'Age verification is required to access this content. Please confirm you are 18+ years old to continue.';
            if (this.currentMessageElement) {
                this.finalizeAssistantMessage(message);
            } else {
                this.addMessage('assistant', message);
            }
        }
    }
    
    addThinkingStep(step, data) {
        // Remove placeholder if present
        const placeholder = this.elements.thinkingSteps.querySelector('.thinking-placeholder');
        if (placeholder) {
            placeholder.remove();
        }
        
        const stepElement = document.createElement('div');
        stepElement.className = 'thinking-step processing';
        
        // Determine icon and title based on step
        const stepInfo = this.getStepInfo(step, data);
        
        stepElement.innerHTML = `
            <div class="step-header">
                <span class="step-icon">${stepInfo.icon}</span>
                <span class="step-title">${stepInfo.title}</span>
            </div>
            <div class="step-details">${stepInfo.details}</div>
            ${stepInfo.data ? `<div class="step-data">${stepInfo.data}</div>` : ''}
        `;
        
        this.elements.thinkingSteps.appendChild(stepElement);
        this.elements.thinkingSteps.scrollTop = this.elements.thinkingSteps.scrollHeight;
        
        // Mark as complete after a short delay
        setTimeout(() => {
            stepElement.classList.remove('processing');
            stepElement.classList.add('complete');
        }, 500);
    }
    
    getStepInfo(step, data) {
        const info = {
            icon: '🔄',
            title: step,
            details: data.message || '',
            data: null
        };
        
        switch (step) {
            case 'processing_start':
                info.icon = '🚀';
                info.title = 'Starting Processing';
                break;
            
            case 'message_stored':
                info.icon = '💾';
                info.title = 'Message Stored';
                break;
            
            case 'checking_preferences':
                info.icon = '🔍';
                info.title = 'Analyzing Preferences';
                break;
            
            case 'preferences_updated':
                info.icon = '✅';
                info.title = 'Preferences Analyzed';
                break;
            
            case 'checking_personality':
                info.icon = '🔍';
                info.title = 'Checking Personality Config';
                break;
                
            case 'personality_detected':
                info.icon = '🎭';
                info.title = 'Personality Updated';
                if (data.archetype) {
                    info.details = `Archetype: ${data.archetype}`;
                }
                if (data.traits && Object.keys(data.traits).length > 0) {
                    const traitsList = Object.entries(data.traits)
                        .map(([k, v]) => `${k}: ${v}/10`)
                        .slice(0, 3)
                        .join(', ');
                    info.data = traitsList;
                }
                break;
                
            case 'personality_loaded':
                info.icon = '🎭';
                info.title = 'Personality Applied';
                if (data.archetype) {
                    info.details = `Using ${data.archetype} personality (depth: ${data.relationship_depth.toFixed(1)}/10)`;
                }
                if (data.traits && Object.keys(data.traits).length > 0) {
                    const traitsList = Object.entries(data.traits)
                        .map(([k, v]) => `${k}: ${v}/10`)
                        .slice(0, 3)
                        .join(', ');
                    info.data = traitsList;
                }
                break;
            
            case 'analyzing_emotion':
                info.icon = '🔍';
                info.title = 'Analyzing Emotion';
                break;
                
            case 'emotion_detected':
                info.icon = '😊';
                info.title = 'Emotion Detected';
                info.details = `${data.emotion} (confidence: ${(data.confidence * 100).toFixed(0)}%, intensity: ${data.intensity})`;
                break;
            
            case 'analyzing_goals':
                info.icon = '🔍';
                info.title = 'Analyzing Goals';
                break;
                
            case 'goals_tracked':
                info.icon = '🎯';
                info.title = 'Goals Tracked';
                info.details = `${data.active_count} active goals`;
                if (data.new_goals > 0) {
                    info.details += `, ${data.new_goals} new`;
                }
                if (data.progress_updates > 0) {
                    info.details += `, ${data.progress_updates} updated`;
                }
                if (data.goals && data.goals.length > 0) {
                    info.data = data.goals
                        .map(g => `${g.title} (${g.category}): ${g.progress.toFixed(0)}%`)
                        .join('\n');
                }
                break;
            
            case 'retrieving_memories':
                info.icon = '🔍';
                info.title = 'Searching Memories';
                break;
                
            case 'memories_retrieved':
                info.icon = '🧠';
                info.title = 'Memories Retrieved';
                info.details = `Found ${data.count} relevant memories`;
                if (data.memories && data.memories.length > 0) {
                    info.data = data.memories
                        .map(m => {
                            const type = m.type ? `[${m.type}]` : '';
                            const importance = m.importance ? `[${m.importance.toFixed(2)}]` : '';
                            return `${type}${importance} ${m.content}`;
                        })
                        .join('\n\n');
                }
                break;
            
            case 'building_context':
                info.icon = '🔧';
                info.title = 'Building Context';
                if (data.message_count) {
                    info.details = `Assembling ${data.message_count} messages`;
                }
                break;
                
            case 'prompt_built':
                info.icon = '📝';
                info.title = 'Context Assembled';
                if (data.context) {
                    const ctx = data.context;
                    const parts = [];
                    if (ctx.memories > 0) parts.push(`${ctx.memories} memories`);
                    if (ctx.messages > 0) parts.push(`${ctx.messages} messages`);
                    if (ctx.personality) parts.push(`${ctx.personality} personality`);
                    if (ctx.emotion) parts.push(`${ctx.emotion} emotion`);
                    if (ctx.goals > 0) parts.push(`${ctx.goals} goals`);
                    if (ctx.preferences) parts.push('preferences');
                    info.details = parts.join(', ');
                } else {
                    // Fallback for old format
                    const features = [];
                    if (data.has_preferences) features.push('preferences');
                    if (data.has_personality) features.push('personality');
                    if (data.has_emotion) features.push('emotion');
                    info.details = `Using ${data.context_messages} messages` + 
                        (features.length > 0 ? ` with ${features.join(', ')}` : '');
                }
                break;
                
            case 'generating_response':
                info.icon = '⚡';
                info.title = 'Generating Response';
                break;
            
            case 'extracting_memories':
                info.icon = '💾';
                info.title = 'Extracting Memories';
                info.details = 'Background task running...';
                break;
                
            default:
                info.title = step.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        }
        
        return info;
    }
    
    clearThinkingSteps() {
        this.elements.thinkingSteps.innerHTML = `
            <div class="thinking-placeholder">
                <p>Thinking steps will appear here when the AI processes your message.</p>
            </div>
        `;
    }
    
    createMessageElement(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        
        return messageDiv;
    }
    
    addMessage(role, content) {
        const messageElement = this.createMessageElement(role, content);
        
        // Add timestamp if enabled
        if (CONFIG.SHOW_TIMESTAMPS) {
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = new Date().toLocaleTimeString('en-US', CONFIG.TIMESTAMP_FORMAT);
            messageElement.querySelector('.message-content').appendChild(timeDiv);
        }
        
        // Remove welcome message if present
        const welcome = this.elements.chatMessages.querySelector('.welcome-message');
        if (welcome) {
            welcome.remove();
        }
        
        this.elements.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    createTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = `
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        return indicator;
    }
    
    updateAssistantMessage(content) {
        if (!this.currentMessageElement) return;
        
        const contentDiv = this.currentMessageElement.querySelector('.message-content');
        
        // Remove typing indicator if present
        const typingIndicator = contentDiv.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        
        contentDiv.textContent = content;
        this.scrollToBottom();
    }
    
    finalizeAssistantMessage(content) {
        if (!this.currentMessageElement) return;
        
        const contentDiv = this.currentMessageElement.querySelector('.message-content');
        contentDiv.textContent = content;
        
        // Add timestamp
        if (CONFIG.SHOW_TIMESTAMPS) {
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = new Date().toLocaleTimeString('en-US', CONFIG.TIMESTAMP_FORMAT);
            contentDiv.appendChild(timeDiv);
        }
        
        this.currentMessageElement = null;
        this.scrollToBottom();
    }
    
    resetSendButton() {
        this.isProcessing = false;
        this.elements.sendBtn.disabled = false;
        this.elements.sendBtn.querySelector('#sendBtnText').textContent = 'Send';
    }
    
    scrollToBottom() {
        if (CONFIG.AUTO_SCROLL) {
            this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
        }
    }
    
    showNotification(message, type = 'info') {
        // Simple notification - could be enhanced with a proper notification system
        const notification = document.createElement('div');
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
            animation: slideIn 0.3s ease-out;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});

