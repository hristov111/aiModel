# Frontend Age Verification Implementation Guide

## Overview

Age verification is now handled through a **frontend popup/modal** instead of requiring users to type "yes" in the chat. This provides a better UX and clearer consent flow.

---

## How It Works

### 1. **User Flow**

```
User: "Tell me something sexy"
   ↓
Backend: Detects explicit content
   ↓
Backend: Checks if age verified → NO
   ↓
Backend: Returns "age_verification_required" event
   ↓
Frontend: Shows age confirmation popup ✅
   ↓
User: Clicks "I am 18+" button
   ↓
Frontend: Calls POST /content/age-verify
   ↓
Backend: Marks session as age-verified
   ↓
User: Re-sends original message
   ↓
Backend: Processes explicit content ✅
```

---

## Backend Changes

### What Was Removed ❌

- Chat-based age detection (no more "yes" parsing)
- Age verification prompts in chat responses
- Pattern matching for "yes", "confirm", "18+", etc.

### What Was Added ✅

**New Event Type:** `age_verification_required`

When explicit content is detected and user hasn't verified age, the backend returns:

```json
{
  "type": "age_verification_required",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "message": "Age verification required to access this content",
    "route": "EXPLICIT",
    "api_endpoint": "/content/age-verify",
    "instructions": "Please confirm you are 18+ years old to continue"
  },
  "timestamp": "2026-01-03T18:45:00.000Z"
}
```

---

## API Endpoints

### 1. Age Verification Endpoint

**POST** `/content/age-verify`

Verify user's age for explicit content access.

**Request:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "confirmed": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Age verified successfully",
  "age_verified": true
}
```

**Headers:**
- `Authorization: Bearer <token>` or `X-User-Id: <user_id>` or `X-API-Key: <api_key>`

**Rate Limit:** 20 requests/minute

---

### 2. Check Session State

**GET** `/content/session/{conversation_id}`

Check if age is already verified for a conversation.

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "age_verified": true,
  "current_route": "EXPLICIT",
  "route_locked": true,
  "route_lock_remaining": 4
}
```

---

## Frontend Implementation

### JavaScript/TypeScript Example

```typescript
// chat.js or chat.ts

class ChatClient {
  private currentConversationId: string | null = null;
  private pendingMessage: string | null = null;
  
  async sendMessage(message: string) {
    this.pendingMessage = message;
    
    const response = await fetch('/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': this.userId,
      },
      body: JSON.stringify({
        message: message,
        conversation_id: this.currentConversationId,
      }),
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          await this.handleEvent(data);
        }
      }
    }
  }
  
  async handleEvent(event: any) {
    switch (event.type) {
      case 'age_verification_required':
        // Show age verification popup
        await this.showAgeVerificationModal(event);
        break;
        
      case 'chunk':
        // Display message chunk
        this.displayChunk(event.chunk);
        break;
        
      case 'done':
        this.currentConversationId = event.conversation_id;
        break;
        
      case 'error':
        this.displayError(event.error);
        break;
    }
  }
  
  async showAgeVerificationModal(event: any) {
    const conversationId = event.conversation_id;
    
    // Show modal/popup (implementation depends on your UI framework)
    const confirmed = await this.displayAgeConfirmationDialog({
      title: 'Age Verification Required',
      message: event.data.instructions,
      confirmText: 'I am 18 or older',
      cancelText: 'Cancel',
    });
    
    if (confirmed) {
      // User confirmed - verify age via API
      await this.verifyAge(conversationId);
      
      // Re-send the original message
      if (this.pendingMessage) {
        await this.sendMessage(this.pendingMessage);
      }
    } else {
      // User declined
      this.displayError('Age verification is required to access this content.');
    }
  }
  
  async verifyAge(conversationId: string): Promise<boolean> {
    const response = await fetch('/content/age-verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': this.userId,
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        confirmed: true,
      }),
    });
    
    const result = await response.json();
    return result.age_verified;
  }
  
  displayAgeConfirmationDialog(options: any): Promise<boolean> {
    // Implementation depends on your UI framework
    // Examples below for different frameworks
    return new Promise((resolve) => {
      // Show modal and resolve with true/false based on user choice
    });
  }
}
```

---

### React Example

