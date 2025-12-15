"""Main chat service orchestrating all components."""

from typing import AsyncIterator, Optional, Dict, Any
from uuid import UUID, uuid4
import logging
import asyncio
from datetime import datetime

from app.models.memory import Message
from app.services.short_term_memory import ConversationBuffer
from app.services.long_term_memory import LongTermMemoryService
from app.services.prompt_builder import PromptBuilder
from app.services.llm_client import LLMClient
from app.services.user_preference_service import UserPreferenceService
from app.services.emotion_service import EmotionService
from app.services.personality_service import PersonalityService
from app.services.personality_detector import PersonalityDetector
from app.core.exceptions import LLMConnectionError, LLMResponseError

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
        self.personality_detector = PersonalityDetector() if personality_service else None
        self.goal_service = goal_service
    
    async def stream_chat(
        self,
        user_message: str,
        conversation_id: UUID = None,
        user_id: str = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process chat message and stream response with thinking steps.
        
        Args:
            user_message: User's message
            conversation_id: Optional conversation ID (creates new if None)
            user_id: External user ID for memory isolation
            
        Yields:
            Dictionaries with event type and data:
            - {"type": "thinking", "step": "...", "data": {...}, "conversation_id": "..."}
            - {"type": "chunk", "chunk": "...", "conversation_id": "..."}
            - {"type": "done", "conversation_id": "..."}
        """
        # Create conversation ID if not provided
        if conversation_id is None:
            conversation_id = uuid4()
            logger.info(f"Created new conversation: {conversation_id} for user: {user_id}")
        
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
            
            # Step 2: Auto-detect and update preferences if present
            preferences_updated = False
            if self.preference_service and user_id:
                await self.preference_service.extract_and_update_preferences(
                    external_user_id=user_id,
                    message_content=user_message
                )
                preferences_updated = True
            
            # Step 3: Auto-detect and update personality if mentioned
            personality_detected = False
            if self.personality_service and self.personality_detector and user_id:
                personality_config_detected = self.personality_detector.detect(user_message)
                if personality_config_detected:
                    await self.personality_service.update_personality(
                        user_id=UUID(user_id),
                        archetype=personality_config_detected.get('archetype'),
                        traits=personality_config_detected.get('traits'),
                        behaviors=personality_config_detected.get('behaviors'),
                        custom_config={'custom_instructions': personality_config_detected.get('custom_instructions')} if personality_config_detected.get('custom_instructions') else None,
                        merge=True
                    )
                    logger.info(f"Auto-updated personality for user {user_id}")
                    personality_detected = True
                    
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
            
            # Step 4: Get user preferences for HARD ENFORCEMENT
            user_preferences = None
            if self.preference_service and user_id:
                user_preferences = await self.preference_service.get_user_preferences(user_id)
            
            # Step 5: Get personality configuration
            personality_config = None
            relationship_state = None
            if self.personality_service and user_id:
                personality_config = await self.personality_service.get_personality(UUID(user_id))
                relationship_state = await self.personality_service.get_relationship_state(UUID(user_id))
                # Update relationship metrics
                await self.personality_service.update_relationship_metrics(
                    user_id=UUID(user_id),
                    message_sent=True
                )
                
                if personality_config:
                    yield {
                        "type": "thinking",
                        "step": "personality_loaded",
                        "data": {
                            "message": "Applied personality configuration",
                            "archetype": personality_config.get('archetype'),
                            "relationship_depth": relationship_state.get('relationship_depth_score', 0) if relationship_state else 0,
                            "traits": personality_config.get('traits', {})
                        },
                        "conversation_id": str(conversation_id),
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
            # Step 6: Detect emotion from user message
            detected_emotion = None
            emotion_context = None
            if self.emotion_service and user_id:
                # Detect and store emotion asynchronously
                emotion = await self.emotion_service.detect_and_store(
                    user_id=UUID(user_id),
                    message=user_message,
                    conversation_id=conversation_id
                )
                
                if emotion:
                    detected_emotion = {
                        'emotion': emotion.emotion,
                        'confidence': emotion.confidence,
                        'intensity': emotion.intensity
                    }
                    logger.info(f"Detected emotion: {emotion.emotion} ({emotion.confidence:.2f})")
                    
                    # Emit emotion detection
                    yield {
                        "type": "thinking",
                        "step": "emotion_detected",
                        "data": {
                            "message": f"Detected emotion: {emotion.emotion}",
                            "emotion": emotion.emotion,
                            "confidence": round(emotion.confidence, 2),
                            "intensity": emotion.intensity
                        },
                        "conversation_id": str(conversation_id),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Get emotion trends for context
                    emotion_context = await self.emotion_service.get_emotion_trends(
                        user_id=UUID(user_id),
                        days=30
                    )
            
            # Step 6.5: Detect and track goals from user message
            goal_context = None
            if self.goal_service and user_id:
                goal_tracking_result = await self.goal_service.detect_and_track_goals(
                    user_id=UUID(user_id),
                    message=user_message,
                    conversation_id=conversation_id,
                    detected_emotion=detected_emotion.get('emotion') if detected_emotion else None
                )
                
                # Get active goals for context
                active_goals = await self.goal_service.get_user_goals(
                    user_id=UUID(user_id),
                    status='active'
                )
                
                if active_goals:
                    goal_context = {
                        'active_goals': active_goals[:5],  # Top 5 active goals
                        'new_goals': goal_tracking_result.get('new_goals', []),
                        'progress_updates': goal_tracking_result.get('progress_updates', []),
                        'completions': goal_tracking_result.get('completions', [])
                    }
                    logger.info(f"Goal tracking: {len(active_goals)} active goals, {len(goal_tracking_result.get('new_goals', []))} new")
                    
                    # Emit goal tracking
                    goal_summary = []
                    for goal in active_goals[:3]:  # Show top 3
                        goal_summary.append({
                            "title": goal.get('title'),
                            "category": goal.get('category'),
                            "progress": goal.get('progress_percentage', 0)
                        })
                    
                    yield {
                        "type": "thinking",
                        "step": "goals_tracked",
                        "data": {
                            "message": f"Tracking {len(active_goals)} active goals",
                            "active_count": len(active_goals),
                            "new_goals": len(goal_tracking_result.get('new_goals', [])),
                            "progress_updates": len(goal_tracking_result.get('progress_updates', [])),
                            "goals": goal_summary
                        },
                        "conversation_id": str(conversation_id),
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
            # Step 7: Retrieve relevant long-term memories
            relevant_memories = await self.long_term_memory.retrieve_relevant_memories(
                conversation_id=conversation_id,
                query_text=user_message
            )
            logger.debug(f"Retrieved {len(relevant_memories)} relevant memories")
            
            # Emit memory retrieval
            yield {
                "type": "thinking",
                "step": "memories_retrieved",
                "data": {
                    "message": f"Retrieved {len(relevant_memories)} relevant memories",
                    "count": len(relevant_memories),
                    "memories": [{"content": m.content[:100], "importance": m.importance_score} for m in relevant_memories[:3]]
                },
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Step 8: Get recent conversation history and summary
            recent_messages = self.conversation_buffer.get_recent_messages(conversation_id)
            conversation_summary = self.conversation_buffer.get_or_create_summary(conversation_id)
            
            # Step 9: Build complete prompt with GOALS + PERSONALITY + EMOTION AWARENESS + HARD PREFERENCE ENFORCEMENT
            system_prompt = self.prompt_builder.build_system_prompt(
                relevant_memories=relevant_memories,
                conversation_summary=conversation_summary,
                user_preferences=user_preferences,      # HARD ENFORCEMENT
                detected_emotion=detected_emotion,       # EMOTION AWARENESS
                emotion_context=emotion_context,         # EMOTION TRENDS
                personality_config=personality_config,   # PERSONALITY TRAITS
                relationship_state=relationship_state,   # RELATIONSHIP CONTEXT
                goal_context=goal_context                # GOALS TRACKING
            )
            
            # Get messages except the current user message (it will be added separately)
            history_messages = [msg for msg in recent_messages if msg.content != user_message]
            
            messages = self.prompt_builder.build_chat_messages(
                system_prompt=system_prompt,
                recent_messages=history_messages,
                current_user_message=user_message
            )
            
            # Emit prompt built
            yield {
                "type": "thinking",
                "step": "prompt_built",
                "data": {
                    "message": "Context assembled, preparing response",
                    "context_messages": len(history_messages),
                    "has_preferences": user_preferences is not None,
                    "has_personality": personality_config is not None,
                    "has_emotion": detected_emotion is not None
                },
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Step 10: Stream LLM response
            logger.info(f"Streaming chat response for conversation {conversation_id}")
            
            # Emit generation start
            yield {
                "type": "thinking",
                "step": "generating_response",
                "data": {"message": "Generating response..."},
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            full_response = []
            
            async for chunk in self.llm_client.stream_chat(messages):
                full_response.append(chunk)
                yield {
                    "type": "chunk",
                    "chunk": chunk,
                    "conversation_id": str(conversation_id)
                }
            
            # Step 11: Store assistant response in short-term memory
            assistant_response = "".join(full_response)
            self.conversation_buffer.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_response
            )
            
            # Step 12: Trigger async memory extraction (non-blocking)
            asyncio.create_task(
                self._extract_memories_async(conversation_id)
            )
            
            # Emit done
            yield {
                "type": "done",
                "conversation_id": str(conversation_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except (LLMConnectionError, LLMResponseError) as e:
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

