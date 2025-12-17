#!/bin/bash
# Computer A Setup - LM Studio Tunnel to VPS
# Run this on the computer where LM Studio is running

set -e

echo "🤖 Computer A - LM Studio Tunnel Setup"
echo "======================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

VPS_USER="emo"
VPS_HOST="66.42.93.128"
LM_STUDIO_PORT="1234"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}Do not run this script as root${NC}"
   echo "Run as your regular user"
   exit 1
fi

echo -e "${GREEN}This computer will ONLY run LM Studio${NC}"
echo "The tunnel will forward LM Studio (port 1234) to VPS"
echo ""

# Check if LM Studio is accessible
echo "Checking if LM Studio is running on port 1234..."
if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✓ LM Studio is running${NC}"
else
    echo -e "${YELLOW}⚠️  LM Studio is not responding on port 1234${NC}"
    echo "Please make sure:"
    echo "  1. LM Studio is installed"
    echo "  2. A model is loaded"
    echo "  3. The server is started (default port 1234)"
    echo ""
    read -p "Continue anyway? (y/N): " continue
    if [[ ! $continue =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Step 1: Installing autossh...${NC}"
if ! command -v autossh &> /dev/null; then
    sudo apt update
    sudo apt install -y autossh
    echo -e "${GREEN}✓ autossh installed${NC}"
else
    echo -e "${GREEN}✓ autossh already installed${NC}"
fi

echo ""
echo -e "${GREEN}Step 2: Testing SSH connection to VPS...${NC}"
if ssh -o BatchMode=yes -o ConnectTimeout=5 ${VPS_USER}@${VPS_HOST} exit 2>/dev/null; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${YELLOW}⚠️  SSH connection test failed${NC}"
    echo "Make sure you can SSH without password (use ssh-copy-id if needed):"
    echo "  ssh-copy-id ${VPS_USER}@${VPS_HOST}"
    echo ""
    read -p "Continue anyway? (y/N): " continue
    if [[ ! $continue =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Step 3: Creating systemd service for LM Studio tunnel...${NC}"

sudo tee /etc/systemd/system/lm-studio-tunnel.service > /dev/null << EOF
[Unit]
Description=LM Studio SSH Tunnel to VPS (Computer A)
After=network.target

[Service]
Type=simple
User=${USER}
ExecStart=/usr/bin/autossh -M 0 \\
    -o "ServerAliveInterval=30" \\
    -o "ServerAliveCountMax=3" \\
    -o "ExitOnForwardFailure=yes" \\
    -o "StrictHostKeyChecking=no" \\
    -R ${LM_STUDIO_PORT}:localhost:${LM_STUDIO_PORT} \\
    ${VPS_USER}@${VPS_HOST} -N
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}Step 4: Enabling and starting service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable lm-studio-tunnel
sudo systemctl start lm-studio-tunnel

sleep 3

# Check status
if sudo systemctl is-active --quiet lm-studio-tunnel; then
    echo -e "${GREEN}✓ LM Studio tunnel started successfully${NC}"
else
    echo -e "${RED}✗ Tunnel service failed to start${NC}"
    echo "Checking logs..."
    sudo journalctl -u lm-studio-tunnel -n 20 --no-pager
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Computer A Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Computer A is now forwarding LM Studio to VPS!"
echo ""
echo "Details:"
echo "  Local:  localhost:${LM_STUDIO_PORT} (LM Studio)"
echo "  Remote: ${VPS_HOST}:${LM_STUDIO_PORT}"
echo ""
echo "Useful commands:"
echo "  Check status:  sudo systemctl status lm-studio-tunnel"
echo "  View logs:     sudo journalctl -u lm-studio-tunnel -f"
echo "  Restart:       sudo systemctl restart lm-studio-tunnel"
echo "  Stop:          sudo systemctl stop lm-studio-tunnel"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "  - Keep LM Studio running at all times"
echo "  - The tunnel will auto-reconnect if connection drops"
echo "  - Computer B will connect to VPS:1234 to reach this LM Studio"
echo ""