```tsx
// components/AgeVerificationModal.tsx

import React, { useState } from 'react';
import { Modal, Button, Text } from './ui';

interface AgeVerificationModalProps {
  open: boolean;
  conversationId: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function AgeVerificationModal({
  open,
  conversationId,
  onConfirm,
  onCancel,
}: AgeVerificationModalProps) {
  const [loading, setLoading] = useState(false);
  
  const handleConfirm = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('/content/age-verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': localStorage.getItem('userId'),
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          confirmed: true,
        }),
      });
      
      const result = await response.json();
      
      if (result.age_verified) {
        onConfirm();
      }
    } catch (error) {
      console.error('Age verification failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Modal open={open} onClose={onCancel}>
      <Modal.Header>
        <h2>Age Verification Required</h2>
      </Modal.Header>
      
      <Modal.Body>
        <Text>
          This conversation contains adult content. To continue, please confirm
          that you are 18 years of age or older.
        </Text>
        
        <Text className="text-sm text-gray-500 mt-4">
          By clicking "I am 18 or older", you certify that you meet the age
          requirement and consent to view adult content.
        </Text>
      </Modal.Body>
      
      <Modal.Footer>
        <Button variant="secondary" onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
        <Button variant="primary" onClick={handleConfirm} loading={loading}>
          I am 18 or older
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
```

```tsx
// components/Chat.tsx

import React, { useState } from 'react';
import { AgeVerificationModal } from './AgeVerificationModal';

export function Chat() {
  const [ageVerificationOpen, setAgeVerificationOpen] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  
  const handleSendMessage = async (message: string) => {
    setPendingMessage(message);
    
    // ... send message via SSE
    // When you receive age_verification_required event:
  };
  
  const handleStreamEvent = (event: any) => {
    if (event.type === 'age_verification_required') {
      setCurrentConversationId(event.conversation_id);
      setAgeVerificationOpen(true);
    }
    // ... handle other event types
  };
  
  const handleAgeConfirmed = async () => {
    setAgeVerificationOpen(false);
    
    // Re-send the pending message
    if (pendingMessage) {
      await handleSendMessage(pendingMessage);
    }
  };
  
  const handleAgeDeclined = () => {
    setAgeVerificationOpen(false);
    setPendingMessage(null);
    // Show error message
  };
  
  return (
    <div>
      {/* Chat UI */}
      
      <AgeVerificationModal
        open={ageVerificationOpen}
        conversationId={currentConversationId!}
        onConfirm={handleAgeConfirmed}
        onCancel={handleAgeDeclined}
      />
    </div>
  );
}
```

---

### Vue Example

```vue
<!-- components/AgeVerificationModal.vue -->

<template>
  <Modal :open="open" @close="onCancel">
    <template #header>
      <h2>Age Verification Required</h2>
    </template>
    
    <template #body>
      <p>
        This conversation contains adult content. To continue, please confirm
        that you are 18 years of age or older.
      </p>
      
      <p class="text-sm text-gray-500 mt-4">
        By clicking "I am 18 or older", you certify that you meet the age
        requirement and consent to view adult content.
      </p>
    </template>
    
    <template #footer>
      <Button variant="secondary" @click="onCancel" :disabled="loading">
        Cancel
      </Button>
      <Button variant="primary" @click="handleConfirm" :loading="loading">
        I am 18 or older
      </Button>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  open: boolean;
  conversationId: string;
}>();

const emit = defineEmits<{
  confirm: [];
  cancel: [];
}>();

const loading = ref(false);

async function handleConfirm() {
  loading.value = true;
  
  try {
    const response = await fetch('/content/age-verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': localStorage.getItem('userId'),
      },
      body: JSON.stringify({
        conversation_id: props.conversationId,
        confirmed: true,
      }),
    });
    
    const result = await response.json();
    
    if (result.age_verified) {
      emit('confirm');
    }
  } catch (error) {
    console.error('Age verification failed:', error);
  } finally {
    loading.value = false;
  }
}
</script>
```

---

## HTML/CSS Example (Vanilla JS)

```html
<!-- Age Verification Modal -->
<div id="ageVerificationModal" class="modal" style="display: none;">
  <div class="modal-content">
    <h2>Age Verification Required</h2>
    <p>
      This conversation contains adult content. To continue, please confirm
      that you are 18 years of age or older.
    </p>
    <p class="disclaimer">
      By clicking "I am 18 or older", you certify that you meet the age
      requirement and consent to view adult content.
    </p>
    <div class="modal-buttons">
      <button id="cancelBtn" class="btn btn-secondary">Cancel</button>
      <button id="confirmBtn" class="btn btn-primary">I am 18 or older</button>
    </div>
  </div>
</div>

<style>
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 24px;
  max-width: 500px;
  width: 90%;
}

.modal-buttons {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  justify-content: flex-end;
}

.disclaimer {
  font-size: 0.875rem;
  color: #666;
  margin-top: 16px;
}
</style>

<script>
let currentConversationId = null;
let pendingMessage = null;

function showAgeVerificationModal(conversationId) {
  currentConversationId = conversationId;
  document.getElementById('ageVerificationModal').style.display = 'flex';
}

function hideAgeVerificationModal() {
  document.getElementById('ageVerificationModal').style.display = 'none';
}

document.getElementById('confirmBtn').addEventListener('click', async () => {
  try {
    const response = await fetch('/content/age-verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': localStorage.getItem('userId'),
      },
      body: JSON.stringify({
        conversation_id: currentConversationId,
        confirmed: true,
      }),
    });
    
    const result = await response.json();
    
    if (result.age_verified) {
      hideAgeVerificationModal();
      
      // Re-send pending message
      if (pendingMessage) {
        sendMessage(pendingMessage);
      }
    }
  } catch (error) {
    console.error('Age verification failed:', error);
  }
});

document.getElementById('cancelBtn').addEventListener('click', () => {
  hideAgeVerificationModal();
  pendingMessage = null;
});

// Handle SSE events
function handleStreamEvent(event) {
  if (event.type === 'age_verification_required') {
    showAgeVerificationModal(event.conversation_id);
  }
  // ... handle other events
}
</script>
```

