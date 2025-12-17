# Quick VPS Setup Instructions

## ✅ Routing Conflict Fixed!

The frontend is now accessible at:
- `http://66.42.93.128/` (root)
- `http://66.42.93.128/ui` (UI route)

The API stays at `POST /chat` for backward compatibility.

---

## 🚀 Complete Setup in 2 Steps:

### Step 1: Configure VPS (Run on VPS)

```bash
ssh emo@66.42.93.128
sudo bash ~/vps_setup.sh
exit
```

This installs:
- ✅ Nginx (reverse proxy)
- ✅ Certbot (SSL certificates)
- ✅ UFW firewall
- ✅ SSH configuration for tunneling

### Step 2: Setup Tunnel (Run on Local Machine)

```bash
cd /home/first/ai/aiModel
sudo bash setup_tunnel.sh
```

This creates:
- ✅ Persistent SSH tunnel
- ✅ Auto-reconnect on failure
- ✅ Auto-start on boot

---

## 🌐 Access Your Application:

After both steps are complete:

### Frontend UI:
```
http://66.42.93.128/
http://66.42.93.128/ui
```

### API Documentation:
```
http://66.42.93.128/docs
```

### Health Check:
```
http://66.42.93.128/health
```

### Chat API:
```bash
curl -X POST http://66.42.93.128/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: your-user-id" \
  -d '{"message": "Hello!"}'
```

---

## 🔧 Troubleshooting:

### Check Tunnel Status:
```bash
# On local machine
sudo systemctl status ai-app-tunnel
sudo journalctl -u ai-app-tunnel -f
```

### Check VPS Status:
```bash
# On VPS
ssh emo@66.42.93.128

# Check nginx
sudo systemctl status nginx

# Check if tunnel port is listening
ss -tlnp | grep 8000

# Check logs
sudo tail -f /var/log/nginx/ai-proxy-access.log
```

### Restart Services:
```bash
# Restart tunnel (local machine)
sudo systemctl restart ai-app-tunnel

# Restart nginx (VPS)
ssh emo@66.42.93.128 "sudo systemctl restart nginx"
```

---

## 📝 What Each Component Does:

| Component | Location | Purpose |
|-----------|----------|---------|
| **Docker** | Local Machine | Runs AI app + PostgreSQL |
| **LM Studio** | Local Machine | Runs AI model |
| **SSH Tunnel** | Local → VPS | Forwards port 8000 securely |
| **Nginx** | VPS | Receives internet traffic, forwards to tunnel |
| **Firewall** | VPS | Protects VPS (only 22, 80, 443 open) |

---

## 🎯 Current Status:

✅ Routing conflict fixed  
✅ Frontend included in Docker  
✅ Docker containers running locally  
⏳ VPS setup needed (run vps_setup.sh on VPS)  
⏳ Tunnel setup needed (run setup_tunnel.sh locally)  


