# Quick Setup Guide

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
cd "/home/bean12/Desktop/AI Service"
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
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

### Port conflicts
- PostgreSQL: Change `5432:5432` in docker-compose.yml
- AI Service: Change `8000:8000` in docker-compose.yml or uvicorn command
- LM Studio: Change port in LM Studio settings

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [API documentation](http://localhost:8000/docs)
- Run tests: `pytest tests/ -v`
- Review example requests in README

