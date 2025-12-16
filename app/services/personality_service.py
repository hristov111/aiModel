"""Service for managing AI personality and relationship state."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import PersonalityProfileModel, RelationshipStateModel, UserModel
from app.services.personality_archetypes import get_archetype, get_archetype_config, ARCHETYPES

logger = logging.getLogger(__name__)


class PersonalityService:
    """Manages AI personality configuration and relationship evolution."""
    
    def __init__(self, db_session: AsyncSession, llm_client=None):
        """
        Initialize personality service.
        
        Args:
            db_session: Database session
            llm_client: Optional LLM client for AI-based personality detection
        """
        self.db = db_session
        self.llm_client = llm_client
    
    async def get_personality(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get user's AI personality configuration.
        
        Args:
            user_id: User ID
            
        Returns:
            Personality config dict or None
        """
        stmt = select(PersonalityProfileModel).where(
            PersonalityProfileModel.user_id == user_id
        )
        result = await self.db.execute(stmt)
        personality = result.scalar_one_or_none()
        
        if not personality:
            return None
        
        return self._personality_to_dict(personality)
    
    async def create_personality(
        self,
        user_id: UUID,
        archetype: Optional[str] = None,
        traits: Optional[Dict[str, int]] = None,
        behaviors: Optional[Dict[str, bool]] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create personality profile for user.
        
        Args:
            user_id: User ID
            archetype: Archetype name (e.g., 'wise_mentor')
            traits: Custom trait values (0-10)
            behaviors: Custom behavior flags
            custom_config: Additional custom configuration
            
        Returns:
            Created personality dict
        """
        # Check if personality already exists
        existing = await self.get_personality(user_id)
        if existing:
            raise ValueError("Personality profile already exists. Use update instead.")
        
        # Start with archetype config if provided
        config = {}
        if archetype and archetype in ARCHETYPES:
            arch_config = get_archetype_config(archetype)
            config.update(arch_config)
        
        # Override with custom values
        if traits:
            config['traits'] = {**config.get('traits', {}), **traits}
        if behaviors:
            config['behaviors'] = {**config.get('behaviors', {}), **behaviors}
        
        # Create personality profile
        personality = PersonalityProfileModel(
            user_id=user_id,
            archetype=archetype,
            relationship_type=config.get('relationship_type', 'assistant'),
            
            # Traits
            humor_level=config.get('traits', {}).get('humor_level', 5),
            formality_level=config.get('traits', {}).get('formality_level', 5),
            enthusiasm_level=config.get('traits', {}).get('enthusiasm_level', 5),
            empathy_level=config.get('traits', {}).get('empathy_level', 7),
            directness_level=config.get('traits', {}).get('directness_level', 5),
            curiosity_level=config.get('traits', {}).get('curiosity_level', 5),
            supportiveness_level=config.get('traits', {}).get('supportiveness_level', 7),
            playfulness_level=config.get('traits', {}).get('playfulness_level', 5),
            
            # Custom config
            backstory=custom_config.get('backstory') if custom_config else None,
            custom_instructions=custom_config.get('custom_instructions') if custom_config else None,
            speaking_style=config.get('speaking_style') or (custom_config.get('speaking_style') if custom_config else None),
            
            # Behaviors
            asks_questions=config.get('behaviors', {}).get('asks_questions', True),
            uses_examples=config.get('behaviors', {}).get('uses_examples', True),
            shares_opinions=config.get('behaviors', {}).get('shares_opinions', True),
            challenges_user=config.get('behaviors', {}).get('challenges_user', False),
            celebrates_wins=config.get('behaviors', {}).get('celebrates_wins', True)
        )
        
        self.db.add(personality)
        await self.db.commit()
        await self.db.refresh(personality)
        
        logger.info(f"Created personality for user {user_id}: archetype={archetype}")
        
        return self._personality_to_dict(personality)
    
    async def update_personality(
        self,
        user_id: UUID,
        archetype: Optional[str] = None,
        traits: Optional[Dict[str, int]] = None,
        behaviors: Optional[Dict[str, bool]] = None,
        custom_config: Optional[Dict[str, Any]] = None,
        merge: bool = True
    ) -> Dict[str, Any]:
        """
        Update personality configuration.
        
        Args:
            user_id: User ID
            archetype: New archetype (if changing completely)
            traits: Trait updates
            behaviors: Behavior updates
            custom_config: Custom configuration updates
            merge: If True, merge with existing; if False, replace completely
            
        Returns:
            Updated personality dict
        """
        # Get existing personality
        stmt = select(PersonalityProfileModel).where(
            PersonalityProfileModel.user_id == user_id
        )
        result = await self.db.execute(stmt)
        personality = result.scalar_one_or_none()
        
        if not personality:
            # Create if doesn't exist
            return await self.create_personality(
                user_id=user_id,
                archetype=archetype,
                traits=traits,
                behaviors=behaviors,
                custom_config=custom_config
            )
        
        # If changing archetype completely
        if archetype and not merge:
            arch_config = get_archetype_config(archetype)
            if arch_config:
                personality.archetype = archetype
                personality.relationship_type = arch_config.get('relationship_type')
                
                # Set all traits from archetype
                for trait_name, value in arch_config.get('traits', {}).items():
                    setattr(personality, trait_name, value)
                
                # Set all behaviors from archetype
                for behavior_name, value in arch_config.get('behaviors', {}).items():
                    setattr(personality, behavior_name, value)
                
                personality.speaking_style = arch_config.get('speaking_style')
        
        # Update individual traits
        if traits:
            for trait_name, value in traits.items():
                if hasattr(personality, trait_name):
                    setattr(personality, trait_name, value)
        
        # Update behaviors
        if behaviors:
            for behavior_name, value in behaviors.items():
                if hasattr(personality, behavior_name):
                    setattr(personality, behavior_name, value)
        
        # Update custom config
        if custom_config:
            if 'backstory' in custom_config:
                personality.backstory = custom_config['backstory']
            if 'custom_instructions' in custom_config:
                personality.custom_instructions = custom_config['custom_instructions']
            if 'speaking_style' in custom_config:
                personality.speaking_style = custom_config['speaking_style']
            if 'relationship_type' in custom_config:
                personality.relationship_type = custom_config['relationship_type']
        
        # Update version
        personality.version += 1
        personality.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(personality)
        
        logger.info(f"Updated personality for user {user_id} (version {personality.version})")
        
        return self._personality_to_dict(personality)
    
    async def delete_personality(self, user_id: UUID) -> bool:
        """
        Delete personality profile (reset to default).
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if didn't exist
        """
        stmt = select(PersonalityProfileModel).where(
            PersonalityProfileModel.user_id == user_id
        )
        result = await self.db.execute(stmt)
        personality = result.scalar_one_or_none()
        
        if not personality:
            return False
        
        await self.db.delete(personality)
        await self.db.commit()
        
        logger.info(f"Deleted personality for user {user_id}")
        
        return True
    
    # ========== Relationship State Management ==========
    
    async def get_relationship_state(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get relationship state metrics.
        
        Args:
            user_id: User ID
            
        Returns:
            Relationship state dict
        """
        stmt = select(RelationshipStateModel).where(
            RelationshipStateModel.user_id == user_id
        )
        result = await self.db.execute(stmt)
        state = result.scalar_one_or_none()
        
        if not state:
            # Create initial state
            state = await self._create_relationship_state(user_id)
        
        # Update days_known
        days_known = (datetime.utcnow() - state.first_interaction).days
        if days_known != state.days_known:
            state.days_known = days_known
            await self.db.commit()
        
        return {
            'total_messages': state.total_messages,
            'relationship_depth_score': round(state.relationship_depth_score, 2),
            'trust_level': round(state.trust_level, 2),
            'days_known': state.days_known,
            'first_interaction': state.first_interaction.isoformat(),
            'last_interaction': state.last_interaction.isoformat(),
            'milestones': state.milestones or [],
            'positive_reactions': state.positive_reactions,
            'negative_reactions': state.negative_reactions
        }
    
    async def update_relationship_metrics(
        self,
        user_id: UUID,
        message_sent: bool = False,
        positive_reaction: bool = False,
        negative_reaction: bool = False
    ) -> None:
        """
        Update relationship metrics after interaction.
        
        Args:
            user_id: User ID
            message_sent: Whether user sent a message
            positive_reaction: Whether user gave positive feedback
            negative_reaction: Whether user gave negative feedback
        """
        stmt = select(RelationshipStateModel).where(
            RelationshipStateModel.user_id == user_id
        )
        result = await self.db.execute(stmt)
        state = result.scalar_one_or_none()
        
        if not state:
            state = await self._create_relationship_state(user_id)
        
        # Update counts
        if message_sent:
            state.total_messages += 1
            state.last_interaction = datetime.utcnow()
            
            # Calculate relationship depth (grows slowly over time)
            # Formula: log(messages) + days_known/30 + (positive_reactions - negative_reactions)/10
            import math
            days_known = (datetime.utcnow() - state.first_interaction).days
            state.days_known = days_known
            
            depth = (
                math.log(state.total_messages + 1) * 1.5 +
                days_known / 30 +
                (state.positive_reactions - state.negative_reactions) / 10
            )
            state.relationship_depth_score = min(depth, 10.0)  # Cap at 10
            
            # Check for milestones
            await self._check_milestones(state)
        
        if positive_reaction:
            state.positive_reactions += 1
            state.trust_level = min(state.trust_level + 0.1, 10.0)
        
        if negative_reaction:
            state.negative_reactions += 1
            state.trust_level = max(state.trust_level - 0.2, 0.0)
        
        await self.db.commit()
    
    async def _create_relationship_state(self, user_id: UUID) -> RelationshipStateModel:
        """Create initial relationship state."""
        state = RelationshipStateModel(
            user_id=user_id,
            total_messages=0,
            relationship_depth_score=0.0,
            trust_level=5.0,
            first_interaction=datetime.utcnow(),
            last_interaction=datetime.utcnow(),
            days_known=0,
            milestones=[]
        )
        
        self.db.add(state)
        await self.db.commit()
        await self.db.refresh(state)
        
        return state
    
    async def _check_milestones(self, state: RelationshipStateModel) -> None:
        """Check and record relationship milestones."""
        milestones = state.milestones or []
        existing_types = {m['type'] for m in milestones}
        
        new_milestones = []
        
        # Message milestones
        message_milestones = [10, 50, 100, 500, 1000]
        for threshold in message_milestones:
            milestone_type = f'{threshold}_messages'
            if state.total_messages >= threshold and milestone_type not in existing_types:
                new_milestones.append({
                    'type': milestone_type,
                    'reached_at': datetime.utcnow().isoformat(),
                    'message': f'Reached {threshold} messages together!'
                })
        
        # Time milestones
        time_milestones = [
            (7, '1_week'),
            (30, '1_month'),
            (90, '3_months'),
            (180, '6_months'),
            (365, '1_year')
        ]
        for days, milestone_type in time_milestones:
            if state.days_known >= days and milestone_type not in existing_types:
                new_milestones.append({
                    'type': milestone_type,
                    'reached_at': datetime.utcnow().isoformat(),
                    'message': f'We\'ve known each other for {milestone_type.replace("_", " ")}!'
                })
        
        # Add new milestones
        if new_milestones:
            state.milestones = milestones + new_milestones
            logger.info(f"New milestones for user {state.user_id}: {[m['type'] for m in new_milestones]}")
    
    def _personality_to_dict(self, personality: PersonalityProfileModel) -> Dict[str, Any]:
        """Convert personality model to dict."""
        return {
            'archetype': personality.archetype,
            'relationship_type': personality.relationship_type,
            'traits': {
                'humor_level': personality.humor_level,
                'formality_level': personality.formality_level,
                'enthusiasm_level': personality.enthusiasm_level,
                'empathy_level': personality.empathy_level,
                'directness_level': personality.directness_level,
                'curiosity_level': personality.curiosity_level,
                'supportiveness_level': personality.supportiveness_level,
                'playfulness_level': personality.playfulness_level
            },
            'behaviors': {
                'asks_questions': personality.asks_questions,
                'uses_examples': personality.uses_examples,
                'shares_opinions': personality.shares_opinions,
                'challenges_user': personality.challenges_user,
                'celebrates_wins': personality.celebrates_wins
            },
            'custom': {
                'backstory': personality.backstory,
                'custom_instructions': personality.custom_instructions,
                'speaking_style': personality.speaking_style
            },
            'meta': {
                'version': personality.version,
                'created_at': personality.created_at.isoformat(),
                'updated_at': personality.updated_at.isoformat()
            }
        }

