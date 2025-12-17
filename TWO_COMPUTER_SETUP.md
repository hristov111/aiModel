# 🖥️ Two Computer Setup Guide

## Architecture Overview

```
Computer B (App+DB) → Internet → VPS → Computer A (LM Studio)
     ↑                                        ↓
     └────────────────────────────────────────┘
                    (via VPS routing)
```

### Components:

- **Computer A**: Runs ONLY LM Studio, tunnels port 1234 to VPS
- **Computer B**: Runs App + Database, connects to VPS for LM Studio
- **VPS**: Routes traffic between Computer B and Computer A

---

## 🚀 Setup Instructions

### Step 1: Configure VPS (One Time)

SSH into your VPS and run the firewall configuration:

```bash
ssh emo@66.42.93.128
sudo bash ~/configure_vps_firewall.sh
exit
```

This opens ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 1234 (LM Studio)

---

### Step 2: Setup Computer A (LM Studio Machine)

**Requirements:**
- LM Studio installed
- Model downloaded and loaded
- Server running on port 1234

**Setup:**

1. Copy `setup_computer_a_lm_studio.sh` to Computer A

2. Run the setup script:
```bash
bash setup_computer_a_lm_studio.sh
```

3. Verify tunnel is active:
```bash
sudo systemctl status lm-studio-tunnel
```

**What this does:**
- Installs autossh
- Creates persistent SSH tunnel to VPS
- Forwards localhost:1234 → VPS:1234
- Auto-reconnects if connection drops
- Starts on boot

---

### Step 3: Setup Computer B (Application Machine)

**Option A: Current Computer (already set up)**

If you're using the current computer where everything is running:

```bash
cd /home/first/ai/aiModel

# The config is already updated to use VPS for LM Studio
# Just restart the containers
docker-compose restart ai-companion
```

**Option B: Different Computer**

If Computer B is a different machine:

1. Clone/copy the project to Computer B

2. Make sure `docker-compose.yml` has:
```yaml
LM_STUDIO_BASE_URL: http://66.42.93.128:1234/v1
```

3. Setup the tunnel for port 8000 (already done if using current machine):
```bash
bash setup_tunnel.sh
```

4. Start the application:
```bash
docker-compose up -d
```

---

## 🌐 Access Your Application

### From Anywhere:
```
http://66.42.93.128/          → Chat UI
http://66.42.93.128/docs      → API Documentation  
http://66.42.93.128/health    → Health Check
```

### Test LM Studio Connection:
```bash
curl http://66.42.93.128:1234/v1/models
```

---

## 📊 Traffic Flow

### When a user sends a chat message:

1. **User** → `http://66.42.93.128/chat` → **VPS**
2. **VPS** → tunnel → **Computer B (App)**
3. **Computer B** → `http://66.42.93.128:1234/v1/chat/completions` → **VPS**
4. **VPS** → tunnel → **Computer A (LM Studio)**
5. **Computer A** → generates response → **VPS**
6. **VPS** → **Computer B**
7. **Computer B** → **VPS** → **User**

---

## 🔍 Monitoring & Troubleshooting

### Computer A (LM Studio):

```bash
# Check tunnel status
sudo systemctl status lm-studio-tunnel

# View logs
sudo journalctl -u lm-studio-tunnel -f

# Test LM Studio locally
curl http://localhost:1234/v1/models

# Restart tunnel
sudo systemctl restart lm-studio-tunnel
```

### Computer B (Application):

```bash
# Check Docker containers
docker ps

# View app logs
docker logs ai_companion_service -f

# Test app locally
curl http://localhost:8000/health

# Check tunnel (if on different machine)
sudo systemctl status ai-app-tunnel
```

### VPS:

```bash
ssh emo@66.42.93.128

# Check nginx
sudo systemctl status nginx

# Check open tunnels
ss -tlnp | grep -E ':(8000|1234)'

# View nginx logs
sudo tail -f /var/log/nginx/ai-proxy-access.log

# Check firewall
sudo ufw status
```

---

## ⚠️ Common Issues

### "Connection refused" to LM Studio:

**Cause:** Computer A tunnel is down or LM Studio is not running

**Fix:**
```bash
# On Computer A
sudo systemctl restart lm-studio-tunnel
# Make sure LM Studio server is running
```

### App can't reach VPS:

**Cause:** Network/firewall issue

**Fix:**
```bash
# Test from Computer B
curl http://66.42.93.128:1234/v1/models

# If fails, check VPS firewall
ssh emo@66.42.93.128 "sudo ufw status"
```

### Web UI not loading:

**Cause:** Computer B tunnel is down

**Fix:**
```bash
# On Computer B (or current machine)
sudo systemctl status ai-app-tunnel
sudo systemctl restart ai-app-tunnel
```

---

## 🔐 Security Notes

1. **Port 1234 is publicly accessible** - Consider:
   - IP whitelist on VPS firewall
   - VPN between computers
   - Authentication in LM Studio (if supported)

2. **Use HTTPS** for production:
```bash
ssh emo@66.42.93.128
sudo certbot --nginx -d yourdomain.com
```

3. **Keep systems updated:**
```bash
sudo apt update && sudo apt upgrade -y
```

---

## 📝 Current Configuration

### VPS (66.42.93.128):
- ✅ Nginx running (proxying port 80 → 8000)
- ✅ Port 8000 tunnel active
- ⏳ Port 1234 needs tunnel from Computer A
- ⏳ Firewall needs configuration

### Computer B (Current/App Machine):
- ✅ Docker containers running
- ✅ Port 8000 tunnel active
- ✅ Config updated to use VPS for LM Studio

### Computer A (LM Studio):
- ⏳ Needs tunnel setup
- ⏳ LM Studio should be running

---

## 🎯 Quick Start Checklist

- [ ] VPS firewall configured (Step 1)
- [ ] Computer A tunnel running (Step 2)
- [ ] Computer B app restarted with new config (Step 3)
- [ ] Test: `curl http://66.42.93.128:1234/v1/models`
- [ ] Test: `curl http://66.42.93.128/health`
- [ ] Test: Send chat message via UI

---

## 📞 Summary of Required Actions

1. **On VPS:**
   ```bash
   ssh emo@66.42.93.128
   sudo bash ~/configure_vps_firewall.sh
   ```

2. **On Computer A (LM Studio):**
   ```bash
   # Transfer setup_computer_a_lm_studio.sh to this machine
   bash setup_computer_a_lm_studio.sh
   ```

3. **On Computer B (App) - if current machine:**
   ```bash
   cd /home/first/ai/aiModel
   docker-compose restart ai-companion
   ```

That's it! Your two-computer setup will be complete. 🚀

