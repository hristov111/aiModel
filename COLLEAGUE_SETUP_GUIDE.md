# 🚀 Colleague Setup Guide - AI Companion Service

**Welcome!** This single document contains everything you need to get the AI Companion Service running on your machine after cloning the repository.

---

## 📋 Table of Contents

1. [Files Missing from GitHub](#files-missing-from-github)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Configuration Files to Create](#configuration-files-to-create)
5. [Running the Service](#running-the-service)
6. [Verification & Testing](#verification--testing)
7. [Troubleshooting](#troubleshooting)

---

## 📂 Files Missing from GitHub

These files are excluded from version control (in `.gitignore`) and **you must create them**:

### Critical Files (You MUST Create):
- **`.env`** - Main configuration file with all environment variables
- **`venv/`** - Python virtual environment (created during setup)
- **`logs/`** - Application logs directory (auto-created by app)
- **`backups/`** - Database backup directory (optional, for production)

### Optional/Generated Files (Will be created automatically):
- `__pycache__/` - Python cache (auto-generated)
- `.pytest_cache/` - Test cache (auto-generated)
- `*.db`, `*.sqlite` - SQLite databases (we use PostgreSQL)
- ML models cache - Downloaded on first run (~90MB)
- `content_audit.log/` - Content classification logs (auto-created)

---

## 🖥️ System Requirements

### Operating System
- **Linux** (Ubuntu 20.04+, Debian 11+) ✅ Recommended
- **macOS** (10.15+) ✅ Supported
- **Windows** (WSL2 required) ⚠️ Use WSL2 with Ubuntu

### Software Requirements
| Software | Minimum Version | Purpose |
|----------|----------------|---------|
| Python | 3.11+ | Application runtime |
| PostgreSQL | 15+ | Database with vector extension |
| Docker | 20.10+ | Container runtime (optional) |
| Git | 2.0+ | Version control |
| LM Studio | Latest | Local LLM inference |
| 8GB RAM | - | Minimum for running with LM Studio |
| 20GB Disk | - | For models, database, and logs |

---

## 🛠️ Installation Steps

### Step 1: Install System Dependencies

#### Ubuntu/Debian:
```bash
# Update package list
sudo apt update

# Python and build tools
sudo apt install -y python3.11 python3.11-venv python3-pip python3-dev

# PostgreSQL client libraries
sudo apt install -y libpq-dev

# Build essentials (required for some Python packages)
sudo apt install -y build-essential gcc

# Rust (required for Python 3.13+ to build pydantic-core)
# Skip if using Python 3.11 or 3.12
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
```

#### macOS:
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 postgresql@15 rust

# Add PostgreSQL to PATH
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

### Step 2: Install Docker (Optional but Recommended)

Docker makes it easier to run PostgreSQL and Redis without manual configuration.

#### Linux:
```bash
# Install Docker
sudo apt install -y docker.io docker-compose

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group (run without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

#### macOS:
```bash
# Download Docker Desktop from: https://www.docker.com/products/docker-desktop
# Install and start Docker Desktop
```

---

### Step 3: Install PostgreSQL with pgvector

#### Option A: Using Docker (Easiest) ✅ Recommended

```bash
# Start PostgreSQL with pgvector extension
docker run -d \
  --name ai-companion-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=changeme_in_production \
  -e POSTGRES_DB=ai_companion \
  -p 5433:5432 \
  --restart unless-stopped \
  pgvector/pgvector:pg15

# Verify it's running
docker ps | grep ai-companion-db

# Test connection
docker exec ai-companion-db psql -U postgres -d ai_companion -c "SELECT 1;"
```

#### Option B: Local Installation (Advanced)

```bash
# Install PostgreSQL
sudo apt install -y postgresql-15 postgresql-contrib-15

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Install pgvector extension
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Create database and enable extension
sudo -u postgres psql << EOF
CREATE DATABASE ai_companion;
\c ai_companion
CREATE EXTENSION vector;
EOF
```

---

### Step 4: Install Redis (Optional - for production scaling)

#### Using Docker (Recommended):
```bash
docker run -d \
  --name ai-companion-redis \
  -p 6379:6379 \
  -e REDIS_PASSWORD=changeme_in_production \
  --restart unless-stopped \
  redis:7-alpine redis-server --requirepass changeme_in_production

# Verify
docker ps | grep ai-companion-redis
```

---

### Step 5: Install LM Studio (Local LLM)

LM Studio provides local LLM inference with an OpenAI-compatible API.

1. **Download LM Studio**
   - Visit: https://lmstudio.ai/
   - Download for your OS (Windows/macOS/Linux)
   - Install and launch

2. **Download a Model**
   - Open LM Studio
   - Go to **"Discover"** tab
   - Search for recommended models:
     - `TheBloke/Mistral-7B-Instruct-v0.2-GGUF` (Good balance)
     - `TheBloke/Llama-2-7B-Chat-GGUF` (Smaller, faster)
     - `TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF` (Larger, better quality)
   - Click **Download** (this may take 10-30 minutes)

3. **Load and Start Server**
   - Go to **"Chat"** tab
   - Select your downloaded model from the dropdown
   - Go to **"Server"** tab
   - Click **"Start Server"**
   - Note the URL: `http://localhost:1234`
   - ✅ Keep LM Studio running while using the AI service

4. **Verify LM Studio is Working**
```bash
# Test the LM Studio API
curl http://localhost:1234/v1/models

# You should see JSON output with your model listed
```

---

### Step 6: Clone Repository and Setup Python Environment

```bash
# Clone the repository
git clone <YOUR_REPO_URL> ai-service
cd ai-service

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies (this may take 5-10 minutes)
pip install -r requirements.txt

# First run will also download the embedding model (~90MB)
```

---

## 📝 Configuration Files to Create

### 1. Create `.env` File (CRITICAL)

This is the **most important file** you need to create. Copy the template below and customize it:

```bash
# Create .env file from template
cp ENV_EXAMPLE.txt .env

# Edit with your preferred editor
nano .env  # or: vim .env, code .env, etc.
```

**Minimal `.env` Configuration for Development:**

```bash
# =============================================================================
# MINIMAL DEVELOPMENT CONFIGURATION
# =============================================================================

# ============================================
# Environment
# ============================================
ENVIRONMENT=development

# ============================================
# OpenAI Configuration (Primary LLM) - OPTIONAL for development
# ============================================
# Get API key from: https://platform.openai.com/api-keys
# Leave empty to use only LM Studio
OPENAI_API_KEY=
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# ============================================
# LM Studio Configuration (Local LLM) - REQUIRED
# ============================================
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL_NAME=local-model
LM_STUDIO_TEMPERATURE=0.8
LM_STUDIO_MAX_TOKENS=2000

# ============================================
# Database Configuration - REQUIRED
# ============================================
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme_in_production
POSTGRES_DB=ai_companion
POSTGRES_PORT=5433

# If using Docker PostgreSQL (from Step 3):
POSTGRES_URL=postgresql+asyncpg://postgres:changeme_in_production@localhost:5433/ai_companion

# If using local PostgreSQL:
# POSTGRES_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_companion

POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20

# ============================================
# Embedding Configuration
# ============================================
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# ============================================
# Memory Configuration
# ============================================
SHORT_TERM_MEMORY_SIZE=10
LONG_TERM_MEMORY_TOP_K=5
MEMORY_SIMILARITY_THRESHOLD=0.15
MEMORY_EXTRACTION_MIN_TURNS=3
MEMORY_EXTRACTION_METHOD=hybrid

# ============================================
# AI Detection Methods
# ============================================
EMOTION_DETECTION_METHOD=hybrid
GOAL_DETECTION_METHOD=hybrid
PERSONALITY_DETECTION_METHOD=hybrid
MEMORY_CATEGORIZATION_METHOD=hybrid
CONTRADICTION_DETECTION_METHOD=hybrid

# ============================================
# Content Classification & Routing
# ============================================
CONTENT_ROUTING_ENABLED=true
CONTENT_AUDIT_LOG_FILE=content_audit.log
SESSION_TIMEOUT_HOURS=24
ROUTE_LOCK_MESSAGE_COUNT=5

# Layer 4: LLM Judge
CONTENT_LLM_JUDGE_ENABLED=true
CONTENT_LLM_JUDGE_THRESHOLD=0.7
CONTENT_LLM_JUDGE_PROVIDER=local

# ============================================
# System Configuration
# ============================================
SYSTEM_PERSONA=A grounded, emotionally present conversational companion. It speaks plainly and naturally, listens more than it talks, remembers meaningful details from previous conversations, and responds with empathy, honesty, and calm curiosity.
RATE_LIMIT_REQUESTS_PER_MINUTE=30

# ============================================
# Authentication
# ============================================
REQUIRE_AUTHENTICATION=true
ALLOW_X_USER_ID_AUTH=true  # Dev-only, set false in production
JWT_SECRET_KEY=CHANGE_THIS_TO_A_LONG_RANDOM_STRING_IN_PRODUCTION
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Generate a secure key with:
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# ============================================
# Memory Consolidation (Background Job)
# ============================================
MEMORY_CONSOLIDATION_JOB_ENABLED=false
MEMORY_CONSOLIDATION_JOB_INTERVAL_MINUTES=60

# ============================================
# CORS Configuration
# ============================================
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# ============================================
# Redis Configuration (Optional for dev)
# ============================================
REDIS_ENABLED=false  # Set to true if you want to use Redis

# If Redis enabled:
# REDIS_PASSWORD=changeme_in_production
# REDIS_PORT=6379
# REDIS_URL=redis://:changeme_in_production@localhost:6379/0

# ============================================
# Application Settings
# ============================================
APP_PORT=8000
LOG_LEVEL=INFO

# ============================================
# Migration Settings
# ============================================
RUN_MIGRATIONS=true
```

**⚠️ Important Notes:**
- **For development:** The above configuration is sufficient
- **For production:** You MUST change:
  - `ENVIRONMENT=production`
  - Generate secure `JWT_SECRET_KEY`
  - Set `ALLOW_X_USER_ID_AUTH=false`
  - Change all passwords
  - Enable `REDIS_ENABLED=true`

---

### 2. Create Required Directories (Optional)

Most directories are auto-created by the application, but you can create them manually:

```bash
# Navigate to project root
cd /path/to/ai-service

# Create directories
mkdir -p logs
mkdir -p backups
mkdir -p content_audit.log

# Set permissions
chmod 755 logs backups content_audit.log
```

---

## 🚀 Running the Service

### Step 7: Initialize Database

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run database migrations
alembic upgrade head

# You should see output like:
# INFO  [alembic.runtime.migration] Running upgrade -> xxx, initial schema
```

---

### Step 8: Start the Service

#### Option A: Development Mode (with auto-reload)

```bash
# Start with uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process
```

#### Option B: Production Mode (Docker)

```bash
# Start all services (PostgreSQL + Redis + AI Service)
docker-compose up -d

# View logs
docker-compose logs -f aiservice

# Stop services
docker-compose down
```

---

## ✅ Verification & Testing

### Test 1: Check Service Health

```bash
# Health check endpoint
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","version":"1.0.0","database":true,"llm":true}
```

---

### Test 2: View API Documentation

Open in your browser:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

### Test 3: Test Chat Endpoint

#### Using X-User-Id Header (Development):

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{
    "message": "Hello! My name is John and I love Python programming.",
    "conversation_id": null
  }'
```

#### Using JWT Token (Recommended):

```bash
# Step 1: Create a JWT token
TOKEN_RESPONSE=$(curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john-doe","expires_in_hours":24}')

echo $TOKEN_RESPONSE
# Extract the access_token from the response

# Step 2: Use the token in chat
ACCESS_TOKEN="<paste-token-here>"

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "message": "Tell me about yourself",
    "conversation_id": null
  }'
```

**Expected Response:**
You should see streaming chunks like:
```
data: {"chunk": "Hello John"}
data: {"chunk": "! It's great"}
data: {"chunk": " to meet you."}
...
data: {"chunk": "", "done": true, "conversation_id": "550e8400-e29b-41d4-a716-446655440000"}
```

---

### Test 4: Verify Database Connection

```bash
# If using Docker PostgreSQL
docker exec ai-companion-db psql -U postgres -d ai_companion -c "\dt"

# You should see tables like:
# users, conversations, memories, emotions, goals, etc.
```

---

### Test 5: Verify LM Studio Connection

```bash
# Check if LM Studio API is responding
curl http://localhost:1234/v1/models

# You should see your loaded model in the response
```

---

### Test 6: Run Unit Tests (Optional)

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

---

## 🐛 Troubleshooting

### Issue 1: LM Studio Connection Failed

**Symptoms:**
```
ERROR: Failed to connect to LM Studio
ConnectionError: Cannot reach http://localhost:1234
```

**Solutions:**
1. **Check if LM Studio server is running:**
   - Open LM Studio → Go to "Server" tab
   - Click "Start Server" if not already started
   
2. **Verify the server URL:**
   ```bash
   curl http://localhost:1234/v1/models
   ```
   
3. **Check if a model is loaded:**
   - LM Studio → "Chat" tab → Select a model from dropdown
   
4. **Firewall issues:**
   ```bash
   # Linux: Allow port 1234
   sudo ufw allow 1234
   ```

---

### Issue 2: Database Connection Failed

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions:**

1. **If using Docker PostgreSQL:**
   ```bash
   # Check if container is running
   docker ps | grep ai-companion-db
   
   # If not running, start it
   docker start ai-companion-db
   
   # Check logs
   docker logs ai-companion-db
   ```

2. **Verify connection string in `.env`:**
   ```bash
   # For Docker PostgreSQL (note port 5433 on host)
   POSTGRES_URL=postgresql+asyncpg://postgres:changeme_in_production@localhost:5433/ai_companion
   ```

3. **Test connection manually:**
   ```bash
   # Using Docker
   docker exec ai-companion-db psql -U postgres -d ai_companion -c "SELECT 1;"
   
   # Using psql directly
   psql postgresql://postgres:changeme_in_production@localhost:5433/ai_companion -c "SELECT 1;"
   ```

4. **Check pgvector extension:**
   ```bash
   docker exec ai-companion-db psql -U postgres -d ai_companion -c "SELECT * FROM pg_extension WHERE extname='vector';"
   ```

---

### Issue 3: Python Package Installation Errors

**Symptoms:**
```
ERROR: Failed building wheel for pydantic-core
error: can't find Rust compiler
```

**Solution for Python 3.13+:**
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env

# Install build dependencies
sudo apt install -y python3-dev libpq-dev build-essential gcc

# Retry installation
pip install -r requirements.txt
```

---

### Issue 4: Embedding Model Download Slow/Stuck

**Symptoms:**
```
Downloading sentence-transformers model... (taking forever)
```

**Solutions:**
1. **Pre-download the model:**
   ```bash
   python3 << EOF
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
   print("Model downloaded successfully!")
   EOF
   ```

2. **Check disk space:**
   ```bash
   df -h
   # Ensure you have at least 2GB free
   ```

3. **Check internet connection:**
   ```bash
   curl -I https://huggingface.co
   ```

---

### Issue 5: Port Already in Use

**Symptoms:**
```
ERROR: Port 8000 is already in use
OSError: [Errno 98] Address already in use
```

**Solutions:**
1. **Find what's using the port:**
   ```bash
   sudo lsof -i :8000
   # or
   sudo netstat -tulpn | grep :8000
   ```

2. **Kill the process:**
   ```bash
   sudo kill -9 <PID>
   ```

3. **Or use a different port:**
   ```bash
   # In .env file
   APP_PORT=8001
   
   # Or when starting
   python -m uvicorn app.main:app --port 8001
   ```

---

### Issue 6: Virtual Environment Issues

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Deactivate and delete old venv
deactivate
rm -rf venv

# Create fresh virtual environment
python3 -m venv venv
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Issue 7: Alembic Migration Errors

**Symptoms:**
```
ERROR: Target database is not up to date
FAILED: Can't locate revision identified by 'xxxxx'
```

**Solutions:**
1. **Reset database (DESTRUCTIVE - dev only):**
   ```bash
   # Drop and recreate database
   docker exec ai-companion-db psql -U postgres -c "DROP DATABASE ai_companion;"
   docker exec ai-companion-db psql -U postgres -c "CREATE DATABASE ai_companion;"
   docker exec ai-companion-db psql -U postgres -d ai_companion -c "CREATE EXTENSION vector;"
   
   # Run migrations from scratch
   alembic upgrade head
   ```

2. **Check migration history:**
   ```bash
   alembic history
   alembic current
   ```

---

### Issue 8: JWT Authentication Errors

**Symptoms:**
```
401 Unauthorized: Invalid token
```

**Solutions:**
1. **Generate a new secure JWT secret:**
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   
2. **Update `.env` file:**
   ```env
   JWT_SECRET_KEY=<paste-generated-secret-here>
   ```

3. **Restart the service:**
   ```bash
   # Press Ctrl+C to stop
   # Start again
   python -m uvicorn app.main:app --reload
   ```

---

## 📚 Additional Resources

### Documentation Files in the Repository

| File | Purpose |
|------|---------|
| `README.md` | Complete project documentation |
| `API_EXAMPLES.md` | Detailed API usage examples |
| `AUTHENTICATION.md` | Authentication setup guide |
| `DOCKER_GUIDE.md` | Docker deployment guide |
| `PRODUCTION_DEPLOYMENT_GUIDE.md` | Production setup |
| `QUICK_REFERENCE.md` | Quick command reference |
| `ENV_EXAMPLE.txt` | Complete environment variable reference |

---

### Useful Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Start development server
python -m uvicorn app.main:app --reload

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Run tests
pytest tests/ -v

# View API docs (in browser)
open http://localhost:8000/docs

# Check service health
curl http://localhost:8000/health

# Generate secure secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Docker commands
docker-compose up -d           # Start all services
docker-compose down            # Stop all services
docker-compose logs -f         # View logs
docker-compose ps              # Check status
docker-compose restart         # Restart services
```

---

## 🎯 Quick Start Summary

**TL;DR - Minimum steps to get running:**

```bash
# 1. Install system dependencies
sudo apt update && sudo apt install -y python3.11 python3-venv libpq-dev build-essential

# 2. Start PostgreSQL with Docker
docker run -d --name ai-companion-db -e POSTGRES_PASSWORD=changeme_in_production \
  -e POSTGRES_DB=ai_companion -p 5433:5432 pgvector/pgvector:pg15

# 3. Download and start LM Studio
# Visit https://lmstudio.ai/ → Download → Install → Load Model → Start Server

# 4. Clone and setup project
git clone <YOUR_REPO_URL> ai-service && cd ai-service
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 5. Create .env file
cp ENV_EXAMPLE.txt .env
# Edit .env with your settings (see Configuration section above)

# 6. Initialize database
alembic upgrade head

# 7. Start service
python -m uvicorn app.main:app --reload

# 8. Test it
curl http://localhost:8000/health
```

---

## 🤝 Need Help?

1. **Check the logs:**
   ```bash
   # If running directly
   tail -f logs/app.log
   
   # If using Docker
   docker-compose logs -f aiservice
   ```

2. **Check troubleshooting section above**

3. **Review the documentation files in the repo**

4. **Contact the team:** [Add your contact info here]

---

## ✅ Setup Checklist

Use this checklist to track your setup progress:

- [ ] System dependencies installed (Python, PostgreSQL libs, build tools)
- [ ] Docker installed and running (optional but recommended)
- [ ] PostgreSQL with pgvector running (Docker or local)
- [ ] LM Studio downloaded, model loaded, and server started
- [ ] Repository cloned
- [ ] Python virtual environment created and activated
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created and configured
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Service started successfully
- [ ] Health check passing (`curl http://localhost:8000/health`)
- [ ] API documentation accessible (`http://localhost:8000/docs`)
- [ ] Chat endpoint tested and working
- [ ] Tests passing (optional: `pytest tests/ -v`)

---

**🎉 Congratulations!** If you've completed all steps, you should have a fully functional AI Companion Service running locally.

**Last Updated:** 2025-01-04
**Version:** 1.0.0




