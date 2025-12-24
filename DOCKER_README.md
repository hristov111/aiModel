# Docker Setup - Quick Start

Professional Docker configuration for AI Companion Service.

## 🚀 Quick Start (2 minutes)

### Development

```bash
# 1. Copy environment file
cp ENV_EXAMPLE.txt .env

# 2. Add your OpenAI API key to .env
nano .env

# 3. Start everything
make dev

# 4. Access
# API: http://localhost:8000/docs
# Database: localhost:5433
```

### Production

```bash
# 1. Configure production settings
cp ENV_EXAMPLE.txt .env
nano .env  # Set ENVIRONMENT=production and change passwords

# 2. Start production
make prod

# 3. Verify
make health
```

## 📁 Files Overview

### Core Files
- `Dockerfile` - Multi-stage build with security hardening
- `docker-compose.yml` - Production configuration
- `docker-compose.dev.yml` - Development with hot-reload
- `docker-entrypoint.sh` - Initialization script
- `Makefile` - Easy command shortcuts

### Configuration
- `nginx/nginx.conf` - Reverse proxy main config
- `nginx/conf.d/ai-companion.conf` - Service configuration
- `nginx/ssl/` - SSL certificates directory

## 🔧 Common Commands

```bash
# Development
make dev          # Start dev environment
make dev-adminer  # Start with database UI

# Production
make prod         # Start production
make prod-nginx   # With Nginx reverse proxy

# Management
make stop         # Stop all services
make logs         # View logs
make logs-api     # API logs only
make shell        # Container shell
make db-shell     # Database shell

# Database
make db-backup    # Create backup
make db-migrate   # Run migrations
make db-restore FILE=backup.sql

# Testing
make test         # Run tests
make health       # Health check
make status       # Service status

# Maintenance
make update       # Pull latest changes
make clean        # Remove all data (WARNING!)
make rebuild      # Clean rebuild
```

## 🏗️ Architecture

```
┌─────────────────┐
│  Nginx (80/443) │  ← Optional reverse proxy with SSL
└────────┬────────┘
         │
┌────────▼────────┐
│  AI Service     │  ← FastAPI application
│   (Port 8000)   │
└────┬────────┬───┘
     │        │
┌────▼─────┐ ┌▼──────────┐
│PostgreSQL│ │   Redis   │  ← Database & Cache
│  (5432)  │ │  (6379)   │
└──────────┘ └───────────┘
```

## 🔒 Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Set strong `JWT_SECRET_KEY`
- [ ] Use `ENVIRONMENT=production`
- [ ] Enable SSL/TLS for external access
- [ ] Restrict database ports (don't expose publicly)
- [ ] Regular backups: `make db-backup`
- [ ] Keep Docker images updated: `make update`

## 📊 Monitoring

### Health Check
```bash
make health
# or
curl http://localhost:8000/health
```

### Metrics (Prometheus)
```bash
curl http://localhost:8000/metrics
```

### Logs
```bash
# Real-time logs
make logs

# Save logs
docker-compose logs --no-color > app.log
```

## 🐛 Troubleshooting

### Service won't start
```bash
make logs              # Check error messages
docker-compose ps      # Check service status
make restart-prod      # Restart services
```

### Port already in use
```bash
sudo lsof -i :8000     # Find process using port
make stop              # Stop all services
```

### Database connection failed
```bash
make logs-db           # Check database logs
docker-compose restart postgres
```

### Fresh start
```bash
make clean             # Remove everything
make prod-build        # Rebuild and start
```

## 🌐 Deployment Scenarios

### Local Development
```bash
make dev
# Hot-reload enabled, debug logging
```

### Local Production Test
```bash
make prod
# Production settings, no hot-reload
```

### VPS/Server
```bash
make prod-nginx
# With Nginx reverse proxy and SSL
```

### Multiple Environments
```bash
# Development
docker-compose -f docker-compose.dev.yml up -d

# Production
docker-compose up -d
```

## 📚 Documentation

- **Full Guide**: See `DOCKER_GUIDE.md` for comprehensive documentation
- **Nginx Setup**: See `nginx/` directory for reverse proxy configuration
- **API Docs**: http://localhost:8000/docs when running

## 🔑 Environment Variables

Critical variables in `.env`:

```bash
# Must set
OPENAI_API_KEY=sk-...           # Your OpenAI key
ENVIRONMENT=production          # Environment mode

# Must change in production
POSTGRES_PASSWORD=...           # Strong password
REDIS_PASSWORD=...              # Strong password
JWT_SECRET_KEY=...              # Random secret

# Optional but recommended
LM_STUDIO_BASE_URL=...         # Local LLM (optional)
CORS_ORIGINS=...               # Allowed origins
```

Generate secrets:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 📦 What's Included

### Security
✅ Non-root user  
✅ Multi-stage build  
✅ Security headers  
✅ Rate limiting  
✅ Health checks  
✅ No privilege escalation  

### Features
✅ Hot-reload (dev)  
✅ Auto-migrations  
✅ Database backups  
✅ Nginx reverse proxy  
✅ SSL/TLS support  
✅ Redis caching  
✅ Prometheus metrics  
✅ Resource limits  

### Developer Experience
✅ Simple Makefile commands  
✅ Database admin UI (Adminer)  
✅ Comprehensive logging  
✅ Easy testing  
✅ Clear documentation  

## 🆘 Getting Help

1. Check logs: `make logs`
2. Review `DOCKER_GUIDE.md` for detailed help
3. Check service status: `make status`
4. Test health: `make health`

## 📝 Best Practices

1. **Always use `.env` file** - Never hardcode secrets
2. **Regular backups** - `make db-backup` daily
3. **Monitor logs** - `make logs` regularly
4. **Keep updated** - `make update` weekly
5. **Use Nginx in production** - For SSL and security
6. **Limit resources** - Configure in docker-compose.yml
7. **Test before deploy** - Use `make prod` locally first

## 🎯 Next Steps

After setup:

1. **Test API**: Visit http://localhost:8000/docs
2. **Create user**: POST to `/api/auth/register`
3. **Get token**: POST to `/api/auth/token`
4. **Chat**: POST to `/api/chat` with Bearer token
5. **Monitor**: Check `/health` and `/metrics`

---

For detailed documentation, see `DOCKER_GUIDE.md`

