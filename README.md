# AI Companion Service

A standalone AI microservice that provides conversational AI capabilities with dual-layer memory (short-term conversation buffer + long-term vector storage). Built with FastAPI, it integrates with LM Studio for local LLM inference and uses PostgreSQL with pgvector for semantic memory retrieval.

## Features

- **Conversational AI**: Stream-based chat responses using LM Studio (OpenAI-compatible)
- **Multi-User Support**: Full user isolation with authentication (X-User-Id, API keys, JWT)
- **Dual-Layer Memory System**:
  - Short-term: In-memory conversation buffer (last N messages)
  - Long-term: Vector database with semantic similarity search
- **Memory Management**: Automatic extraction and storage of important facts per user
- **REST API**: Clean, well-documented endpoints with OpenAPI/Swagger
- **Rate Limiting**: Built-in rate limiting for production readiness
- **Streaming Responses**: Server-Sent Events (SSE) for real-time streaming
- **Provider Abstraction**: Swappable LLM providers (LM Studio, OpenAI, etc.)
- **Docker Support**: Containerized deployment with docker-compose
- **Security**: Conversation ownership verification, user-scoped data access

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ├─────────POST /chat
       ├─────────POST /conversation/reset
       └─────────POST /memory/clear
       │
┌──────▼──────────────────────────────┐
│      FastAPI REST API               │
│  (Streaming, Rate Limiting, CORS)   │
└──────┬──────────────────────────────┘
       │
┌──────▼──────────────────────────────┐
│     Chat Service Orchestrator       │
└──┬────┬────┬────┬───────────────────┘
   │    │    │    │
   │    │    │    └─────► LLM Client ──────► LM Studio
   │    │    │
   │    │    └──────────► Prompt Builder
   │    │
   │    └───────────────► Long-Term Memory
   │                      ├─ Memory Retrieval
   │                      ├─ Memory Extraction
   │                      └─ Vector Store ──► PostgreSQL + pgvector
   │
   └────────────────────► Short-Term Memory (In-Memory Buffer)
```

## Technology Stack

- **Framework**: FastAPI (async, streaming support)
- **Database**: PostgreSQL 15+ with pgvector extension
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2, 384-dim)
- **LLM**: LM Studio (OpenAI-compatible API)
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Rate Limiting**: slowapi
- **Python**: 3.11+

## Prerequisites

### Required

1. **PostgreSQL 15+ with pgvector extension**
   ```bash
   # Using Docker
   docker run -d \
     --name ai-companion-db \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=ai_companion \
     -p 5432:5432 \
     pgvector/pgvector:pg15
   ```

2. **LM Studio**
   - Download from [lmstudio.ai](https://lmstudio.ai/)
   - Load a model (e.g., Llama 2, Mistral, etc.)
   - Start the local server (default: http://localhost:1234)
   - Ensure "Server" tab shows the server is running

3. **Python 3.11+**

## Installation

### Option 1: Local Development

1. **Clone and setup virtual environment**
   ```bash
   cd "/home/bean12/Desktop/AI Service"
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   Key configuration variables:
   ```env
   # LM Studio
   LM_STUDIO_BASE_URL=http://localhost:1234/v1
   LM_STUDIO_MODEL_NAME=local-model
   
   # Database
   POSTGRES_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_companion
   
   # Memory
   SHORT_TERM_MEMORY_SIZE=10
   LONG_TERM_MEMORY_TOP_K=5
   ```

4. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start the service**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Option 2: Docker

1. **Using docker-compose (includes PostgreSQL)**
   ```bash
   # Start all services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f ai-companion
   
   # Stop services
   docker-compose down
   ```

2. **Build Docker image only**
   ```bash
   docker build -t ai-companion-service .
   ```

3. **Run with custom configuration**
   ```bash
   docker run -d \
     --name ai-companion \
     -p 8000:8000 \
     -e POSTGRES_URL=postgresql+asyncpg://user:pass@host/db \
     -e LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1 \
     ai-companion-service
   ```

## Usage

### Authentication

All API endpoints require authentication. See [AUTHENTICATION.md](AUTHENTICATION.md) for detailed guide.

**Quick Start (Development):**
```bash
# Add X-User-Id header to all requests
curl -H "X-User-Id: your-user-id" ...
```

**Production:** Implement JWT authentication (see AUTHENTICATION.md)