---

## Testing the Flow

### 1. Test Age Verification Trigger

```bash
# Send explicit message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test_user" \
  -d '{
    "message": "Tell me something sexy"
  }'

# Expected response:
# data: {"type":"age_verification_required","conversation_id":"...","data":{...}}
```

### 2. Test Age Verification API

```bash
# Verify age
curl -X POST http://localhost:8000/content/age-verify \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test_user" \
  -d '{
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "confirmed": true
  }'

# Expected response:
# {"success":true,"message":"Age verified successfully","age_verified":true}
```

### 3. Test Session Persistence

```bash
# Send explicit message again (should work now)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test_user" \
  -d '{
    "message": "Tell me something sexy",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'

# Should process normally without age verification
```

---

## Best Practices

### 1. **Store Age Verification State**

```typescript
// Don't ask again for the same conversation
const ageVerifiedConversations = new Set<string>();

if (event.type === 'age_verification_required') {
  if (!ageVerifiedConversations.has(event.conversation_id)) {
    showAgeVerificationModal(event.conversation_id);
  }
}

// After successful verification
ageVerifiedConversations.add(conversationId);
```

### 2. **Handle Errors Gracefully**

```typescript
try {
  await verifyAge(conversationId);
} catch (error) {
  // Show user-friendly error
  showError('Unable to verify age. Please try again.');
}
```

### 3. **Provide Clear UI Feedback**

```typescript
// Show loading state while verifying
setLoading(true);
await verifyAge(conversationId);
setLoading(false);

// Show success message
showToast('Age verified successfully');
```

### 4. **Remember to Re-send Message**

```typescript
// Important: After verification, automatically re-send the original message
if (ageVerified && pendingMessage) {
  await sendMessage(pendingMessage);
  setPendingMessage(null);
}
```

---

## Migration Notes

### Old Behavior (Removed)
- ❌ User types explicit message
- ❌ AI asks "Are you 18+?"
- ❌ User types "yes"
- ❌ AI confirms and asks to repeat question

### New Behavior (Current)
- ✅ User types explicit message
- ✅ Frontend shows age popup
- ✅ User clicks "I am 18+"
- ✅ Message automatically re-sent
- ✅ AI responds to original message

---

## Security Considerations

1. **Server-Side Enforcement**
   - Age verification is checked server-side
   - Cannot be bypassed by frontend manipulation

2. **Session-Based**
   - Verification is tied to conversation ID
   - Each conversation requires its own verification

3. **Rate Limited**
   - 20 verifications per minute per user
   - Prevents abuse

4. **Audit Logged**
   - All verification attempts are logged
   - Includes user ID, conversation ID, timestamp

---

## Support & Troubleshooting

### Common Issues

**Q: Age verification popup shows but API call fails**
A: Check that the user authentication header is included in the request

**Q: User verified age but still gets prompted**
A: Ensure you're passing the correct `conversation_id` in subsequent messages

**Q: Age verification not triggering**
A: Check that content is actually classified as explicit/fetish (requires age verification)

---

## Summary

✅ **Backend Changes Complete**
- Removed chat-based "yes" detection
- Added `age_verification_required` event type
- API endpoint already exists and working

✅ **Frontend Implementation Needed**
- Listen for `age_verification_required` event
- Show age confirmation popup/modal
- Call `/content/age-verify` API when user confirms
- Re-send original message after verification

✅ **Better UX**
- Clear consent flow
- No ambiguous "yes" responses
- Professional age gate interface
- Automatic message re-submission

---

**Date:** January 3, 2026  
**Status:** ✅ Backend Complete, Frontend Implementation Required

