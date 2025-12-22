#!/usr/bin/env python3
"""
User Data Inspector - Show all database information for a specific user
"""

import asyncio
import sys
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from uuid import UUID

# Add app to path
sys.path.insert(0, '/home/bean12/Desktop/AI Service')

from app.core.config import settings
from app.models.database import (
    UserModel, 
    ConversationModel, 
    MemoryModel,
    PersonalityProfileModel,
    EmotionHistoryModel,
    RelationshipStateModel,
    GoalModel,
    GoalProgressModel,
    MessageModel
)


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(text: str, color: str = Colors.CYAN):
    """Print a formatted header"""
    print(f"\n{color}{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{color}{Colors.BOLD}{text.center(80)}{Colors.END}")
    print(f"{color}{Colors.BOLD}{'=' * 80}{Colors.END}\n")


def print_section(text: str):
    """Print a section header"""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}📋 {text}{Colors.END}")
    print(f"{Colors.YELLOW}{'-' * 80}{Colors.END}")


def print_field(name: str, value, indent: int = 0):
    """Print a field with formatting"""
    spaces = "  " * indent
    if value is None:
        value = f"{Colors.RED}None{Colors.END}"
    elif isinstance(value, bool):
        value = f"{Colors.GREEN if value else Colors.RED}{value}{Colors.END}"
    elif isinstance(value, datetime):
        value = value.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(value, UUID):
        value = str(value)[:8] + "..."
    
    print(f"{spaces}{Colors.BLUE}{name}:{Colors.END} {value}")


