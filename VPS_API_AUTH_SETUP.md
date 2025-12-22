# 🔐 VPS API Authorization Setup

## ✅ Changes Implemented

Successfully added API key authorization for all requests to your LLM API!

---

## 📝 What Was Changed

### 1. **Config Settings** (`app/core/config.py`)
Added new configuration parameter:
```python
vps_api_key: str = ""  # API key for VPS LLM authorization
```

### 2. **LLM Client** (`app/services/llm_client.py`)
Updated to use the API key from settings:
```python
# Get API key from settings (for VPS authorization)
api_key = settings.vps_api_key or "not-needed"

# Create OpenAI client pointing to LM Studio/VPS
self.client = AsyncOpenAI(
    base_url=self.base_url,
    api_key=api_key,  # Use VPS_API_KEY if configured
    timeout=httpx.Timeout(timeout, connect=5.0),
    max_retries=2,
)

# Log initialization (mask API key for security)
masked_key = api_key[:8] + "..." if len(api_key) > 8 else "not-needed"
logger.info(f"Initialized LM Studio client: {self.base_url} (API key: {masked_key})")
```

### 3. **Environment Example** (`ENV_EXAMPLE.txt`)
Added the new configuration option with documentation.

---

## 🚀 How to Configure

### Step 1: Add to Your `.env` File

Add this line to your `.env` file (create it if it doesn't exist):

```bash
# VPS API Authorization (if using remote LLM server)
VPS_API_KEY=your-actual-secret-key-here
```

**Example with your current setup:**
```bash
# LM Studio Configuration
LM_STUDIO_BASE_URL=http://66.42.93.128/llm/v1
LM_STUDIO_MODEL_NAME=qwen2.5-7b-instruct
LM_STUDIO_TEMPERATURE=0.7
LM_STUDIO_MAX_TOKENS=150

# VPS API Authorization
VPS_API_KEY=sk_your_secret_api_key_12345
```

### Step 2: Restart the Application

```bash
cd "/home/bean12/Desktop/AI Service"
pkill -f uvicorn
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🔍 How It Works

### Authorization Flow

```
┌─────────────────────────────────────────────┐
│ 1. App loads VPS_API_KEY from .env         │
├─────────────────────────────────────────────┤
│ 2. LLM Client initializes with API key     │
├─────────────────────────────────────────────┤
│ 3. Every request includes header:          │
│    Authorization: Bearer <your-key>        │
├─────────────────────────────────────────────┤
│ 4. VPS validates key before processing     │
├─────────────────────────────────────────────┤
│ 5. Request succeeds ✅                     │
└─────────────────────────────────────────────┘
```

### HTTP Request Example

Every request to your LLM now includes:

```http
POST http://66.42.93.128/llm/v1/chat/completions
Authorization: Bearer sk_your_secret_api_key_12345
Content-Type: application/json

{
  "model": "qwen2.5-7b-instruct",
  "messages": [...],
  "temperature": 0.7,
  "stream": true
}
```

---

## 🔒 Security Features

### 1. **API Key Masking in Logs**
Your API key is never fully exposed in logs:
```
Initialized LM Studio client: http://66.42.93.128/llm/v1 (API key: sk_your_...)
```

### 2. **Environment Variable Protection**
- API key stored in `.env` (git ignored)
- Never hardcoded in source code
- Loaded at runtime only

### 3. **Backward Compatibility**
If `VPS_API_KEY` is not set:
- Defaults to `"not-needed"`
- Works with local LM Studio without auth

---

## ✅ Verification

### Check if API Key is Loaded

Look for this in your app logs when starting:
```
Initialized LM Studio client: http://66.42.93.128/llm/v1 (API key: sk_your_...)
```

If you see `(API key: not-need...)`, the key wasn't loaded from `.env`.

### Test API Request

```bash
# Check health endpoint
curl http://localhost:8000/health

# Send a test message (should use API key)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: testuser" \
  -d '{"message": "Hello!"}'
```

If your VPS requires auth, requests will now succeed! ✅

---

## 🛠️ Troubleshooting

### Error: "Authentication failed" or "401 Unauthorized"

**Problem**: VPS is rejecting the API key

**Solutions**:
1. Check your `.env` file has the correct key
2. No extra spaces: `VPS_API_KEY=sk_key` (not `VPS_API_KEY= sk_key`)
3. Restart the app after changing `.env`
4. Verify the key is valid on your VPS

### Error: "VPS_API_KEY not found"

**Problem**: Settings not loading from `.env`

**Solutions**:
1. Ensure `.env` file exists in project root
2. Check file permissions: `chmod 600 .env`
3. Verify pydantic-settings is installed: `pip install pydantic-settings`

---

## 📋 Checklist

- [x] ✅ Config updated with `vps_api_key` setting
- [x] ✅ LLM client uses API key from settings
- [x] ✅ API key masked in logs for security
- [x] ✅ ENV_EXAMPLE.txt updated with documentation
- [ ] ⏳ Add `VPS_API_KEY` to your `.env` file
- [ ] ⏳ Restart the application
- [ ] ⏳ Test that requests work with authorization

---

## 🎯 Summary

All LLM requests now include your VPS API key in the `Authorization` header automatically! 

Your VPS can now:
- ✅ Validate incoming requests
- ✅ Track usage per API key
- ✅ Rate limit per key
- ✅ Secure your LLM endpoint

**Implementation Date**: December 18, 2025  
**Status**: Ready to use! Just add your key to `.env` and restart.

