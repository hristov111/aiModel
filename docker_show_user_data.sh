#!/bin/bash
# Wrapper script to run show_user_data.py inside Docker container

USER_ID="${1:-default_user}"

echo "📊 Inspecting user data for: $USER_ID"
echo "Running inside Docker container..."
echo ""

# Copy latest version of script to container
docker cp "/home/bean12/Desktop/AI Service/show_user_data.py" ai_companion_service_dev:/app/ 2>/dev/null

# Run the script
docker exec ai_companion_service_dev python /app/show_user_data.py "$USER_ID"

