#!/bin/bash
# Start AI Companion Service with Docker

cd "/home/bean12/Desktop/AI Service"

echo "🚀 Starting AI Companion Service with Docker..."
echo ""

# Stop any running Python processes
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "✅ Stopped Python process"

# Start with docker-compose
sudo docker compose -f docker-compose.dev.yml up -d

echo ""
echo "✅ Docker containers starting..."
echo ""
echo "Waiting for services to be healthy..."
sleep 5

# Check status
sudo docker compose -f docker-compose.dev.yml ps

echo ""
echo "📊 Access Points:"
echo "  • API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • Chat UI: http://localhost:8000/ui"
echo "  • Health: http://localhost:8000/health"
echo "  • Database: localhost:5433"
echo "  • Redis: localhost:6379"
echo ""
echo "📋 Useful Commands:"
echo "  • View logs: sudo docker compose -f docker-compose.dev.yml logs -f"
echo "  • Stop: sudo docker compose -f docker-compose.dev.yml down"
echo "  • Restart: sudo docker compose -f docker-compose.dev.yml restart"
echo ""

# Test health
echo "🔍 Testing API health..."
sleep 3
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "⚠️  API not ready yet, wait a few seconds"

echo ""
echo "✅ Done! Your service should be running now."

