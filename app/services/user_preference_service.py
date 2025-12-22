"""Service for managing user communication preferences."""

import logging
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import UserModel
from app.services.preference_extractor import CommunicationPreferences, PreferenceExtractor

logger = logging.getLogger(__name__)


class UserPreferenceService:
    """Service for managing user preferences."""
    
    def __init__(self, session: AsyncSession, llm_client=None):
        """
        Initialize user preference service.
        
        Args:
            session: Database session
            llm_client: Optional LLM client for AI-based preference extraction
        """
        self.session = session
        self.extractor = PreferenceExtractor(llm_client=llm_client)
    
    async def get_user_preferences(self, external_user_id: str) -> Optional[Dict]:
        """
        Get user's communication preferences.
        
        Args:
            external_user_id: User's external ID
            
        Returns:
            Preferences dictionary or None
        """
        result = await self.session.execute(
            select(UserModel).where(UserModel.external_user_id == external_user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.extra_metadata:
            return None
        
        return user.extra_metadata.get('communication_preferences')
    
    async def update_user_preferences(
        self,
        external_user_id: str,
        preferences: Dict,
        merge: bool = True
    ) -> Dict:
        """
        Update user's communication preferences.
        
        Args:
            external_user_id: User's external ID
            preferences: New preferences dictionary
            merge: If True, merge with existing; if False, replace
            
        Returns:
            Updated preferences dictionary
        """
        result = await self.session.execute(
            select(UserModel).where(UserModel.external_user_id == external_user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User not found: {external_user_id}")
        
        # Initialize metadata if needed
        if user.extra_metadata is None:
            user.extra_metadata = {}
        
        if merge and 'communication_preferences' in user.extra_metadata:
            # Merge with existing preferences
            existing = user.extra_metadata['communication_preferences']
            for key, value in preferences.items():
                if value is not None:  # Only update non-None values
                    existing[key] = value
            user.extra_metadata['communication_preferences'] = existing
        else:
            # Replace preferences
            user.extra_metadata['communication_preferences'] = preferences
        
        # Mark as modified for SQLAlchemy
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, 'extra_metadata')
        
        await self.session.flush()
        
        logger.info(f"Updated preferences for user {external_user_id}: {preferences}")
        
        return user.extra_metadata['communication_preferences']
    
    async def extract_and_update_preferences(
        self,
        external_user_id: str,
        message_content: str
    ) -> Optional[Dict]:
        """
        Extract preferences from a message and update user's preferences.
        
        Args:
            external_user_id: User's external ID
            message_content: User's message
            
        Returns:
            Updated preferences if any were detected, None otherwise
        """
        # Extract preferences from message (now async with LLM support)
        detected_prefs = await self.extractor.extract_from_message(message_content)
        
        # Convert to dict
        pref_dict = detected_prefs.to_dict()
        
        # Check if any preferences were detected
        has_prefs = any(
            v is not None and k != 'last_updated' 
            for k, v in pref_dict.items()
        )
        
        if not has_prefs:
            return None
        
        # Update user preferences
        updated_prefs = await self.update_user_preferences(
            external_user_id,
            pref_dict,
            merge=True
        )
        
        logger.info(f"Auto-detected and updated preferences for {external_user_id}")
        
        return updated_prefs
    
    async def clear_user_preferences(self, external_user_id: str) -> None:
        """
        Clear all user preferences.
        
        Args:
            external_user_id: User's external ID
        """
        result = await self.session.execute(
            select(UserModel).where(UserModel.external_user_id == external_user_id)
        )
        user = result.scalar_one_or_none()
        
        if user and user.extra_metadata:
            if 'communication_preferences' in user.extra_metadata:
                del user.extra_metadata['communication_preferences']
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(user, 'metadata')
                await self.session.flush()
                logger.info(f"Cleared preferences for user {external_user_id}")

