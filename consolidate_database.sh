#!/bin/bash
# Consolidate to ONE persistent PostgreSQL database

cd "/home/bean12/Desktop/AI Service"

echo "════════════════════════════════════════════════════════════════"
echo "  🔄 Database Consolidation Script"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "This will:"
echo "  1. Stop all services"
echo "  2. Create ONE persistent database volume"
echo "  3. Back up your current data (optional)"
echo "  4. Update docker-compose to use the persistent volume"
echo "  5. Start services with the new persistent database"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Check if we need sudo
if groups | grep -q docker; then
    DOCKER_CMD="docker"
    COMPOSE_CMD="docker compose"
else
    DOCKER_CMD="sudo docker"
    COMPOSE_CMD="sudo docker compose"
fi

echo ""
echo "🛑 Step 1: Stopping all services..."
$COMPOSE_CMD -f docker-compose.dev.yml down 2>/dev/null
$COMPOSE_CMD down 2>/dev/null
sleep 2

echo ""
echo "📊 Current volumes:"
$DOCKER_CMD volume ls | grep postgres

echo ""
echo "💾 Step 2: Creating persistent volume..."
$DOCKER_CMD volume create ai_companion_postgres_persistent || echo "Volume may already exist"

echo ""
echo "📦 Step 3: Which database contains your important data?"
echo "  1. aiservice_postgres_data (Dec 29 - Production)"
echo "  2. aiservice_postgres_data_dev (Jan 6 - Current Dev)"
echo "  3. aiservice_postgres_dev_data (Dec 24 - Oldest)"
echo "  4. Start fresh (no data migration)"
echo ""
read -p "Select (1-4): " choice

if [ "$choice" != "4" ]; then
    case $choice in
        1) SOURCE_VOLUME="aiservice_postgres_data" ;;
        2) SOURCE_VOLUME="aiservice_postgres_data_dev" ;;
        3) SOURCE_VOLUME="aiservice_postgres_dev_data" ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac
    
    echo ""
    echo "🔄 Migrating data from $SOURCE_VOLUME to ai_companion_postgres_persistent..."
    
    # Copy data using a temporary container
    $DOCKER_CMD run --rm \
        -v $SOURCE_VOLUME:/source:ro \
        -v ai_companion_postgres_persistent:/target \
        alpine sh -c "cp -a /source/. /target/"
    
    echo "✅ Data migration complete!"
fi

echo ""
echo "📝 Step 4: Updating docker-compose configurations..."
# Backup current files
cp docker-compose.dev.yml docker-compose.dev.yml.backup
cp docker-compose.yml docker-compose.yml.backup

# Update dev compose
sed -i 's/postgres_data_dev:/postgres_persistent_data:/' docker-compose.dev.yml
sed -i 's/aiservice_postgres_data_dev/ai_companion_postgres_persistent/' docker-compose.dev.yml

# Update prod compose
sed -i 's/postgres_data:/postgres_persistent_data:/' docker-compose.yml
sed -i 's/aiservice_postgres_data/ai_companion_postgres_persistent/' docker-compose.yml

echo "✅ Configurations updated!"

echo ""
echo "🚀 Step 5: Starting services with persistent database..."
$COMPOSE_CMD -f docker-compose.dev.yml up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 8

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ Consolidation Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 New persistent volume: ai_companion_postgres_persistent"
echo ""
echo "🗑️  Old volumes (can be safely deleted after verification):"
echo "   - aiservice_postgres_data"
echo "   - aiservice_postgres_data_dev"
echo "   - aiservice_postgres_dev_data"
echo ""
echo "To delete old volumes later:"
echo "   $DOCKER_CMD volume rm aiservice_postgres_data"
echo "   $DOCKER_CMD volume rm aiservice_postgres_data_dev"
echo "   $DOCKER_CMD volume rm aiservice_postgres_dev_data"
echo ""
echo "🔍 Test your database at: http://localhost:8080 (Adminer)"
echo ""
echo "════════════════════════════════════════════════════════════════"

