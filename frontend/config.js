/**
 * Configuration for AI Chat Frontend
 * 
 * These settings can be modified in the UI via the Settings modal.
 * Values are stored in localStorage for persistence.
 */

const CONFIG = {
    // Default API configuration
    DEFAULT_API_URL: 'http://localhost:8000',
    DEFAULT_USER_ID: 'user123',
    
    // Storage keys
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
    
    // Connection settings
    RECONNECT_DELAY: 3000, // ms
    MAX_RECONNECT_ATTEMPTS: 5,
    
    // Message formatting
    TIMESTAMP_FORMAT: {
        hour: '2-digit',
        minute: '2-digit'
    }
};

/**
 * Get configuration value from localStorage or use default
 */
function getConfig(key) {
    const storageKey = CONFIG.STORAGE_KEYS[key];
    if (!storageKey) return null;
    
    const stored = localStorage.getItem(storageKey);
    if (stored) return stored;
    
    // Return defaults
    switch (key) {
        case 'API_URL':
            return CONFIG.DEFAULT_API_URL;
        case 'USER_ID':
            return CONFIG.DEFAULT_USER_ID;
        case 'THINKING_VISIBLE':
            return CONFIG.THINKING_PANEL_DEFAULT_VISIBLE ? 'true' : 'false';
        default:
            return null;
    }
}

/**
 * Save configuration value to localStorage
 */
function setConfig(key, value) {
    const storageKey = CONFIG.STORAGE_KEYS[key];
    if (!storageKey) return false;
    
    if (value === null || value === undefined) {
        localStorage.removeItem(storageKey);
    } else {
        localStorage.setItem(storageKey, value);
    }
    return true;
}

/**
 * Clear all stored configuration
 */
function clearConfig() {
    Object.values(CONFIG.STORAGE_KEYS).forEach(key => {
        localStorage.removeItem(key);
    });
}

// Export for use in chat.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CONFIG, getConfig, setConfig, clearConfig };
}