async def show_user_data(external_user_id: str):
    """Show all database information for a user"""
    
    # Create database engine
    engine = create_async_engine(settings.postgres_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        
        # ==========================================
        # 1. GET USER INFO
        # ==========================================
        print_header(f"USER DATA INSPECTOR: {external_user_id}")
        
        result = await session.execute(
            select(UserModel).where(UserModel.external_user_id == external_user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"{Colors.RED}❌ User '{external_user_id}' not found in database!{Colors.END}")
            return
        
        print_section("👤 User Information")
        print_field("Database ID", user.id)
        print_field("External User ID", user.external_user_id)
        print_field("Created At", user.created_at)
        print_field("Last Active", user.last_active)
        
        # ==========================================
        # 2. GET CONVERSATIONS
        # ==========================================
        print_section("💬 Conversations")
        
        result = await session.execute(
            select(ConversationModel)
            .where(ConversationModel.user_id == user.id)
            .order_by(ConversationModel.created_at.desc())
        )
        conversations = result.scalars().all()
        
        print(f"{Colors.BOLD}Total Conversations:{Colors.END} {len(conversations)}")
        
        for i, conv in enumerate(conversations[:5], 1):  # Show first 5
            print(f"\n  {Colors.CYAN}Conversation {i}:{Colors.END}")
            print_field("ID", conv.id, indent=1)
            print_field("Created", conv.created_at, indent=1)
            print_field("Updated", conv.updated_at, indent=1)
        
        if len(conversations) > 5:
            print(f"\n  {Colors.YELLOW}... and {len(conversations) - 5} more{Colors.END}")
        
        # ==========================================
        # 3. GET MEMORIES
        # ==========================================
        print_section("🧠 Long-term Memories")
        
        result = await session.execute(
            select(MemoryModel)
            .where(MemoryModel.user_id == user.id)
            .where(MemoryModel.is_active == True)
            .order_by(MemoryModel.importance.desc())
        )
        memories = result.scalars().all()
        
        # Count by type
        type_counts = {}
        for mem in memories:
            type_counts[mem.memory_type] = type_counts.get(mem.memory_type, 0) + 1
        
        print(f"{Colors.BOLD}Total Active Memories:{Colors.END} {len(memories)}")
        print(f"{Colors.BOLD}By Type:{Colors.END}")
        for mem_type, count in sorted(type_counts.items()):
            print(f"  • {mem_type}: {count}")
        
        print(f"\n{Colors.BOLD}Top 10 Most Important Memories:{Colors.END}")
        for i, mem in enumerate(memories[:10], 1):
            importance_bar = "█" * int(mem.importance * 10)
            importance_color = Colors.GREEN if mem.importance >= 0.7 else Colors.YELLOW if mem.importance >= 0.5 else Colors.RED
            
            print(f"\n  {Colors.CYAN}{i}. [{mem.memory_type}]{Colors.END} {importance_color}{importance_bar} {mem.importance:.2f}{Colors.END}")
            print(f"     {Colors.BOLD}\"{mem.content[:80]}...\"{Colors.END}" if len(mem.content) > 80 else f"     {Colors.BOLD}\"{mem.content}\"{Colors.END}")
            print_field("Created", mem.created_at, indent=2)
            if mem.superseded_by:
                print_field("Superseded by", mem.superseded_by, indent=2)
        
        # Show superseded memories count
        result = await session.execute(
            select(func.count()).select_from(MemoryModel)
            .where(MemoryModel.user_id == user.id)
            .where(MemoryModel.is_active == False)
        )
        superseded_count = result.scalar()
        if superseded_count > 0:
            print(f"\n  {Colors.YELLOW}📦 {superseded_count} superseded/inactive memories{Colors.END}")
        
        # ==========================================
        # 4. GET RELATIONSHIP STATE
        # ==========================================
        print_section("💕 Relationship State")
        
        result = await session.execute(
            select(RelationshipStateModel).where(RelationshipStateModel.user_id == user.id)
        )
        relationship = result.scalar_one_or_none()
        
        if relationship:
            print_field("Total Messages", relationship.total_messages)
            print_field("Relationship Depth Score", f"{relationship.relationship_depth_score:.1f}/10")
            print_field("Trust Level", f"{relationship.trust_level:.1f}/10")
            print_field("Days Known", relationship.days_known)
            print_field("First Interaction", relationship.first_interaction)
            print_field("Last Interaction", relationship.last_interaction)
            print_field("Positive Reactions", relationship.positive_reactions)
            print_field("Negative Reactions", relationship.negative_reactions)
            
            milestones = relationship.milestones or []
            if milestones:
                print(f"\n{Colors.BOLD}Milestones:{Colors.END}")
                for milestone in milestones:
                    if isinstance(milestone, dict):
                        print(f"  🎉 {milestone.get('type')} - {milestone.get('reached_at', 'N/A')}")
                    else:
                        print(f"  🎉 {milestone}")
        else:
            print(f"{Colors.YELLOW}No relationship state tracked{Colors.END}")
        
        # ==========================================
        # 5. GET PERSONALITY
        # ==========================================
        print_section("🎭 Personality Profile")
        
        result = await session.execute(
            select(PersonalityProfileModel)
            .where(PersonalityProfileModel.user_id == user.id)
        )
        personality = result.scalar_one_or_none()
        
        if personality:
            print_field("Version", personality.version)
            print_field("Archetype", personality.archetype)
            print_field("Relationship Type", personality.relationship_type)
            
            print(f"\n{Colors.BOLD}Traits:{Colors.END}")
            trait_fields = {
                'humor_level': personality.humor_level,
                'formality_level': personality.formality_level,
                'enthusiasm_level': personality.enthusiasm_level,
                'empathy_level': personality.empathy_level,
                'directness_level': personality.directness_level,
                'curiosity_level': personality.curiosity_level,
                'supportiveness_level': personality.supportiveness_level,
                'playfulness_level': personality.playfulness_level,
            }
            for trait, value in sorted(trait_fields.items()):
                if value is not None:
                    bar = "█" * int(value) + "░" * (10 - int(value))
                    trait_name = trait.replace('_level', '').replace('_', ' ').title()
                    print(f"  • {trait_name}: {Colors.CYAN}{bar}{Colors.END} {value}/10")
            
            print(f"\n{Colors.BOLD}Behaviors:{Colors.END}")
            behaviors = {
                'asks_questions': personality.asks_questions,
                'uses_examples': personality.uses_examples,
                'shares_opinions': personality.shares_opinions,
                'challenges_user': personality.challenges_user,
                'celebrates_wins': personality.celebrates_wins,
            }
            for behavior, enabled in sorted(behaviors.items()):
                if enabled is not None:
                    status = f"{Colors.GREEN}✓ Enabled{Colors.END}" if enabled else f"{Colors.RED}✗ Disabled{Colors.END}"
                    behavior_name = behavior.replace('_', ' ').title()
                    print(f"  • {behavior_name}: {status}")
            
            if personality.backstory:
                print(f"\n{Colors.BOLD}Backstory:{Colors.END}")
                print(f"  {personality.backstory[:200]}..." if len(personality.backstory) > 200 else f"  {personality.backstory}")
            
            if personality.speaking_style:
                print(f"\n{Colors.BOLD}Speaking Style:{Colors.END}")
                print(f"  {personality.speaking_style[:200]}..." if len(personality.speaking_style) > 200 else f"  {personality.speaking_style}")
            
            print_field("\nCustom Instructions", personality.custom_instructions[:100] + "..." if personality.custom_instructions and len(personality.custom_instructions) > 100 else personality.custom_instructions)
            print_field("Last Updated", personality.updated_at)
        else:
            print(f"{Colors.YELLOW}No personality profile set{Colors.END}")
        
        # ==========================================
        # 6. GET EMOTIONS
        # ==========================================
        print_section("😊 Emotion History")
        
        result = await session.execute(
            select(EmotionHistoryModel)
            .where(EmotionHistoryModel.user_id == user.id)
            .order_by(EmotionHistoryModel.detected_at.desc())
            .limit(10)
        )
        emotions = result.scalars().all()
        
        if emotions:
            print(f"{Colors.BOLD}Recent Emotions (last 10):{Colors.END}")
            
            emotion_icons = {
                'happy': '😊', 'sad': '😢', 'angry': '😠', 'anxious': '😰',
                'excited': '🤩', 'grateful': '🙏', 'frustrated': '😤',
                'lonely': '😔', 'proud': '😌', 'surprised': '😲',
                'disappointed': '😞', 'confused': '😕', 'content': '😌',
                'overwhelmed': '😵', 'hopeful': '🤞', 'bored': '😑'
            }
            
            for i, emotion in enumerate(emotions, 1):
                icon = emotion_icons.get(emotion.emotion, '😐')
                confidence_bar = "█" * int(emotion.confidence * 10)
                print(f"\n  {i}. {icon} {Colors.BOLD}{emotion.emotion}{Colors.END} {Colors.CYAN}{confidence_bar}{Colors.END} ({emotion.confidence:.0%})")
                print_field("Intensity", emotion.intensity, indent=2)
                print_field("Detected", emotion.detected_at, indent=2)
                if emotion.message_snippet:
                    print(f"     {Colors.YELLOW}Message: \"{emotion.message_snippet}\"{Colors.END}")
                if emotion.indicators:
                    indicators = emotion.indicators if isinstance(emotion.indicators, list) else []
                    if indicators:
                        print(f"     {Colors.YELLOW}Indicators: {', '.join(indicators)}{Colors.END}")
        else:
            print(f"{Colors.YELLOW}No emotion data recorded{Colors.END}")
        
        # ==========================================
        # 7. GET GOALS
        # ==========================================
        print_section("🎯 Goals & Progress")
        
        result = await session.execute(
            select(GoalModel)
            .where(GoalModel.user_id == user.id)
            .order_by(GoalModel.created_at.desc())
        )
        goals = result.scalars().all()
        
        if goals:
            active_goals = [g for g in goals if g.status == 'active']
            completed_goals = [g for g in goals if g.status == 'completed']
            
            print(f"{Colors.BOLD}Active Goals:{Colors.END} {len(active_goals)}")
            print(f"{Colors.BOLD}Completed Goals:{Colors.END} {len(completed_goals)}")
            
            if active_goals:
                print(f"\n{Colors.BOLD}Active Goals:{Colors.END}")
                for i, goal in enumerate(active_goals, 1):
                    progress = goal.progress_percentage / 100.0 if goal.progress_percentage else 0.0
                    progress_bar = "█" * int(progress * 10) + "░" * (10 - int(progress * 10))
                    print(f"\n  {i}. {Colors.BOLD}{goal.title}{Colors.END}")
                    print(f"     Progress: {Colors.GREEN}{progress_bar}{Colors.END} {goal.progress_percentage:.0f}%")
                    print_field("Category", goal.category, indent=2)
                    print_field("Mention Count", goal.mention_count, indent=2)
                    print_field("Created", goal.created_at, indent=2)
                    if goal.target_date:
                        print_field("Target Date", goal.target_date, indent=2)
                    if goal.last_mentioned_at:
                        print_field("Last Mentioned", goal.last_mentioned_at, indent=2)
                    if goal.description:
                        print(f"     {Colors.YELLOW}Description: {goal.description[:80]}...{Colors.END}" if len(goal.description) > 80 else f"     {Colors.YELLOW}Description: {goal.description}{Colors.END}")
            
            if completed_goals:
                print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Completed Goals:{Colors.END}")
                for goal in completed_goals[:5]:
                    completed_date = f" ({goal.completed_at.strftime('%Y-%m-%d')})" if goal.completed_at else ""
                    print(f"  • {goal.title}{completed_date}")
        else:
            print(f"{Colors.YELLOW}No goals tracked{Colors.END}")
        
        # ==========================================
        # SUMMARY
        # ==========================================
        print_header("📊 SUMMARY", Colors.GREEN)
        
        print(f"{Colors.BOLD}Data Overview:{Colors.END}")
        print(f"  • {Colors.CYAN}Conversations:{Colors.END} {len(conversations)}")
        print(f"  • {Colors.CYAN}Active Memories:{Colors.END} {len(memories)}")
        print(f"  • {Colors.CYAN}Emotions Recorded:{Colors.END} {len(emotions)}")
        print(f"  • {Colors.CYAN}Goals:{Colors.END} {len(goals)}")
        print(f"  • {Colors.CYAN}Personality Version:{Colors.END} {personality.version if personality else 'N/A'}")
        if relationship:
            print(f"  • {Colors.CYAN}Total Messages:{Colors.END} {relationship.total_messages}")
            print(f"  • {Colors.CYAN}Days Known:{Colors.END} {relationship.days_known}")
        
        # Database size info
        result = await session.execute(
            select(func.pg_size_pretty(func.pg_database_size('ai_companion')))
        )
        db_size = result.scalar()
        print(f"\n{Colors.BOLD}Database Size:{Colors.END} {db_size}")
        
        print(f"\n{Colors.GREEN}✅ Data inspection complete!{Colors.END}\n")
    
    await engine.dispose()


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        user_id = "myuser123"  # Default user
    
    print(f"{Colors.BOLD}Connecting to database...{Colors.END}")
    asyncio.run(show_user_data(user_id))


if __name__ == "__main__":
    main()

