"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    conversation_id: Optional[UUID] = Field(default=None, description="Conversation ID (creates new if not provided)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hello, how are you?",
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint (non-streaming)."""
    response: str = Field(..., description="Assistant response")
    conversation_id: UUID = Field(..., description="Conversation ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "I'm doing well, thank you for asking!",
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class ResetConversationRequest(BaseModel):
    """Request model for resetting conversation."""
    conversation_id: UUID = Field(..., description="Conversation ID to reset")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class ResetConversationResponse(BaseModel):
    """Response model for reset conversation."""
    success: bool = Field(..., description="Whether reset was successful")
    message: str = Field(..., description="Status message")
    conversation_id: UUID = Field(..., description="Conversation ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Conversation reset successfully",
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class ClearMemoryRequest(BaseModel):
    """Request model for clearing memory."""
    conversation_id: UUID = Field(..., description="Conversation ID to clear memories for")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class ClearMemoryResponse(BaseModel):
    """Response model for clear memory."""
    success: bool = Field(..., description="Whether clear was successful")
    message: str = Field(..., description="Status message")
    conversation_id: UUID = Field(..., description="Conversation ID")
    memories_cleared: int = Field(..., description="Number of memories cleared")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Memories cleared successfully",
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "memories_cleared": 15
            }
        }


class ConversationInfo(BaseModel):
    """Information about a conversation."""
    id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ListConversationsResponse(BaseModel):
    """Response model for listing user conversations."""
    conversations: List[ConversationInfo]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversations": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "Chat about AI",
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T11:45:00",
                        "message_count": 12
                    }
                ],
                "total": 1
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    database: bool = Field(..., description="Database connection status")
    llm: bool = Field(..., description="LLM connection status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "database": True,
                "llm": True
            }
        }


class UserPreferencesRequest(BaseModel):
    """Request model for updating user preferences."""
    language: Optional[str] = Field(None, description="Preferred language (e.g., 'Spanish', 'French')")
    formality: Optional[str] = Field(None, description="Formality level: 'casual', 'formal', or 'professional'")
    tone: Optional[str] = Field(None, description="Tone: 'enthusiastic', 'calm', 'friendly', or 'neutral'")
    emoji_usage: Optional[bool] = Field(None, description="Whether to use emojis")
    response_length: Optional[str] = Field(None, description="Response length: 'brief', 'detailed', or 'balanced'")
    explanation_style: Optional[str] = Field(None, description="Explanation style: 'simple', 'technical', or 'analogies'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "language": "Spanish",
                "formality": "casual",
                "tone": "friendly",
                "emoji_usage": True,
                "response_length": "balanced",
                "explanation_style": "simple"
            }
        }


class UserPreferencesResponse(BaseModel):
    """Response model for user preferences."""
    preferences: Dict
    message: str = "Preferences retrieved successfully"
    
    class Config:
        json_schema_extra = {
            "example": {
                "preferences": {
                    "language": "Spanish",
                    "formality": "casual",
                    "tone": "friendly",
                    "emoji_usage": True,
                    "response_length": "balanced",
                    "explanation_style": "simple",
                    "last_updated": "2024-01-15T10:30:00"
                },
                "message": "Preferences retrieved successfully"
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid request",
                "detail": "Message cannot be empty"
            }
        }


# ========== Authentication & JWT Models ==========

class CreateTokenRequest(BaseModel):
    """Request model for creating JWT token."""
    user_id: str = Field(..., min_length=1, max_length=255, description="User identifier")
    expires_in_hours: Optional[int] = Field(
        default=None,
        ge=1,
        le=8760,  # Max 1 year
        description="Token expiration in hours (default: 24)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "alice123",
                "expires_in_hours": 24
            }
        }


class TokenResponse(BaseModel):
    """Response model for JWT token creation."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user_id: str = Field(..., description="User ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "user_id": "alice123"
            }
        }


class ValidateTokenRequest(BaseModel):
    """Request model for token validation."""
    token: str = Field(..., min_length=1, description="JWT token to validate")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class ValidateTokenResponse(BaseModel):
    """Response model for token validation."""
    valid: bool = Field(..., description="Whether token is valid")
    user_id: Optional[str] = Field(None, description="User ID if valid")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    error: Optional[str] = Field(None, description="Error message if invalid")
    
    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "user_id": "alice123",
                "expires_at": "2024-01-16T12:00:00Z",
                "error": None
            }
        }


