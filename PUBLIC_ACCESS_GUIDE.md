# 🌐 Public Access Setup Guide

This guide will help you expose your LLM Studio model publicly with password authentication so you can access it from any network.

---

## 🚀 Quick Start (Choose One Option)

### Option 1: Quick Testing with ngrok (5 minutes)

**Best for:** Testing, temporary access, development

1. **Install ngrok:**
   ```bash
   curl -sSL https://ngrok-agent.s3.amazonaws.com/install.sh | sh
   ```

2. **Start your service:**
   ```bash
   cd /home/first/ai/aiModel
   source venv/bin/activate
   
   # Make sure LM Studio is running on port 1234
   # Then start the API service
   python app/main.py
   ```

3. **Expose publicly (in another terminal):**
   ```bash
   ngrok http 8000
   ```

4. **Get your public URL:**
   - Copy the `https://` URL from ngrok output (e.g., `https://abc123.ngrok.io`)

5. **Test it:**
   ```bash
   curl -X POST https://abc123.ngrok.io/api/chat \
     -H "X-User-Id: alice" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello!", "conversation_id": "test-1"}'
   ```

**Pros:**
- ✅ Setup in 5 minutes
- ✅ HTTPS automatically configured
- ✅ No need for domain or VPS

**Cons:**
- ❌ URL changes every restart (free tier)
- ❌ Not suitable for production
- ❌ Limited bandwidth

---

### Option 2: Production Setup with VPS (30 minutes)

**Best for:** Permanent deployment, production use, custom domain

#### Step 1: Run Setup Script

```bash
cd /home/first/ai/aiModel
./setup_public_access.sh
```

This will:
- Generate secure secrets
- Create `.env.production` configuration
- Create nginx configuration
- Create systemd service file
- Create token generation script

#### Step 2: Install Dependencies

```bash
# Install nginx and SSL certificate manager
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx postgresql-client

# Copy nginx configuration
sudo cp nginx-ai-model.conf /etc/nginx/sites-available/ai-model
sudo ln -s /etc/nginx/sites-available/ai-model /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 3: Get SSL Certificate

```bash
# Replace with your domain
sudo certbot --nginx -d yourdomain.com
```

#### Step 4: Install System Service

```bash
# Copy systemd service
sudo cp ai-model.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ai-model
sudo systemctl start ai-model

# Check status
sudo systemctl status ai-model
```

#### Step 5: Open Firewall Ports

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### Step 6: Generate Authentication Token

```bash
source venv/bin/activate
python generate_token.py alice
```

Save the generated token and API key securely!

---

### Option 3: Docker Deployment (20 minutes)

**Best for:** Containerized deployments, easy scaling

1. **Create environment file:**
   ```bash
   ./setup_public_access.sh
   ```

2. **Build and start services:**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

3. **Configure nginx (optional, for HTTPS):**
   - Use the generated `nginx-ai-model.conf`
   - Install on host machine or use nginx container

4. **Generate tokens:**
   ```bash
   docker exec -it ai_companion_service python generate_token.py alice
   ```

---

## 🔐 Authentication Methods

Your service supports 3 authentication methods:

### Method 1: JWT Token (Recommended)

**Generate token:**
```bash
python generate_token.py alice 48  # 48 hours validity
```

**Use in requests:**
```bash
curl -X POST https://yourdomain.com/api/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is machine learning?",
    "conversation_id": "conv-123"
  }'
```

### Method 2: API Key (Long-lived)

**Generate API key:**
```bash
python generate_token.py alice
```

**Use in requests:**
```bash
curl -X POST https://yourdomain.com/api/chat \
  -H "X-API-Key: user_alice_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing",
    "conversation_id": "conv-123"
  }'
```

### Method 3: User ID (Development Only)

**⚠️ Only enable in development!**

Set in `.env`:
```env
REQUIRE_AUTHENTICATION=false
```

Then use:
```bash
curl -X POST https://yourdomain.com/api/chat \
  -H "X-User-Id: alice" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello!",
    "conversation_id": "conv-123"
  }'
```

---

## 🌍 Accessing from Another Network

### Using Python

```python
import requests

API_URL = "https://yourdomain.com/api/chat"
JWT_TOKEN = "your_jwt_token_here"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

