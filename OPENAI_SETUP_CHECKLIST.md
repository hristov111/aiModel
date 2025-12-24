# OpenAI Integration Setup Checklist

## ✅ Implementation Complete

All code changes have been implemented successfully:

- [x] Added OpenAI configuration to `app/core/config.py`
- [x] Created `OpenAIClient` class in `app/services/llm_client.py`
- [x] Created content filter service in `app/services/content_filter.py`
- [x] Added LLM client factory with provider selection
- [x] Updated `app/services/chat_service.py` for dual-model flow
- [x] Updated `app/core/dependencies.py` to use OpenAI by default
- [x] Updated `ENV_EXAMPLE.txt` with OpenAI configuration

## 🔧 Setup Required (Do This Now)

### 1. Get OpenAI API Key
- [ ] Go to https://platform.openai.com/api-keys
- [ ] Create a new API key
- [ ] Copy the key (starts with `sk-proj-...` or `sk-...`)

### 2. Update Environment File
- [ ] Edit your `.env` file
- [ ] Add the following lines:
```env
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
```

### 3. Verify Local Model Setup
- [ ] Ensure LM Studio is running: `curl http://localhost:1234/v1/models`
- [ ] Verify `LM_STUDIO_BASE_URL=http://localhost:1234/v1` in `.env`

### 4. Restart Service
- [ ] Stop current service (Ctrl+C)
- [ ] Start service: `uvicorn app.main:app --reload`
- [ ] Check logs for: `Initialized OpenAI client: model=gpt-4o-mini`

## 🧪 Testing Checklist

### Test 1: Normal Request (Should use OpenAI)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{"message": "Explain quantum computing in simple terms"}'
```
- [ ] Response received within 1-3 seconds
- [ ] Logs show: `No explicit content detected - using OpenAI response`

### Test 2: Explicit Content (Should switch to local model)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{"message": "Write an explicit adult story about two people"}'
```
- [ ] Thinking step shows: `"Switching to unrestricted model for explicit content..."`
- [ ] Logs show: `🔞 Explicit content detected - switching to local model`
- [ ] Response generated from local model

### Test 3: Health Check
```bash
curl http://localhost:8000/health
```
- [ ] Response shows `"llm": true` (OpenAI accessible)
- [ ] Response shows `"database": true` (PostgreSQL connected)

### Test 4: All AI Features
- [ ] Emotion detection working
- [ ] Personality detection working
- [ ] Memory extraction working
- [ ] Goal tracking working
- [ ] Preferences being respected

## 📊 Monitoring

### Check Logs
```bash
tail -f app.log | grep -E "OpenAI|explicit|Local model"
```

### Expected Log Patterns
**On Startup:**
```
Initialized OpenAI client: model=gpt-4o-mini
ContentFilter initialized with sensitivity: medium
```

**Normal Request:**
```
Generating response with OpenAI for explicit content check...
No explicit content detected - using OpenAI response
```

**Explicit Request:**
```
Generating response with OpenAI for explicit content check...
🔞 Explicit content detected - switching to local model
Regenerating all AI chains with local model...
Local model generated X chars
```

## 🐛 Common Issues & Solutions

### Issue: "OpenAI API key not configured"
**Solution:**
```bash
# Check if .env file has the key
grep OPENAI_API_KEY .env

# If missing, add it:
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

### Issue: "Failed to connect to OpenAI"
**Solutions:**
1. Check internet connection
2. Verify API key: https://platform.openai.com/api-keys
3. Check OpenAI status: https://status.openai.com/

### Issue: Local model not responding for explicit content
**Solution:**
```bash
# Check if LM Studio is running
curl http://localhost:1234/v1/models

# If not running, start LM Studio
```

### Issue: Everything flagged as explicit (false positives)
**Solution:**
```python
# Edit app/services/content_filter.py
# Change sensitivity from "medium" to "low"
content_filter = ContentFilter(sensitivity="low")
```

### Issue: Explicit content not being detected (false negatives)
**Solution:**
```python
# Edit app/services/content_filter.py
# Change sensitivity from "medium" to "high"
content_filter = ContentFilter(sensitivity="high")
```

## 💰 Cost Tracking

### Monitor OpenAI Usage
- [ ] Set up billing alerts in OpenAI dashboard
- [ ] Monitor token usage: https://platform.openai.com/usage
- [ ] Set monthly spending limits if needed

### Estimated Costs (gpt-4o-mini)
- Small usage (100 requests/day): ~$0.30/day
- Medium usage (1,000 requests/day): ~$3-5/day
- Large usage (10,000 requests/day): ~$30-50/day

## 📋 Production Deployment Checklist

Before deploying to production:

- [ ] OpenAI API key set in production environment
- [ ] Rate limits configured appropriately
- [ ] Billing alerts set up in OpenAI dashboard
- [ ] Local model is running and accessible
- [ ] Health checks passing
- [ ] Logs configured for monitoring
- [ ] Content filter sensitivity tested with real use cases
- [ ] Backup plan if OpenAI API is down
- [ ] Cost monitoring in place

## 🎯 Success Criteria

Your integration is successful when:

- [x] ✅ Code implemented without errors
- [ ] ✅ OpenAI API key configured
- [ ] ✅ Normal requests use OpenAI (fast responses)
- [ ] ✅ Explicit requests use local model (uncensored)
- [ ] ✅ All AI features working (emotions, personality, etc.)
- [ ] ✅ No errors in logs
- [ ] ✅ Health check passing

## 📚 Documentation

Reference documents created:
- `OPENAI_INTEGRATION_SUMMARY.md` - Detailed technical documentation
- `QUICK_START_OPENAI.md` - Quick setup and testing guide
- `OPENAI_SETUP_CHECKLIST.md` - This checklist

## 🚀 Next Steps

1. Complete setup checklist above
2. Test both normal and explicit requests
3. Monitor costs for first week
4. Adjust content filter sensitivity if needed
5. Deploy to production when ready

---

**Need Help?**
- Review logs: `tail -f app.log`
- Check health: `curl http://localhost:8000/health`
- Read docs: `OPENAI_INTEGRATION_SUMMARY.md`