# ========== Emotion Detection Models ==========

class EmotionEntry(BaseModel):
    """Single emotion detection entry."""
    emotion: str = Field(..., description="Detected emotion (e.g., happy, sad, angry)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence (0-1)")
    intensity: str = Field(..., description="Emotion intensity (low, medium, high)")
    indicators: List[str] = Field(default=[], description="Detection indicators (keyword, emoji, phrase)")
    message_snippet: Optional[str] = Field(None, description="First 100 chars of message")
    detected_at: str = Field(..., description="ISO timestamp when detected")
    conversation_id: Optional[str] = Field(None, description="Associated conversation ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "emotion": "happy",
                "confidence": 0.85,
                "intensity": "high",
                "indicators": ["emoji", "keyword"],
                "message_snippet": "I'm so excited about this! 😊",
                "detected_at": "2024-01-15T10:30:00",
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class EmotionHistoryResponse(BaseModel):
    """Response with user's emotion history."""
    emotions: List[EmotionEntry] = Field(..., description="List of detected emotions")
    total_count: int = Field(..., description="Total number of emotions")
    period_days: int = Field(..., description="Time period in days")
    message: str = Field(default="Emotion history retrieved successfully")
    
    class Config:
        json_schema_extra = {
            "example": {
                "emotions": [
                    {
                        "emotion": "happy",
                        "confidence": 0.85,
                        "intensity": "high",
                        "indicators": ["emoji", "keyword"],
                        "message_snippet": "I'm so excited!",
                        "detected_at": "2024-01-15T10:30:00",
                        "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                ],
                "total_count": 1,
                "period_days": 30,
                "message": "Emotion history retrieved successfully"
            }
        }


class EmotionStatistics(BaseModel):
    """Emotion statistics and trends."""
    total_emotions_detected: int = Field(..., description="Total emotions detected")
    period_days: int = Field(..., description="Analysis period in days")
    emotions: List[Dict] = Field(..., description="Emotion breakdown with counts and percentages")
    sentiment_breakdown: Dict = Field(..., description="Positive, negative, neutral sentiment counts")
    message: str = Field(default="Emotion statistics retrieved successfully")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_emotions_detected": 25,
                "period_days": 30,
                "emotions": [
                    {"emotion": "happy", "count": 10, "percentage": 40.0, "avg_confidence": 0.82},
                    {"emotion": "excited", "count": 8, "percentage": 32.0, "avg_confidence": 0.88}
                ],
                "sentiment_breakdown": {
                    "positive": {"count": 18, "percentage": 72.0},
                    "negative": {"count": 5, "percentage": 20.0},
                    "neutral": {"count": 2, "percentage": 8.0}
                },
                "message": "Emotion statistics retrieved successfully"
            }
        }


class EmotionTrendsResponse(BaseModel):
    """Emotion trend analysis."""
    dominant_emotion: Optional[str] = Field(None, description="Most frequent emotion")
    emotion_distribution: Dict[str, float] = Field(default={}, description="Emotion percentages")
    recent_trend: str = Field(..., description="Trend direction (improving, stable, declining)")
    needs_attention: bool = Field(default=False, description="Whether user may need support")
    message: str = Field(default="Emotion trends analyzed successfully")
    
    class Config:
        json_schema_extra = {
            "example": {
                "dominant_emotion": "happy",
                "emotion_distribution": {"happy": 0.6, "excited": 0.3, "grateful": 0.1},
                "recent_trend": "improving",
                "needs_attention": False,
                "message": "Emotion trends analyzed successfully"
            }
        }


class ClearEmotionHistoryResponse(BaseModel):
    """Response for clearing emotion history."""
    success: bool = Field(..., description="Whether clear was successful")
    message: str = Field(..., description="Status message")
    emotions_cleared: int = Field(..., description="Number of emotions cleared")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Emotion history cleared successfully",
                "emotions_cleared": 25
            }
        }


# ========== Personality System Models ==========

