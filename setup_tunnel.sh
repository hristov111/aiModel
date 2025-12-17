#!/bin/bash
# Local Machine Tunnel Setup
# This creates a persistent SSH tunnel to your VPS

set -e

echo "🔌 Setting up SSH Tunnel to VPS"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

VPS_USER="emo"
VPS_HOST="66.42.93.128"
LOCAL_PORT="8000"
REMOTE_PORT="8000"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}Do not run this script as root${NC}"
   echo "Run as your regular user: bash setup_tunnel.sh"
   exit 1
fi

echo -e "${GREEN}Step 1: Installing autossh...${NC}"
sudo apt install -y autossh

echo -e "${GREEN}Step 2: Testing SSH connection...${NC}"
if ssh -o BatchMode=yes -o ConnectTimeout=5 ${VPS_USER}@${VPS_HOST} exit 2>/dev/null; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${YELLOW}⚠️  SSH connection test failed${NC}"
    echo "Make sure you can SSH without password (use ssh-copy-id if needed)"
    read -p "Continue anyway? (y/N): " continue
    if [[ ! $continue =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}Step 3: Creating systemd service...${NC}"
sudo tee /etc/systemd/system/ai-app-tunnel.service > /dev/null << EOF
[Unit]
Description=AI App SSH Tunnel to VPS
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=${USER}
ExecStart=/usr/bin/autossh -M 0 \\
    -o "ServerAliveInterval=30" \\
    -o "ServerAliveCountMax=3" \\
    -o "ExitOnForwardFailure=yes" \\
    -o "StrictHostKeyChecking=no" \\
    -R ${REMOTE_PORT}:localhost:${LOCAL_PORT} \\
    ${VPS_USER}@${VPS_HOST} -N
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}Step 4: Enabling and starting service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable ai-app-tunnel
sudo systemctl start ai-app-tunnel

sleep 2

# Check status
if sudo systemctl is-active --quiet ai-app-tunnel; then
    echo -e "${GREEN}✓ Tunnel service started successfully${NC}"
else
    echo -e "${RED}✗ Tunnel service failed to start${NC}"
    sudo systemctl status ai-app-tunnel
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Tunnel Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Tunnel Details:"
echo "  Local:  localhost:${LOCAL_PORT}"
echo "  Remote: ${VPS_HOST}:${REMOTE_PORT}"
echo ""
echo "Useful commands:"
echo "  Check status:  sudo systemctl status ai-app-tunnel"
echo "  View logs:     sudo journalctl -u ai-app-tunnel -f"
echo "  Restart:       sudo systemctl restart ai-app-tunnel"
echo "  Stop:          sudo systemctl stop ai-app-tunnel"
echo ""
echo "Test your setup:"
echo "  curl http://${VPS_HOST}/health"
echo ""

