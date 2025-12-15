# Production Deployment Guide

## 🚀 Complete Guide to Deploying AI Companion Service in Production

This guide covers everything you need to deploy the AI Service safely and securely in a production environment.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Security Configuration](#security-configuration)
3. [Infrastructure Setup](#infrastructure-setup)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [Deployment Options](#deployment-options)
7. [Monitoring & Observability](#monitoring--observability)
8. [Backup & Disaster Recovery](#backup--disaster-recovery)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### ✅ Security Checklist

- [ ] **JWT Secret Key**: Generate strong random secret (32+ characters)
  ```bash
  python -c 'import secrets; print(secrets.token_urlsafe(32))'
  ```

- [ ] **Database Credentials**: Use strong, unique passwords
  - Minimum 16 characters
  - Mix of letters, numbers, symbols
  - Never use default passwords in production

- [ ] **CORS Origins**: Specify exact allowed origins (never use `*`)
  ```env
  CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
  ```

- [ ] **Authentication**: Ensure `REQUIRE_AUTHENTICATION=true`

- [ ] **HTTPS/TLS**: Enable HTTPS for all communications
  - Use reverse proxy (nginx, Traefik, AWS ALB)
  - Force HTTPS redirects
  - Use valid SSL certificates (Let's Encrypt, commercial CA)

- [ ] **Environment Variables**: Use secrets management
  - AWS Secrets Manager
  - HashiCorp Vault
  - Kubernetes Secrets
  - Azure Key Vault
  - **Never commit `.env` files to version control**

- [ ] **Rate Limiting**: Configure appropriate limits
  ```env
  RATE_LIMIT_REQUESTS_PER_MINUTE=60  # Adjust based on load
  ```

- [ ] **Input Validation**: Verify limits are in place
  - Max message length: 4000 characters (default)
  - Request size limits enforced

---

## Security Configuration

### 1. Generate Production Secrets

```bash
# Generate JWT secret
export JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY"

# Generate database password
export DB_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(24))')
echo "DB_PASSWORD=$DB_PASSWORD"
```

### 2. Environment Configuration

Create `.env.production` (NEVER commit this file):

```env
# CRITICAL: Mark environment as production
ENVIRONMENT=production

# Authentication - REQUIRED
REQUIRE_AUTHENTICATION=true
JWT_SECRET_KEY=<your-strong-random-secret-from-above>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Database - Use strong credentials
POSTGRES_URL=postgresql+asyncpg://ai_service:<strong-password>@postgres-host:5432/ai_companion
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_OVERFLOW=40

# LLM Configuration
LM_STUDIO_BASE_URL=http://llm-service:1234/v1
LM_STUDIO_MODEL_NAME=production-model
LM_STUDIO_TEMPERATURE=0.7
LM_STUDIO_MAX_TOKENS=2000

# Redis for Distributed Memory
REDIS_URL=redis://redis-host:6379/0
REDIS_ENABLED=true

# Security
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Logging
LOG_LEVEL=INFO
```

### 3. Production Validation

The application automatically validates production settings on startup:

```python
# These checks run automatically in production:
# ✅ JWT secret is not default
# ✅ JWT secret is strong (32+ chars)
# ✅ Authentication is enabled
# ✅ CORS is not wildcard (*)
# ⚠️  Warns about weak database passwords
```

If any critical check fails, the application **will not start**.

---

## Infrastructure Setup

### Option 1: Docker Compose (Small Scale)

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ai_companion
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  ai-service:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - ai-service
    restart: always

volumes:
  postgres_data:
  redis_data:
```

### Option 2: Kubernetes (Scalable)

```yaml
# k8s/production/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-companion-service
  namespace: production
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
        image: your-registry/ai-companion:v4.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: ai-companion-secrets
              key: jwt-secret-key
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: ai-companion-secrets
              key: postgres-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: ai-companion-secrets
              key: redis-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: ai-companion-service
  namespace: production
spec:
  selector:
    app: ai-companion
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## Database Setup

### 1. Create Production Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE ai_companion;
CREATE USER ai_service WITH ENCRYPTED PASSWORD 'your-strong-password';
GRANT ALL PRIVILEGES ON DATABASE ai_companion TO ai_service;

# Enable pgvector extension
\c ai_companion
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Run Migrations

```bash
# Backup first!
pg_dump -U ai_service ai_companion > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migrations
alembic upgrade head

# Verify
alembic current
```

### 3. Database Tuning (PostgreSQL)

```sql
-- postgresql.conf optimizations
max_connections = 200
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
work_mem = 10485kB
```

---

## Monitoring & Observability

### 1. Prometheus Metrics

The service exposes metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

**Key Metrics:**
- `http_requests_total` - Total requests by endpoint and status
- `http_request_duration_seconds` - Request latency
- `http_requests_in_progress` - Active requests
- `llm_requests_total` - LLM API calls
- `memory_retrievals_total` - Memory operations

### 2. Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ai-companion'
    scrape_interval: 15s
    static_configs:
      - targets: ['ai-service:8000']
```

### 3. Grafana Dashboards

Import dashboards for:
- Request rate and latency
- Error rates
- Database performance
- Memory usage
- LLM performance

### 4. Alerting Rules

```yaml
# alerts.yml
groups:
  - name: ai_companion
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: SlowResponses
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 5
        for: 10m
        annotations:
          summary: "95th percentile latency > 5s"
      
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        annotations:
          summary: "Database is down"
```

### 5. Centralized Logging

**Option A: ELK Stack**
```bash
# Configure log shipping to Elasticsearch
# Use Filebeat or Fluentd
```

**Option B: CloudWatch (AWS)**
```python
# Add CloudWatch handler to logging
import watchtower
handler = watchtower.CloudWatchLogHandler(log_group='ai-companion')
logger.addHandler(handler)
```

---

## Backup & Disaster Recovery

### 1. Database Backups

**Automated Daily Backups:**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="ai_companion"

# Full backup
pg_dump -U ai_service -Fc $DB_NAME > $BACKUP_DIR/backup_$DATE.dump

# Compress
gzip $BACKUP_DIR/backup_$DATE.dump

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/backup_$DATE.dump.gz s3://your-bucket/backups/

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.dump.gz" -mtime +30 -delete
```

**Cron Job:**
```cron
0 2 * * * /usr/local/bin/backup.sh
```

### 2. Point-in-Time Recovery (PITR)

Enable WAL archiving in PostgreSQL:
```ini
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'
```

### 3. Restore Procedure

```bash
# Restore from backup
pg_restore -U ai_service -d ai_companion -c backup_20240115.dump

# Verify
psql -U ai_service -d ai_companion -c "SELECT COUNT(*) FROM memories;"
```

---

## Performance Optimization

### 1. Database Indexing

Verify indexes exist (migrations create these):
```sql
-- Check indexes
\di

-- Key indexes:
-- ix_memories_user_id
-- ix_memories_conversation_id
-- ix_conversations_user_id
-- ix_emotion_history_user_id
-- ix_goals_user_id
```

### 2. Connection Pooling

Configure based on load:
```env
# For 3 app instances with 100 concurrent users:
POSTGRES_POOL_SIZE=20  # Per instance
POSTGRES_MAX_OVERFLOW=40
```

### 3. Redis Configuration

```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60
```

### 4. Application Tuning

```env
# Memory configuration
SHORT_TERM_MEMORY_SIZE=10
LONG_TERM_MEMORY_TOP_K=5
MEMORY_SIMILARITY_THRESHOLD=0.7

# LLM configuration
LM_STUDIO_MAX_TOKENS=2000
LM_STUDIO_TEMPERATURE=0.7
```

---

## Health Checks

### Application Health

```bash
# Health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "4.0.0",
  "database": true,
  "llm": true
}
```

### Database Health

```bash
psql -U ai_service -d ai_companion -c "SELECT 1;"
```

### Redis Health

```bash
redis-cli -h redis-host ping
```

---

## Scaling Guidelines

### Horizontal Scaling

1. **Requirements:**
   - Redis enabled (`REDIS_ENABLED=true`)
   - Stateless application design ✅
   - Load balancer configured

2. **Deploy Multiple Instances:**
   ```bash
   # Kubernetes
   kubectl scale deployment ai-companion --replicas=5
   
   # Docker Compose
   docker-compose up -d --scale ai-service=5
   ```

### Vertical Scaling

Adjust resource limits based on load:
- **Light load** (< 100 req/min): 1 CPU, 2GB RAM
- **Medium load** (100-500 req/min): 2 CPU, 4GB RAM
- **Heavy load** (> 500 req/min): 4 CPU, 8GB RAM

---

## Troubleshooting

### Common Issues

**1. Application won't start (production validation failed)**
```
ValueError: JWT_SECRET_KEY is using default value!
```
**Solution:** Set strong JWT_SECRET_KEY in environment

**2. Database connection errors**
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution:** Check postgres URL, credentials, network connectivity

**3. High latency**
- Check database query performance
- Review Prometheus metrics
- Check LLM service response time
- Verify network latency

**4. Memory leaks**
- Monitor `/metrics` for memory usage
- Check for unclosed database connections
- Review Redis memory usage

---

## Security Best Practices

1. **Principle of Least Privilege**
   - Database user has minimal required permissions
   - Application runs as non-root user
   - Network policies restrict access

2. **Regular Updates**
   - Update dependencies monthly
   - Apply security patches promptly
   - Monitor CVE databases

3. **Audit Logging**
   - Log all authentication attempts
   - Log sensitive operations
   - Retain logs for 90+ days

4. **Penetration Testing**
   - Conduct regular security audits
   - Test authentication bypasses
   - Verify input validation

5. **Data Protection**
   - Encrypt data at rest (database encryption)
   - Encrypt data in transit (TLS/HTTPS)
   - Implement data retention policies

---

## Post-Deployment Checklist

- [ ] All services healthy (`/health` returns 200)
- [ ] Metrics being collected (`/metrics` accessible to Prometheus)
- [ ] Logs being shipped to central logging
- [ ] Alerts configured and tested
- [ ] Backups running automatically
- [ ] SSL certificates valid and auto-renewing
- [ ] Rate limiting working as expected
- [ ] Authentication required for all endpoints
- [ ] Documentation updated with production URLs
- [ ] Team trained on monitoring and alerts
- [ ] Incident response plan documented
- [ ] Rollback procedure tested

---

## Support & Maintenance

### Regular Maintenance Tasks

**Daily:**
- Check health endpoints
- Review error logs
- Monitor metrics dashboards

**Weekly:**
- Review backup success
- Check disk space
- Review slow queries

**Monthly:**
- Update dependencies
- Review security advisories
- Analyze performance trends
- Optimize database queries

### Emergency Contacts

Document your escalation procedures and on-call rotations.

---

## Additional Resources

- [README.md](README.md) - Getting started guide
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [AUTHENTICATION.md](AUTHENTICATION.md) - Authentication guide

---

**Last Updated:** 2024-01-15  
**Version:** 4.0.0

