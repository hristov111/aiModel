# 👋 Welcome, Colleague!

If you're reading this, you've just cloned the AI Companion Service repository and need to get it running on your machine. This document will guide you to the right resources.

---

## 📚 Setup Documentation - Choose Your Path

I've created **3 documents** for you, depending on your experience level and needs:

### 🎯 Option 1: Quick Start (5 minutes read)
**File:** [`COLLEAGUE_QUICK_START.txt`](COLLEAGUE_QUICK_START.txt)

**For:** Experienced developers who know Docker, Python, and just need the commands  
**Contains:**
- What's missing from GitHub (summary)
- 5-minute setup commands
- Minimum .env configuration
- Quick troubleshooting
- One-page command reference

**Start here if:** You're comfortable with Python development and just need a quick reference.

---

### 📖 Option 2: Complete Setup Guide (30 minutes read)
**File:** [`COLLEAGUE_SETUP_GUIDE.md`](COLLEAGUE_SETUP_GUIDE.md) ⭐ **RECOMMENDED**

**For:** Anyone who wants a thorough, step-by-step guide  
**Contains:**
- Complete system requirements
- Detailed installation steps for all components
- Full .env configuration guide with explanations
- Comprehensive troubleshooting section
- Verification tests
- Additional resources

**Start here if:** This is your first time setting up the project, or you want detailed explanations.

---

### 📋 Option 3: Missing Files Reference
**File:** [`MISSING_FILES_CHECKLIST.md`](MISSING_FILES_CHECKLIST.md)

**For:** Quick reference to understand what's excluded from Git  
**Contains:**
- Complete list of files not in GitHub
- Why they're excluded
- Which ones you need to create manually
- Storage requirements
- Security considerations

**Start here if:** You just want to know what files are missing and why.

---

### 🔧 Option 4: Development Workflow (For Active Development)
**File:** [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md) + [`docker-compose.dev.yml`](docker-compose.dev.yml)

**For:** Developers who want to make code changes and see them instantly  
**Contains:**
- Development environment setup with hot-reload
- How to edit code without rebuilding Docker
- Common development tasks
- Testing and debugging
- Database/Redis access

**Start here if:** You'll be actively developing and making code changes.

**Quick Start:**
```bash
# Clone and setup
git clone <repo-url> && cd ai-service
cp ENV_EXAMPLE.txt .env && nano .env

# Start development environment (with hot-reload)
docker-compose -f docker-compose.dev.yml up

# Edit code → Save → Auto-reloads! ✨
```

---

## 🚀 Recommended Approach

### For First-Time Setup:
1. **Read:** [`COLLEAGUE_SETUP_GUIDE.md`](COLLEAGUE_SETUP_GUIDE.md) (30 min)
2. **Keep handy:** [`COLLEAGUE_QUICK_START.txt`](COLLEAGUE_QUICK_START.txt) (quick reference)
3. **If stuck:** Check troubleshooting section in setup guide

### For Quick Setup (Experienced):
1. **Follow:** [`COLLEAGUE_QUICK_START.txt`](COLLEAGUE_QUICK_START.txt) (5 min)
2. **If issues:** Refer to [`COLLEAGUE_SETUP_GUIDE.md`](COLLEAGUE_SETUP_GUIDE.md)

### For Active Development:
1. **Setup:** Follow setup guide to create `.env`
2. **Start dev mode:** `docker-compose -f docker-compose.dev.yml up`
3. **Read:** [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md) for development workflow
4. **Edit code:** Changes auto-reload, no rebuild needed!

---

## ⚡ Super Quick Start (TL;DR)

If you're really in a hurry and know what you're doing:

```bash
# 1. Install Python 3.11+, Docker, LM Studio
# 2. Start PostgreSQL
docker run -d --name ai-companion-db -e POSTGRES_PASSWORD=changeme_in_production \
  -e POSTGRES_DB=ai_companion -p 5433:5432 pgvector/pgvector:pg15

# 3. Start LM Studio server (GUI: Server tab → Start Server)

# 4. Setup project
git clone <repo-url> ai-service && cd ai-service
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 5. Create .env (IMPORTANT!)
cp ENV_EXAMPLE.txt .env
# Edit .env - minimum: LM_STUDIO_BASE_URL, POSTGRES_URL, JWT_SECRET_KEY

# 6. Run migrations and start
alembic upgrade head
python -m uvicorn app.main:app --reload

# 7. Test
curl http://localhost:8000/health
```

**⚠️ Warning:** This assumes you know what each step does. If anything fails, read the full guide.

---

## 🎯 What You Need to Know

### Files You MUST Create:
1. **`.env`** - Configuration file (copy from `ENV_EXAMPLE.txt` and edit)
   - This is the MOST IMPORTANT file
   - Contains API keys, database URLs, secrets
   - Use `ENV_EXAMPLE.txt` as a template

### Software You MUST Install:
1. **Python 3.11+** - Application runtime
2. **PostgreSQL 15+** - Database with pgvector extension (easiest via Docker)
3. **LM Studio** - Local LLM server (download from lmstudio.ai)
4. **Docker** - Container runtime (recommended for PostgreSQL)

### What Happens Automatically:
- `venv/` - Created when you run `python3 -m venv venv`
- `__pycache__/` - Created by Python automatically
- `logs/` - Created by application on first run
- ML models - Downloaded on first run (~90MB)

---

## 📋 Quick Checklist

Before starting, make sure you have:
- [ ] Access to this GitHub repository
- [ ] Admin/sudo access on your machine (for installing software)
- [ ] At least 20GB free disk space
- [ ] At least 8GB RAM
- [ ] Internet connection (for downloading models and packages)
- [ ] 1-2 hours for initial setup (including downloads)