class PersonalityTraits(BaseModel):
    """Personality trait values (0-10 scales)."""
    humor_level: Optional[int] = Field(None, ge=0, le=10, description="0=serious, 10=very humorous")
    formality_level: Optional[int] = Field(None, ge=0, le=10, description="0=casual, 10=very formal")
    enthusiasm_level: Optional[int] = Field(None, ge=0, le=10, description="0=reserved, 10=very enthusiastic")
    empathy_level: Optional[int] = Field(None, ge=0, le=10, description="0=logical, 10=highly empathetic")
    directness_level: Optional[int] = Field(None, ge=0, le=10, description="0=indirect, 10=very direct")
    curiosity_level: Optional[int] = Field(None, ge=0, le=10, description="0=passive, 10=very curious")
    supportiveness_level: Optional[int] = Field(None, ge=0, le=10, description="0=challenging, 10=highly supportive")
    playfulness_level: Optional[int] = Field(None, ge=0, le=10, description="0=serious, 10=very playful")


class PersonalityBehaviors(BaseModel):
    """Personality behavior flags."""
    asks_questions: Optional[bool] = Field(None, description="Should AI ask questions?")
    uses_examples: Optional[bool] = Field(None, description="Should AI give examples?")
    shares_opinions: Optional[bool] = Field(None, description="Should AI share opinions?")
    challenges_user: Optional[bool] = Field(None, description="Should AI challenge/push user?")
    celebrates_wins: Optional[bool] = Field(None, description="Should AI celebrate achievements?")


class PersonalityCustomConfig(BaseModel):
    """Custom personality configuration."""
    backstory: Optional[str] = Field(None, max_length=1000, description="Optional backstory for AI")
    custom_instructions: Optional[str] = Field(None, max_length=2000, description="Custom behavior instructions")
    speaking_style: Optional[str] = Field(None, max_length=500, description="How AI should speak")


class CreatePersonalityRequest(BaseModel):
    """Request to create personality profile."""
    archetype: Optional[str] = Field(None, description="Predefined archetype (wise_mentor, supportive_friend, etc.)")
    relationship_type: Optional[str] = Field(None, description="Relationship type (friend, mentor, coach, etc.)")
    traits: Optional[PersonalityTraits] = Field(None, description="Personality trait values")
    behaviors: Optional[PersonalityBehaviors] = Field(None, description="Behavioral preferences")
    custom: Optional[PersonalityCustomConfig] = Field(None, description="Custom configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "archetype": "wise_mentor",
                "traits": {
                    "humor_level": 4,
                    "empathy_level": 8
                },
                "custom": {
                    "backstory": "You are a retired professor who loves teaching"
                }
            }
        }


class UpdatePersonalityRequest(BaseModel):
    """Request to update personality profile."""
    archetype: Optional[str] = Field(None, description="Change archetype")
    relationship_type: Optional[str] = Field(None, description="Change relationship type")
    traits: Optional[PersonalityTraits] = Field(None, description="Update traits")
    behaviors: Optional[PersonalityBehaviors] = Field(None, description="Update behaviors")
    custom: Optional[PersonalityCustomConfig] = Field(None, description="Update custom config")
    merge: bool = Field(True, description="Merge with existing (true) or replace (false)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "traits": {
                    "enthusiasm_level": 9
                },
                "merge": True
            }
        }


class PersonalityResponse(BaseModel):
    """Response with personality configuration."""
    archetype: Optional[str] = Field(None, description="Current archetype")
    relationship_type: Optional[str] = Field(None, description="Relationship type")
    traits: Dict[str, int] = Field(..., description="Personality traits")
    behaviors: Dict[str, bool] = Field(..., description="Behavioral preferences")
    custom: Dict[str, Optional[str]] = Field(..., description="Custom configuration")
    meta: Dict[str, Any] = Field(..., description="Metadata (version, timestamps)")
    message: str = Field(default="Personality retrieved successfully")
    
    class Config:
        json_schema_extra = {
            "example": {
                "archetype": "wise_mentor",
                "relationship_type": "mentor",
                "traits": {
                    "humor_level": 4,
                    "empathy_level": 8,
                    "directness_level": 7
                },
                "behaviors": {
                    "asks_questions": True,
                    "challenges_user": True
                },
                "custom": {
                    "backstory": "A retired professor",
                    "speaking_style": "Thoughtful and measured"
                },
                "meta": {
                    "version": 1,
                    "created_at": "2024-01-15T10:00:00"
                },
                "message": "Personality retrieved successfully"
            }
        }


class ArchetypeInfo(BaseModel):
    """Information about a personality archetype."""
    name: str = Field(..., description="Archetype identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Archetype description")
    relationship_type: str = Field(..., description="Default relationship type")
    example_greeting: str = Field(..., description="Example greeting")


