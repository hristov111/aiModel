"""Service for managing AI personality and relationship state."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import PersonalityProfileModel, RelationshipStateModel, UserModel
from app.services.personality_archetypes import get_archetype, get_archetype_config, ARCHETYPES

logger = logging.getLogger(__name__)


class PersonalityService:
    """Manages AI personality configuration and relationship evolution."""
    
    def __init__(self, db_session: AsyncSession, llm_client=None, cache=None):
        """
        Initialize personality service.
        
        Args:
            db_session: Database session
            llm_client: Optional LLM client for AI-based personality detection
            cache: Optional PersonalityCache for Redis caching
        """
        self.db = db_session
        self.llm_client = llm_client
        self.cache = cache
        if cache:
            logger.info("✅ PersonalityService initialized WITH Redis cache")
        else:
            logger.info("⚠️ PersonalityService initialized WITHOUT cache")
    
    async def get_personality(self, user_id: UUID, personality_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get AI personality configuration by name.
        First checks for user-specific personality, then falls back to global personalities.
        Uses Redis cache for global personalities (5-10x faster).
        
        Args:
            user_id: User ID
            personality_name: Optional personality name (if None, returns first personality found)
            
        Returns:
            Personality config dict or None
        """
        # First, try to find user-specific personality
        stmt = select(PersonalityProfileModel).where(
            PersonalityProfileModel.user_id == user_id
        )
        
        if personality_name:
            stmt = stmt.where(PersonalityProfileModel.personality_name == personality_name)
        
        result = await self.db.execute(stmt)
        personality = result.scalar_one_or_none()
        
        if personality:
            return self._personality_to_dict(personality)
        
        # If not found and personality_name was specified, look for global personality
        if personality_name:
            # Try cache first
            if self.cache:
                cached_config = await self.cache.get_personality_config(personality_name)
                if cached_config:
                    logger.debug(f"✅ Config cache hit for '{personality_name}'")
                    return cached_config
            
            # Not in cache, query database
            system_user_stmt = select(UserModel.id).where(
                UserModel.external_user_id == 'system'
            )
            system_user_result = await self.db.execute(system_user_stmt)
            system_user_id = system_user_result.scalar_one_or_none()
            
            if system_user_id:
                global_stmt = select(PersonalityProfileModel).where(
                    PersonalityProfileModel.user_id == system_user_id,
                    PersonalityProfileModel.personality_name == personality_name
                )
                global_result = await self.db.execute(global_stmt)
                global_personality = global_result.scalar_one_or_none()
                
                if global_personality:
                    config = self._personality_to_dict(global_personality)
                    
                    # Cache for next time
                    if self.cache and config:
                        await self.cache.set_personality_config(personality_name, config)
                        logger.debug(f"💾 Cached config for '{personality_name}'")
                    
                    return config
        
        return None
    
    async def list_personalities(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        List all personalities for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of personality dicts
        """
        stmt = select(PersonalityProfileModel).where(
            PersonalityProfileModel.user_id == user_id
        ).order_by(PersonalityProfileModel.created_at)
        
        result = await self.db.execute(stmt)
        personalities = result.scalars().all()
        
        return [self._personality_to_dict(p) for p in personalities]
    
    async def get_personality_id(self, user_id: UUID, personality_name: str) -> Optional[UUID]:
        """
        Get personality ID by personality name.
        First checks for user-specific personality, then falls back to global personalities.
        Uses Redis cache for global personalities (5-10x faster).
        
        Args:
            user_id: User ID (for user-specific personalities)
            personality_name: Personality name
            
        Returns:
            Personality UUID or None
        """
        # First, try to find user-specific personality (not cached)
        stmt = select(PersonalityProfileModel.id).where(
            PersonalityProfileModel.user_id == user_id,
            PersonalityProfileModel.personality_name == personality_name
        )
        result = await self.db.execute(stmt)
        personality_id = result.scalar_one_or_none()
        
        if personality_id:
            return personality_id
        
        # Try cache for global personality
        if self.cache:
            cached_id = await self.cache.get_personality_id(personality_name)
            if cached_id:
                logger.debug(f"✅ Cache hit for personality '{personality_name}'")
                return UUID(cached_id)
        
        # If not found, look for global personality (owned by system user)
        system_user_stmt = select(UserModel.id).where(
            UserModel.external_user_id == 'system'
        )
        system_user_result = await self.db.execute(system_user_stmt)
        system_user_id = system_user_result.scalar_one_or_none()
        
        if system_user_id:
            global_stmt = select(PersonalityProfileModel.id).where(
                PersonalityProfileModel.user_id == system_user_id,
                PersonalityProfileModel.personality_name == personality_name
            )
            global_result = await self.db.execute(global_stmt)
            global_personality_id = global_result.scalar_one_or_none()
            
            # Cache the result for next time
            if global_personality_id and self.cache:
                await self.cache.set_personality_id(personality_name, str(global_personality_id))
                logger.debug(f"💾 Cached personality '{personality_name}' -> {global_personality_id}")
            
            return global_personality_id
        
        return None
    
    async def create_personality(
        self,
        user_id: UUID,
        personality_name: str,
        archetype: Optional[str] = None,
        traits: Optional[Dict[str, int]] = None,
        behaviors: Optional[Dict[str, bool]] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create personality profile for user.
        
        Args:
            user_id: User ID
            personality_name: Unique name for this personality
            archetype: Archetype name (e.g., 'wise_mentor')
            traits: Custom trait values (0-10)
            behaviors: Custom behavior flags
            custom_config: Additional custom configuration
            
        Returns:
            Created personality dict
        """
        # Check if personality with this name already exists for user
        existing = await self.get_personality(user_id, personality_name)
        if existing:
            raise ValueError(f"Personality '{personality_name}' already exists for this user.")
        
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
            personality_name=personality_name.lower().strip(),
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
        
        # Create initial relationship state for this personality
        await self._create_relationship_state(user_id, personality.id)
        
        logger.info(f"Created personality '{personality_name}' for user {user_id}: archetype={archetype}")
        
        return self._personality_to_dict(personality)
    
    async def update_personality(
        self,
        user_id: UUID,
        personality_name: str,
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
            personality_name: Name of personality to update
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
            PersonalityProfileModel.user_id == user_id,
            PersonalityProfileModel.personality_name == personality_name
        )
        result = await self.db.execute(stmt)
        personality = result.scalar_one_or_none()
        
        if not personality:
            raise ValueError(f"Personality '{personality_name}' not found for this user")
        
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
        
        logger.info(f"Updated personality '{personality_name}' for user {user_id} (version {personality.version})")
        
        return self._personality_to_dict(personality)
    
    async def delete_personality(self, user_id: UUID, personality_name: str) -> bool:
        """
        Delete personality profile.
        
        Args:
            user_id: User ID
            personality_name: Name of personality to delete
            
        Returns:
            True if deleted, False if didn't exist
        """
        stmt = select(PersonalityProfileModel).where(
            PersonalityProfileModel.user_id == user_id,
            PersonalityProfileModel.personality_name == personality_name
        )
        result = await self.db.execute(stmt)
        personality = result.scalar_one_or_none()
        
        if not personality:
            return False
        
        await self.db.delete(personality)
        await self.db.commit()
        
        logger.info(f"Deleted personality '{personality_name}' for user {user_id}")
        
        return True
    
    # ========== Relationship State Management ==========
    
    async def get_relationship_state(self, user_id: UUID, personality_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get relationship state metrics for a specific personality.
        
        Args:
            user_id: User ID
            personality_id: Personality ID (if None, gets first relationship state found)
            
        Returns:
            Relationship state dict
        """
        stmt = select(RelationshipStateModel).where(
            RelationshipStateModel.user_id == user_id
        )
        
        if personality_id:
            stmt = stmt.where(RelationshipStateModel.personality_id == personality_id)
        
        result = await self.db.execute(stmt)
        state = result.scalar_one_or_none()
        
        if not state and personality_id:
            # Create initial state for this personality
            state = await self._create_relationship_state(user_id, personality_id)
        
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
        personality_id: UUID,
        message_sent: bool = False,
        positive_reaction: bool = False,
        negative_reaction: bool = False
    ) -> None:
        """
        Update relationship metrics after interaction with a specific personality.
        
        Args:
            user_id: User ID
            personality_id: Personality ID
            message_sent: Whether user sent a message
            positive_reaction: Whether user gave positive feedback
            negative_reaction: Whether user gave negative feedback
        """
        stmt = select(RelationshipStateModel).where(
            RelationshipStateModel.user_id == user_id,
            RelationshipStateModel.personality_id == personality_id
        )
        result = await self.db.execute(stmt)
        state = result.scalar_one_or_none()
        
        if not state:
            state = await self._create_relationship_state(user_id, personality_id)
        
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
    
    async def _create_relationship_state(self, user_id: UUID, personality_id: UUID) -> RelationshipStateModel:
        """Create initial relationship state for a personality."""
        state = RelationshipStateModel(
            user_id=user_id,
            personality_id=personality_id,
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
            'id': str(personality.id),
            'personality_name': personality.personality_name,
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

