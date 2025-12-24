#!/bin/bash
set -e

echo "======================================"
echo "AI Companion Service - Starting..."
echo "======================================"

# Function to wait for PostgreSQL
wait_for_postgres() {
    echo "Waiting for PostgreSQL..."
    local max_attempts=30
    local attempt=0
    
    # Extract database host and port from POSTGRES_URL
    # Format: postgresql+asyncpg://user:pass@host:port/db
    local db_host=$(echo "${POSTGRES_URL}" | sed -n 's/.*@\([^:]*\):.*/\1/p')
    local db_port=$(echo "${POSTGRES_URL}" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    local db_name=$(echo "${POSTGRES_URL}" | sed -n 's/.*\/\([^?]*\).*/\1/p')
    
    echo "  Connecting to: ${db_host}:${db_port}/${db_name}"
    
    while [ $attempt -lt $max_attempts ]; do
        if python -c "import psycopg2; conn = psycopg2.connect(host='${db_host}', port=${db_port}, user='postgres', password='postgres', dbname='${db_name}'); conn.close()" 2>/dev/null; then
            echo "✓ PostgreSQL is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "  Attempt $attempt/$max_attempts - PostgreSQL not ready yet..."
        sleep 2
    done
    
    echo "✗ PostgreSQL failed to become ready"
    return 1
}

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    if alembic upgrade head; then
        echo "✓ Migrations completed successfully"
    else
        echo "✗ Migration failed"
        return 1
    fi
}

# Wait for PostgreSQL
if ! wait_for_postgres; then
    echo "Failed to connect to PostgreSQL. Exiting..."
    exit 1
fi

# Run migrations if enabled
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    if ! run_migrations; then
        echo "Migration failed. Exiting..."
        exit 1
    fi
fi

echo "======================================"
echo "Starting application..."
echo "Environment: ${ENVIRONMENT:-development}"
echo "======================================"

# Execute the main command
exec "$@"