class ListArchetypesResponse(BaseModel):
    """Response with available archetypes."""
    archetypes: List[ArchetypeInfo] = Field(..., description="Available personality archetypes")
    total: int = Field(..., description="Total number of archetypes")
    message: str = Field(default="Archetypes retrieved successfully")


class RelationshipStateResponse(BaseModel):
    """Response with relationship state metrics."""
    total_messages: int = Field(..., description="Total messages exchanged")
    relationship_depth_score: float = Field(..., ge=0, le=10, description="Relationship depth (0-10)")
    trust_level: float = Field(..., ge=0, le=10, description="Trust level (0-10)")
    days_known: int = Field(..., description="Days since first interaction")
    first_interaction: str = Field(..., description="ISO timestamp of first interaction")
    last_interaction: str = Field(..., description="ISO timestamp of last interaction")
    milestones: List[Dict] = Field(..., description="Relationship milestones reached")
    positive_reactions: int = Field(..., description="Number of positive reactions")
    negative_reactions: int = Field(..., description="Number of negative reactions")
    message: str = Field(default="Relationship state retrieved successfully")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_messages": 156,
                "relationship_depth_score": 6.8,
                "trust_level": 7.5,
                "days_known": 45,
                "first_interaction": "2024-01-01T10:00:00",
                "last_interaction": "2024-02-15T14:30:00",
                "milestones": [
                    {"type": "100_messages", "reached_at": "2024-02-10T12:00:00"}
                ],
                "positive_reactions": 12,
                "negative_reactions": 1,
                "message": "Relationship state retrieved successfully"
            }
        }


# =====================================================================
# GOALS & PROGRESS TRACKING MODELS
# =====================================================================

class GoalRequest(BaseModel):
    """Request to create a new goal."""
    title: str = Field(..., min_length=1, max_length=255, description="Goal title")
    description: Optional[str] = Field(None, description="Detailed description")
    category: str = Field(
        default='personal',
        description="Goal category: learning, health, career, financial, personal, creative, social"
    )
    target_date: Optional[str] = Field(None, description="Target date (ISO format)")
    motivation: Optional[str] = Field(None, description="Why you want to achieve this")
    check_in_frequency: Optional[str] = Field(
        default='weekly',
        description="How often to check in: daily, weekly, biweekly, monthly, never"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Learn Spanish",
                "description": "Become conversational in Spanish for my trip to Spain",
                "category": "learning",
                "target_date": "2025-12-31T00:00:00",
                "motivation": "I want to connect with locals and understand the culture",
                "check_in_frequency": "weekly"
            }
        }
    }


