#!/bin/bash
# Clear all memories from the AI Companion database

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        CLEAR ALL MEMORIES - CAUTION!                     ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "This will delete:"
echo "  • All conversations"
echo "  • All memories (short-term and long-term)"
echo "  • All emotion history"
echo "  • All goals and progress"
echo "  • All personality profiles"
echo "  • All relationship states"
echo ""
echo "Users themselves will NOT be deleted (you can still use same user IDs)"
echo ""
echo -n "Type 'CLEAR' to proceed: "
read confirmation

if [ "$confirmation" = "CLEAR" ]; then
    echo ""
    echo "Clearing all data..."
    
    docker exec ai_companion_db psql -U postgres -d ai_companion << 'EOF'
TRUNCATE TABLE memories CASCADE;
TRUNCATE TABLE emotion_history CASCADE;
TRUNCATE TABLE messages CASCADE;
TRUNCATE TABLE conversations CASCADE;
TRUNCATE TABLE goals CASCADE;
TRUNCATE TABLE goal_progress CASCADE;
TRUNCATE TABLE personality_profiles CASCADE;
TRUNCATE TABLE relationship_state CASCADE;
EOF
    
    echo ""
    echo "✅ All memories cleared!"
    echo ""
    echo "Database is now clean. Users can start fresh conversations."
else
    echo ""
    echo "❌ Cancelled. No data was deleted."
fi

