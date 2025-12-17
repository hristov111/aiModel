#!/bin/bash
# Setup script for public access to AI Model service

set -e

echo "🚀 AI Model Public Access Setup"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to generate secrets
generate_secret() {
    python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
}

# Check if .env.production exists
if [ -f ".env.production" ]; then
    echo -e "${YELLOW}⚠️  .env.production already exists${NC}"
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo "Exiting without changes."
        exit 0
    fi
fi

# Generate secrets
echo -e "${GREEN}Generating secure secrets...${NC}"
JWT_SECRET=$(generate_secret)
DB_PASSWORD=$(generate_secret)

# Get user input
read -p "Enter your domain name (e.g., api.example.com): " DOMAIN
read -p "Enter CORS origins (comma-separated, e.g., https://example.com): " CORS_ORIGINS

# Create .env.production
cat > .env.production << EOF
# Production Environment Configuration
ENVIRONMENT=production

# Authentication (REQUIRED)
REQUIRE_AUTHENTICATION=true
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Database Configuration
POSTGRES_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@localhost:5432/ai_companion
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_OVERFLOW=40

# LM Studio Configuration
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL_NAME=local-model
LM_STUDIO_TEMPERATURE=0.7
LM_STUDIO_MAX_TOKENS=2000

# Security
CORS_ORIGINS=${CORS_ORIGINS}
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Logging
LOG_LEVEL=INFO

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
EOF

echo -e "${GREEN}✅ Created .env.production${NC}"
echo ""

# Create helper script for generating tokens
cat > generate_token.py << 'EOF'
#!/usr/bin/env python3
"""Generate JWT token for API authentication."""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.auth import create_jwt_token, generate_api_key

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_token.py <user_id> [hours]")
        print("\nExamples:")
        print("  python generate_token.py alice")
        print("  python generate_token.py bob 48")
        sys.exit(1)
    
    user_id = sys.argv[1]
    hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    
    # Generate JWT token
    jwt_token = create_jwt_token(user_id=user_id, expires_in_hours=hours)
    
    # Generate API key
    api_key = generate_api_key(user_id=user_id)
    
    print(f"\n🔑 Authentication Credentials for user: {user_id}")
    print("=" * 70)
    print(f"\nJWT Token (expires in {hours}h):")
    print(f"  {jwt_token}")
    print(f"\nAPI Key (no expiration):")
    print(f"  {api_key}")
    print("\n" + "=" * 70)
    print("\n📝 Usage Examples:\n")
    print("Using JWT Token:")
    print(f'  curl -H "Authorization: Bearer {jwt_token}" \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"message": "Hello!", "conversation_id": "conv-1"}\' \\')
    print('       https://your-domain.com/api/chat')
    print("\nUsing API Key:")
    print(f'  curl -H "X-API-Key: {api_key}" \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"message": "Hello!", "conversation_id": "conv-1"}\' \\')
    print('       https://your-domain.com/api/chat')
    print()

if __name__ == "__main__":
    main()
EOF

chmod +x generate_token.py

echo -e "${GREEN}✅ Created generate_token.py${NC}"
echo ""

# Create systemd service file
cat > ai-model.service << EOF
[Unit]
Description=AI Model Service
After=network.target postgresql.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python app/main.py
Restart=always
RestartSec=10
EnvironmentFile=$(pwd)/.env.production

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Created ai-model.service${NC}"
echo ""

# Create nginx configuration
cat > nginx-ai-model.conf << EOF
server {
    listen 80;
    server_name ${DOMAIN};

    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN};

    # SSL certificates (will be added by certbot)
    # ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Max upload size
    client_max_body_size 10M;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    # Proxy to FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts for LLM responses
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

echo -e "${GREEN}✅ Created nginx-ai-model.conf${NC}"
echo ""

# Print next steps
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo ""
echo "1. Install nginx and certbot (if not already installed):"
echo "   sudo apt update && sudo apt install nginx certbot python3-certbot-nginx"
echo ""
echo "2. Copy nginx configuration:"
echo "   sudo cp nginx-ai-model.conf /etc/nginx/sites-available/ai-model"
echo "   sudo ln -s /etc/nginx/sites-available/ai-model /etc/nginx/sites-enabled/"
echo "   sudo nginx -t"
echo ""
echo "3. Get SSL certificate:"
echo "   sudo certbot --nginx -d ${DOMAIN}"
echo ""
echo "4. Install systemd service:"
echo "   sudo cp ai-model.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable ai-model"
echo "   sudo systemctl start ai-model"
echo ""
echo "5. Make sure LM Studio is running on port 1234"
echo ""
echo "6. Generate authentication tokens:"
echo "   source venv/bin/activate"
echo "   python generate_token.py YOUR_USER_ID"
echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Your service will be accessible at: https://${DOMAIN}"
echo ""

# Save credentials securely
echo -e "${RED}⚠️  IMPORTANT: Save these credentials securely!${NC}"
echo ""
echo "JWT Secret Key: ${JWT_SECRET}"
echo "Database Password: ${DB_PASSWORD}"
echo ""
echo "These are stored in .env.production - never commit this file to git!"