## API Endpoints

#### 1. Chat (Streaming)

Stream chat responses with memory integration:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, my name is Alice and I love programming",
    "conversation_id": null
  }'
```

**Response (SSE Stream):**
```
data: {"chunk": "Hello Alice"}
data: {"chunk": "! It's great"}
data: {"chunk": " to meet you."}
...
data: {"chunk": "", "done": true, "conversation_id": "550e8400-e29b-41d4-a716-446655440000"}
```

**Python Client Example:**
```python
import httpx
import json

async with httpx.AsyncClient() as client:
    async with client.stream(
        'POST',
        'http://localhost:8000/chat',
        json={"message": "Tell me about yourself", "conversation_id": None},
        timeout=60.0
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'chunk' in data:
                    print(data['chunk'], end='', flush=True)
```

#### 2. Reset Conversation

Clear short-term memory while keeping long-term memories:

```bash
curl -X POST http://localhost:8000/conversation/reset \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Conversation reset successfully",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 3. Clear Memories

Delete all memories (short and long-term) for a conversation:

```bash
curl -X POST http://localhost:8000/memory/clear \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Memories cleared successfully",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "memories_cleared": 15
}
```

#### 4. Health Check

Check service health:

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": true,
  "llm": true
}
```

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration

All configuration is done through environment variables. See `.env.example` for all available options:

| Variable | Default | Description |
|----------|---------|-------------|
| `LM_STUDIO_BASE_URL` | `http://localhost:1234/v1` | LM Studio API base URL |
| `LM_STUDIO_MODEL_NAME` | `local-model` | Model name to use |
| `LM_STUDIO_TEMPERATURE` | `0.7` | Sampling temperature |
| `LM_STUDIO_MAX_TOKENS` | `2000` | Max tokens to generate |
| `POSTGRES_URL` | - | PostgreSQL connection URL |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `EMBEDDING_DIMENSION` | `384` | Embedding dimension |
| `SHORT_TERM_MEMORY_SIZE` | `10` | Messages to keep in buffer |
| `LONG_TERM_MEMORY_TOP_K` | `5` | Memories to retrieve per query |
| `MEMORY_SIMILARITY_THRESHOLD` | `0.7` | Min similarity for retrieval (0-1) |
| `SYSTEM_PERSONA` | `a helpful AI assistant...` | AI personality |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `30` | API rate limit |
| `REQUIRE_AUTHENTICATION` | `true` | Enable/disable auth (dev only) |
| `JWT_SECRET_KEY` | - | Secret key for JWT tokens |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Allowed CORS origins |
| `LOG_LEVEL` | `INFO` | Logging level |

## Development

### Project Structure

```
/home/bean12/Desktop/AI Service/
├── app/
│   ├── main.py                    # FastAPI app initialization
│   ├── api/
│   │   ├── routes.py              # REST endpoints
│   │   └── models.py              # Request/response models
│   ├── core/
│   │   ├── config.py              # Environment configuration
│   │   ├── database.py            # Database session management
│   │   ├── dependencies.py        # Dependency injection
│   │   └── exceptions.py          # Custom exceptions
│   ├── services/
│   │   ├── chat_service.py        # Main orchestrator
│   │   ├── llm_client.py          # LM Studio client
│   │   ├── prompt_builder.py     # Prompt construction
│   │   ├── short_term_memory.py  # Conversation buffer
│   │   ├── long_term_memory.py   # Memory facade
│   │   ├── memory_retrieval.py   # Semantic search
│   │   └── memory_extraction.py  # Fact extraction
│   ├── repositories/
│   │   └── vector_store.py        # Postgres pgvector CRUD
│   ├── models/
│   │   ├── memory.py              # Domain models
│   │   └── database.py            # SQLAlchemy models
│   └── utils/
│       ├── embeddings.py          # Embedding generation
│       └── rate_limiter.py        # Rate limiting
├── migrations/                     # Alembic migrations
├── tests/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Memory System

### Short-Term Memory

- In-memory conversation buffer
- Stores last N messages (configurable)
- Includes conversation summaries
- TTL-based expiration for inactive conversations

### Long-Term Memory

- PostgreSQL with pgvector for semantic search
- Stores atomic facts with:
  - Content (text)
  - Embedding (384-dim vector)
  - Type (fact, preference, event, context)
  - Importance score (0.0-1.0)
  - Metadata (JSONB)
  - Timestamps
- Automatic extraction from conversations
- Cosine similarity search with re-ranking

### Memory Flow

1. **User sends message** → Stored in short-term buffer
2. **Query embedding generated** → Search long-term memories
3. **Top-K memories retrieved** → Re-ranked by importance × similarity
4. **Prompt constructed** → System persona + memories + recent history
5. **LLM responds** → Response streamed to client
6. **Background extraction** → Important facts stored in long-term memory

## Troubleshooting

### LM Studio Connection Issues

1. Ensure LM Studio server is running (check Server tab)
2. Verify the base URL (default: http://localhost:1234/v1)
3. Check firewall settings
4. Test connection:
   ```bash
   curl http://localhost:1234/v1/models
   ```

### PostgreSQL Connection Issues

1. Verify PostgreSQL is running:
   ```bash
   docker ps | grep postgres
   ```
2. Check pgvector extension:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```
3. Test connection:
   ```bash
   psql postgresql://postgres:postgres@localhost:5432/ai_companion
   ```

