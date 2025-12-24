# Docker Deployment Guide

Complete guide for deploying the AI Companion Service using Docker.

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Nginx Reverse Proxy](#nginx-reverse-proxy)
- [Database Management](#database-management)
- [Monitoring and Logs](#monitoring-and-logs)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

## Quick Start

### Prerequisites

- Docker Engine 20.10+ ([Install Docker](https://docs.docker.com/engine/install/))
- Docker Compose 2.0+ ([Install Compose](https://docs.docker.com/compose/install/))
- At least 4GB RAM available for Docker
- OpenAI API key (for LLM functionality)

### Development Environment (5 minutes)

```bash
# 1. Clone the repository
cd "/home/bean12/Desktop/AI Service"

# 2. Copy environment template
cp ENV_EXAMPLE.txt .env

# 3. Edit .env and add your OpenAI API key
nano .env  # or vim, code, etc.

# 4. Start development environment
make dev

# 5. Access the service
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Database: localhost:5433
```

### Production Environment

```bash
# 1. Configure production .env
cp ENV_EXAMPLE.txt .env
nano .env  # Set ENVIRONMENT=production and strong passwords

# 2. Start production environment
make prod

# 3. Verify deployment
make health
```

## Architecture

### Docker Services

The deployment consists of multiple containerized services:

```
┌─────────────────┐
│     Nginx       │  (Optional - Reverse Proxy & SSL)
│   Port 80/443   │
└────────┬────────┘
         │
┌────────▼────────┐
│   AI Service    │  (FastAPI Application)
│    Port 8000    │
└────┬────────┬───┘
     │        │
     │        │
┌────▼─────┐ ┌▼──────────┐
│PostgreSQL│ │   Redis   │
│Port 5432 │ │ Port 6379 │
└──────────┘ └───────────┘
```

### Service Details

| Service | Image | Purpose |
|---------|-------|---------|
| **aiservice** | Custom (Python 3.11) | Main FastAPI application |
| **postgres** | pgvector/pgvector:pg15 | Database with vector support |
| **redis** | redis:7-alpine | Caching and distributed state |
| **nginx** | nginx:alpine | Reverse proxy (optional) |

## Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp ENV_EXAMPLE.txt .env
```

#### Critical Settings

```bash
# Environment
ENVIRONMENT=production  # or development

# OpenAI (Required)
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL_NAME=gpt-4o-mini

# Database (Change passwords!)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_THIS_IN_PRODUCTION
POSTGRES_DB=ai_companion

# Redis (Change password!)
REDIS_PASSWORD=CHANGE_THIS_IN_PRODUCTION

# Authentication
JWT_SECRET_KEY=CHANGE_THIS_TO_A_LONG_RANDOM_STRING
```

#### Generate Secure Secrets

```bash
# Generate JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate passwords
openssl rand -base64 32
```

### Docker Compose Files

| File | Purpose | Usage |
|------|---------|-------|
| `docker-compose.yml` | Production | `docker-compose up -d` |
| `docker-compose.dev.yml` | Development | `docker-compose -f docker-compose.dev.yml up -d` |

### Resource Limits

Production limits (configurable in `docker-compose.yml`):

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '0.5'
      memory: 1G
```

## Development Setup

### Starting Development Environment

```bash
# Basic development
make dev

# With database admin UI (Adminer)
make dev-adminer
# Access Adminer at: http://localhost:8080
# Server: postgres, User: postgres, Password: postgres
```

### Development Features

- **Hot Reload**: Code changes automatically reload
- **Debug Logging**: Full debug output
- **Exposed Ports**: Direct access to all services
- **Source Mounting**: Local code mounted in container

### Development Tools

```bash
# View logs
make logs          # All services
make logs-api      # API only
make logs-db       # Database only

# Shell access
make shell         # App container shell
make db-shell      # PostgreSQL shell

# Run tests
make test          # Run all tests
make test-coverage # With coverage report
```

## Production Deployment

### Initial Setup

1. **Prepare Environment**

```bash
# Copy and configure .env
cp ENV_EXAMPLE.txt .env
nano .env

# Important: Set strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

2. **Build and Deploy**

```bash
# Build production images
make prod-build

# Or start with existing images
make prod
```

3. **Verify Deployment**

```bash
# Check service status
make status

# Check health
make health

# View logs
make logs
```

### Production Configuration

#### Database Performance Tuning

In `docker-compose.yml`, adjust PostgreSQL settings:

```yaml
environment:
  POSTGRES_SHARED_BUFFERS: 256MB      # 25% of available RAM
  POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB  # 50-75% of available RAM
  POSTGRES_WORK_MEM: 16MB             # RAM / max_connections / 2
```

#### Application Scaling

Scale the service horizontally:

```bash
# Run multiple instances
docker-compose up -d --scale aiservice=3

# Use load balancer (nginx) for distribution
make prod-nginx
```

### Updates and Maintenance

```bash
# Update to latest version
make update

# Restart services
make restart-prod

# Clean rebuild
make rebuild
```

## Nginx Reverse Proxy

### Enable Nginx

```bash
# Start with Nginx
make prod-nginx
```

### SSL/TLS Setup

#### Option 1: Let's Encrypt (Recommended for Production)

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy to project
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
sudo chmod 600 nginx/ssl/key.pem

# Update nginx configuration
nano nginx/conf.d/ai-companion.conf
# Uncomment SSL lines and update server_name
```

#### Option 2: Self-Signed (Development/Testing)

```bash
# Generate self-signed certificate
cd nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem -out cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Start with SSL enabled
make prod-nginx
```

### Nginx Configuration

Key files:
- `nginx/nginx.conf` - Main configuration
- `nginx/conf.d/ai-companion.conf` - Service-specific config
- `nginx/ssl/` - SSL certificates

## Database Management

### Backups

```bash
# Create backup
make db-backup
# Saves to: ./backups/backup_prod_YYYYMMDD_HHMMSS.sql

# Automated backups (add to crontab)
0 2 * * * cd /path/to/project && make db-backup
```

### Restore

```bash
# Restore from backup
make db-restore FILE=backups/backup_prod_20240101_020000.sql
```

### Migrations

```bash
# Run migrations
make db-migrate

# Or manually
docker-compose exec aiservice alembic upgrade head

# Create new migration
docker-compose exec aiservice alembic revision --autogenerate -m "description"
```

### Direct Database Access

```bash
# PostgreSQL shell
make db-shell

# Or manually
docker-compose exec postgres psql -U postgres -d ai_companion

# Common queries
\dt              # List tables
\d+ memories     # Describe table
SELECT COUNT(*) FROM memories;
```

## Monitoring and Logs

### Viewing Logs

```bash
# All services
make logs

# Specific service
make logs-api
make logs-db

# Follow logs with tail
docker-compose logs -f --tail=100 aiservice

# Save logs to file
docker-compose logs --no-color > logs/debug_$(date +%Y%m%d).log
```

### Health Checks

```bash
# Quick health check
make health

# Detailed status
make status

# Manual health check
curl http://localhost:8000/health
```

### Metrics (Prometheus)

Metrics endpoint available at: `http://localhost:8000/metrics`

```bash
# View metrics
curl http://localhost:8000/metrics

# Key metrics:
# - http_requests_total
# - http_request_duration_seconds
# - memory_operations_total
# - llm_requests_total
```

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
make logs

# Check if port is in use
sudo lsof -i :8000
sudo lsof -i :5433

# Restart services
make restart-prod
```

#### 2. Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check health
docker-compose exec postgres pg_isready -U postgres

# View database logs
make logs-db

# Restart database
docker-compose restart postgres
```

#### 3. Migration Errors

```bash
# Check migration status
docker-compose exec aiservice alembic current

# Reset database (WARNING: destroys data)
docker-compose down -v
docker-compose up -d
```

#### 4. Out of Memory

```bash
# Check resource usage
docker stats

# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory

# Reduce service memory limits in docker-compose.yml
```

#### 5. Permission Denied

```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod +x docker-entrypoint.sh

# Fix log file permissions
sudo chmod 666 content_audit.log
```

### Debug Mode

```bash
# Start with debug logging
LOG_LEVEL=DEBUG make prod

# Shell into container
make shell

# Check Python packages
pip list

# Test imports
python -c "from app.main import app; print('OK')"
```

### Clean Slate

```bash
# Remove everything and start fresh
make clean
make prod-build
```

## Security Best Practices

### 1. Secrets Management

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Rotate secrets regularly
# Update .env, then:
make restart-prod
```

### 2. Network Security

```yaml
# Limit service exposure
# Only expose necessary ports
ports:
  - "127.0.0.1:8000:8000"  # Localhost only

# Use custom networks
networks:
  ai_network:
    driver: bridge
```

### 3. Container Security

- Run as non-root user (already configured)
- Use specific image versions, not `latest`
- Regular security updates: `make update`
- Limit resource usage (configured in compose)

### 4. SSL/TLS

```bash
# Use Let's Encrypt for production
# Enable HTTPS in nginx configuration
# Redirect HTTP to HTTPS

# Test SSL configuration
https://www.ssllabs.com/ssltest/
```

### 5. Firewall

```bash
# Allow only necessary ports
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 5432/tcp   # PostgreSQL (use SSH tunnel if needed)
sudo ufw deny 6379/tcp   # Redis
sudo ufw enable
```

### 6. Monitoring

```bash
# Enable health checks (already configured)
# Monitor logs regularly
# Set up alerts for errors

# Example: Simple monitoring script
watch -n 5 'make health'
```

## Advanced Topics

### Docker Swarm Deployment

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml ai-companion

# Scale services
docker service scale ai-companion_aiservice=3
```

### Kubernetes Deployment

See `KUBERNETES_GUIDE.md` (to be created if needed)

### CI/CD Integration

```bash
# Build and tag
make build
docker tag ai-companion:latest registry.example.com/ai-companion:v1.0.0

# Push to registry
docker push registry.example.com/ai-companion:v1.0.0

# Deploy
docker-compose pull
docker-compose up -d
```

## Quick Reference

### Essential Commands

```bash
# Development
make dev              # Start dev environment
make stop             # Stop all services
make logs             # View logs
make shell            # Container shell
make test             # Run tests

# Production
make prod             # Start production
make prod-nginx       # With Nginx
make health           # Health check
make db-backup        # Backup database

# Maintenance
make update           # Update services
make clean            # Remove all data
make rebuild          # Clean rebuild
```

### Useful Docker Commands

```bash
# View running containers
docker ps

# View all containers
docker ps -a

# Container logs
docker logs -f ai_companion_service

# Execute command in container
docker exec -it ai_companion_service bash

# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# View resource usage
docker stats

# Inspect container
docker inspect ai_companion_service
```

## Support

For issues and questions:
- Check this guide first
- Review application logs: `make logs`
- Check GitHub issues
- Open a new issue with logs and configuration (redact secrets!)

---

**Last Updated**: December 2024  
**Version**: 1.0.0

