# 🚀 Docker Quick Start - 5 Minutes to Running

## Prerequisites Check

```bash
# Check Docker is installed
docker --version
# Should show: Docker version 20.10+

# Check Docker Compose is installed
docker-compose --version
# Should show: Docker Compose version 2.0+

# Check Docker is running
docker ps
# Should show empty list or running containers
```

## Setup in 4 Steps

### Step 1: Copy Environment File (30 seconds)

```bash
cd "/home/bean12/Desktop/AI Service"
cp ENV_EXAMPLE.txt .env
```

### Step 2: Add Your OpenAI API Key (1 minute)

```bash
nano .env
# or: code .env
# or: vim .env
```

Find this line:
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

Replace with your actual key:
```bash
OPENAI_API_KEY=sk-proj-xxx...your-real-key
```

Save and exit.

### Step 3: Start Development Environment (2 minutes)

```bash
make dev
```

Wait for services to start... ☕

### Step 4: Test It Works (30 seconds)

```bash
# Check health
make health

# Or visit in browser:
# http://localhost:8000/docs
```

## ✅ You're Done!

Your AI Companion Service is now running:

- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000
- **Database**: localhost:5433
- **Redis**: localhost:6379

## 🎯 Next Steps

### Create Your First User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "SecurePass123!"}'
```

### Get Authentication Token

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=SecurePass123!"
```

Copy the `access_token` from response.

### Send Your First Message

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"message": "Hello! What can you do?"}'
```

## 🔧 Useful Commands

```bash
make logs          # View logs
make stop          # Stop services
make dev           # Restart services
make shell         # Access container
make db-backup     # Backup database
```

## 🐛 Troubleshooting

### Port Already in Use?

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Or change port in .env:
APP_PORT=8080
```

### Services Won't Start?

```bash
# Check logs for errors
make logs

# Try clean restart
make stop
make dev
```

### Can't Connect to Database?

```bash
# Check database is running
docker-compose ps postgres

# Check logs
make logs-db

# Restart database
docker-compose restart postgres
```

## 📚 Full Documentation

- **Quick Reference**: `DOCKER_README.md`
- **Complete Guide**: `DOCKER_GUIDE.md`
- **Setup Summary**: `DOCKER_SETUP_SUMMARY.md`

## 🆘 Still Having Issues?

1. Check logs: `make logs`
2. Check service status: `make status`
3. Review `DOCKER_GUIDE.md` troubleshooting section
4. Make sure `.env` has your OpenAI API key
5. Ensure Docker has enough memory (4GB minimum)

---

**Ready to Code!** 🎉

