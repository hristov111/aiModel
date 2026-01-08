# 🔧 Development Guide - AI Companion Service

This guide is for developers who want to make code changes and test them quickly using Docker.

---

## 🚀 Quick Start (Development Mode)

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd ai-service

# 2. Create .env file
cp ENV_EXAMPLE.txt .env
nano .env  # Edit configuration (see below)

# 3. Start in development mode (with hot-reload)
docker-compose -f docker-compose.dev.yml up

# 4. Make changes to code in ./app/ → Auto-reloads! ✨
```

That's it! The service will automatically reload when you save any `.py` file.

---

## 📋 Minimum .env Configuration for Development

```bash
# Environment
ENVIRONMENT=development

# LM Studio (or leave empty if using OpenAI only)
LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
LM_STUDIO_MODEL_NAME=local-model

# OpenAI (optional for development)
OPENAI_API_KEY=  # Can leave empty

# Database (defaults work fine for dev)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme
POSTGRES_DB=ai_companion
POSTGRES_PORT=5433

# Redis (defaults work fine for dev)
REDIS_PASSWORD=changeme
REDIS_ENABLED=true

# Auth (generate a random string)
JWT_SECRET_KEY=dev-secret-change-in-production
ALLOW_X_USER_ID_AUTH=true

# Logging
LOG_LEVEL=DEBUG
```

**Generate JWT secret:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🔥 Key Difference: Development vs Production

| Feature | Development (`docker-compose.dev.yml`) | Production (`docker-compose.yml`) |
|---------|----------------------------------------|-----------------------------------|
| **Code Location** | Mounted from `./app/` (editable) | Baked into Docker image |
| **Code Changes** | ✅ Instant reload (no rebuild) | ❌ Requires rebuild (~2-5 min) |
| **Auto-reload** | ✅ Enabled (`--reload` flag) | ❌ Disabled |
| **Logging** | DEBUG level | INFO level |
| **Container Names** | `*_dev` suffix | Production names |
| **Use Case** | Active development | Deployment/Testing |
| **Command** | `docker-compose -f docker-compose.dev.yml up` | `docker-compose up -d` |

---

## 🛠️ Common Development Tasks

### Start Development Environment

```bash
# Start with logs visible (recommended)
docker-compose -f docker-compose.dev.yml up

# Or start in background
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f aiservice
```

---

### Make Code Changes

1. **Edit any file in `./app/` directory**
   ```bash
   nano app/services/chat_service.py
   # Make your changes and save
   ```

2. **Watch the logs** - You'll see:
   ```
   INFO: Will watch for changes in these directories: ['/app/app']
   WARNING: StatReload detected changes in 'chat_service.py'. Reloading...
   INFO: Started reloader process
   ```

3. **Test your changes** immediately!

**Files that trigger auto-reload:**
- ✅ All `.py` files in `./app/`
- ✅ `./migrations/` files
- ✅ `./frontend/` files

**Files that DON'T auto-reload (require restart):**
- ⚠️ `.env` file
- ⚠️ `requirements.txt`
- ⚠️ `Dockerfile`
- ⚠️ `docker-compose.dev.yml`

---

### Run Database Migrations

```bash
# Create new migration
docker-compose -f docker-compose.dev.yml exec aiservice alembic revision --autogenerate -m "Add new feature"

# Apply migrations
docker-compose -f docker-compose.dev.yml exec aiservice alembic upgrade head

# Rollback migration
docker-compose -f docker-compose.dev.yml exec aiservice alembic downgrade -1

# View migration history
docker-compose -f docker-compose.dev.yml exec aiservice alembic history
```

---

### Access Database Directly

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d ai_companion

# Common queries:
\dt                          # List tables
\d users                     # Describe users table
SELECT * FROM users LIMIT 5; # Query data
\q                          # Exit
```

---

### Access Redis

```bash
# Connect to Redis
docker-compose -f docker-compose.dev.yml exec redis redis-cli -a changeme

# Common commands:
KEYS *              # List all keys
GET key_name        # Get value
FLUSHALL            # Clear all data (careful!)
exit                # Exit
```

---

### Run Tests

```bash
# If you mounted ./tests directory, run:
docker-compose -f docker-compose.dev.yml exec aiservice pytest tests/ -v

# With coverage
docker-compose -f docker-compose.dev.yml exec aiservice pytest tests/ --cov=app --cov-report=html

# Run specific test file
docker-compose -f docker-compose.dev.yml exec aiservice pytest tests/test_chat.py -v
```

---

### Access Container Shell

```bash
# Get bash shell inside the container
docker-compose -f docker-compose.dev.yml exec aiservice bash

# Now you're inside the container, you can:
ls -la /app/app/          # View files
python -m app.main        # Run Python scripts
alembic current           # Check migration status
exit                      # Exit container
```

---

### Restart Service Only

```bash
# Restart just the AI service (keeps DB and Redis running)
docker-compose -f docker-compose.dev.yml restart aiservice

# Or restart everything
docker-compose -f docker-compose.dev.yml restart
```

---

### Stop Development Environment

```bash
# Stop all services (keeps data)
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (fresh start)
docker-compose -f docker-compose.dev.yml down -v

# Stop specific service
docker-compose -f docker-compose.dev.yml stop aiservice
```

---

### Rebuild After Dependency Changes

If you changed `requirements.txt` or `Dockerfile`:

```bash
# Rebuild image
docker-compose -f docker-compose.dev.yml build

# Start with new image
docker-compose -f docker-compose.dev.yml up
```

---

