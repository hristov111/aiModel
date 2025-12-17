#!/bin/bash
# Add LM Studio proxy to Nginx on VPS
# Run on VPS: sudo bash add_lm_studio_nginx_proxy.sh

set -e

echo "🔧 Adding LM Studio Proxy to Nginx"
echo "==================================="

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run with sudo"
   exit 1
fi

# Update nginx config to add /llm location
cat > /etc/nginx/sites-available/ai-proxy << 'EOF'
# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=llm_limit:10m rate=5r/s;

server {
    listen 80;
    server_name 66.42.93.128;
    
    client_max_body_size 10M;
    
    access_log /var/log/nginx/ai-proxy-access.log;
    error_log /var/log/nginx/ai-proxy-error.log;
    
    # LM Studio API (proxied from Computer A tunnel)
    location /llm/ {
        limit_req zone=llm_limit burst=10 nodelay;
        
        # Remove /llm prefix when proxying
        rewrite ^/llm/(.*) /$1 break;
        
        proxy_pass http://127.0.0.1:1234;
        
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Long timeouts for LLM processing
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }
    
    # Main app (Computer B)
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
EOF

# Test and reload nginx
nginx -t
systemctl reload nginx

echo ""
echo "✅ Nginx Updated!"
echo ""
echo "LM Studio is now accessible at:"
echo "  http://66.42.93.128/llm/v1/models"
echo "  http://66.42.93.128/llm/v1/chat/completions"
echo ""
echo "Test it:"
echo "  curl http://66.42.93.128/llm/v1/models"
echo ""

