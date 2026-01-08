# 🔧 Environment Configuration Guide

Complete guide to setting up environment variables for the AI Companion Service.

---

## 📁 Available Environment Templates

| File | Purpose | When to Use |
|------|---------|-------------|
| **ENV_EXAMPLE.txt** | Complete reference | All configuration options with detailed comments |
| **ENV_DEVELOPMENT_TEMPLATE.txt** | Quick dev setup | Local development and testing |
| **ENV_PRODUCTION_TEMPLATE.txt** | Production ready | Deploying to production servers |

---

## 🚀 Quick Start

### For Local Development (5 minutes)

```bash
# 1. Copy the development template
cp ENV_DEVELOPMENT_TEMPLATE.txt .env

# 2. Edit the file
nano .env

# 3. Add your OpenAI API key
# Change: OPENAI_API_KEY=sk-your-openai-api-key-here
# To:     OPENAI_API_KEY=sk-proj-...your-actual-key...

# 4. Start services
make dev

# 5. Test it works
curl http://localhost:8000/health
```

**That's it!** Your development environment is ready.

---

### For Production Deployment (30 minutes)

```bash
# 1. Copy the production template
cp ENV_PRODUCTION_TEMPLATE.txt .env

# 2. Generate secure secrets
python3 -c "import secrets; print('JWT_SECRET_KEY:', secrets.token_urlsafe(32))"
python3 -c "import secrets; print('POSTGRES_PASSWORD:', secrets.token_urlsafe(16))"
python3 -c "import secrets; print('REDIS_PASSWORD:', secrets.token_urlsafe(16))"

# 3. Edit .env and replace ALL <CHANGE-ME> values:
nano .env

# Key changes:
# - OPENAI_API_KEY=<your-real-key>
# - JWT_SECRET_KEY=<generated-secret>
# - POSTGRES_PASSWORD=<generated-password>
# - REDIS_PASSWORD=<generated-password>
# - CORS_ORIGINS=https://yourdomain.com
# - ALLOW_X_USER_ID_AUTH=false

# 4. Deploy
make prod

# 5. Verify
curl http://localhost:8000/health
```

---

## 📋 Configuration Categories

### 🔴 CRITICAL (Must Configure)

These settings are required for the app to work:

| Setting | Development | Production | Where to Get |
|---------|-------------|------------|--------------|
| `OPENAI_API_KEY` | Required | Required | https://platform.openai.com/api-keys |
| `ENVIRONMENT` | development | production | Set manually |
| `JWT_SECRET_KEY` | Any string | Strong secret (32+ chars) | `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `POSTGRES_URL` | Auto (Docker) | Configure | Database connection string |
| `REDIS_ENABLED` | false | **true** | Enable for production scaling |

---

### 🟡 IMPORTANT (Should Configure)

These settings improve security and performance:

| Setting | Default | Production Recommendation |
|---------|---------|---------------------------|
| `ALLOW_X_USER_ID_AUTH` | true | **false** (security risk) |
| `POSTGRES_POOL_SIZE` | 10 | 30 (for 100+ users) |
| `POSTGRES_MAX_OVERFLOW` | 20 | 50 (for 100+ users) |
| `LM_STUDIO_MAX_TOKENS` | 150 ⚠️ | 2000 (avoid cut-off responses) |
| `CORS_ORIGINS` | localhost | Your actual domain |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | 30 | 60-120 (adjust as needed) |

---

### 🟢 OPTIONAL (Can Use Defaults)

These settings have sensible defaults:

- AI detection methods (emotion, personality, goals)
- Memory configuration (similarity thresholds)
- Content routing settings
- Logging levels
- System persona

---

## 🎯 Environment-Specific Configurations

### Development Environment

**Focus:** Easy setup, debugging, fast iteration

```env
ENVIRONMENT=development
ALLOW_X_USER_ID_AUTH=true  # Convenient for testing
LOG_LEVEL=DEBUG  # Verbose logging
REDIS_ENABLED=false  # Optional for single instance
POSTGRES_POOL_SIZE=10  # Smaller pool is fine
```

**Access patterns:**
- Use `X-User-Id` header for quick testing
- Check detailed logs for debugging
- Run single instance only

---

### Staging Environment

**Focus:** Production-like testing

```env
ENVIRONMENT=staging
ALLOW_X_USER_ID_AUTH=false  # Test real auth
LOG_LEVEL=INFO
REDIS_ENABLED=true  # Test distributed setup
POSTGRES_POOL_SIZE=20
```

**Access patterns:**
- Use JWT tokens like production
- Test with multiple instances
- Monitor metrics and logs

---

### Production Environment

**Focus:** Security, performance, scalability

```env
ENVIRONMENT=production
ALLOW_X_USER_ID_AUTH=false  # MUST be false
LOG_LEVEL=INFO  # or WARNING
REDIS_ENABLED=true  # MUST be true for scaling
POSTGRES_POOL_SIZE=30  # Larger pool
JWT_SECRET_KEY=<strong-random-key>  # MUST be secure
```

**Access patterns:**
- JWT tokens only
- Multiple instances with load balancer
- Monitoring and alerting enabled
- HTTPS/TLS required

---

## 🔐 Security Best Practices

### Secrets Management

**❌ DON'T:**
- Commit `.env` files to Git
- Use default passwords in production
- Share secrets in plain text
- Use weak JWT secrets (< 32 chars)

**✅ DO:**
- Use `.env` files for local dev only
- Use secret managers in production (AWS Secrets Manager, HashiCorp Vault, etc.)
- Rotate secrets regularly
- Generate strong random secrets

### Production Security Checklist

```bash
# Before deploying to production, verify:
[ ] ENVIRONMENT=production
[ ] JWT_SECRET_KEY is strong (32+ chars)
[ ] ALLOW_X_USER_ID_AUTH=false
[ ] All passwords changed from defaults
[ ] CORS_ORIGINS set to actual domain
[ ] HTTPS/TLS enabled
[ ] Database backups configured
[ ] Monitoring enabled
```

---

## 🐛 Troubleshooting

### "Failed to connect to database"

**Check:**
1. Is PostgreSQL running? `docker ps | grep postgres`
2. Is the connection string correct?
3. Can you ping the database? `docker exec -it postgres psql -U postgres`

**Fix:**
```bash
# Restart database
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

