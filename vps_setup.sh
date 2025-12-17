#!/bin/bash
# VPS Setup Script for Reverse Proxy
# Run this on your VPS: emo@66.42.93.128

set -e

echo "🚀 VPS Reverse Proxy Setup"
echo "=========================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run with sudo${NC}" 
   echo "Usage: sudo bash vps_setup.sh"
   exit 1
fi

echo -e "${GREEN}Step 1: Installing nginx, certbot, and ufw...${NC}"
apt update
apt install -y nginx certbot python3-certbot-nginx ufw

echo -e "${GREEN}Step 2: Configuring SSH for reverse tunneling...${NC}"
# Backup sshd_config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Ensure GatewayPorts is set
if grep -q "^GatewayPorts" /etc/ssh/sshd_config; then
    sed -i 's/^GatewayPorts.*/GatewayPorts no/' /etc/ssh/sshd_config
else
    echo "GatewayPorts no" >> /etc/ssh/sshd_config
fi

# Restart SSH
systemctl restart sshd
echo -e "${GREEN}✓ SSH configured for reverse tunneling${NC}"

echo -e "${GREEN}Step 3: Creating nginx configuration...${NC}"
cat > /etc/nginx/sites-available/ai-proxy << 'EOF'
# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    listen 80;
    server_name 66.42.93.128;
    
    # Max body size for large requests
    client_max_body_size 10M;
    
    # Logging
    access_log /var/log/nginx/ai-proxy-access.log;
    error_log /var/log/nginx/ai-proxy-error.log;
    
    location / {
        # Rate limiting
        limit_req zone=api_limit burst=20 nodelay;
        
        # Proxy to local tunnel (port 8000 is tunneled from local machine)
        proxy_pass http://127.0.0.1:8000;
        
        # Headers
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts for LLM responses (can be slow)
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Disable buffering for streaming responses
        proxy_buffering off;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/ai-proxy /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t

# Restart nginx
systemctl restart nginx
systemctl enable nginx

echo -e "${GREEN}✓ Nginx configured and started${NC}"

echo -e "${GREEN}Step 4: Configuring firewall...${NC}"
# Allow SSH, HTTP, HTTPS
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall (non-interactive)
echo "y" | ufw enable

ufw status

echo -e "${GREEN}✓ Firewall configured${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ VPS Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. On your LOCAL machine, create the SSH tunnel:"
echo "   ssh -R 8000:localhost:8000 emo@66.42.93.128 -N"
echo ""
echo "2. Test the connection:"
echo "   curl http://66.42.93.128/health"
echo ""
echo "3. Optional: Setup SSL certificate if you have a domain"
echo "   sudo certbot --nginx -d yourdomain.com"
echo ""

