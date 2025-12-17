# Quick Setup Guide

## System Requirements

### Install System Dependencies

**Ubuntu/Debian:**
```bash
# Python virtual environment
sudo apt install python3-venv python3-dev -y

# PostgreSQL client and development files
sudo apt install libpq-dev -y

# Build tools (required for Python 3.13+)
sudo apt install build-essential gcc -y

# Rust (required for Python 3.13+ to build pydantic-core)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
```

**Note:** Python 3.13 requires Rust to build some packages from source. If you encounter build errors, make sure Rust is installed and sourced.

### Install Docker (Optional - for containerized deployment)

```bash
# Install Docker and Docker Compose
sudo apt update
sudo apt install docker.io docker-compose -y

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group (to run without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

## Prerequisites Setup

### 1. PostgreSQL with pgvector

**Option A: Docker (Recommended)**
```bash
docker run -d \
  --name ai-companion-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ai_companion \
  -p 5432:5432 \
  pgvector/pgvector:pg15
```

**Option B: Local Installation**
```bash
# Install PostgreSQL 15+
sudo apt install postgresql-15 postgresql-contrib-15

# Install pgvector extension
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Enable extension in database
psql -U postgres -d ai_companion -c "CREATE EXTENSION vector;"
```

### 2. LM Studio

1. Download from [lmstudio.ai](https://lmstudio.ai/)
2. Install and launch
3. Download a model:
   - Go to "Discover" tab
   - Search for models (e.g., "Llama 2 7B", "Mistral 7B")
   - Click download
4. Load the model:
   - Go to "Chat" tab
   - Select your downloaded model
5. Start the server:
   - Go to "Server" tab
   - Click "Start Server"
   - Note the URL (default: http://localhost:1234)

## Quick Start

### Local Development

```bash
# 1. Setup environment
cd /home/first/ai/aiModel
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure
cat > .env << EOF
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL_NAME=local-model
POSTGRES_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_companion
LOG_LEVEL=INFO
EOF

# 4. Run migrations
alembic upgrade head

# 5. Start service
python -m uvicorn app.main:app --reload
```

### Docker

```bash
# Start everything (PostgreSQL + AI Service)
docker-compose up -d

# View logs
docker-compose logs -f ai-companion

# Stop
docker-compose down
```

## Verification

### Test LM Studio Connection
```bash
curl http://localhost:1234/v1/models
```

### Test Database Connection
```bash
psql postgresql://postgres:postgres@localhost:5432/ai_companion -c "SELECT 1;"
```

### Test AI Service
```bash
# Health check
curl http://localhost:8000/health

# Interactive docs
open http://localhost:8000/docs
```

### Test Chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, who are you?"}'
```

## Common Issues

### LM Studio not responding
- Check if server is running (Server tab in LM Studio)
- Verify model is loaded
- Try restarting LM Studio

### Database connection error
- Ensure PostgreSQL is running: `docker ps` or `systemctl status postgresql`
- Check credentials in .env file
- Verify pgvector extension: `psql -c "SELECT * FROM pg_extension WHERE extname='vector';"`

### Embedding model download slow
- First run downloads ~90MB model
- Pre-download: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"`

### Python package build errors (Python 3.13+)
If you see errors like "Failed building wheel for pydantic-core" or "Rust not found":
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env

# Install build dependencies
sudo apt install python3-dev libpq-dev build-essential gcc -y

# Retry installation
pip install -r requirements.txt
```

### Port conflicts
- PostgreSQL: Change `5432:5432` in docker-compose.yml
- AI Service: Change `8000:8000` in docker-compose.yml or uvicorn command
- LM Studio: Change port in LM Studio settings

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [API documentation](http://localhost:8000/docs)
- Run tests: `pytest tests/ -v`
- Review example requests in README

