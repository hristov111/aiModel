#!/bin/bash
# Test Explicit Conversation Context Lock
# This script demonstrates that follow-up messages stay in explicit mode

echo "🧪 Testing Explicit Conversation Context Lock"
echo "=============================================="
echo ""

# Get JWT token
JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJteXVzZXIxMjMiLCJpYXQiOjE3NjY2MDk5NDMsImV4cCI6MTc2NjY5NjM0MywidHlwZSI6ImFjY2Vzc190b2tlbiJ9.E8KQPxmWsay24j8ObEbKWw70_aqsU9FrkU7U4qo8N8A"

echo "📝 Step 1: Send explicit message (should classify as EXPLICIT)"
echo "Message: 'I want to have sex with you'"
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to have sex with you"}' | head -20)

# Extract conversation ID from response
CONV_ID=$(echo "$RESPONSE" | grep -o '"conversation_id":"[^"]*"' | head -1 | cut -d'"' -f4)

echo "✅ Conversation ID: $CONV_ID"
echo ""
sleep 2

echo "📝 Step 2: Send follow-up message (NOT explicit, but should stay in EXPLICIT route)"
echo "Message: 'continue please'"
echo ""

RESPONSE2=$(curl -s -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"continue please\", \"conversation_id\": \"$CONV_ID\"}" | head -20)

echo "✅ Sent follow-up"
echo ""
sleep 2

echo "📝 Step 3: Send another follow-up"
echo "Message: 'keep going'"
echo ""

RESPONSE3=$(curl -s -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"keep going\", \"conversation_id\": \"$CONV_ID\"}" | head -20)

echo "✅ Sent 3rd message"
echo ""

echo "🔍 Checking logs for route locking..."
echo "=============================================="
docker logs ai_companion_service_dev 2>&1 | tail -50 | grep -E "Route locked|route_lock_message_count|Authenticated user via JWT"
echo ""
echo "✅ Test complete!"
echo ""
echo "Expected behavior:"
echo "  - Message 1: Classified as EXPLICIT → Lock set for 5 messages"
echo "  - Message 2: 'Route locked to EXPLICIT (4 messages remaining)'"
echo "  - Message 3: 'Route locked to EXPLICIT (3 messages remaining)'"
echo ""
echo "📖 See EXPLICIT_CONTEXT_FIX.md for more details"

