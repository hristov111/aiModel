# Quick Start: OpenAI Integration

## Setup (2 minutes)

### 1. Add OpenAI API Key to `.env`
```bash
# Edit your .env file
nano .env

# Add these lines:
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
```

### 2. Verify Local Model (for explicit content)
Ensure LM Studio is running:
```bash
curl http://localhost:1234/v1/models
```

### 3. Restart the service
```bash
# Stop current service (Ctrl+C)
# Start again
uvicorn app.main:app --reload
```

## How It Works

### Normal Conversations
- Uses **OpenAI (gpt-4o-mini)** by default
- Fast, high-quality responses
- All AI features work: emotions, personality, memories

### Explicit Content
- System **automatically detects** explicit content in responses
- Switches to **local model** for uncensored output
- **Regenerates all AI chains** (emotions, personality, etc.) with local model

## Testing

### Test Normal Chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{
    "message": "What is Python used for?"
  }'
```

### Test Explicit Content Detection
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{
    "message": "Write me an explicit adult story"
  }'
```

Watch for the message:
```json
{
  "type": "thinking",
  "step": "explicit_content_detected",
  "data": {
    "message": "Switching to unrestricted model for explicit content..."
  }
}
```

## Monitor Logs

```bash
# Watch for OpenAI and explicit content detection
tail -f app.log | grep -E "OpenAI|explicit|Local model"
```

### Expected Log Entries

**Service Start:**
```
Initialized OpenAI client: model=gpt-4o-mini
ContentFilter initialized with sensitivity: medium
```

**Normal Request:**
```
Generating response with OpenAI for explicit content check...
No explicit content detected - using OpenAI response
```

**Explicit Content Request:**
```
Generating response with OpenAI for explicit content check...
🔞 Explicit content detected - switching to local model
Regenerating all AI chains with local model...
Local model generated 450 chars
```

## Configuration Options

### Change Model
Edit `.env`:
```env
# Use GPT-4o (more expensive, higher quality)
OPENAI_MODEL_NAME=gpt-4o

# Use GPT-3.5 Turbo (cheaper, faster)
OPENAI_MODEL_NAME=gpt-3.5-turbo
```

### Adjust Content Filter Sensitivity
Edit `app/services/content_filter.py`:
```python
# In get_content_filter() function
content_filter = ContentFilter(sensitivity="high")  # More strict
content_filter = ContentFilter(sensitivity="low")   # More permissive
```

### Disable OpenAI (Use Only Local Model)
Edit `app/core/dependencies.py`:
```python
def get_llm_client_dep() -> LLMClient:
    """Get LLM client dependency."""
    return get_llm_client(provider="local")  # Change from "openai" to "local"
```

## Troubleshooting

### "OpenAI API key not configured"
❌ **Problem**: Missing API key
✅ **Solution**: Add `OPENAI_API_KEY` to `.env` file

### "Failed to connect to OpenAI"
❌ **Problem**: Network or API key issue
✅ **Solution**: 
- Check internet connection
- Verify API key is valid
- Check OpenAI service status

### Local model not responding for explicit content
❌ **Problem**: LM Studio not running
✅ **Solution**: Start LM Studio at `http://localhost:1234`

### Content not being detected as explicit
❌ **Problem**: Sensitivity too low
✅ **Solution**: Increase sensitivity in `content_filter.py`

## Cost Estimation

### OpenAI API Costs (gpt-4o-mini)
- **Input**: $0.15 per 1M tokens
- **Output**: $0.60 per 1M tokens
- **Average request**: ~$0.001-0.005 per chat

### Example Usage
- 1,000 requests/day: ~$3-5/day
- 10,000 requests/day: ~$30-50/day

**Note**: Explicit content requests don't incur additional OpenAI costs (they switch to local).

## Next Steps

1. ✅ Set up OpenAI API key
2. ✅ Test normal and explicit requests
3. 📊 Monitor usage and costs
4. 🎨 Customize content filter if needed
5. 🚀 Deploy to production

## Support

For issues or questions:
- Check `OPENAI_INTEGRATION_SUMMARY.md` for detailed information
- Review logs in `app.log`
- Test with `curl` commands above

