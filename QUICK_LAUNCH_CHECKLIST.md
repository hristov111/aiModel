# ⚡ Quick Launch Checklist

**Goal:** Production-ready deployment in 2-3 hours for 1-100 concurrent users

---

## 🎯 Phase 1: IMMEDIATE (Before Launch)

### ✅ Step 1: Enable Redis (5 minutes)

1. **Edit `.env` file:**
```bash
# Add these lines
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0
```

2. **Verify Redis service in docker-compose.dev.yml:**
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
```

3. **Test:**
```bash
make dev
# Check logs: should see "Redis enabled" message
make logs-api | grep -i redis
```

---

### ✅ Step 2: Increase Database Pool (5 minutes)

1. **Edit `.env` file:**
```env
POSTGRES_POOL_SIZE=30
POSTGRES_MAX_OVERFLOW=50
```

2. **Also update PostgreSQL max connections:**
```bash
# Access PostgreSQL container
make db-shell

# Run this SQL:
ALTER SYSTEM SET max_connections = 300;

# Exit and restart
\q
make restart-dev
```

---

### ✅ Step 3: Add Database Indexes (1 hour)

1. **Create migration:**
```bash
alembic revision -m "add_performance_indexes"
```

2. **Edit the new migration file** in `migrations/versions/`:
```python
"""Add performance indexes

Revision ID: xxx
"""
from alembic import op

def upgrade():
    # Memory queries
    op.create_index(
        'idx_memories_conversation_user',
        'memories',
        ['conversation_id', 'user_id'],
        unique=False
    )
    
    # Vector similarity
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_memories_embedding_ivfflat 
        ON memories 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)
    
    # Importance + time
    op.create_index(
        'idx_memories_importance_created',
        'memories',
        ['importance', 'created_at'],
        unique=False
    )
    
    # User conversations
    op.create_index(
        'idx_conversations_user_updated',
        'conversations',
        ['user_id', 'updated_at'],
        unique=False
    )

def downgrade():
    op.drop_index('idx_conversations_user_updated', 'conversations')
    op.drop_index('idx_memories_importance_created', 'memories')
    op.drop_index('idx_memories_embedding_ivfflat', 'memories')
    op.drop_index('idx_memories_conversation_user', 'memories')
```

3. **Apply migration:**
```bash
make db-migrate
# or manually:
alembic upgrade head
```

---

### ✅ Step 4: Production Security (10 minutes)

1. **Generate strong JWT secret:**
```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
# Copy the output
```

2. **Edit `.env` file:**
```env
ENVIRONMENT=production
REQUIRE_AUTHENTICATION=true
ALLOW_X_USER_ID_AUTH=false
JWT_SECRET_KEY=<paste-your-generated-secret-here>
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

3. **Verify security:**
```bash
# App should validate on startup
make logs-api | grep -i "production configuration"
# Should see: "✅ Production configuration validated successfully"
```

---

### ✅ Step 5: Test Everything (30 minutes)

1. **Restart services:**
```bash
make restart-dev
```

2. **Check health:**
```bash
curl http://localhost:8000/health | jq
```

3. **Test chat endpoint:**
```bash
# Get JWT token first
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test-user","expires_in_hours":24}'

# Save the token
export TOKEN="<your-token-here>"

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"Hello! How are you?"}'
```

4. **Monitor metrics:**
```bash
curl http://localhost:8000/metrics
```

5. **Check Redis is working:**
```bash
# Enter Redis CLI
docker exec -it <redis-container-id> redis-cli

# Check keys
KEYS *
# Should see session and conversation keys

# Exit
exit
```

---

## 🚀 Deployment Options

### Option A: VPS Deployment (Recommended)

1. **Copy files to VPS:**
```bash
rsync -avz --exclude 'venv' --exclude '__pycache__' \
  ./ user@your-vps.com:/opt/ai-service/
```

2. **On VPS, setup:**
```bash
cd /opt/ai-service
cp ENV_EXAMPLE.txt .env
# Edit .env with your production values
nano .env

# Start services
make prod
```

