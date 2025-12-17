"""SQLAlchemy database models."""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, Enum as SQLEnum,
    ForeignKey, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PG_ENUM
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship
from pgvector.sqlalchemy import Vector
import uuid
import enum


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""
    pass


class MemoryTypeEnum(str, enum.Enum):
    """Memory type enumeration - values match database enum."""
    FACT = "fact"
    PREFERENCE = "preference"
    EVENT = "event"
    CONTEXT = "context"
    
    # Allow case-insensitive lookup
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value == value.lower():
                    return member
        return None


class UserModel(Base):
    """User accounts table."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_user_id = Column(String(255), unique=True, nullable=False, index=True)  # From your auth system
    email = Column(String(255), unique=True, nullable=True)
    display_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    last_active = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    extra_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Relationships
    conversations = relationship("ConversationModel", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_users_external_user_id", "external_user_id"),
        Index("ix_users_email", "email"),
    )


class ConversationModel(Base):
    """Conversation tracking table."""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)  # Optional conversation title
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    last_summary = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("UserModel", back_populates="conversations")
    memories = relationship("MemoryModel", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_conversations_user_id", "user_id"),
        Index("ix_conversations_updated_at", "updated_at"),
    )


class MemoryModel(Base):
    """Long-term memory storage with vector embeddings and intelligence."""
    __tablename__ = "memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=False)  # 384-dimensional vector for all-MiniLM-L6-v2
    # Use PostgreSQL ENUM type (must match database enum type name 'memorytypeenum')
    memory_type = Column(
        PG_ENUM('fact', 'preference', 'event', 'context', name='memorytypeenum', create_type=False),
        nullable=False,
        default='fact'
    )
    
    # Enhanced Intelligence Fields
    category = Column(String(50), nullable=True)  # personal_fact, preference, goal, event, relationship, challenge, achievement
    importance = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0 (final calculated score)
    importance_scores = Column(JSONB, nullable=True)  # Breakdown: {emotional: 0.7, explicit: 0.8, frequency: 0.3, recency: 0.9}
    
    # Temporal Intelligence
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    last_accessed = Column(DateTime, nullable=True)  # When last retrieved
    access_count = Column(Integer, nullable=False, default=0)  # How many times retrieved
    decay_factor = Column(Float, nullable=False, default=1.0)  # 0.0-1.0, reduces over time
    
    # Consolidation & Relationships
    is_active = Column(Boolean, nullable=False, default=True)  # False if consolidated/superseded
    consolidated_from = Column(JSONB, nullable=True)  # UUIDs of memories merged into this one
    superseded_by = Column(UUID(as_uuid=True), nullable=True)  # UUID of memory that replaced this
    
    # Entity Extraction
    related_entities = Column(JSONB, nullable=True)  # {people: ['Alice', 'Bob'], places: ['Paris'], topics: ['python', 'ai']}
    
    # Original metadata
    extra_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Relationships
    conversation = relationship("ConversationModel", back_populates="memories")
    
    # Indexes for performance
    __table_args__ = (
        Index("ix_memories_conversation_id", "conversation_id"),
        Index("ix_memories_user_id", "user_id"),
        Index("ix_memories_created_at", "created_at"),
        Index("ix_memories_importance", "importance"),
        Index("ix_memories_category", "category"),
        Index("ix_memories_is_active", "is_active"),
        Index("ix_memories_last_accessed", "last_accessed"),
        # Vector similarity index (cosine distance)
        Index(
            "ix_memories_embedding_cosine",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )


class MessageModel(Base):
    """Message audit log for conversations."""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    conversation = relationship("ConversationModel", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index("ix_messages_conversation_id", "conversation_id"),
        Index("ix_messages_timestamp", "timestamp"),
    )


class EmotionHistoryModel(Base):
    """Emotion detection history for user messages."""
    __tablename__ = "emotion_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True)
    emotion = Column(String(50), nullable=False)  # sad, happy, angry, etc.
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    intensity = Column(String(20), nullable=False)  # low, medium, high
    indicators = Column(JSONB, nullable=True)  # ['keyword', 'emoji', 'phrase']
    message_snippet = Column(Text, nullable=True)  # First 100 chars of message
    detected_at = Column(DateTime, nullable=False, default=func.now())
    
    # Indexes for querying
    __table_args__ = (
        Index("ix_emotion_history_user_id", "user_id"),
        Index("ix_emotion_history_detected_at", "detected_at"),
        Index("ix_emotion_history_emotion", "emotion"),
    )


class PersonalityProfileModel(Base):
    """AI personality configuration for each user."""
    __tablename__ = "personality_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Core Identity
    archetype = Column(String(50), nullable=True)  # wise_mentor, supportive_friend, professional_coach, creative_partner, etc.
    relationship_type = Column(String(50), nullable=True)  # friend, mentor, coach, therapist, partner, assistant
    
    # Personality Traits (0-10 scales)
    humor_level = Column(Integer, nullable=True, default=5)  # 0=serious, 10=very humorous
    formality_level = Column(Integer, nullable=True, default=5)  # 0=casual, 10=very formal
    enthusiasm_level = Column(Integer, nullable=True, default=5)  # 0=reserved, 10=very enthusiastic
    empathy_level = Column(Integer, nullable=True, default=7)  # 0=logical, 10=highly empathetic
    directness_level = Column(Integer, nullable=True, default=5)  # 0=indirect/gentle, 10=very direct
    curiosity_level = Column(Integer, nullable=True, default=5)  # 0=passive, 10=very curious
    supportiveness_level = Column(Integer, nullable=True, default=7)  # 0=challenging, 10=highly supportive
    playfulness_level = Column(Integer, nullable=True, default=5)  # 0=serious, 10=very playful
    
    # Advanced Configuration
    backstory = Column(Text, nullable=True)  # Optional backstory for roleplay
    custom_instructions = Column(Text, nullable=True)  # User's custom personality notes
    speaking_style = Column(Text, nullable=True)  # How AI should speak
    
    # Behavioral Preferences
    asks_questions = Column(Boolean, nullable=True, default=True)  # Should AI ask questions?
    uses_examples = Column(Boolean, nullable=True, default=True)  # Should AI give examples?
    shares_opinions = Column(Boolean, nullable=True, default=True)  # Should AI share opinions?
    challenges_user = Column(Boolean, nullable=True, default=False)  # Should AI challenge/push user?
    celebrates_wins = Column(Boolean, nullable=True, default=True)  # Should AI celebrate achievements?
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    version = Column(Integer, nullable=False, default=1)  # Track personality evolution
    
    # Indexes
    __table_args__ = (
        Index("ix_personality_profiles_user_id", "user_id"),
    )


class RelationshipStateModel(Base):
    """Tracks the evolving relationship between user and AI."""
    __tablename__ = "relationship_state"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Relationship Metrics
    total_messages = Column(Integer, nullable=False, default=0)
    relationship_depth_score = Column(Float, nullable=False, default=0.0)  # 0-10, grows over time
    trust_level = Column(Float, nullable=False, default=5.0)  # 0-10, based on user engagement
    
    # Timeline
    first_interaction = Column(DateTime, nullable=False, default=func.now())
    last_interaction = Column(DateTime, nullable=False, default=func.now())
    days_known = Column(Integer, nullable=False, default=0)  # Auto-calculated
    
    # Milestones (JSONB array)
    milestones = Column(JSONB, nullable=True, default=[])  # [{type: '100_messages', reached_at: '...'}]
    
    # User Feedback
    positive_reactions = Column(Integer, nullable=False, default=0)  # Thumbs up count
    negative_reactions = Column(Integer, nullable=False, default=0)  # Thumbs down count
    
    # Metadata
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index("ix_relationship_state_user_id", "user_id"),
    )


class GoalModel(Base):
    """User goals with progress tracking."""
    __tablename__ = "goals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Goal Details
    title = Column(String(255), nullable=False)  # "Learn Spanish"
    description = Column(Text, nullable=True)  # Detailed description
    category = Column(String(50), nullable=False)  # learning, health, career, personal, financial, creative, social
    
    # Status & Progress
    status = Column(String(20), nullable=False, default='active')  # active, completed, abandoned, paused
    progress_percentage = Column(Float, nullable=False, default=0.0)  # 0-100
    
    # Timeline
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    target_date = Column(DateTime, nullable=True)  # Optional deadline
    completed_at = Column(DateTime, nullable=True)
    
    # Tracking
    last_mentioned_at = Column(DateTime, nullable=True)  # When user last mentioned this goal
    mention_count = Column(Integer, nullable=False, default=0)  # How often mentioned
    check_in_frequency = Column(String(20), nullable=True)  # daily, weekly, biweekly, monthly, never
    last_check_in = Column(DateTime, nullable=True)  # When AI last asked about it
    
    # Milestones (JSONB array)
    milestones = Column(JSONB, nullable=True, default=[])  # [{name: 'Complete module 1', completed: true, date: '...'}]
    
    # AI Observations (JSONB)
    progress_notes = Column(JSONB, nullable=True, default=[])  # [{date: '...', observation: 'User mentioned practicing daily'}]
    
    # Motivation & Context
    motivation = Column(Text, nullable=True)  # Why user wants to achieve this
    obstacles = Column(JSONB, nullable=True, default=[])  # Challenges user faces
    
    # Metadata
    extra_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Indexes
    __table_args__ = (
        Index("ix_goals_user_id", "user_id"),
        Index("ix_goals_status", "status"),
        Index("ix_goals_category", "category"),
        Index("ix_goals_target_date", "target_date"),
        Index("ix_goals_last_mentioned_at", "last_mentioned_at"),
    )


class GoalProgressModel(Base):
    """Tracks individual progress updates for goals."""
    __tablename__ = "goal_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Progress Details
    progress_type = Column(String(50), nullable=False)  # mention, update, milestone, setback, completion
    content = Column(Text, nullable=False)  # What was said/done
    progress_delta = Column(Float, nullable=True)  # Change in percentage (can be negative)
    
    # Sentiment
    sentiment = Column(String(20), nullable=True)  # positive, negative, neutral
    emotion = Column(String(50), nullable=True)  # From emotion detection
    
    # Source
    conversation_id = Column(UUID(as_uuid=True), nullable=True)  # Where this came from
    detected_automatically = Column(Boolean, nullable=False, default=True)
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Metadata
    extra_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Indexes
    __table_args__ = (
        Index("ix_goal_progress_goal_id", "goal_id"),
        Index("ix_goal_progress_user_id", "user_id"),
        Index("ix_goal_progress_created_at", "created_at"),
        Index("ix_goal_progress_progress_type", "progress_type"),
    )

