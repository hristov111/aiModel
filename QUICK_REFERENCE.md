# 🚀 Quick Reference - Public API Access

## 📋 One-Page Cheat Sheet

---

## ⚡ Super Fast Setup (ngrok - 2 minutes)

```bash
# Terminal 1: Start service
cd /home/first/ai/aiModel
source venv/bin/activate
python app/main.py

# Terminal 2: Expose publicly
ngrok http 8000

# Test it (replace URL with your ngrok URL)
curl -X POST https://YOUR-NGROK-URL.ngrok.io/api/chat \
  -H "X-User-Id: alice" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "conversation_id": "test-1"}'
```

---

## 🏭 Production Setup (VPS - 10 commands)

```bash
# 1. Run setup script
./setup_public_access.sh

# 2. Install nginx
sudo apt install nginx certbot python3-certbot-nginx -y

# 3. Configure nginx
sudo cp nginx-ai-model.conf /etc/nginx/sites-available/ai-model
sudo ln -s /etc/nginx/sites-available/ai-model /etc/nginx/sites-enabled/
sudo nginx -t

# 4. Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# 5. Install service
sudo cp ai-model.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-model
sudo systemctl start ai-model

# 6. Generate auth token
source venv/bin/activate
python generate_token.py alice

# 7. Test it
python test_public_api.py https://yourdomain.com/api/chat jwt YOUR_TOKEN
```

---

## 🔐 Generate Authentication

```bash
# Generate JWT token + API key
python generate_token.py <username> [hours]

# Examples:
python generate_token.py alice        # 24-hour token
python generate_token.py bob 48       # 48-hour token
```

---

## 🧪 Test Your API

```bash
# Test with JWT token
python test_public_api.py https://yourdomain.com/api/chat jwt YOUR_JWT_TOKEN

# Test with API key
python test_public_api.py https://yourdomain.com/api/chat api_key user_alice_xxx

# Test with user ID (dev only)
python test_public_api.py http://localhost:8000/api/chat user_id alice
```

---

## 📡 API Usage Examples

### Using curl

```bash
# JWT Token
curl -X POST https://yourdomain.com/api/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "conversation_id": "conv-1"}'

# API Key
curl -X POST https://yourdomain.com/api/chat \
  -H "X-API-Key: user_alice_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "conversation_id": "conv-1"}'
```

### Using Python

```python
import requests

response = requests.post(
    "https://yourdomain.com/api/chat",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={"message": "Hello!", "conversation_id": "conv-1"}
)
print(response.json())
```

### Using JavaScript

```javascript
fetch('https://yourdomain.com/api/chat', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer YOUR_TOKEN',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        message: 'Hello!',
        conversation_id: 'conv-1'
    })
}).then(r => r.json()).then(console.log);
```

---

## 🔍 Troubleshooting Commands

```bash
# Check service status
sudo systemctl status ai-model

# View logs
sudo journalctl -u ai-model -f

# Check nginx
sudo systemctl status nginx
sudo nginx -t

# Test LM Studio
curl http://localhost:1234/v1/models

# Check health
curl https://yourdomain.com/health

# View metrics
curl https://yourdomain.com/metrics

# Check open ports
sudo netstat -tulpn | grep LISTEN

# Test local connection
curl http://localhost:8000/health
```

---

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker logs -f ai_companion_service

# Generate token
docker exec -it ai_companion_service python generate_token.py alice

# Restart service
docker-compose restart ai-companion

# Stop all
docker-compose down
```

---

## 🛠️ Common Fixes

### "Connection refused"
```bash
# Check if service is running
sudo systemctl status ai-model
sudo systemctl start ai-model
```

### "Authentication failed"
```bash
# Generate new token
python generate_token.py alice

# Check auth is enabled
grep REQUIRE_AUTHENTICATION .env.production
```

### "LM Studio connection error"
```bash
# Make sure LM Studio is running
curl http://localhost:1234/v1/models

# Check environment variable
grep LM_STUDIO_BASE_URL .env.production
```

### "502 Bad Gateway"
```bash
# Service might be down
sudo systemctl restart ai-model

# Check logs
sudo journalctl -u ai-model -n 50
```

---

## 📊 Service Management

```bash
# Start service
sudo systemctl start ai-model

# Stop service
sudo systemctl stop ai-model

# Restart service
sudo systemctl restart ai-model

# Check status
sudo systemctl status ai-model

# Enable auto-start on boot
sudo systemctl enable ai-model

# Disable auto-start
sudo systemctl disable ai-model

# View real-time logs
sudo journalctl -u ai-model -f

# View last 100 lines
sudo journalctl -u ai-model -n 100
```

---

## 🌐 Firewall Configuration

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status

# Enable firewall
sudo ufw enable
```

---

## 🔐 Security Checklist

- [ ] `REQUIRE_AUTHENTICATION=true` in production
- [ ] Strong JWT_SECRET_KEY (32+ chars)
- [ ] HTTPS/SSL certificate installed
- [ ] CORS configured (no wildcard `*`)
- [ ] Firewall enabled (only 80, 443)
- [ ] Rate limiting enabled
- [ ] `.env.production` not in git
- [ ] Database password changed

---

## 📚 Important Files

| File | Purpose |
|------|---------|
| `.env.production` | Production configuration (never commit!) |
| `setup_public_access.sh` | Automated setup script |
| `generate_token.py` | Create auth tokens |
| `test_public_api.py` | Test your API |
| `nginx-ai-model.conf` | Nginx configuration |
| `ai-model.service` | Systemd service file |

---

## 🔗 Quick Links

- Health Check: `https://yourdomain.com/health`
- API Docs: `https://yourdomain.com/docs`
- Metrics: `https://yourdomain.com/metrics`
- Chat UI: `https://yourdomain.com/chat`

---

## 📞 Emergency Recovery

```bash
# Full restart
sudo systemctl restart ai-model
sudo systemctl restart nginx

# Check everything
sudo systemctl status ai-model
sudo systemctl status nginx
sudo systemctl status postgresql

# View all logs
sudo journalctl -xe

# Nuclear option: rebuild
cd /home/first/ai/aiModel
docker-compose down
docker-compose up -d --build
```

---

## 💾 Backup Commands

```bash
# Backup database
pg_dump -U postgres ai_companion > backup_$(date +%Y%m%d).sql

# Backup environment
cp .env.production .env.production.backup

# Backup nginx config
sudo cp /etc/nginx/sites-available/ai-model nginx-backup.conf
```

---

**For detailed instructions, see:** [PUBLIC_ACCESS_GUIDE.md](PUBLIC_ACCESS_GUIDE.md)

**Last Updated:** December 2025