### Embedding Model Download

The first run downloads the embedding model (~90MB). This may take time:
```bash
# Pre-download manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Memory Issues

If experiencing memory growth:
1. Reduce `SHORT_TERM_MEMORY_SIZE`
2. Implement conversation cleanup:
   ```python
   # Cleanup expired conversations
   buffer.cleanup_expired()
   ```
3. Consider using Redis for production short-term memory

## 🌐 Public Access & Deployment

### Quick Start: Expose Your Service Publicly

Want to access your LLM from another network with password authentication?

**⚡ Quick Test (5 minutes):**
```bash
# Terminal 1: Start service
python app/main.py

# Terminal 2: Expose publicly
ngrok http 8000
```

**🏭 Production Setup (30 minutes):**
```bash
./setup_public_access.sh
```

**📚 Complete Guides:**
- **[EXPOSE_PUBLIC_SUMMARY.md](EXPOSE_PUBLIC_SUMMARY.md)** - Decision tree & quick overview
- **[PUBLIC_ACCESS_GUIDE.md](PUBLIC_ACCESS_GUIDE.md)** - Complete setup guide (ngrok, VPS, Docker)
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - One-page command reference
- **[PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)** - Full production deployment

### Included Tools:
- `setup_public_access.sh` - Automated setup script
- `generate_token.py` - Generate JWT tokens and API keys
- `test_public_api.py` - Test your public endpoint

## Production Deployment

### Recommendations

1. **Use Redis for short-term memory** (distributed deployments)
2. **Configure PostgreSQL connection pooling** properly
3. **Set up monitoring** (health endpoint + logging)
4. **Enable HTTPS** (reverse proxy with nginx/traefik)
5. **Adjust rate limits** based on load
6. **Scale horizontally** (stateless design)
7. **Set resource limits** (Docker/Kubernetes)
8. **Use secrets management** (not environment files)

### Example Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-companion-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-companion
  template:
    metadata:
      labels:
        app: ai-companion
    spec:
      containers:
      - name: ai-companion
        image: ai-companion-service:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
```

## License

MIT

## Support

For issues and questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review logs: `docker-compose logs -f ai-companion`
- Open an issue on GitHub

## Production Readiness

**✅ This service is now production-ready!**

Recent improvements:
- ✅ Full JWT authentication implementation
- ✅ Production security validation
- ✅ Prometheus metrics & monitoring
- ✅ Request ID tracking for distributed tracing
- ✅ Redis support for horizontal scaling
- ✅ CI/CD pipeline with GitHub Actions
- ✅ Comprehensive test coverage
- ✅ Complete deployment documentation

**See [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) for details.**

## Roadmap

**Completed (v4.0.0):**
- [x] Multi-user support with user ID tracking
- [x] Redis integration for distributed short-term memory
- [x] Advanced memory extraction using LLM
- [x] Memory importance decay over time

**Future Features:**
- [ ] Conversation summarization endpoint
- [ ] WebSocket support for bidirectional streaming
- [ ] Support for additional LLM providers (OpenAI, Anthropic, etc.)
- [ ] Memory visualization dashboard
- [ ] Conversation export/import
- [ ] GraphQL API option
- [ ] Admin dashboard