---

## 🆘 Getting Help

### If Something Goes Wrong:
1. **Check logs:**
   ```bash
   # Application logs
   tail -f logs/app.log
   
   # Docker logs
   docker logs ai-companion-db
   ```

2. **Consult troubleshooting:**
   - See "Troubleshooting" section in [`COLLEAGUE_SETUP_GUIDE.md`](COLLEAGUE_SETUP_GUIDE.md)
   - See "Quick Fixes" in [`COLLEAGUE_QUICK_START.txt`](COLLEAGUE_QUICK_START.txt)

3. **Verify your setup:**
   ```bash
   # Check PostgreSQL
   docker ps | grep ai-companion-db
   
   # Check LM Studio
   curl http://localhost:1234/v1/models
   
   # Check service
   curl http://localhost:8000/health
   ```

4. **Common issues:**
   - LM Studio not starting → Open LM Studio GUI → Server tab → Start Server
   - Database connection failed → Check `.env` file `POSTGRES_URL` matches your setup
   - Module not found → Activate virtual environment: `source venv/bin/activate`
   - Port in use → Kill the process or use a different port

### Resources in This Repository:
- `README.md` - Project overview and architecture
- `API_EXAMPLES.md` - How to use the API
- `ENV_EXAMPLE.txt` - Complete list of configuration options
- `DOCKER_GUIDE.md` - Docker deployment details
- `AUTHENTICATION.md` - Authentication setup
- `PRODUCTION_DEPLOYMENT_GUIDE.md` - Production deployment

---

## 🎓 Understanding the Project

### Architecture Overview:
```
Client → FastAPI → Chat Service → LM Studio (Local LLM)
                 ↓
                Memory System → PostgreSQL + pgvector
```

### Key Components:
1. **FastAPI Application** - REST API with streaming support
2. **LM Studio** - Local LLM inference (privacy-focused)
3. **PostgreSQL + pgvector** - Database with vector similarity search
4. **Memory System** - Dual-layer (short-term + long-term) memory
5. **Authentication** - JWT tokens and user management

### What Makes This Special:
- ✅ **Privacy-first:** Local LLM processing (no data sent to cloud)
- ✅ **Memory:** Remembers conversations using semantic search
- ✅ **Multi-user:** Isolated data per user
- ✅ **Production-ready:** Authentication, rate limiting, monitoring
- ✅ **Extensible:** Clean architecture, easy to customize

---

## 📊 Expected Setup Time

| Phase | Time | What Happens |
|-------|------|--------------|
| Reading documentation | 5-30 min | Depends on which guide you choose |
| Installing system software | 10-30 min | Python, Docker, PostgreSQL |
| Downloading LM Studio + model | 15-60 min | Depends on internet speed |
| Python setup + dependencies | 5-15 min | Virtual env, pip install |
| Configuration (.env file) | 5-10 min | Copy and edit template |
| Database migration | 1-2 min | Create tables |
| First run (model download) | 5-10 min | Embedding model download |
| **Total** | **45-150 min** | **Mostly waiting for downloads** |

---

## ✅ Success Criteria

You'll know everything is working when:

✅ Service starts without errors  
✅ `curl http://localhost:8000/health` returns `{"status":"healthy"}`  
✅ `http://localhost:8000/docs` shows API documentation  
✅ Chat endpoint returns streaming responses  
✅ Tests pass (optional): `pytest tests/ -v`  

---

## 🎉 Next Steps After Setup

Once everything is running:

1. **Explore API documentation:**
   - Open http://localhost:8000/docs in your browser
   - Try the interactive API tester

2. **Test the chat endpoint:**
   - See examples in `API_EXAMPLES.md`
   - Try different queries

3. **Understand the codebase:**
   - Review `README.md` for architecture
   - Check `/home/bean12/Desktop/AI Service/app/` for source code

4. **Make changes:**
   - Service auto-reloads on code changes (when using `--reload`)
   - Test your changes with `pytest`

5. **Deploy (if needed):**
   - See `PRODUCTION_DEPLOYMENT_GUIDE.md`
   - Use Docker Compose for easy deployment

---

## 📞 Contact & Support

- **Project maintainer:** [Add your contact info here]
- **Team chat:** [Add team channel/Slack here]
- **Issues:** Check GitHub issues or create a new one

---

## 🔐 Security Reminder

**NEVER commit these files:**
- `.env` - Contains secrets and API keys
- `backups/*.sql` - May contain user data
- `*.db` - Database files

**Always:**
- Use strong passwords in production
- Generate secure JWT secrets
- Keep your `.env` file backed up securely
- Don't share your LM Studio models without proper licensing

---

## 📝 Quick Reference Card

Print or save this for quick reference:

```
╔══════════════════════════════════════════════════════════╗
║  AI COMPANION SERVICE - QUICK COMMANDS                   ║
╠══════════════════════════════════════════════════════════╣
║  Activate venv:     source venv/bin/activate            ║
║  Start service:     python -m uvicorn app.main:app      ║
║                     --reload                             ║
║  Check health:      curl http://localhost:8000/health   ║
║  API docs:          http://localhost:8000/docs          ║
║  Run tests:         pytest tests/ -v                     ║
║  Run migrations:    alembic upgrade head                 ║
║  Generate secret:   python3 -c "import secrets;         ║
║                     print(secrets.token_urlsafe(32))"   ║
╚══════════════════════════════════════════════════════════╝
```

---

**Good luck with your setup! 🚀**

If you have any questions or run into issues, don't hesitate to reach out to the team.

**Last Updated:** 2025-01-04  
**Version:** 1.0.0