## 🧪 Testing Your Changes

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. View API Documentation
Open in browser: http://localhost:8000/docs

### 3. Test Chat Endpoint
```bash
# Using X-User-Id (development)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: dev-user" \
  -d '{"message": "Hello, test my changes!"}'

# Using JWT token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id":"dev-user","expires_in_hours":24}'

# Use the token from response in subsequent requests
```

---

## 🐛 Debugging Tips

### View Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Just AI service
docker-compose -f docker-compose.dev.yml logs -f aiservice

# Last 100 lines
docker-compose -f docker-compose.dev.yml logs --tail=100 aiservice

# With timestamps
docker-compose -f docker-compose.dev.yml logs -f -t aiservice
```

---

### Check Service Status

```bash
# List running containers
docker-compose -f docker-compose.dev.yml ps

# Check resource usage
docker stats ai_companion_service_dev
```

---

### Common Issues

#### 1. Port Already in Use
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Or change port in .env
APP_PORT=8001
```

#### 2. Changes Not Reloading
```bash
# Check if --reload is enabled in logs
docker-compose -f docker-compose.dev.yml logs aiservice | grep reload

# Manually restart
docker-compose -f docker-compose.dev.yml restart aiservice
```

#### 3. Database Connection Error
```bash
# Check if PostgreSQL is healthy
docker-compose -f docker-compose.dev.yml ps postgres

# View PostgreSQL logs
docker-compose -f docker-compose.dev.yml logs postgres

# Test connection
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d ai_companion -c "SELECT 1;"
```

#### 4. Module Import Errors
```bash
# Rebuild with new dependencies
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up
```

---

## 📊 Development Workflow Example

Here's a typical development session:

```bash
# Morning: Start development
cd ai-service
docker-compose -f docker-compose.dev.yml up

# Open another terminal for work
# Edit code in your IDE
code app/services/chat_service.py

# Save file → Service auto-reloads ✨
# Test in browser: http://localhost:8000/docs

# Need to add a new database field?
docker-compose -f docker-compose.dev.yml exec aiservice alembic revision --autogenerate -m "Add field"
docker-compose -f docker-compose.dev.yml exec aiservice alembic upgrade head

# Test your changes
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -H "X-User-Id: test" -d '{"message":"test"}'

# Check logs if something breaks
docker-compose -f docker-compose.dev.yml logs -f aiservice

# Evening: Stop development
docker-compose -f docker-compose.dev.yml down
```

---

## 🔄 Switching Between Development and Production

You can run both simultaneously (they use different ports/containers):

```bash
# Terminal 1: Development (port 8000)
docker-compose -f docker-compose.dev.yml up

# Terminal 2: Production (port 8001 if configured)
docker-compose up -d
```

Or use one at a time:

```bash
# Stop production
docker-compose down

# Start development
docker-compose -f docker-compose.dev.yml up

# Later: Stop development
docker-compose -f docker-compose.dev.yml down

# Start production
docker-compose up -d
```

---

## 📝 Best Practices

### 1. Use Git Branches
```bash
# Create feature branch
git checkout -b feature/my-new-feature

# Make changes
# ... edit code ...

# Test thoroughly
docker-compose -f docker-compose.dev.yml up

# Commit when working
git add .
git commit -m "Add new feature"
git push origin feature/my-new-feature
```

### 2. Keep .env Secure
```bash
# NEVER commit .env
# Use .env.example as template
git add .env.example
git commit -m "Update env template"
```

### 3. Test Before Pushing
```bash
# Run tests
docker-compose -f docker-compose.dev.yml exec aiservice pytest tests/ -v

# Check code quality (if configured)
docker-compose -f docker-compose.dev.yml exec aiservice flake8 app/
docker-compose -f docker-compose.dev.yml exec aiservice black app/ --check
```

### 4. Clean Up Regularly
```bash
# Remove unused volumes
docker volume prune

# Remove unused images
docker image prune

# Full cleanup (careful!)
docker system prune -a
```

---

## 🎓 Learning the Codebase

### Key Files to Understand

1. **`app/main.py`** - FastAPI application entry point
2. **`app/api/routes.py`** - API endpoints
3. **`app/services/chat_service.py`** - Main chat logic
4. **`app/services/llm_client.py`** - LLM integration
5. **`app/core/config.py`** - Configuration management
6. **`app/models/database.py`** - Database models

### Explore the Code

```bash
# View file structure
docker-compose -f docker-compose.dev.yml exec aiservice find /app/app -name "*.py" -type f

# Search for specific code
docker-compose -f docker-compose.dev.yml exec aiservice grep -r "def chat" /app/app/

# Count lines of code
docker-compose -f docker-compose.dev.yml exec aiservice find /app/app -name "*.py" -exec wc -l {} + | sort -n
```

---

## 📚 Additional Resources

- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Metrics:** http://localhost:8000/metrics (if enabled)
- **Project README:** [README.md](README.md)
- **API Examples:** [API_EXAMPLES.md](API_EXAMPLES.md)
- **Production Guide:** [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)

---

## 🎉 You're Ready to Develop!

Key commands to remember:

```bash
# Start development
docker-compose -f docker-compose.dev.yml up

# View logs
docker-compose -f docker-compose.dev.yml logs -f aiservice

# Access container
docker-compose -f docker-compose.dev.yml exec aiservice bash

# Run migrations
docker-compose -f docker-compose.dev.yml exec aiservice alembic upgrade head

# Stop everything
docker-compose -f docker-compose.dev.yml down
```

**Happy coding! 🚀**

---

**Last Updated:** 2025-01-04  
**Version:** 1.0.0