---

### "LLM Connection Error"

**Check:**
1. Is your OpenAI API key valid?
2. Do you have API credits?
3. Is LM Studio running (if using local)?

**Fix:**
```bash
# Test OpenAI connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# For LM Studio
curl http://localhost:1234/v1/models
```

---

### "Redis connection failed"

**Check:**
1. Is Redis enabled? `REDIS_ENABLED=true`
2. Is Redis running? `docker ps | grep redis`
3. Is the URL correct?

**Fix:**
```bash
# If not using Redis
REDIS_ENABLED=false

# If using Redis, restart it
docker-compose restart redis
```

---

### "Authentication failed"

**Check:**
1. Is authentication required? `REQUIRE_AUTHENTICATION=true`
2. Are you sending correct headers?
3. Is JWT secret configured?

**Fix:**
```bash
# For development, temporarily disable
REQUIRE_AUTHENTICATION=false

# For production, create valid token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test-user","expires_in_hours":24}'
```

---

## 📊 Performance Tuning

### Database Pool Sizing

Calculate optimal pool size:
```
Pool Size = (Concurrent Users / 10) × 2
Max Overflow = Pool Size × 1.5

Examples:
- 50 users:  POOL_SIZE=10, MAX_OVERFLOW=15
- 100 users: POOL_SIZE=20, MAX_OVERFLOW=30
- 500 users: POOL_SIZE=100, MAX_OVERFLOW=150
```

### Memory Settings

```env
# For better recall (lower threshold)
MEMORY_SIMILARITY_THRESHOLD=0.15  # Recommended

# For stricter matching (higher threshold)
MEMORY_SIMILARITY_THRESHOLD=0.7

# More memories in context
LONG_TERM_MEMORY_TOP_K=10  # Default: 5
```

### Rate Limiting

```env
# Development (no limits)
RATE_LIMIT_REQUESTS_PER_MINUTE=1000

# Production (reasonable limits)
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# High traffic (adjust as needed)
RATE_LIMIT_REQUESTS_PER_MINUTE=120
```

---

## 🔄 Migrating Environments

### Local Dev → Production

```bash
# 1. Start with production template
cp ENV_PRODUCTION_TEMPLATE.txt .env

# 2. Copy your dev API keys
# (Keep: OPENAI_API_KEY, VPS_API_KEY if used)

# 3. Generate new production secrets
# (Change: JWT_SECRET_KEY, passwords)

# 4. Update infrastructure settings
# (Change: CORS_ORIGINS, database URLs)

# 5. Enable production features
REDIS_ENABLED=true
ALLOW_X_USER_ID_AUTH=false
ENVIRONMENT=production
```

---

## 📚 Related Documentation

- **PRODUCTION_OPTIMIZATION_REPORT.md** - Complete optimization guide
- **QUICK_LAUNCH_CHECKLIST.md** - Step-by-step deployment
- **API_EXAMPLES.md** - API usage examples
- **AUTHENTICATION.md** - Authentication setup
- **README.md** - General overview

---

## 💡 Tips

1. **Keep ENV_EXAMPLE.txt updated** when adding new config options
2. **Use templates** rather than copying from other environments
3. **Test locally first** before deploying to production
4. **Monitor metrics** at `/metrics` endpoint
5. **Review logs** regularly for issues

---

**Need help?** Check the troubleshooting section above or review the production deployment guide.

**Ready to launch?** Follow QUICK_LAUNCH_CHECKLIST.md for step-by-step instructions.




