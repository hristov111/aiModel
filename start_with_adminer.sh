#!/bin/bash
# Start AI Companion Service with Adminer Database UI

cd "/home/bean12/Desktop/AI Service"

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 Starting AI Companion with Adminer Database UI"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if we need sudo
if groups | grep -q docker; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="sudo docker compose"
fi

# Start main services
echo "🐳 Starting main services..."
$COMPOSE_CMD -f docker-compose.dev.yml up -d

# Wait for database to be ready
echo "⏳ Waiting for database..."
sleep 5

# Start Adminer
echo "🎨 Starting Adminer..."
$COMPOSE_CMD -f docker-compose.adminer.yml up -d

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ Services Started!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 ADMINER Database UI: http://localhost:8080"
echo ""
echo "   Login credentials:"
echo "   • System:   PostgreSQL"
echo "   • Server:   postgres"
echo "   • Username: postgres"
echo "   • Password: changeme"
echo "   • Database: ai_companion"
echo ""
echo "📡 API Service: http://localhost:8000"
echo "📚 API Docs:    http://localhost:8000/docs"
echo ""
echo "════════════════════════════════════════════════════════════════"