class UpdateGoalRequest(BaseModel):
    """Request to update an existing goal."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = Field(None, description="active, completed, paused, abandoned")
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    target_date: Optional[str] = None
    motivation: Optional[str] = None
    check_in_frequency: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "progress_percentage": 45.0,
                "status": "active"
            }
        }
    }


class ProgressUpdateRequest(BaseModel):
    """Request to manually log progress on a goal."""
    content: str = Field(..., description="Description of progress made")
    progress_type: str = Field(
        default='update',
        description="Type: mention, update, milestone, setback, completion"
    )
    progress_delta: Optional[float] = Field(
        None,
        description="Change in percentage (can be negative)"
    )
    sentiment: Optional[str] = Field(
        None,
        description="positive, negative, neutral"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "Completed 5 lessons today and practiced speaking for 30 minutes!",
                "progress_type": "update",
                "progress_delta": 10.0,
                "sentiment": "positive"
            }
        }
    }


class GoalResponse(BaseModel):
    """Goal response."""
    id: str
    title: str
    description: Optional[str]
    category: str
    status: str
    progress_percentage: float
    target_date: Optional[str]
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    last_mentioned_at: Optional[str]
    mention_count: int
    check_in_frequency: Optional[str]
    last_check_in: Optional[str]
    milestones: List[Dict]
    progress_notes: List[Dict]
    motivation: Optional[str]
    obstacles: List[str]
    message: str = "Goal retrieved successfully"
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Learn Spanish",
                "description": "Become conversational in Spanish",
                "category": "learning",
                "status": "active",
                "progress_percentage": 35.0,
                "target_date": "2025-12-31T00:00:00",
                "created_at": "2024-01-15T10:00:00",
                "updated_at": "2024-02-20T14:30:00",
                "completed_at": None,
                "last_mentioned_at": "2024-02-20T14:30:00",
                "mention_count": 12,
                "check_in_frequency": "weekly",
                "last_check_in": "2024-02-18T09:00:00",
                "milestones": [],
                "progress_notes": [
                    {
                        "date": "2024-02-20T14:30:00",
                        "observation": "User mentioned practicing daily",
                        "type": "update",
                        "sentiment": "positive"
                    }
                ],
                "motivation": "For my trip to Spain",
                "obstacles": [],
                "message": "Goal retrieved successfully"
            }
        }
    }


class GoalListResponse(BaseModel):
    """List of goals response."""
    goals: List[GoalResponse]
    total: int
    active: int
    completed: int
    message: str = "Goals retrieved successfully"


class ProgressEntryResponse(BaseModel):
    """Single progress entry."""
    id: str
    type: str
    content: str
    sentiment: Optional[str]
    emotion: Optional[str]
    progress_delta: Optional[float]
    created_at: str


class GoalProgressHistoryResponse(BaseModel):
    """Progress history for a goal."""
    goal_id: str
    entries: List[ProgressEntryResponse]
    total: int
    message: str = "Progress history retrieved successfully"


class GoalAnalyticsResponse(BaseModel):
    """Analytics about user's goals."""
    total_goals: int
    active_goals: int
    completed_goals: int
    paused_goals: int
    abandoned_goals: int
    completion_rate: float
    by_category: Dict[str, Dict]
    average_progress: float
    goals_with_deadlines: int
    overdue_goals: int
    recent_activity: List[Dict]
    message: str = "Analytics retrieved successfully"
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_goals": 10,
                "active_goals": 6,
                "completed_goals": 3,
                "paused_goals": 1,
                "abandoned_goals": 0,
                "completion_rate": 30.0,
                "by_category": {
                    "learning": {
                        "total": 4,
                        "active": 3,
                        "completed": 1
                    }
                },
                "average_progress": 42.5,
                "goals_with_deadlines": 5,
                "overdue_goals": 1,
                "recent_activity": [],
                "message": "Analytics retrieved successfully"
            }
        }
    }


class CheckinGoalsResponse(BaseModel):
    """Goals that need check-ins."""
    goals: List[GoalResponse]
    total: int
    message: str = "Check-in goals retrieved successfully"


class DeleteGoalResponse(BaseModel):
    """Goal deletion response."""
    success: bool = True
    message: str = "Goal deleted successfully"


# ==========================================
# Content Classification & Age Verification
# ==========================================

class AgeVerificationRequest(BaseModel):
    """Request model for age verification."""
    conversation_id: UUID = Field(..., description="Conversation ID")
    confirmed: bool = Field(..., description="User confirms they are 18+")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "confirmed": True
            }
        }


class AgeVerificationResponse(BaseModel):
    """Response model for age verification."""
    success: bool = True
    message: str = "Age verification updated"
    age_verified: bool


class ContentClassificationResponse(BaseModel):
    """Response model for content classification."""
    label: str = Field(..., description="Content label")
    confidence: float = Field(..., description="Classification confidence")
    indicators: List[str] = Field(default=[], description="Detection indicators")
    route: str = Field(..., description="Routing destination")
    
    class Config:
        json_schema_extra = {
            "example": {
                "label": "SAFE",
                "confidence": 0.95,
                "indicators": [],
                "route": "NORMAL"
            }
        }


class SessionStateResponse(BaseModel):
    """Response model for session state."""
    conversation_id: str
    age_verified: bool
    current_route: str
    route_locked: bool
    route_lock_message_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "age_verified": True,
                "current_route": "NORMAL",
                "route_locked": False,
                "route_lock_message_count": 0
            }
        }


class ContentAuditStatsResponse(BaseModel):
    """Response model for content audit statistics."""
    total_logs: int
    label_distribution: Dict[str, int]
    route_distribution: Dict[str, int]
    action_distribution: Dict[str, int]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_logs": 100,
                "label_distribution": {"SAFE": 80, "SUGGESTIVE": 15, "EXPLICIT_CONSENSUAL_ADULT": 5},
                "route_distribution": {"NORMAL": 80, "ROMANCE": 15, "EXPLICIT": 5},
                "action_distribution": {"generate": 95, "refuse": 3, "age_verify": 2}
            }
        }
