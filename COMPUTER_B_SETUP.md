# 🖥️ Computer B Setup Guide (App + Database)

## Overview

Computer B runs the AI application and database. It connects to Computer A's LM Studio via VPS.

---

## 📋 Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)
- Access to VPS for port 8000 tunnel

---

## 🚀 Setup Instructions

### Step 1: Transfer Project Files

Copy the entire project folder to Computer B:

```bash
# Option A: Clone from git (if you have it in a repo)
git clone <your-repo-url>
cd aiModel

# Option B: Transfer via SCP from Computer A
# (Run on Computer A)
tar -czf aiModel.tar.gz /home/first/ai/aiModel
scp aiModel.tar.gz user@computer-b:/home/user/
# (Then on Computer B)
tar -xzf aiModel.tar.gz
cd aiModel
```

### Step 2: Create Environment Configuration

Create `.env` file on Computer B:

```bash
cat > .env << 'EOF'
# AI Companion Service Configuration for Computer B

# ============================================
# Environment
# ============================================
ENVIRONMENT=development

# ============================================
# LM Studio (via VPS - Computer A)
# ============================================
LM_STUDIO_BASE_URL=http://66.42.93.128/llm/v1
LM_STUDIO_MODEL_NAME=local-model
LM_STUDIO_TEMPERATURE=0.7
LM_STUDIO_MAX_TOKENS=2000

# ============================================
# Database Configuration (Docker)
# ============================================
POSTGRES_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/ai_companion
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20

# ============================================
# Memory Configuration
# ============================================
SHORT_TERM_MEMORY_SIZE=10
LONG_TERM_MEMORY_TOP_K=5
MEMORY_SIMILARITY_THRESHOLD=0.3

# ============================================
# System Configuration
# ============================================
SYSTEM_PERSONA=a helpful, knowledgeable AI assistant with memory of past conversations
RATE_LIMIT_REQUESTS_PER_MINUTE=30

# ============================================
# Authentication
# ============================================
REQUIRE_AUTHENTICATION=false

# ============================================
# CORS Configuration
# ============================================
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://66.42.93.128

# ============================================
# Logging
# ============================================
LOG_LEVEL=INFO
EOF
```

### Step 3: Setup SSH Tunnel to VPS

Create tunnel service:

```bash
sudo tee /etc/systemd/system/ai-app-tunnel.service > /dev/null << 'EOF'
[Unit]
Description=AI App SSH Tunnel to VPS (Computer B)
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=YOUR_USERNAME_HERE
ExecStart=/usr/bin/autossh -M 0 \
    -o "ServerAliveInterval=30" \
    -o "ServerAliveCountMax=3" \
    -o "ExitOnForwardFailure=yes" \
    -o "StrictHostKeyChecking=no" \
    -R 8000:localhost:8000 \
    emo@66.42.93.128 -N
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Replace YOUR_USERNAME_HERE with your actual username
sudo sed -i "s/YOUR_USERNAME_HERE/$USER/" /etc/systemd/system/ai-app-tunnel.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable ai-app-tunnel
sudo systemctl start ai-app-tunnel

# Verify
sudo systemctl status ai-app-tunnel
```

### Step 4: Start Docker Containers

```bash
# Make sure Docker is running
sudo systemctl start docker

# Start the application
docker-compose up -d

# Check status
docker ps

# Should see:
# - ai_companion_db (PostgreSQL)
# - ai_companion_service (App)
```

### Step 5: Run Database Migrations

```bash
docker exec ai_companion_service alembic upgrade head
```

### Step 6: Verify Everything

```bash
# Check local app
curl http://localhost:8000/health

# Check via VPS
curl http://66.42.93.128/health

# Check LM Studio connection (via VPS)
curl http://66.42.93.128/llm/v1/models
```

---

## 🌐 Access Your Application

### From Computer B (local):
```
http://localhost:8000/          → Chat UI
http://localhost:8000/docs      → API Documentation
```

### From Anywhere (via VPS):
```
http://66.42.93.128/            → Chat UI
http://66.42.93.128/docs        → API Documentation
http://66.42.93.128/health      → Health Check
```

---

## 📊 Architecture

```
Computer B (THIS MACHINE)
├── Docker Containers
│   ├── PostgreSQL + pgvector (port 5432)
│   └── AI App (port 8000)
├── SSH Tunnel to VPS
│   └── Forwards localhost:8000 → VPS:8000
└── Connects to LM Studio via
    └── http://66.42.93.128/llm/v1 (proxied to Computer A)
```

---

## 🔍 Monitoring

### Check Docker Containers:
```bash
docker ps
docker logs ai_companion_service -f
docker logs ai_companion_db -f
```

### Check Tunnel:
```bash
sudo systemctl status ai-app-tunnel
sudo journalctl -u ai-app-tunnel -f
```

### Check VPS Connection:
```bash
ssh emo@66.42.93.128 "ss -tlnp | grep 8000"
```

---

## 🔧 Troubleshooting

### App can't reach LM Studio:

**Check VPS nginx proxy:**
```bash
ssh emo@66.42.93.128
sudo systemctl status nginx
sudo tail -f /var/log/nginx/ai-proxy-error.log
```

**Test LM Studio directly:**
```bash
curl http://66.42.93.128/llm/v1/models
```

### Tunnel keeps disconnecting:

**Check logs:**
```bash
sudo journalctl -u ai-app-tunnel -n 50
```

**Restart tunnel:**
```bash
sudo systemctl restart ai-app-tunnel
```

### Database issues:

**Check PostgreSQL:**
```bash
docker logs ai_companion_db
```

**Rerun migrations:**
```bash
docker exec ai_companion_service alembic upgrade head
```

---

## 📝 Important Notes

1. **Computer B should NOT have LM Studio** - it connects via VPS
2. **Port 8000 tunnel must be active** for public access
3. **VPS nginx must be configured** (see VPS setup)
4. **Computer A's LM Studio tunnel** must be running

---

## ✅ Checklist

Before Computer B can work, ensure:

- [ ] VPS nginx configured with LM Studio proxy
- [ ] Computer A's port 1234 tunnel is active
- [ ] Computer B's environment (.env) points to VPS
- [ ] Computer B's port 8000 tunnel is active
- [ ] Docker containers are running on Computer B
- [ ] Database migrations completed

---

## 🎯 Quick Start Commands

```bash
# On Computer B
cd aiModel

# Start everything
docker-compose up -d
docker exec ai_companion_service alembic upgrade head

# Verify
curl http://localhost:8000/health
curl http://66.42.93.128/health
```

That's it! Computer B is now running the application and connecting to Computer A's LM Studio via VPS. 🚀