data = {
    "message": "What is the meaning of life?",
    "conversation_id": "conv-42"
}

response = requests.post(API_URL, json=data, headers=headers)
print(response.json())
```

### Using JavaScript/Frontend

```javascript
const API_URL = 'https://yourdomain.com/api/chat';
const JWT_TOKEN = 'your_jwt_token_here';

async function chat(message, conversationId) {
    const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${JWT_TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            conversation_id: conversationId
        })
    });
    
    return await response.json();
}

// Usage
chat('Hello!', 'conv-123').then(console.log);
```

### Using curl

```bash
# Simple test
curl -X POST https://yourdomain.com/api/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, AI!",
    "conversation_id": "test-1"
  }'
```

---

## 📱 Frontend Web Interface

Your service includes a web chat interface at:

```
https://yourdomain.com/chat
```

Update `frontend/config.js` to set your domain:

```javascript
const API_CONFIG = {
    baseUrl: 'https://yourdomain.com',
    defaultUserId: 'alice',
    defaultToken: 'your_jwt_token_here'
};
```

---

## 🔧 Troubleshooting

### Issue: Service not accessible

**Check if service is running:**
```bash
sudo systemctl status ai-model
```

**Check logs:**
```bash
sudo journalctl -u ai-model -f
```

**Check nginx:**
```bash
sudo nginx -t
sudo systemctl status nginx
```

### Issue: LM Studio connection fails

**Make sure LM Studio is running:**
```bash
curl http://localhost:1234/v1/models
```

**Check environment variable:**
```bash
# In .env.production
LM_STUDIO_BASE_URL=http://localhost:1234/v1
```

**For Docker, use:**
```bash
LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
```

### Issue: Authentication errors

**Verify token:**
```python
from app.core.auth import decode_jwt_token
token = "your_token_here"
print(decode_jwt_token(token))
```

**Check environment:**
```bash
grep REQUIRE_AUTHENTICATION .env.production
# Should be: REQUIRE_AUTHENTICATION=true
```

### Issue: CORS errors

**Update CORS origins in `.env.production`:**
```env
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

**Restart service:**
```bash
sudo systemctl restart ai-model
```

---

## 🛡️ Security Checklist

Before going live:

- [ ] ✅ `REQUIRE_AUTHENTICATION=true` in production
- [ ] ✅ Strong JWT_SECRET_KEY generated (32+ characters)
- [ ] ✅ HTTPS/SSL certificate installed
- [ ] ✅ CORS configured with specific origins (no `*`)
- [ ] ✅ Rate limiting enabled
- [ ] ✅ Firewall configured (only ports 80, 443 open)
- [ ] ✅ Database password changed from default
- [ ] ✅ `.env.production` never committed to git
- [ ] ✅ Backups configured
- [ ] ✅ Monitoring/logging set up

---

## 📊 Monitoring

### Check service health:
```bash
curl https://yourdomain.com/health
```

### View metrics (Prometheus format):
```bash
curl https://yourdomain.com/metrics
```

### Monitor logs:
```bash
# Systemd service
sudo journalctl -u ai-model -f

# Docker
docker logs -f ai_companion_service
```

---

## 🚦 Performance Tips

### For better performance:

1. **Use a VPS close to your users** (lower latency)

2. **Enable Redis for distributed deployments:**
   ```env
   REDIS_URL=redis://localhost:6379/0
   REDIS_ENABLED=true
   ```

3. **Adjust memory settings based on load:**
   ```env
   SHORT_TERM_MEMORY_SIZE=10
   LONG_TERM_MEMORY_TOP_K=5
   ```

4. **Scale horizontally with load balancer:**
   ```bash
   # Run multiple instances behind nginx
   docker-compose up -d --scale ai-companion=3
   ```

---

## 📚 Additional Resources

- [Full Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md)
- [API Documentation](http://yourdomain.com/docs)
- [Authentication Guide](AUTHENTICATION.md)
- [Security Checklist](SECURITY_CHECKLIST.md)

---

## 🆘 Need Help?

If you encounter issues:

1. Check the logs first
2. Review the troubleshooting section
3. Verify all prerequisites are installed
4. Ensure LM Studio is running and accessible

---

**Last Updated:** December 2025

