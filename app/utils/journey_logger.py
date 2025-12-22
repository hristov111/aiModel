"""Message journey logging for detailed tracking of each step."""

import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any

# Create a separate logger for journeys
journey_logger = logging.getLogger('message_journey')
journey_logger.setLevel(logging.INFO)

# Create file handler for journey logs
journey_handler = logging.FileHandler('message_journey.log')
journey_handler.setLevel(logging.INFO)

# Create formatter with detailed format
class JourneyFormatter(logging.Formatter):
    """Custom formatter for journey logs."""
    
    def format(self, record):
        # Format: timestamp | request_id | STEP: step_name | message
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        request_id = getattr(record, 'request_id', 'unknown')
        step = getattr(record, 'step', 'UNKNOWN')
        user_id = getattr(record, 'user_id', 'unknown')
        
        return f"{timestamp} | {request_id} | USER: {user_id} | STEP: {step} | {record.getMessage()}"

journey_handler.setFormatter(JourneyFormatter())
journey_logger.addHandler(journey_handler)

# Don't propagate to root logger (separate file)
journey_logger.propagate = False


class JourneyLogger:
    """Helper class for logging message journeys with detailed step tracking."""
    
    def __init__(self, request_id: str, user_id: str):
        """
        Initialize journey logger.
        
        Args:
            request_id: Unique request identifier
            user_id: User making the request
        """
        self.request_id = request_id
        self.user_id = user_id
        self.start_time = time.time()
        self.last_step_time = self.start_time
        
    def _get_elapsed(self) -> tuple[float, float]:
        """Get elapsed time from start and from last step."""
        current = time.time()
        total_elapsed = current - self.start_time
        step_elapsed = current - self.last_step_time
        self.last_step_time = current
        return total_elapsed, step_elapsed
    
    def log_step(
        self, 
        step_name: str, 
        message: str, 
        data: Optional[Dict[str, Any]] = None,
        level: str = "INFO"
    ):
        """
        Log a step in the message journey.
        
        Args:
            step_name: Name of the step (e.g., "START", "MEMORY_RETRIEVAL")
            message: Human-readable message
            data: Optional data dictionary to include
            level: Log level (INFO, DEBUG, WARNING, ERROR)
        """
        total_elapsed, step_elapsed = self._get_elapsed()
        
        # Format message with timing
        full_message = f"{message} [total: +{total_elapsed:.3f}s, step: {step_elapsed:.3f}s]"
        
        # Add data if provided
        if data:
            data_str = ", ".join(f"{k}={v}" for k, v in data.items())
            full_message += f" | {data_str}"
        
        # Log with extra fields
        extra = {
            'request_id': self.request_id,
            'step': step_name,
            'user_id': self.user_id
        }
        
        # Log at appropriate level
        if level == "INFO":
            journey_logger.info(full_message, extra=extra)
        elif level == "DEBUG":
            journey_logger.debug(full_message, extra=extra)
        elif level == "WARNING":
            journey_logger.warning(full_message, extra=extra)
        elif level == "ERROR":
            journey_logger.error(full_message, extra=extra)
    
    # Convenience methods for common steps
    
    def log_start(self, message_text: str):
        """Log the start of a message journey."""
        preview = message_text[:80] + "..." if len(message_text) > 80 else message_text
        self.log_step("START", f"Message received: '{preview}'")
    
    def log_conversation_created(self, conversation_id: str):
        """Log new conversation creation."""
        self.log_step("CONVERSATION_CREATED", "New conversation created", {
            "conversation_id": str(conversation_id)[:8] + "..."
        })
    
    def log_user_resolved(self, user_db_id: str):
        """Log user resolution to database UUID."""
        self.log_step("USER_RESOLVED", "User resolved to database UUID", {
            "user_db_id": str(user_db_id)[:8] + "..."
        })
    
    def log_preferences_loaded(self, has_preferences: bool):
        """Log user preferences loading."""
        self.log_step("PREFERENCES_LOADED", f"User preferences {'loaded' if has_preferences else 'not found'}")
    
    def log_emotion_detection_start(self):
        """Log emotion detection start."""
        self.log_step("EMOTION_DETECTION_START", "Starting emotion detection...")
    
    def log_emotion_detected(self, emotion: str, confidence: float, intensity: str):
        """Log emotion detection result."""
        self.log_step("EMOTION_DETECTED", f"Detected emotion: {emotion}", {
            "confidence": f"{confidence:.2f}",
            "intensity": intensity
        })
    
    def log_personality_loaded(self, archetype: Optional[str]):
        """Log personality configuration loading."""
        self.log_step("PERSONALITY_LOADED", f"Personality {'loaded: ' + archetype if archetype else 'not configured'}")
    
    def log_goals_tracking(self, active_goals: int, new_goals: int):
        """Log goal tracking."""
        self.log_step("GOALS_TRACKED", f"Goal tracking complete", {
            "active_goals": active_goals,
            "new_goals": new_goals
        })
    
    def log_memory_retrieval_start(self, query: str):
        """Log start of memory retrieval."""
        preview = query[:50] + "..." if len(query) > 50 else query
        self.log_step("MEMORY_RETRIEVAL_START", f"Retrieving memories for: '{preview}'")
    
    def log_memory_retrieved(self, count: int, top_k: int):
        """Log memory retrieval completion."""
        self.log_step("MEMORY_RETRIEVED", f"Retrieved {count}/{top_k} memories")
    
    def log_prompt_building_start(self):
        """Log prompt building start."""
        self.log_step("PROMPT_BUILDING_START", "Building prompt context...")
    
    def log_prompt_built(self, memories: int, messages: int, has_personality: bool, has_emotion: bool):
        """Log prompt building completion."""
        self.log_step("PROMPT_BUILT", "Prompt constructed successfully", {
            "memories": memories,
            "recent_messages": messages,
            "personality": "yes" if has_personality else "no",
            "emotion": "yes" if has_emotion else "no"
        })
    
    def log_llm_call_start(self, model: str):
        """Log LLM call start."""
        self.log_step("LLM_CALL_START", f"Calling LLM", {"model": model})
    
    def log_streaming_start(self):
        """Log streaming start."""
        self.log_step("STREAMING_START", "Starting response stream...")
    
    def log_streaming_chunk(self, chunks_count: int):
        """Log streaming progress."""
        if chunks_count % 50 == 0:  # Log every 50 chunks
            self.log_step("STREAMING_PROGRESS", f"Streamed {chunks_count} chunks", level="DEBUG")
    
    def log_streaming_complete(self, total_chunks: int, full_response_length: int):
        """Log streaming completion."""
        self.log_step("STREAMING_COMPLETE", "Response streaming finished", {
            "chunks": total_chunks,
            "response_length": full_response_length
        })
    
    def log_memory_extraction_start(self):
        """Log memory extraction start."""
        self.log_step("MEMORY_EXTRACTION_START", "Starting memory extraction (background task)...")
    
    def log_memory_extracted(self, count: int, method: str):
        """Log memory extraction completion."""
        self.log_step("MEMORY_EXTRACTED", f"Extracted {count} new memories", {
            "method": method
        })
    
    def log_error(self, error_type: str, error_message: str):
        """Log an error in the journey."""
        self.log_step("ERROR", f"{error_type}: {error_message}", level="ERROR")
    
    def log_complete(self):
        """Log journey completion with total time."""
        total_time = time.time() - self.start_time
        self.log_step("COMPLETE", f"✅ Message journey finished successfully", {
            "total_time": f"{total_time:.3f}s"
        })

