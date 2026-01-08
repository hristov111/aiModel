#!/bin/bash
# AI Companion Service - Docker Startup Script
# Run this script to start the service properly with Docker

cd "/home/bean12/Desktop/AI Service"

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 AI Companion Service - Starting with Docker"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if we need sudo
if groups | grep -q docker; then
    DOCKER_CMD="docker"
    COMPOSE_CMD="docker compose"
else
    DOCKER_CMD="sudo docker"
    COMPOSE_CMD="sudo docker compose"
fi

# Stop any existing Python processes
echo "🛑 Stopping any existing Python services..."
pkill -f "uvicorn app.main:app" 2>/dev/null
sleep 2

# Stop existing containers
echo "🛑 Stopping existing Docker containers..."
$COMPOSE_CMD -f docker-compose.dev.yml down 2>/dev/null
sleep 2

# Start with Docker Compose
echo ""
echo "🐳 Starting Docker containers..."
echo ""
$COMPOSE_CMD -f docker-compose.dev.yml up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to start..."
sleep 8

# Show status
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  📊 Service Status"
echo "════════════════════════════════════════════════════════════════"
$COMPOSE_CMD -f docker-compose.dev.yml ps

# Test health
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  🔍 Health Check"
echo "════════════════════════════════════════════════════════════════"
sleep 2
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "⚠️  Service not ready yet, wait 10 more seconds and try: curl http://localhost:8000/health"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ Service Started!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📡 API Services:"
echo "   • API:        http://localhost:8000"
echo "   • API Docs:   http://localhost:8000/docs"
echo "   • Chat UI:    http://localhost:8000/ui"
echo "   • Health:     http://localhost:8000/health"
echo ""
echo "🎨 Database UI (Adminer):"
echo "   • URL:        http://localhost:8080"
echo "   • Server:     postgres"
echo "   • Username:   postgres"
echo "   • Password:   changeme"
echo "   • Database:   ai_companion"
echo ""
echo "🔧 Direct Access:"
echo "   • Database:   localhost:5433"
echo "   • Redis:      localhost:6379"
echo ""
echo "📋 Useful Commands:"
echo "   • View logs:    $COMPOSE_CMD -f docker-compose.dev.yml logs -f"
echo "   • Stop:         $COMPOSE_CMD -f docker-compose.dev.yml down"
echo "   • Restart:      $COMPOSE_CMD -f docker-compose.dev.yml restart"
echo "   • Shell:        $COMPOSE_CMD -f docker-compose.dev.yml exec aiservice bash"
echo ""
echo "🎯 CORS Configured for: localhost:4200, localhost:3000, localhost:8080, 66.42.93.128"
echo ""
echo "════════════════════════════════════════════════════════════════"

