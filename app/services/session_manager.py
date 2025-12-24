"""Session state management for content routing and age verification."""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from uuid import UUID

from app.services.content_router import ModelRoute

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """Session state for a conversation."""
    conversation_id: UUID
    user_id: UUID
    
    # Age verification
    age_verified: bool = False
    age_verified_at: Optional[datetime] = None
    
    # Content mode
    current_route: ModelRoute = ModelRoute.NORMAL
    route_locked_until: Optional[datetime] = None
    route_lock_message_count: int = 0
    
    # Tracking
    explicit_attempts_without_verification: int = 0
    last_classification_label: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class SessionManager:
    """
    Manages session state for content routing.
    
    Features:
    - Age verification tracking
    - Session lock-in (prevents mode switching mid-conversation)
    - Explicit attempt tracking
    """
    
    # Session lock-in: stay in explicit mode for N messages
    ROUTE_LOCK_MESSAGE_COUNT = 5
    
    # Session timeout: clear after inactivity
    SESSION_TIMEOUT_HOURS = 24
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[UUID, SessionState] = {}
        logger.info("SessionManager initialized")
    
    def get_session(self, conversation_id: UUID, user_id: UUID) -> SessionState:
        """
        Get or create session state.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            
        Returns:
            SessionState instance
        """
        if conversation_id not in self.sessions:
            self.sessions[conversation_id] = SessionState(
                conversation_id=conversation_id,
                user_id=user_id,
            )
            logger.info(f"Created new session for conversation {conversation_id}")
        
        session = self.sessions[conversation_id]
        session.updated_at = datetime.utcnow()
        
        return session
    
    def verify_age(self, conversation_id: UUID) -> None:
        """
        Mark session as age-verified.
        
        Args:
            conversation_id: Conversation ID
        """
        if conversation_id in self.sessions:
            session = self.sessions[conversation_id]
            session.age_verified = True
            session.age_verified_at = datetime.utcnow()
            session.explicit_attempts_without_verification = 0
            logger.info(f"Age verified for conversation {conversation_id}")
    
    def is_age_verified(self, conversation_id: UUID) -> bool:
        """
        Check if session is age-verified.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if age verified
        """
        if conversation_id not in self.sessions:
            return False
        
        return self.sessions[conversation_id].age_verified
    
    def requires_age_verification(self, conversation_id: UUID, route: ModelRoute) -> bool:
        """
        Check if route requires age verification.
        
        Args:
            conversation_id: Conversation ID
            route: Target route
            
        Returns:
            True if age verification required
        """
        # Explicit routes require age verification
        if route in (ModelRoute.EXPLICIT, ModelRoute.FETISH):
            return not self.is_age_verified(conversation_id)
        
        return False
    
    def track_explicit_attempt(self, conversation_id: UUID) -> int:
        """
        Track explicit content attempt without age verification.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Number of attempts
        """
        if conversation_id in self.sessions:
            session = self.sessions[conversation_id]
            session.explicit_attempts_without_verification += 1
            return session.explicit_attempts_without_verification
        
        return 0
    
    def set_route(self, conversation_id: UUID, route: ModelRoute) -> None:
        """
        Set current route and apply lock-in if needed.
        
        Args:
            conversation_id: Conversation ID
            route: Model route
        """
        if conversation_id not in self.sessions:
            return
        
        session = self.sessions[conversation_id]
        previous_route = session.current_route
        session.current_route = route
        session.last_classification_label = route.value
        
        # Apply lock-in for explicit routes
        if route in (ModelRoute.EXPLICIT, ModelRoute.FETISH):
            session.route_lock_message_count = self.ROUTE_LOCK_MESSAGE_COUNT
            logger.info(
                f"Route locked to {route} for {self.ROUTE_LOCK_MESSAGE_COUNT} messages "
                f"(conversation {conversation_id})"
            )
        
        # Decrement lock counter if locked
        elif session.route_lock_message_count > 0:
            session.route_lock_message_count -= 1
            logger.debug(
                f"Route lock count: {session.route_lock_message_count} "
                f"(conversation {conversation_id})"
            )
        
        if previous_route != route:
            logger.info(
                f"Route changed: {previous_route} -> {route} "
                f"(conversation {conversation_id})"
            )
    
    def get_current_route(self, conversation_id: UUID) -> ModelRoute:
        """
        Get current route, respecting lock-in.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Current route
        """
        if conversation_id not in self.sessions:
            return ModelRoute.NORMAL
        
        session = self.sessions[conversation_id]
        
        # If locked, return locked route
        if session.route_lock_message_count > 0:
            logger.debug(
                f"Route locked to {session.current_route} "
                f"({session.route_lock_message_count} messages remaining)"
            )
            return session.current_route
        
        return session.current_route
    
    def is_route_locked(self, conversation_id: UUID) -> bool:
        """
        Check if route is currently locked.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if route is locked
        """
        if conversation_id not in self.sessions:
            return False
        
        return self.sessions[conversation_id].route_lock_message_count > 0
    
    def clear_session(self, conversation_id: UUID) -> None:
        """
        Clear session state.
        
        Args:
            conversation_id: Conversation ID
        """
        if conversation_id in self.sessions:
            del self.sessions[conversation_id]
            logger.info(f"Cleared session for conversation {conversation_id}")
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions.
        
        Returns:
            Number of sessions removed
        """
        now = datetime.utcnow()
        timeout = timedelta(hours=self.SESSION_TIMEOUT_HOURS)
        
        expired = [
            conv_id
            for conv_id, session in self.sessions.items()
            if now - session.updated_at > timeout
        ]
        
        for conv_id in expired:
            del self.sessions[conv_id]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        
        return len(expired)
    
    def get_age_verification_prompt(self, attempt_count: int) -> str:
        """
        Get age verification prompt based on attempt count.
        
        Args:
            attempt_count: Number of explicit attempts
            
        Returns:
            Age verification prompt
        """
        if attempt_count == 1:
            return """Before we continue with explicit content, I need to confirm:

Are you 18 years of age or older?

Please respond with "yes" or "no"."""
        
        elif attempt_count == 2:
            return """I need age confirmation before proceeding with adult content.

Please confirm you are 18 or older by responding "yes"."""
        
        else:
            return """Age verification is required for explicit content.

Please confirm you are 18+ to continue."""


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get or create global session manager instance.
    
    Returns:
        SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

