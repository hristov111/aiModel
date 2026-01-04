"""Main chat service orchestrating all components."""

from typing import AsyncIterator, Optional, Dict, Any
from uuid import UUID, uuid4
import logging
import asyncio
import re
from datetime import datetime

from app.models.memory import Message
from app.services.short_term_memory import ConversationBuffer
from app.services.long_term_memory import LongTermMemoryService
from app.services.prompt_builder import PromptBuilder
from app.services.llm_client import LLMClient, get_llm_client, OpenAIClient
from app.services.user_preference_service import UserPreferenceService
from app.services.emotion_service import EmotionService
from app.services.personality_service import PersonalityService
from app.services.personality_detector import PersonalityDetector
from app.services.content_filter import get_content_filter
from app.services.content_classifier import get_content_classifier, ContentLabel, ClassificationResult
from app.services.content_router import get_content_router, ModelRoute
from app.services.session_manager import get_session_manager
from app.services.content_audit_logger import get_audit_logger
from app.core.exceptions import LLMConnectionError, LLMResponseError
from app.core.config import settings
from app.utils.journey_logger import JourneyLogger

logger = logging.getLogger(__name__)


class ChatService:
    """Main orchestrator for chat operations with memory integration."""
    
    def __init__(
        self,
        conversation_buffer: ConversationBuffer,
        long_term_memory: LongTermMemoryService,
        prompt_builder: PromptBuilder,
        llm_client: LLMClient,
        preference_service: Optional[UserPreferenceService] = None,
        emotion_service: Optional[EmotionService] = None,
        personality_service: Optional[PersonalityService] = None,
        goal_service = None
    ):
        """
        Initialize chat service.
        
        Args:
            conversation_buffer: Short-term memory buffer
            long_term_memory: Long-term memory service
            prompt_builder: Prompt builder
            llm_client: LLM client
            preference_service: User preference service (optional)
            emotion_service: Emotion detection service (optional)
            personality_service: Personality service (optional)
            goal_service: Goal tracking service (optional)
        """
        self.conversation_buffer = conversation_buffer
        self.long_term_memory = long_term_memory
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client
        self.preference_service = preference_service
        self.emotion_service = emotion_service
        self.personality_service = personality_service
        self.personality_detector = PersonalityDetector(llm_client=llm_client) if personality_service else None
        self.goal_service = goal_service
    
    async def stream_chat(
        self,
        user_message: str,
        conversation_id: UUID = None,
        user_id: str = None,
        db_session = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process chat message and stream response with thinking steps.
        
        Args:
            user_message: User's message
            conversation_id: Optional conversation ID (creates new if None)
            user_id: External user ID for memory isolation
            db_session: Database session for UUID lookup
            
        Yields:
            Dictionaries with event type and data:
            - {"type": "thinking", "step": "...", "data": {...}, "conversation_id": "..."}
            - {"type": "chunk", "chunk": "...", "conversation_id": "..."}
            - {"type": "done", "conversation_id": "..."}
        """
        # Create journey logger for detailed tracking
        request_id = str(uuid4())
        journey = JourneyLogger(request_id, user_id or "anonymous")
        journey.log_start(user_message)
        
        # Create conversation ID if not provided
        if conversation_id is None:
            conversation_id = uuid4()
            logger.info(f"Created new conversation: {conversation_id} for user: {user_id}")
            journey.log_conversation_created(str(conversation_id))
        
        # Try to get or create database UUID for user
        user_db_id = None
        if user_id and db_session:
            try:
                from app.core.auth import get_or_create_user_db_id
                user_db_id = await get_or_create_user_db_id(db_session, user_id, auto_create=True)
                if user_db_id:
                    logger.info(f"Resolved user {user_id} to database UUID: {user_db_id}")
                    journey.log_user_resolved(str(user_db_id))
            except Exception as e:
                logger.debug(f"Could not resolve/create user DB ID: {e}")
                journey.log_step("USER_RESOLUTION_FAILED", "Could not resolve/create user DB ID", level="DEBUG")
        
        # Create conversation record in database if user is registered
        if user_db_id and db_session:
            try:
                from app.models.database import ConversationModel
                from sqlalchemy import select
                
                # Check if conversation already exists
                result = await db_session.execute(
                    select(ConversationModel).where(ConversationModel.id == conversation_id)
                )
                existing_conv = result.scalar_one_or_none()
                
                if not existing_conv:
                    # Create new conversation record
                    conversation = ConversationModel(
                        id=conversation_id,
                        user_id=user_db_id
                    )
                    db_session.add(conversation)
                    await db_session.commit()
                    logger.info(f"Created conversation record in database: {conversation_id}")
            except Exception as e:
                logger.warning(f"Could not create conversation in database: {e}")
                # Continue anyway - conversation will work in-memory
        
        try:
            # Emit processing start
            yield {
                "type": "thinking",
                "step": "processing_start",
                "data": {"message": "Processing your message..."},
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Step 1: Add user message to short-term memory
            self.conversation_buffer.add_message(
                conversation_id=conversation_id,
                role="user",
                content=user_message
            )
            
            yield {
                "type": "thinking",
                "step": "message_stored",
                "data": {"message": "Message received and stored"},
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Step 2: Auto-detect and update preferences if present
            preferences_updated = False
            updated_prefs = None
            if self.preference_service and user_id and user_db_id:  # Only if user exists
                journey.log_step("PREFERENCES_CHECK", "Checking user preferences...")
                yield {
                    "type": "thinking",
                    "step": "checking_preferences",
                    "data": {"message": "Analyzing communication preferences..."},
                    "conversation_id": str(conversation_id),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                try:
                    # Extract and update preferences (returns None if no preferences detected)
                    updated_prefs = await self.preference_service.extract_and_update_preferences(
                        external_user_id=user_id,
                        message_content=user_message
                    )
                    
                    # Commit if preferences were actually detected and updated
                    if updated_prefs:
                        try:
                            await db_session.commit()
                            preferences_updated = True
                            logger.info(f"Preferences updated and committed for {user_id}: {updated_prefs}")
                        except Exception as e:
                            logger.warning(f"Failed to commit preferences: {e}")
                            await db_session.rollback()
                except Exception as e:
                    logger.warning(f"Could not update preferences for {user_id}: {e}")
                
                if preferences_updated:
                    yield {
                        "type": "thinking",
                        "step": "preferences_updated",
                        "data": {
                            "message": "Communication preferences updated",
                            "preferences": updated_prefs
                        },
                        "conversation_id": str(conversation_id),
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
            # ==========================================
            # OPTIMIZED: PARALLEL DETECTION
            # ==========================================
            
            yield {
                "type": "thinking",
                "step": "analyzing",
                "data": {"message": "Analyzing message (parallel detection)..."},
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Prepare context once for all detections
            recent_messages_context = self.conversation_buffer.get_recent_messages(conversation_id)
            context_for_detection = [msg.content for msg in recent_messages_context[-3:]]
            
            # ==========================================
            # PARALLEL TASK 1: Personality Detection
            # ==========================================
            async def detect_personality():
                """Detect personality preferences in parallel."""
                if not (self.personality_service and self.personality_detector and user_db_id):
                    logger.info(f"Personality detection failed: {self.personality_service and self.personality_detector and user_db_id}")
                    return None
                    
                try:
                    personality_config_detected = await self.personality_detector.detect(
                        user_message,
                        context=context_for_detection if context_for_detection else None
                    )
                    
                    if personality_config_detected:
                        logger.info(f"Personality detection successful: {personality_config_detected}")
                        await self.personality_service.update_personality(
                            user_id=user_db_id,
                            archetype=personality_config_detected.get('archetype'),
                            traits=personality_config_detected.get('traits'),
                            behaviors=personality_config_detected.get('behaviors'),
                            custom_config={'custom_instructions': personality_config_detected.get('custom_instructions')} 
                                if personality_config_detected.get('custom_instructions') else None,
                            merge=True
                        )
                        logger.info(f"Auto-updated personality for user {user_id}")
                        return personality_config_detected
                    return None
                except Exception as e:
                    logger.warning(f"Personality detection failed: {e}")
                    return None
            
            # ==========================================
            # PARALLEL TASK 2: Emotion Detection
            # ==========================================
            async def detect_emotion():
                """Detect emotion in parallel."""
                if not (self.emotion_service and user_db_id):
                    return None
                    
                try:
                    context_messages = [msg.content for msg in recent_messages_context[-3:] if msg.role == "user"]
                    emotion = await self.emotion_service.detect_and_store(
                        user_id=user_db_id,
                        message=user_message,
                        conversation_id=conversation_id,
                        context=context_messages if context_messages else None
                    )
                    
                    if emotion:
                        logger.info(f"Detected emotion: {emotion.emotion} ({emotion.confidence:.2f})")
                        return {
                            'emotion': emotion.emotion,
                            'confidence': emotion.confidence,
                            'intensity': emotion.intensity
                        }
                    return None
                except Exception as e:
                    logger.warning(f"Emotion detection failed: {e}")
                    return None
            
            # ==========================================
            # PARALLEL TASK 3: Load Personality Config
            # ==========================================
            async def load_personality():
                """Load existing personality config in parallel."""
                if not (self.personality_service and user_db_id):
                    return None, None
                    
                try:
                    personality_config = await self.personality_service.get_personality(user_db_id)
                    relationship_state = await self.personality_service.get_relationship_state(user_db_id)
                    
                    # Update relationship metrics
                    await self.personality_service.update_relationship_metrics(
                        user_id=user_db_id,
                        message_sent=True
                    )
                    return personality_config, relationship_state
                except Exception as e:
                    logger.warning(f"Could not load personality: {e}")
                    return None, None
            
            # ==========================================
            # PARALLEL TASK 4: Load User Preferences
            # ==========================================
            async def load_preferences():
                """Load user preferences in parallel."""
                if not (self.preference_service and user_id):
                    return None
                    
                try:
                    return await self.preference_service.get_user_preferences(user_id)
                except Exception as e:
                    logger.warning(f"Could not load preferences: {e}")
                    return None

            # ==========================================
            # PARALLEL TASK 5: Load Active Goals
            # ==========================================
            async def load_goals():
                """Load user's active goals in parallel (fast DB read, no LLM)."""
                if not (self.goal_service and user_db_id):
                    return None
                try:
                    active_goals = await self.goal_service.get_user_goals(
                        user_id=user_db_id,
                        include_completed=False
                    )
                    return {"active_goals": active_goals}
                except Exception as e:
                    logger.warning(f"Could not load goals: {e}")
                    return None
            
            # ==========================================
            # RUN ALL DETECTIONS IN PARALLEL
            # ==========================================
            logger.info("Running parallel detections...")
            
            # Execute all tasks simultaneously
            (
                personality_config_detected,
                detected_emotion,
                (personality_config, relationship_state),
                user_preferences,
                goal_context
            ) = await asyncio.gather(
                detect_personality(),
                detect_emotion(),
                load_personality(),
                load_preferences(),
                load_goals(),
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(personality_config_detected, Exception):
                logger.warning(f"Personality detection error: {personality_config_detected}")
                personality_config_detected = None
            if isinstance(detected_emotion, Exception):
                logger.warning(f"Emotion detection error: {detected_emotion}")
                detected_emotion = None
            if isinstance(personality_config, Exception) or isinstance(relationship_state, Exception):
                logger.warning(f"Personality load error")
                personality_config, relationship_state = None, None
            if isinstance(user_preferences, Exception):
                logger.warning(f"Preferences load error: {user_preferences}")
                user_preferences = None
            if isinstance(goal_context, Exception):
                logger.warning(f"Goals load error: {goal_context}")
                goal_context = None
            
            logger.info("Parallel detections completed")
            
            # ==========================================
            # FIX: Use detected personality immediately
            # ==========================================
            # If personality was just detected, use it instead of loaded
            # (prevents race condition where old personality is used for current response)
            final_personality_config = personality_config_detected or personality_config
            
            # ==========================================
            # EMIT DETECTION RESULTS
            # ==========================================
            
            # Emit personality detection result
            if personality_config_detected:
                yield {
                    "type": "thinking",
                    "step": "personality_detected",
                    "data": {
                        "message": "Updated personality preferences",
                        "archetype": personality_config_detected.get('archetype'),
                        "traits": personality_config_detected.get('traits', {})
                    },
                    "conversation_id": str(conversation_id),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Emit personality config (use final personality)
            if final_personality_config:
                yield {
                    "type": "thinking",
                    "step": "personality_loaded",
                    "data": {
                        "message": "Applied personality configuration",
                        "archetype": final_personality_config.get('archetype'),
                        "relationship_depth": relationship_state.get('relationship_depth_score', 0) if relationship_state else 0,
                        "traits": final_personality_config.get('traits', {})
                    },
                    "conversation_id": str(conversation_id),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Emit emotion detection result
            if detected_emotion:
                yield {
                    "type": "thinking",
                    "step": "emotion_detected",
                    "data": {
                        "message": f"Detected emotion: {detected_emotion['emotion']}",
                        "emotion": detected_emotion['emotion'],
                        "confidence": round(detected_emotion['confidence'], 2),
                        "intensity": detected_emotion['intensity']
                    },
                    "conversation_id": str(conversation_id),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Get emotion trends for context
            emotion_context = None
            if detected_emotion and self.emotion_service and user_db_id:
                try:
                    emotion_context = await self.emotion_service.get_emotion_trends(
                        user_id=user_db_id,
                        days=30
                    )
                except Exception as e:
                    logger.warning(f"Could not get emotion trends: {e}")
            
            # Note: Goal *tracking* (detecting/recording new goal events) runs in background,
            # but we still load active goals above for prompt context injection.
            
            # Step 7: Retrieve relevant long-term memories
            yield {
                "type": "thinking",
                "step": "retrieving_memories",
                "data": {"message": "Searching long-term memories..."},
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            journey.log_memory_retrieval_start(user_message)
            relevant_memories = await self.long_term_memory.retrieve_relevant_memories(
                conversation_id=conversation_id,
                query_text=user_message
            )
            logger.debug(f"Retrieved {len(relevant_memories)} relevant memories")
            journey.log_memory_retrieved(len(relevant_memories), settings.long_term_memory_top_k)
            
            # Emit memory retrieval
            memory_preview = []
            for m in relevant_memories[:3]:
                memory_preview.append({
                    "content": m.content[:80] + "..." if len(m.content) > 80 else m.content,
                    "type": m.memory_type.value if hasattr(m.memory_type, 'value') else str(m.memory_type),
                    "importance": round(m.importance, 2)
                })
            
            yield {
                "type": "thinking",
                "step": "memories_retrieved",
                "data": {
                    "message": f"Found {len(relevant_memories)} relevant memories",
                    "count": len(relevant_memories),
                    "memories": memory_preview
                },
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Step 8: Get recent conversation history and summary
            recent_messages = self.conversation_buffer.get_recent_messages(conversation_id)
            conversation_summary = self.conversation_buffer.get_or_create_summary(conversation_id)
            
            yield {
                "type": "thinking",
                "step": "building_context",
                "data": {
                    "message": "Assembling conversation context...",
                    "message_count": len(recent_messages)
                },
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Step 9: Build complete prompt with GOALS + PERSONALITY + EMOTION AWARENESS + HARD PREFERENCE ENFORCEMENT
            # Use final_personality_config (detected or loaded) for immediate application
            system_prompt = self.prompt_builder.build_system_prompt(
                relevant_memories=relevant_memories,
                conversation_summary=conversation_summary,
                user_preferences=user_preferences,           # HARD ENFORCEMENT
                detected_emotion=detected_emotion,            # EMOTION AWARENESS
                emotion_context=emotion_context,              # EMOTION TRENDS
                personality_config=final_personality_config,  # PERSONALITY TRAITS (immediate)
                relationship_state=relationship_state,        # RELATIONSHIP CONTEXT
                goal_context=goal_context                     # GOALS TRACKING
            )
            
            # Get messages except the current user message (it will be added separately)
            history_messages = [msg for msg in recent_messages if msg.content != user_message]
            
            messages = self.prompt_builder.build_chat_messages(
                system_prompt=system_prompt,
                recent_messages=history_messages,
                current_user_message=user_message
            )
            
            # Emit prompt built (use final personality for accurate reporting)
            context_summary = {
                "memories": len(relevant_memories),
                "messages": len(history_messages),
                "preferences": user_preferences is not None,
                "personality": final_personality_config.get('archetype') if final_personality_config else None,
                "emotion": detected_emotion.get('emotion') if detected_emotion else None,
                "goals": len(goal_context.get('active_goals', [])) if goal_context else 0
            }
            
            yield {
                "type": "thinking",
                "step": "prompt_built",
                "data": {
                    "message": "AI context assembled and ready",
                    "context": context_summary
                },
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Step 10: Fast response generation with explicit content detection
            logger.info(f"Generating chat response for conversation {conversation_id}")
            journey.log_prompt_building_start()
            journey.log_prompt_built(
                len(relevant_memories),
                len(recent_messages),
                final_personality_config is not None,
                detected_emotion is not None
            )
            
            # ==========================================
            # CONTENT CLASSIFICATION & ROUTING
            # ==========================================
            
            # Get services
            # Create LLM judge client for classification (use fast OpenAI model)
            llm_judge_client = None
            if settings.content_llm_judge_enabled:
                from app.services.llm_client import OpenAIClient
                try:
                    llm_judge_client = OpenAIClient(
                        model_name="gpt-4o-mini",  # Fast and cheap
                        temperature=0.3,  # Low temperature for consistent classification
                        max_tokens=150  # Short response
                    )
                except Exception as e:
                    logger.warning(f"Failed to create LLM judge client: {e}")
            
            classifier = get_content_classifier(
                llm_client=llm_judge_client,
                enable_llm_judge=settings.content_llm_judge_enabled
            )
            router = get_content_router()
            session_manager = get_session_manager()
            audit_logger = get_audit_logger()
            
            # Get or create session FIRST (before classification)
            session = session_manager.get_session(conversation_id, user_db_id or conversation_id)
            
            # ALWAYS classify content (even if route is locked)
            # This allows SAFE content to break out of explicit mode
            classification = classifier.classify(user_message)
            logger.info(
                f"Content classified: {classification.label.value} "
                f"(confidence: {classification.confidence:.2f})"
            )
            
            # Determine route from classification
            route = router.route(classification)
            
            # Check if route is locked and should stay locked
            if session_manager.is_route_locked(conversation_id):
                locked_route = session_manager.get_current_route(conversation_id)
                
                # If new content is also explicit, stay locked
                if route in (ModelRoute.EXPLICIT, ModelRoute.FETISH, ModelRoute.ROMANCE):
                    route = locked_route  # Keep the locked route
                    logger.info(
                        f"Route locked to {locked_route.value} "
                        f"({session.route_lock_message_count} messages remaining) - "
                        f"continuing explicit conversation"
                    )
                else:
                    # New content is SAFE - break the lock!
                    logger.info(
                        f"Breaking route lock: user switched from {locked_route.value} to SAFE content "
                        f"(was locked for {session.route_lock_message_count} more messages)"
                    )
                    # Clear the lock by setting count to 0
                    session.route_lock_message_count = 0
            
            # Age verification is now handled by frontend popup via API endpoint
            # No need to detect "yes" in chat anymore
            # Check if age verification is required
            if session_manager.requires_age_verification(conversation_id, route):
                attempt_count = session_manager.track_explicit_attempt(conversation_id)
                
                logger.warning(
                    f"Age verification required for {route} "
                    f"(attempt {attempt_count}, conversation {conversation_id})"
                )
                
                # Log audit
                audit_logger.log_classification(
                    conversation_id=conversation_id,
                    user_id=user_db_id or conversation_id,
                    original_text=user_message,
                    classification=classification,
                    route=route,
                    route_locked=session_manager.is_route_locked(conversation_id),
                    age_verified=False,
                    action="age_verify_required",
                    session_info={"attempt_count": attempt_count}
                )
                
                # Return age verification required event
                # Frontend should show age confirmation popup
                yield {
                    "type": "age_verification_required",
                    "conversation_id": str(conversation_id),
                    "data": {
                        "message": "Age verification required to access this content",
                        "route": route.value,
                        "api_endpoint": "/content/age-verify",
                        "instructions": "Please confirm you are 18+ years old to continue"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                yield {
                    "type": "done",
                    "conversation_id": str(conversation_id),
                    "timestamp": datetime.utcnow().isoformat()
                }
                return
            
            # Check if should refuse
            if router.should_refuse(route):
                refusal_message = router.get_refusal_message(route)
                
                logger.warning(
                    f"Refusing content: {classification.label.value} "
                    f"(route: {route}, conversation {conversation_id})"
                )
                
                # Log audit
                audit_logger.log_classification(
                    conversation_id=conversation_id,
                    user_id=user_db_id or conversation_id,
                    original_text=user_message,
                    classification=classification,
                    route=route,
                    route_locked=False,
                    age_verified=session.age_verified,
                    action="refuse",
                    refusal_reason=classification.label.value
                )
                
                # Return refusal
                yield {
                    "type": "thinking",
                    "step": "content_refused",
                    "data": {"message": f"Content refused: {classification.label.value}"},
                    "conversation_id": str(conversation_id),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                for chunk in refusal_message:
                    yield {
                        "type": "chunk",
                        "chunk": chunk,
                        "conversation_id": str(conversation_id)
                    }
                
                yield {
                    "type": "done",
                    "conversation_id": str(conversation_id),
                    "timestamp": datetime.utcnow().isoformat()
                }
                return
            
            # Update session route
            session_manager.set_route(conversation_id, route)
            
            # Get appropriate client and system prompt
            active_llm_client = router.get_client(route)
            route_system_prompt = router.get_system_prompt(route)
            
            # Override system prompt in messages if explicit route
            if route in (ModelRoute.EXPLICIT, ModelRoute.FETISH, ModelRoute.ROMANCE):
                # Replace system message with route-specific prompt
                if messages and messages[0]["role"] == "system":
                    messages[0]["content"] = route_system_prompt
                else:
                    messages.insert(0, {"role": "system", "content": route_system_prompt})
            
            # Log audit
            audit_logger.log_classification(
                conversation_id=conversation_id,
                user_id=user_db_id or conversation_id,
                original_text=user_message,
                classification=classification,
                route=route,
                route_locked=session_manager.is_route_locked(conversation_id),
                age_verified=session.age_verified,
                action="generate",
                session_info={
                    "route_lock_count": session.route_lock_message_count,
                    "current_route": session.current_route.value
                }
            )
            
            # Emit routing info
            yield {
                "type": "thinking",
                "step": "content_routed",
                "data": {
                    "message": f"Content routed to {route.value}",
                    "label": classification.label.value,
                    "confidence": round(classification.confidence, 2),
                    "route": route.value
                },
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # For backward compatibility
            is_explicit = route in (ModelRoute.EXPLICIT, ModelRoute.FETISH)
            model_name = "local-model" if is_explicit else settings.openai_model_name
            
            journey.log_llm_call_start(model_name)
            
            # Emit generation start
            yield {
                "type": "thinking",
                "step": "generating_response",
                "data": {"message": "Generating response..."},
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Stream response directly from chosen LLM (FAST - no waiting!)
            logger.info(f"Streaming response from {model_name}...")
            journey.log_streaming_start()
            
            full_response = []
            chunk_count = 0
            
            try:
                async for chunk in active_llm_client.stream_chat(messages):
                    full_response.append(chunk)
                    chunk_count += 1
                    journey.log_streaming_chunk(chunk_count)
                    yield {
                        "type": "chunk",
                        "chunk": chunk,
                        "conversation_id": str(conversation_id)
                    }
                
                assistant_response = "".join(full_response)
                logger.info(f"{model_name} generated {len(assistant_response)} chars")
                
            except LLMConnectionError as e:
                # If local model fails, attempt fallback to OpenAI with safety warning
                if route in (ModelRoute.EXPLICIT, ModelRoute.FETISH):
                    logger.warning(
                        f"Local model connection failed for {route}, falling back to OpenAI: {e}"
                    )
                    
                    # Emit warning to user
                    yield {
                        "type": "thinking",
                        "step": "model_fallback",
                        "data": {
                            "message": "Local model unavailable, using fallback model with safety restrictions"
                        },
                        "conversation_id": str(conversation_id),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Use OpenAI as fallback with modified prompt
                    fallback_client = OpenAIClient(
                        model_name=settings.openai_model_name,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    # Modify system prompt to be safer (OpenAI has content filters)
                    fallback_prompt = """You are a helpful AI assistant. Be respectful and maintain appropriate boundaries. 
Note: Explicit content may be limited due to content policy restrictions."""
                    
                    if messages and messages[0]["role"] == "system":
                        messages[0]["content"] = fallback_prompt
                    
                    # Try streaming with fallback client
                    try:
                        async for chunk in fallback_client.stream_chat(messages):
                            full_response.append(chunk)
                            chunk_count += 1
                            journey.log_streaming_chunk(chunk_count)
                            yield {
                                "type": "chunk",
                                "chunk": chunk,
                                "conversation_id": str(conversation_id)
                            }
                        
                        assistant_response = "".join(full_response)
                        logger.info(f"Fallback model generated {len(assistant_response)} chars")
                        
                    except Exception as fallback_error:
                        logger.error(f"Fallback model also failed: {fallback_error}")
                        raise  # Re-raise to be caught by outer exception handler
                else:
                    # For non-explicit routes, just re-raise the error
                    logger.error(f"LLM connection failed for {route}: {e}")
                    raise
            
            # Step 11: Store assistant response in short-term memory
            self.conversation_buffer.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_response
            )
            
            # Step 12: Trigger comprehensive background analysis (non-blocking)
            # This includes: goal tracking, memory extraction, and other non-urgent tasks
            yield {
                "type": "thinking",
                "step": "background_analysis",
                "data": {"message": "Running background analysis (goals, memories)..."},
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Determine which LLM client to use for background analysis
            bg_llm_client = get_llm_client(provider="local") if is_explicit else self.llm_client
            
            # Start background analysis in fire-and-forget mode
            asyncio.create_task(
                self._background_analysis(
                    user_message=user_message,
                    user_db_id=user_db_id,
                    conversation_id=conversation_id,
                    detected_emotion=detected_emotion,
                    llm_client=bg_llm_client
                )
            )
            
            # Log streaming completion
            full_response_text = "".join(full_response)
            journey.log_streaming_complete(chunk_count, len(full_response_text))
            
            # Emit done
            yield {
                "type": "done",
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log journey completion
            journey.log_complete()
            
        except (LLMConnectionError, LLMResponseError) as e:
            journey.log_error("LLMError", str(e))
            logger.error(f"LLM error in chat: {e}")
            error_message = "I'm having trouble connecting to my language model. Please try again."
            yield {
                "type": "error",
                "error": error_message,
                "conversation_id": str(conversation_id)
            }
        except Exception as e:
            logger.error(f"Unexpected error in chat: {e}", exc_info=True)
            error_message = "An unexpected error occurred. Please try again."
            yield {
                "type": "error",
                "error": error_message,
                "conversation_id": str(conversation_id)
            }
    
    async def _extract_memories_async(self, conversation_id: UUID) -> None:
        """
        Extract and store memories asynchronously (background task).
        NOTE: This method is deprecated. Use _background_analysis instead.
        
        Args:
            conversation_id: Conversation identifier
        """
        try:
            recent_messages = self.conversation_buffer.get_recent_messages(conversation_id)
            
            count = await self.long_term_memory.extract_and_store_memories(
                conversation_id=conversation_id,
                messages=recent_messages
            )
            
            if count > 0:
                logger.info(f"Background task: Stored {count} new memories for conversation {conversation_id}")
                
        except Exception as e:
            logger.error(f"Error in background memory extraction: {e}")
    
    async def _background_analysis(
        self,
        user_message: str,
        user_db_id: UUID,
        conversation_id: UUID,
        detected_emotion: Optional[Dict] = None,
        llm_client: Optional[LLMClient] = None
    ) -> None:
        """
        Run non-urgent analysis tasks in background after response is sent.
        
        Args:
            user_message: The user's message
            user_db_id: User database UUID
            conversation_id: Conversation identifier
            detected_emotion: Previously detected emotion (optional)
            llm_client: LLM client to use (for explicit content handling)
        """
        try:
            logger.info(f"Starting background analysis for conversation {conversation_id}")
            
            # Use provided LLM client or fall back to default
            bg_llm = llm_client or self.llm_client
            
            # Goal detection and tracking (non-urgent)
            # Note: Goal service uses its own LLM client, not the background one
            if self.goal_service:
                try:
                    goal_tracking_result = await self.goal_service.detect_and_track_goals(
                        user_id=user_db_id,
                        message=user_message,
                        conversation_id=conversation_id,
                        detected_emotion=detected_emotion.get('emotion') if detected_emotion else None
                    )
                    if goal_tracking_result:
                        new_goals = goal_tracking_result.get('new_goals', [])
                        progress_updates = goal_tracking_result.get('progress_updates', [])
                        logger.info(f"Background: Tracked goals - {len(new_goals)} new, {len(progress_updates)} updates")
                except Exception as e:
                    logger.warning(f"Background goal tracking failed: {e}")
            
            # Memory extraction (non-urgent) - use specific LLM client
            try:
                recent_messages = self.conversation_buffer.get_recent_messages(conversation_id)
                
                # Create new memory extractor with the appropriate LLM client
                from app.services.memory_extraction import MemoryExtractor
                from app.repositories.vector_store import VectorStoreRepository
                from app.utils.embeddings import get_embedding_generator
                from app.core.database import engine
                from sqlalchemy.ext.asyncio import AsyncSession
                from sqlalchemy.orm import sessionmaker
                
                # We need a database session for memory extraction
                async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
                async with async_session() as db:
                    vector_store = VectorStoreRepository(db, llm_client=bg_llm)
                    embedding_gen = get_embedding_generator()
                    memory_extractor = MemoryExtractor(
                        vector_store=vector_store,
                        embedding_generator=embedding_gen,
                        llm_client=bg_llm
                    )
                    
                    count = await memory_extractor.extract_and_store(
                        conversation_id=conversation_id,
                        messages=recent_messages
                    )
                    await db.commit()
                    
                    if count > 0:
                        logger.info(f"Background: Extracted {count} memories")
            except Exception as e:
                logger.warning(f"Background memory extraction failed: {e}")
                
        except Exception as e:
            logger.error(f"Error in background analysis: {e}", exc_info=True)
    
    async def reset_conversation(self, conversation_id: UUID) -> None:
        """
        Reset conversation (clear short-term memory only).
        
        Args:
            conversation_id: Conversation identifier
        """
        self.conversation_buffer.reset_conversation(conversation_id)
        logger.info(f"Reset conversation {conversation_id}")
    
    async def clear_memories(self, conversation_id: UUID) -> None:
        """
        Clear all memories (short and long-term) for a conversation.
        
        Args:
            conversation_id: Conversation identifier
        """
        # Clear short-term memory
        self.conversation_buffer.clear_conversation(conversation_id)
        
        # Clear long-term memories
        count = await self.long_term_memory.clear_memories(conversation_id)
        
        logger.info(f"Cleared all memories for conversation {conversation_id} ({count} long-term memories)")

