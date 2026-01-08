"""FastAPI route handlers."""

import json
import logging
from typing import AsyncIterator, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from uuid import UUID

from app.api.models import (
    ChatRequest, ChatResponse,
    ResetConversationRequest, ResetConversationResponse,
    ClearMemoryRequest, ClearMemoryResponse,
    ListConversationsResponse, ConversationInfo,
    UserPreferencesRequest, UserPreferencesResponse,
    EmotionHistoryResponse, EmotionStatistics, EmotionTrendsResponse,
    ClearEmotionHistoryResponse, EmotionEntry,
    CreatePersonalityRequest, UpdatePersonalityRequest, PersonalityResponse,
    ListArchetypesResponse, RelationshipStateResponse, ArchetypeInfo,
    GoalRequest, UpdateGoalRequest, ProgressUpdateRequest, GoalResponse,
    GoalListResponse, ProgressEntryResponse, GoalProgressHistoryResponse,
    GoalAnalyticsResponse, CheckinGoalsResponse, DeleteGoalResponse,
    AgeVerificationRequest, AgeVerificationResponse, ContentClassificationResponse,
    SessionStateResponse, ContentAuditStatsResponse,
    HealthResponse, ErrorResponse,
    CreateTokenRequest, TokenResponse, ValidateTokenRequest, ValidateTokenResponse
)
from app.services.chat_service import ChatService
from app.services.user_preference_service import UserPreferenceService
from app.services.emotion_service import EmotionService
from app.services.personality_service import PersonalityService
from app.services.personality_archetypes import list_archetypes, get_archetype_config
from app.core.dependencies import get_chat_service, get_preference_service, get_emotion_service, get_personality_service
from app.core.config import settings
from app.core.auth import (
    get_current_user_id, 
    verify_conversation_ownership,
    create_jwt_token,
    validate_jwt_token,
    decode_jwt_token
)
from app.core.database import engine, get_db
from app.utils.rate_limiter import limiter
from app.services.llm_client import LMStudioClient
from sqlalchemy.ext.asyncio import AsyncSession
import app

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/chat")
@limiter.limit(f"{settings.rate_limit_requests_per_minute}/minute")
async def chat_endpoint(
    request: Request,
    chat_request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream chat responses with memory integration and thinking steps.
    
    Requires authentication via X-User-Id, X-API-Key, or Authorization header.
    Accepts a user message and optional conversation ID.
    Returns a streaming response with Server-Sent Events.
    
    Event types:
    - thinking: Processing step with details
    - chunk: Response content chunk
    - done: Response complete
    - error: Error occurred
    """
    logger.info(f"Chat request: user={user_id}, conversation_id={chat_request.conversation_id}")
    
    # Verify conversation ownership if continuing existing conversation
    if chat_request.conversation_id:
        await verify_conversation_ownership(db, chat_request.conversation_id, user_id)
    
    async def generate_stream() -> AsyncIterator[str]:
        """Generate SSE stream with thinking steps and response chunks."""
        try:
            async for event in chat_service.stream_chat(
                user_message=chat_request.message,
                conversation_id=chat_request.conversation_id,
                user_id=user_id,
                db_session=db,
                system_prompt=chat_request.system_prompt  # Pass custom system prompt
            ):
                # Event is already a dictionary with type, data, etc.
                # Send as SSE
                data = json.dumps(event)
                yield f"data: {data}\n\n"
            
        except Exception as e:
            logger.error(f"Error in chat stream: {e}", exc_info=True)
            error_data = json.dumps({
                "type": "error",
                "error": "An error occurred during chat",
                "detail": str(e)
            })
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/conversation/reset", response_model=ResetConversationResponse)
async def reset_conversation_endpoint(
    reset_request: ResetConversationRequest,
    chat_service: ChatService = Depends(get_chat_service),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset a conversation (clear short-term memory, keep long-term).
    
    Requires authentication and conversation ownership.
    """
    try:
        # Verify ownership
        await verify_conversation_ownership(db, reset_request.conversation_id, user_id)
        
        await chat_service.reset_conversation(reset_request.conversation_id)
        
        return ResetConversationResponse(
            success=True,
            message="Conversation reset successfully",
            conversation_id=reset_request.conversation_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/clear", response_model=ClearMemoryResponse)
async def clear_memory_endpoint(
    clear_request: ClearMemoryRequest,
    chat_service: ChatService = Depends(get_chat_service),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Clear all memories (short and long-term) for a conversation.
    
    Requires authentication and conversation ownership.
    """
    try:
        # Verify ownership
        await verify_conversation_ownership(db, clear_request.conversation_id, user_id)
        
        # Get count before clearing
        await chat_service.clear_memories(clear_request.conversation_id)
        
        return ClearMemoryResponse(
            success=True,
            message="Memories cleared successfully",
            conversation_id=clear_request.conversation_id,
            memories_cleared=0  # Chat service doesn't return count currently
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    from sqlalchemy import text
    
    # Check database
    db_healthy = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_healthy = True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
    
    # Check LLM
    llm_healthy = False
    try:
        llm_client = LMStudioClient()
        llm_healthy = await llm_client.health_check()
    except Exception as e:
        logger.warning(f"LLM health check failed: {e}")
    
    status = "healthy" if (db_healthy and llm_healthy) else "degraded"
    
    return HealthResponse(
        status=status,
        version=app.__version__,
        database=db_healthy,
        llm=llm_healthy
    )


@router.get("/conversations", response_model=ListConversationsResponse)
async def list_conversations(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """
    List all conversations for the authenticated user.
    
    Returns conversations sorted by most recently updated.
    """
    from app.models.database import UserModel, ConversationModel, MessageModel
    from sqlalchemy import func, select
    
    try:
        # Get user
        user_result = await db.execute(
            select(UserModel).where(UserModel.external_user_id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            # Create user if doesn't exist
            from app.core.auth import ensure_user_exists
            user = await ensure_user_exists(db, user_id)
            await db.commit()
        
        # Query conversations with message count
        query = (
            select(
                ConversationModel,
                func.count(MessageModel.id).label('message_count')
            )
            .outerjoin(MessageModel, ConversationModel.id == MessageModel.conversation_id)
            .where(ConversationModel.user_id == user.id)
            .group_by(ConversationModel.id)
            .order_by(ConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        conversations = []
        for conv, msg_count in rows:
            conversations.append(ConversationInfo(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=msg_count
            ))
        
        # Get total count
        count_query = select(func.count(ConversationModel.id)).where(
            ConversationModel.user_id == user.id
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        return ListConversationsResponse(
            conversations=conversations,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_preferences(
    user_id: str = Depends(get_current_user_id),
    preference_service: UserPreferenceService = Depends(get_preference_service)
):
    """
    Get user's communication preferences.
    
    Returns the user's stored preferences for how they want the AI to communicate.
    """
    try:
        preferences = await preference_service.get_user_preferences(user_id)
        
        if not preferences:
            preferences = {}
        
        return UserPreferencesResponse(
            preferences=preferences,
            message="Preferences retrieved successfully" if preferences else "No preferences set"
        )
    except Exception as e:
        logger.error(f"Error getting preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    preferences_request: UserPreferencesRequest,
    user_id: str = Depends(get_current_user_id),
    preference_service: UserPreferenceService = Depends(get_preference_service)
):
    """
    Update user's communication preferences.
    
    Set how you want the AI to communicate with you. Changes take effect immediately.
    Can update individual preferences without affecting others.
    """
    try:
        # Convert request to dict, filtering out None values
        prefs_dict = {
            k: v for k, v in preferences_request.dict().items() 
            if v is not None
        }
        
        if not prefs_dict:
            raise HTTPException(status_code=400, detail="No preferences provided")
        
        updated_prefs = await preference_service.update_user_preferences(
            external_user_id=user_id,
            preferences=prefs_dict,
            merge=True
        )
        
        return UserPreferencesResponse(
            preferences=updated_prefs,
            message="Preferences updated successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/preferences")
async def clear_preferences(
    user_id: str = Depends(get_current_user_id),
    preference_service: UserPreferenceService = Depends(get_preference_service)
):
    """
    Clear all user preferences (reset to defaults).
    """
    try:
        await preference_service.clear_user_preferences(user_id)
        return {"success": True, "message": "Preferences cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== Emotion Detection Endpoints ==========

@router.get("/emotions/history", response_model=EmotionHistoryResponse)
async def get_emotion_history(
    user_id: str = Depends(get_current_user_id),
    emotion_service: EmotionService = Depends(get_emotion_service),
    limit: int = 20,
    days: int = 30
):
    """
    Get recent emotion detection history for the authenticated user.
    
    **Parameters:**
    - `limit`: Maximum number of emotions to return (default: 20, max: 100)
    - `days`: Look back this many days (default: 30)
    
    **Returns:**
    - List of detected emotions with confidence scores and timestamps
    """
    try:
        # Validate parameters
        limit = min(limit, 100)
        days = min(days, 365)
        
        emotions = await emotion_service.get_recent_emotions(
            user_id=UUID(user_id),
            limit=limit,
            days=days
        )
        
        # Convert to response model
        emotion_entries = [EmotionEntry(**e) for e in emotions]
        
        return EmotionHistoryResponse(
            emotions=emotion_entries,
            total_count=len(emotion_entries),
            period_days=days
        )
    except Exception as e:
        logger.error(f"Error fetching emotion history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emotions/statistics", response_model=EmotionStatistics)
async def get_emotion_statistics(
    user_id: str = Depends(get_current_user_id),
    emotion_service: EmotionService = Depends(get_emotion_service),
    days: int = 30
):
    """
    Get detailed emotion statistics and sentiment analysis.
    
    **Parameters:**
    - `days`: Analyze emotions from this many days back (default: 30)
    
    **Returns:**
    - Total counts, emotion breakdown, sentiment analysis (positive/negative/neutral)
    """
    try:
        days = min(days, 365)
        
        stats = await emotion_service.get_emotion_statistics(
            user_id=UUID(user_id),
            days=days
        )
        
        return EmotionStatistics(**stats)
    except Exception as e:
        logger.error(f"Error fetching emotion statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emotions/trends", response_model=EmotionTrendsResponse)
async def get_emotion_trends(
    user_id: str = Depends(get_current_user_id),
    emotion_service: EmotionService = Depends(get_emotion_service),
    days: int = 30
):
    """
    Analyze emotion trends and patterns.
    
    **Parameters:**
    - `days`: Analyze emotions from this many days back (default: 30)
    
    **Returns:**
    - Dominant emotion, trend direction (improving/stable/declining), attention flags
    """
    try:
        days = min(days, 365)
        
        trends = await emotion_service.get_emotion_trends(
            user_id=UUID(user_id),
            days=days
        )
        
        return EmotionTrendsResponse(**trends)
    except Exception as e:
        logger.error(f"Error analyzing emotion trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/emotions/history", response_model=ClearEmotionHistoryResponse)
async def clear_emotion_history(
    user_id: str = Depends(get_current_user_id),
    emotion_service: EmotionService = Depends(get_emotion_service),
    conversation_id: UUID = None
):
    """
    Clear emotion history for the authenticated user.
    
    **Parameters:**
    - `conversation_id`: (Optional) Clear emotions for specific conversation only
    
    **Returns:**
    - Success status and count of emotions cleared
    """
    try:
        cleared_count = await emotion_service.clear_emotion_history(
            user_id=UUID(user_id),
            conversation_id=conversation_id
        )
        
        return ClearEmotionHistoryResponse(
            success=True,
            message="Emotion history cleared successfully",
            emotions_cleared=cleared_count
        )
    except Exception as e:
        logger.error(f"Error clearing emotion history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== Personality System Endpoints ==========

@router.get("/personality/archetypes", response_model=ListArchetypesResponse)
async def get_archetypes():
    """
    List all available personality archetypes.
    
    **Returns:**
    - List of predefined personality archetypes with descriptions
    """
    try:
        archetypes_list = list_archetypes()
        archetype_info = [ArchetypeInfo(**arch) for arch in archetypes_list]
        
        return ListArchetypesResponse(
            archetypes=archetype_info,
            total=len(archetype_info)
        )
    except Exception as e:
        logger.error(f"Error listing archetypes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personality", response_model=PersonalityResponse)
async def get_personality(
    user_id: str = Depends(get_current_user_id),
    personality_service: PersonalityService = Depends(get_personality_service)
):
    """
    Get current AI personality configuration for the authenticated user.
    
    **Returns:**
    - Personality traits, behaviors, and custom configuration
    """
    try:
        personality = await personality_service.get_personality(UUID(user_id))
        
        if not personality:
            raise HTTPException(
                status_code=404,
                detail="No personality configured. Use POST /personality to create one."
            )
        
        return PersonalityResponse(**personality)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting personality: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personality", response_model=PersonalityResponse, status_code=201)
async def create_personality(
    request: CreatePersonalityRequest,
    user_id: str = Depends(get_current_user_id),
    personality_service: PersonalityService = Depends(get_personality_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Create AI personality configuration.
    
    **Options:**
    - Use a predefined `archetype` (wise_mentor, supportive_friend, etc.)
    - Customize individual `traits` (0-10 scales)
    - Set `behaviors` (True/False flags)
    - Add custom `backstory` or `instructions`
    
    **Examples:**
    ```json
    {
      "archetype": "wise_mentor"
    }
    ```
    
    ```json
    {
      "traits": {
        "humor_level": 8,
        "empathy_level": 9
      },
      "behaviors": {
        "asks_questions": true,
        "celebrates_wins": true
      }
    }
    ```
    """
    try:
        # Get database UUID for user
        from app.core.auth import get_user_db_id
        user_db_id = await get_user_db_id(db, user_id)
        
        if not user_db_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Convert request to service format
        traits_dict = request.traits.dict(exclude_none=True) if request.traits else None
        behaviors_dict = request.behaviors.dict(exclude_none=True) if request.behaviors else None
        custom_dict = request.custom.dict(exclude_none=True) if request.custom else None
        
        if custom_dict and 'relationship_type' not in custom_dict and request.relationship_type:
            custom_dict = custom_dict or {}
            custom_dict['relationship_type'] = request.relationship_type
        
        personality = await personality_service.create_personality(
            user_id=user_db_id,
            archetype=request.archetype,
            traits=traits_dict,
            behaviors=behaviors_dict,
            custom_config=custom_dict
        )
        
        return PersonalityResponse(**personality, message="Personality created successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating personality: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/personality", response_model=PersonalityResponse)
async def update_personality(
    request: UpdatePersonalityRequest,
    user_id: str = Depends(get_current_user_id),
    personality_service: PersonalityService = Depends(get_personality_service)
):
    """
    Update AI personality configuration.
    
    **Parameters:**
    - `merge`: If true (default), merge with existing config. If false, replace completely.
    
    **Examples:**
    ```json
    {
      "traits": {
        "enthusiasm_level": 9
      },
      "merge": true
    }
    ```
    
    ```json
    {
      "archetype": "professional_coach",
      "merge": false
    }
    ```
    """
    try:
        traits_dict = request.traits.dict(exclude_none=True) if request.traits else None
        behaviors_dict = request.behaviors.dict(exclude_none=True) if request.behaviors else None
        custom_dict = request.custom.dict(exclude_none=True) if request.custom else None
        
        if custom_dict and 'relationship_type' not in custom_dict and request.relationship_type:
            custom_dict = custom_dict or {}
            custom_dict['relationship_type'] = request.relationship_type
        
        personality = await personality_service.update_personality(
            user_id=UUID(user_id),
            archetype=request.archetype,
            traits=traits_dict,
            behaviors=behaviors_dict,
            custom_config=custom_dict,
            merge=request.merge
        )
        
        return PersonalityResponse(**personality, message="Personality updated successfully")
    except Exception as e:
        logger.error(f"Error updating personality: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/personality")
async def delete_personality(
    user_id: str = Depends(get_current_user_id),
    personality_service: PersonalityService = Depends(get_personality_service)
):
    """
    Delete AI personality configuration (reset to default).
    
    **Returns:**
    - Success status
    """
    try:
        deleted = await personality_service.delete_personality(UUID(user_id))
        
        if not deleted:
            raise HTTPException(status_code=404, detail="No personality to delete")
        
        return {
            "success": True,
            "message": "Personality deleted successfully (reset to default)"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting personality: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personality/relationship", response_model=RelationshipStateResponse)
async def get_relationship_state(
    user_id: str = Depends(get_current_user_id),
    personality_service: PersonalityService = Depends(get_personality_service)
):
    """
    Get relationship state metrics.
    
    **Returns:**
    - Total messages, relationship depth score, trust level
    - Days known, milestones reached
    - Positive/negative reaction counts
    """
    try:
        state = await personality_service.get_relationship_state(UUID(user_id))
        return RelationshipStateResponse(**state)
    except Exception as e:
        logger.error(f"Error getting relationship state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "AI Companion Service",
        "version": app.__version__,
        "features": {
            "multi_user": True,
            "adaptive_communication": True,
            "preference_learning": True,
            "emotion_detection": True,
            "personality_system": True,
            "goals_tracking": True
        },
        "docs": "/docs",
        "health": "/health",
        "authentication": "Required (X-User-Id, X-API-Key, or Authorization header)"
    }


# =====================================================================
# AUTHENTICATION ENDPOINTS
# =====================================================================

@router.post("/auth/token", response_model=TokenResponse, tags=["authentication"])
async def create_token(
    request: CreateTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a JWT access token for a user.
    
    This endpoint generates a JWT token that can be used for authentication.
    Use the token in the Authorization header: `Bearer <token>`
    
    **Note:** In production, this endpoint should be protected and only accessible
    after proper user authentication (e.g., login with username/password, OAuth, etc.)
    """
    try:
        # Ensure user exists in database
        from app.core.auth import ensure_user_exists
        await ensure_user_exists(db, request.user_id)
        await db.commit()
        
        # Create JWT token
        expires_hours = request.expires_in_hours or settings.jwt_expiration_hours
        token = create_jwt_token(
            user_id=request.user_id,
            expires_in_hours=expires_hours
        )
        
        logger.info(f"Created JWT token for user: {request.user_id}")
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_hours * 3600,  # Convert to seconds
            user_id=request.user_id
        )
        
    except Exception as e:
        logger.error(f"Failed to create token: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create token: {str(e)}"
        )


@router.post("/auth/validate", response_model=ValidateTokenResponse, tags=["authentication"])
async def validate_token(request: ValidateTokenRequest):
    """
    Validate a JWT access token.
    
    Checks if a token is valid, not expired, and properly signed.
    Returns user information if valid.
    """
    try:
        # Validate token
        user_id = validate_jwt_token(request.token)
        
        if user_id:
            # Token is valid, get expiration info
            payload = decode_jwt_token(request.token)
            expires_at = None
            if payload and "exp" in payload:
                from datetime import datetime
                expires_at = datetime.fromtimestamp(payload["exp"])
            
            return ValidateTokenResponse(
                valid=True,
                user_id=user_id,
                expires_at=expires_at,
                error=None
            )
        else:
            return ValidateTokenResponse(
                valid=False,
                user_id=None,
                expires_at=None,
                error="Invalid or expired token"
            )
            
    except Exception as e:
        logger.error(f"Token validation error: {e}", exc_info=True)
        return ValidateTokenResponse(
            valid=False,
            user_id=None,
            expires_at=None,
            error=str(e)
        )


# =====================================================================
# GOALS & PROGRESS TRACKING ENDPOINTS
# =====================================================================

@router.post("/goals", response_model=GoalResponse, status_code=201)
@limiter.limit("50/minute")
async def create_goal(
    request: Request,
    goal_request: GoalRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new goal.
    
    - **title**: Goal title (required)
    - **description**: Detailed description
    - **category**: learning, health, career, financial, personal, creative, social
    - **target_date**: Optional deadline
    - **motivation**: Why you want to achieve this
    - **check_in_frequency**: How often to check in (daily, weekly, biweekly, monthly, never)
    """
    from app.services.goal_service import GoalService
    from datetime import datetime
    from uuid import UUID
    
    goal_service = GoalService(db)
    
    # Parse target date if provided
    target_date = None
    if goal_request.target_date:
        try:
            target_date = datetime.fromisoformat(goal_request.target_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid target_date format. Use ISO format.")
    
    goal = await goal_service.create_goal(
        user_id=UUID(user_id),
        title=goal_request.title,
        category=goal_request.category,
        description=goal_request.description,
        target_date=target_date,
        motivation=goal_request.motivation,
        check_in_frequency=goal_request.check_in_frequency
    )
    
    return GoalResponse(**goal)


@router.get("/goals", response_model=GoalListResponse)
@limiter.limit("100/minute")
async def get_goals(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status: active, completed, paused, abandoned"),
    category: Optional[str] = Query(None, description="Filter by category"),
    include_completed: bool = Query(False, description="Include completed goals"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's goals with optional filtering.
    
    - **status**: Filter by status
    - **category**: Filter by category
    - **include_completed**: Include completed goals
    """
    from app.services.goal_service import GoalService
    from uuid import UUID
    
    goal_service = GoalService(db)
    
    goals = await goal_service.get_user_goals(
        user_id=UUID(user_id),
        status=status,
        category=category,
        include_completed=include_completed
    )
    
    active_count = len([g for g in goals if g['status'] == 'active'])
    completed_count = len([g for g in goals if g['status'] == 'completed'])
    
    return GoalListResponse(
        goals=[GoalResponse(**g) for g in goals],
        total=len(goals),
        active=active_count,
        completed=completed_count
    )


@router.get("/goals/{goal_id}", response_model=GoalResponse)
@limiter.limit("100/minute")
async def get_goal(
    request: Request,
    goal_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific goal by ID."""
    from app.services.goal_service import GoalService
    from uuid import UUID
    
    goal_service = GoalService(db)
    
    try:
        goal = await goal_service.get_goal(UUID(goal_id), UUID(user_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid goal ID format")
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return GoalResponse(**goal)


@router.put("/goals/{goal_id}", response_model=GoalResponse)
@limiter.limit("50/minute")
async def update_goal(
    request: Request,
    goal_id: str,
    update_request: UpdateGoalRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a goal.
    
    Can update: title, description, category, status, progress_percentage,
    target_date, motivation, check_in_frequency
    """
    from app.services.goal_service import GoalService
    from uuid import UUID
    from datetime import datetime
    
    goal_service = GoalService(db)
    
    # Prepare updates
    updates = update_request.model_dump(exclude_none=True)
    
    # Parse target_date if provided
    if 'target_date' in updates and updates['target_date']:
        try:
            updates['target_date'] = datetime.fromisoformat(updates['target_date'].replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid target_date format")
    
    try:
        goal = await goal_service.update_goal(UUID(goal_id), UUID(user_id), **updates)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid goal ID format")
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return GoalResponse(**goal)


@router.delete("/goals/{goal_id}", response_model=DeleteGoalResponse)
@limiter.limit("50/minute")
async def delete_goal(
    request: Request,
    goal_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a goal (sets status to 'abandoned')."""
    from app.services.goal_service import GoalService
    from uuid import UUID
    
    goal_service = GoalService(db)
    
    try:
        goal = await goal_service.update_goal(
            UUID(goal_id),
            UUID(user_id),
            status='abandoned'
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid goal ID format")
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return DeleteGoalResponse()


@router.post("/goals/{goal_id}/progress", response_model=ProgressEntryResponse)
@limiter.limit("100/minute")
async def log_progress(
    request: Request,
    goal_id: str,
    progress_request: ProgressUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually log progress on a goal.
    
    - **content**: Description of what was done
    - **progress_type**: mention, update, milestone, setback, completion
    - **progress_delta**: Change in percentage (e.g., +10.0 or -5.0)
    - **sentiment**: positive, negative, neutral
    """
    from app.services.goal_service import GoalService
    from uuid import UUID
    
    goal_service = GoalService(db)
    
    try:
        progress = await goal_service.record_progress(
            goal_id=UUID(goal_id),
            user_id=UUID(user_id),
            content=progress_request.content,
            progress_type=progress_request.progress_type,
            progress_delta=progress_request.progress_delta,
            sentiment=progress_request.sentiment,
            detected_automatically=False
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid goal ID format")
    
    return ProgressEntryResponse(**progress)


@router.get("/goals/{goal_id}/progress", response_model=GoalProgressHistoryResponse)
@limiter.limit("100/minute")
async def get_goal_progress_history(
    request: Request,
    goal_id: str,
    limit: int = Query(50, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get progress history for a specific goal."""
    from app.services.goal_service import GoalService
    from uuid import UUID
    
    goal_service = GoalService(db)
    
    try:
        entries = await goal_service.get_goal_progress_history(
            UUID(goal_id),
            UUID(user_id),
            limit=limit
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid goal ID format")
    
    return GoalProgressHistoryResponse(
        goal_id=goal_id,
        entries=[ProgressEntryResponse(**e) for e in entries],
        total=len(entries)
    )


@router.get("/goals/analytics/summary", response_model=GoalAnalyticsResponse)
@limiter.limit("50/minute")
async def get_goal_analytics(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive analytics about user's goals.
    
    Includes:
    - Total, active, completed goals
    - Completion rate
    - Breakdown by category
    - Average progress
    - Deadline tracking
    - Recent activity
    """
    from app.services.goal_service import GoalService
    from uuid import UUID
    
    goal_service = GoalService(db)
    
    analytics = await goal_service.get_goal_analytics(UUID(user_id))
    
    return GoalAnalyticsResponse(**analytics)


@router.get("/goals/checkin/needed", response_model=CheckinGoalsResponse)
@limiter.limit("50/minute")
async def get_goals_needing_checkin(
    request: Request,
    days: int = Query(7, ge=1, le=30, description="Days since last check-in"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get goals that need a check-in.
    
    Returns goals that haven't been checked on in the specified number of days.
    """
    from app.services.goal_service import GoalService
    from uuid import UUID
    
    goal_service = GoalService(db)
    
    goals = await goal_service.get_goals_needing_checkin(
        UUID(user_id),
        days_since_last=days
    )
    
    return CheckinGoalsResponse(
        goals=[GoalResponse(**g) for g in goals],
        total=len(goals)
    )


# ==========================================
# Content Classification & Age Verification
# ==========================================

@router.post("/content/age-verify", response_model=AgeVerificationResponse)
@limiter.limit("20/minute")
async def verify_age(
    request: Request,
    age_request: AgeVerificationRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify user's age for explicit content access.
    
    This endpoint allows users to confirm they are 18+ years old,
    which is required for accessing explicit content routes.
    """
    from app.services.session_manager import get_session_manager
    
    # Verify conversation ownership
    await verify_conversation_ownership(db, age_request.conversation_id, user_id)
    
    session_manager = get_session_manager()
    
    if age_request.confirmed:
        session_manager.verify_age(age_request.conversation_id)
        logger.info(f"Age verified for conversation {age_request.conversation_id}")
        
        return AgeVerificationResponse(
            success=True,
            message="Age verified successfully",
            age_verified=True
        )
    else:
        logger.info(f"Age verification declined for conversation {age_request.conversation_id}")
        
        return AgeVerificationResponse(
            success=True,
            message="Age verification declined",
            age_verified=False
        )


@router.get("/content/session/{conversation_id}", response_model=SessionStateResponse)
@limiter.limit("50/minute")
async def get_session_state(
    request: Request,
    conversation_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current session state for a conversation.
    
    Returns information about age verification, current route, and lock status.
    """
    from app.services.session_manager import get_session_manager
    
    # Verify conversation ownership
    await verify_conversation_ownership(db, conversation_id, user_id)
    
    session_manager = get_session_manager()
    
    # Get user DB ID
    from app.core.auth import get_or_create_user_db_id
    user_db_id = await get_or_create_user_db_id(db, user_id, auto_create=False)
    
    if not user_db_id:
        raise HTTPException(status_code=404, detail="User not found")
    
    session = session_manager.get_session(conversation_id, user_db_id)
    
    return SessionStateResponse(
        conversation_id=str(conversation_id),
        age_verified=session.age_verified,
        current_route=session.current_route.value,
        route_locked=session_manager.is_route_locked(conversation_id),
        route_lock_message_count=session.route_lock_message_count
    )


@router.post("/content/classify", response_model=ContentClassificationResponse)
@limiter.limit("50/minute")
async def classify_content(
    request: Request,
    chat_request: ChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Classify content without generating a response.
    
    Useful for testing the content classification system or
    pre-checking content before sending.
    """
    from app.services.content_classifier import get_content_classifier
    from app.services.content_router import get_content_router
    
    classifier = get_content_classifier()
    router = get_content_router()
    
    classification = classifier.classify(chat_request.message)
    route = router.route(classification)
    
    return ContentClassificationResponse(
        label=classification.label.value,
        confidence=classification.confidence,
        indicators=classification.indicators[:5],
        route=route.value
    )


@router.get("/content/audit/stats", response_model=ContentAuditStatsResponse)
@limiter.limit("20/minute")
async def get_audit_stats(
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get content audit statistics.
    
    Returns aggregated statistics about content classification and routing.
    Requires authentication.
    """
    from app.services.content_audit_logger import get_audit_logger
    
    audit_logger = get_audit_logger()
    stats = audit_logger.get_stats()
    
    return ContentAuditStatsResponse(**stats)


@router.post("/content/session/{conversation_id}/clear")
@limiter.limit("20/minute")
async def clear_session(
    request: Request,
    conversation_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Clear session state for a conversation.
    
    Resets age verification and route lock status.
    """
    from app.services.session_manager import get_session_manager
    
    # Verify conversation ownership
    await verify_conversation_ownership(db, conversation_id, user_id)
    
    session_manager = get_session_manager()
    session_manager.clear_session(conversation_id)
    
    logger.info(f"Cleared session for conversation {conversation_id}")
    
    return {"success": True, "message": "Session cleared successfully"}