3. **Setup Nginx reverse proxy:**
```bash
# Use the provided config
sudo cp nginx/nginx.conf /etc/nginx/sites-available/ai-service
sudo ln -s /etc/nginx/sites-available/ai-service /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

4. **Setup SSL with Let's Encrypt:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

### Option B: Docker Compose (Development)

```bash
make prod
```

Access at: http://localhost:8000

---

### Option C: Kubernetes (Advanced)

See `PRODUCTION_DEPLOYMENT_GUIDE.md` for full Kubernetes setup.

---

## ✅ Post-Launch Monitoring

### 1. Check logs regularly:
```bash
make logs-api
```

### 2. Monitor metrics:
```bash
# View Prometheus metrics
curl http://localhost:8000/metrics

# Key metrics to watch:
# - http_requests_total
# - http_request_duration_seconds
# - database_query_duration_seconds
# - llm_requests_total
```

### 3. Database health:
```bash
make db-shell
# Then:
SELECT count(*) FROM conversations;
SELECT count(*) FROM memories;
SELECT count(*) FROM users;
```

### 4. Redis health:
```bash
docker exec -it <redis-container> redis-cli INFO
```

---

## 🔴 If Something Goes Wrong

### Issue: Can't connect to database
```bash
# Check if postgres is running
docker ps | grep postgres

# Check logs
make logs-db

# Restart
make restart-dev
```

---

### Issue: Redis not working
```bash
# Check if redis is running
docker ps | grep redis

# Test connection
docker exec -it <redis-container> redis-cli PING
# Should respond: PONG

# Check logs
docker logs <redis-container>
```

---

### Issue: LLM not responding
```bash
# Check if you have API key set
echo $OPENAI_API_KEY

# Or check .env file
grep OPENAI .env

# Test OpenAI connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

### Issue: High latency
```bash
# Check database queries
make db-shell
SELECT * FROM pg_stat_activity WHERE state = 'active';

# Check if indexes were created
\d memories
# Should show indexes
```

---

## 📊 Success Criteria

After completing Phase 1, you should have:

- ✅ Services running without errors
- ✅ Health check returning 200 OK
- ✅ JWT authentication working
- ✅ Redis enabled and storing sessions
- ✅ Database indexes created
- ✅ Response time < 5 seconds
- ✅ No security warnings on startup
- ✅ Metrics endpoint accessible

---

## 🎯 What's Next?

### Week 2-3: Scale to 100+ Users

When you start seeing 50+ concurrent users:

1. **Implement Redis Session Manager** (see PRODUCTION_OPTIMIZATION_REPORT.md #1)
2. **Deploy multiple instances** with load balancer
3. **Enable LLM response caching**
4. **Set up monitoring dashboard** (Grafana)

---

## 💡 Pro Tips

1. **Monitor costs from day 1:**
```bash
# Track OpenAI usage
# https://platform.openai.com/usage
```

2. **Backup database daily:**
```bash
# Add to crontab
0 2 * * * cd /opt/ai-service && make db-backup
```

3. **Keep logs for debugging:**
```bash
# Rotate logs
make logs-api > logs/app-$(date +%Y%m%d).log
```

4. **Test failover scenarios:**
```bash
# Kill one service at a time and verify others keep working
docker stop <container-id>
# Test if app still works
# Restart
docker start <container-id>
```

---

## 📞 Support Resources

- **Full Optimization Report:** `PRODUCTION_OPTIMIZATION_REPORT.md`
- **Deployment Guide:** `PRODUCTION_DEPLOYMENT_GUIDE.md`
- **Scalability Analysis:** `PRODUCTION_SCALABILITY_ANALYSIS.md`
- **Architecture Patterns:** `ARCHITECTURE_PATTERNS.md`
- **Security Checklist:** `SECURITY_CHECKLIST.md`

---

**Time Estimate: 2-3 hours**  
**Difficulty: Medium**  
**Result: Production-ready for 1-100 users**

**Good luck! 🚀**




