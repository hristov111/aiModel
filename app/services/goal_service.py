"""Goal tracking and management service."""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import GoalModel, GoalProgressModel
from app.services.goal_detector import GoalDetector

logger = logging.getLogger(__name__)


class GoalService:
    """
    Manages user goals, tracks progress, and provides insights.
    """
    
    def __init__(self, db_session: AsyncSession, llm_client=None):
        """
        Initialize goal service.
        
        Args:
            db_session: Database session
            llm_client: Optional LLM client for AI-based goal detection
        """
        self.db = db_session
        self.detector = GoalDetector(llm_client=llm_client)
    
    async def create_goal(
        self,
        user_id: UUID,
        title: str,
        category: str = 'personal',
        description: Optional[str] = None,
        target_date: Optional[datetime] = None,
        motivation: Optional[str] = None,
        check_in_frequency: Optional[str] = 'weekly'
    ) -> Dict:
        """
        Create a new goal.
        
        Args:
            user_id: User ID
            title: Goal title
            category: Goal category
            description: Detailed description
            target_date: Optional deadline
            motivation: Why user wants this
            check_in_frequency: How often to check in
            
        Returns:
            Created goal dict
        """
        goal = GoalModel(
            user_id=user_id,
            title=title,
            category=category,
            description=description,
            target_date=target_date,
            motivation=motivation,
            check_in_frequency=check_in_frequency,
            status='active',
            progress_percentage=0.0
        )
        
        self.db.add(goal)
        await self.db.commit()
        await self.db.refresh(goal)
        
        logger.info(f"Created goal for user {user_id}: {title}")
        
        return self._goal_to_dict(goal)
    
    async def get_user_goals(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        category: Optional[str] = None,
        include_completed: bool = False
    ) -> List[Dict]:
        """
        Get user's goals with optional filtering.
        
        Args:
            user_id: User ID
            status: Filter by status
            category: Filter by category
            include_completed: Include completed goals
            
        Returns:
            List of goal dicts
        """
        stmt = select(GoalModel).where(GoalModel.user_id == user_id)
        
        if status:
            stmt = stmt.where(GoalModel.status == status)
        elif not include_completed:
            stmt = stmt.where(GoalModel.status.in_(['active', 'paused']))
        
        if category:
            stmt = stmt.where(GoalModel.category == category)
        
        stmt = stmt.order_by(desc(GoalModel.updated_at))
        
        result = await self.db.execute(stmt)
        goals = result.scalars().all()
        
        return [self._goal_to_dict(g) for g in goals]
    
    async def get_goal(self, goal_id: UUID, user_id: UUID) -> Optional[Dict]:
        """Get a specific goal."""
        stmt = select(GoalModel).where(
            and_(
                GoalModel.id == goal_id,
                GoalModel.user_id == user_id
            )
        )
        
        result = await self.db.execute(stmt)
        goal = result.scalar_one_or_none()
        
        if not goal:
            return None
        
        return self._goal_to_dict(goal)
    
    async def update_goal(
        self,
        goal_id: UUID,
        user_id: UUID,
        **updates
    ) -> Optional[Dict]:
        """Update goal fields."""
        stmt = select(GoalModel).where(
            and_(
                GoalModel.id == goal_id,
                GoalModel.user_id == user_id
            )
        )
        
        result = await self.db.execute(stmt)
        goal = result.scalar_one_or_none()
        
        if not goal:
            return None
        
        for key, value in updates.items():
            if hasattr(goal, key):
                setattr(goal, key, value)
        
        goal.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(goal)
        
        return self._goal_to_dict(goal)
    
    async def record_progress(
        self,
        goal_id: UUID,
        user_id: UUID,
        content: str,
        progress_type: str = 'mention',
        progress_delta: Optional[float] = None,
        sentiment: Optional[str] = None,
        emotion: Optional[str] = None,
        conversation_id: Optional[UUID] = None,
        detected_automatically: bool = True
    ) -> Dict:
        """
        Record a progress update for a goal.
        
        Args:
            goal_id: Goal ID
            user_id: User ID
            content: What was said/done
            progress_type: Type of progress
            progress_delta: Change in percentage
            sentiment: positive, negative, neutral
            emotion: Detected emotion
            conversation_id: Source conversation
            detected_automatically: Auto-detected vs manual
            
        Returns:
            Created progress entry
        """
        # Create progress entry
        progress = GoalProgressModel(
            goal_id=goal_id,
            user_id=user_id,
            content=content,
            progress_type=progress_type,
            progress_delta=progress_delta,
            sentiment=sentiment,
            emotion=emotion,
            conversation_id=conversation_id,
            detected_automatically=detected_automatically
        )
        
        self.db.add(progress)
        
        # Update goal
        stmt = select(GoalModel).where(GoalModel.id == goal_id)
        result = await self.db.execute(stmt)
        goal = result.scalar_one_or_none()
        
        if goal:
            # Update last mentioned
            goal.last_mentioned_at = datetime.utcnow()
            goal.mention_count += 1
            
            # Update progress percentage if provided
            if progress_delta is not None:
                new_progress = max(0, min(100, goal.progress_percentage + progress_delta))
                goal.progress_percentage = new_progress
            
            # Add to progress notes
            if not goal.progress_notes:
                goal.progress_notes = []
            
            goal.progress_notes.append({
                'date': datetime.utcnow().isoformat(),
                'observation': content[:200],
                'type': progress_type,
                'sentiment': sentiment
            })
            
            # Check for completion
            if progress_type == 'completion' or goal.progress_percentage >= 100:
                goal.status = 'completed'
                goal.completed_at = datetime.utcnow()
                logger.info(f"Goal completed: {goal.title}")
        
        await self.db.commit()
        await self.db.refresh(progress)
        
        return {
            'id': str(progress.id),
            'goal_id': str(progress.goal_id),
            'progress_type': progress.progress_type,
            'sentiment': progress.sentiment,
            'created_at': progress.created_at.isoformat()
        }
    
    async def detect_and_track_goals(
        self,
        user_id: UUID,
        message: str,
        conversation_id: Optional[UUID] = None,
        detected_emotion: Optional[str] = None
    ) -> Dict:
        """
        Automatically detect and track goals from user message.
        
        Returns:
            {
                'new_goals': [],
                'progress_updates': [],
                'completions': []
            }
        """
        result = {
            'new_goals': [],
            'progress_updates': [],
            'completions': []
        }
        
        # 1. Check for new goal declaration
        detected_goal = await self.detector.detect_goal(message)
        if detected_goal and detected_goal.get('confidence', 0) > 0.7:
            # Parse target_date (LLM may return ISO string)
            target_date = detected_goal.get('target_date')
            if isinstance(target_date, str) and target_date.strip():
                try:
                    target_date = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
                except Exception:
                    logger.debug(f"Ignoring unparsable goal target_date: {target_date!r}")
                    target_date = None
            elif not isinstance(target_date, datetime):
                target_date = None

            # Create goal
            goal = await self.create_goal(
                user_id=user_id,
                title=detected_goal['title'],
                category=detected_goal['category'],
                target_date=target_date,
                motivation=detected_goal.get('motivation') or self.detector.extract_motivation(message)
            )
            result['new_goals'].append(goal)
            logger.info(f"Auto-created goal: {detected_goal['title']}")
        
        # 2. Check for progress on existing goals
        existing_goals = await self.get_user_goals(user_id, include_completed=False)
        
        if existing_goals:
            mentions = self.detector.detect_progress_mention(
                message,
                existing_goals
            )
            
            for mention in mentions:
                if mention['match_score'] > 0.3:  # Confidence threshold
                    progress = await self.record_progress(
                        goal_id=UUID(mention['goal_id']),
                        user_id=user_id,
                        content=message,
                        progress_type=mention['progress_type'],
                        sentiment=mention['sentiment'],
                        emotion=detected_emotion,
                        conversation_id=conversation_id,
                        detected_automatically=True
                    )
                    
                    result['progress_updates'].append({
                        'goal': mention['goal_title'],
                        'type': mention['progress_type'],
                        'sentiment': mention['sentiment']
                    })
                    
                    # Check if completion
                    if mention['progress_type'] == 'completion':
                        result['completions'].append(mention['goal_title'])
        
        return result
    
    async def get_goals_needing_checkin(
        self,
        user_id: UUID,
        days_since_last: int = 7
    ) -> List[Dict]:
        """
        Get goals that need a check-in.
        
        Args:
            user_id: User ID
            days_since_last: Days since last check-in
            
        Returns:
            List of goals needing attention
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_since_last)
        
        stmt = (
            select(GoalModel)
            .where(
                and_(
                    GoalModel.user_id == user_id,
                    GoalModel.status == 'active',
                    or_(
                        GoalModel.last_check_in.is_(None),
                        GoalModel.last_check_in < cutoff_date
                    )
                )
            )
            .order_by(GoalModel.last_mentioned_at.asc())
        )
        
        result = await self.db.execute(stmt)
        goals = result.scalars().all()
        
        return [self._goal_to_dict(g) for g in goals]
    
    async def mark_checkin_done(self, goal_id: UUID) -> None:
        """Mark that AI checked in on this goal."""
        stmt = select(GoalModel).where(GoalModel.id == goal_id)
        result = await self.db.execute(stmt)
        goal = result.scalar_one_or_none()
        
        if goal:
            goal.last_check_in = datetime.utcnow()
            await self.db.commit()
    
    async def get_goal_analytics(self, user_id: UUID) -> Dict:
        """
        Get analytics about user's goals.
        
        Returns:
            Rich analytics dict
        """
        # Get all goals
        all_goals_stmt = select(GoalModel).where(GoalModel.user_id == user_id)
        result = await self.db.execute(all_goals_stmt)
        all_goals = result.scalars().all()
        
        # Calculate stats
        stats = {
            'total_goals': len(all_goals),
            'active_goals': len([g for g in all_goals if g.status == 'active']),
            'completed_goals': len([g for g in all_goals if g.status == 'completed']),
            'paused_goals': len([g for g in all_goals if g.status == 'paused']),
            'abandoned_goals': len([g for g in all_goals if g.status == 'abandoned']),
            'completion_rate': 0.0,
            'by_category': {},
            'average_progress': 0.0,
            'goals_with_deadlines': 0,
            'overdue_goals': 0
        }
        
        if stats['total_goals'] > 0:
            stats['completion_rate'] = (
                stats['completed_goals'] / stats['total_goals'] * 100
            )
        
        # By category
        for goal in all_goals:
            if goal.category not in stats['by_category']:
                stats['by_category'][goal.category] = {
                    'total': 0,
                    'active': 0,
                    'completed': 0,
                    'avg_progress': 0.0
                }
            
            stats['by_category'][goal.category]['total'] += 1
            if goal.status == 'active':
                stats['by_category'][goal.category]['active'] += 1
            elif goal.status == 'completed':
                stats['by_category'][goal.category]['completed'] += 1
        
        # Average progress (active goals only)
        active_goals = [g for g in all_goals if g.status == 'active']
        if active_goals:
            stats['average_progress'] = sum(
                g.progress_percentage for g in active_goals
            ) / len(active_goals)
        
        # Deadlines
        now = datetime.utcnow()
        for goal in all_goals:
            if goal.target_date:
                stats['goals_with_deadlines'] += 1
                if goal.target_date < now and goal.status == 'active':
                    stats['overdue_goals'] += 1
        
        # Recent activity
        stmt = (
            select(GoalProgressModel)
            .where(GoalProgressModel.user_id == user_id)
            .order_by(desc(GoalProgressModel.created_at))
            .limit(10)
        )
        result = await self.db.execute(stmt)
        recent_progress = result.scalars().all()
        
        stats['recent_activity'] = [
            {
                'goal_id': str(p.goal_id),
                'type': p.progress_type,
                'sentiment': p.sentiment,
                'date': p.created_at.isoformat()
            }
            for p in recent_progress
        ]
        
        return stats
    
    async def get_goal_progress_history(
        self,
        goal_id: UUID,
        user_id: UUID,
        limit: int = 50
    ) -> List[Dict]:
        """Get progress history for a goal."""
        stmt = (
            select(GoalProgressModel)
            .where(
                and_(
                    GoalProgressModel.goal_id == goal_id,
                    GoalProgressModel.user_id == user_id
                )
            )
            .order_by(desc(GoalProgressModel.created_at))
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        progress_entries = result.scalars().all()
        
        return [
            {
                'id': str(p.id),
                'type': p.progress_type,
                'content': p.content,
                'sentiment': p.sentiment,
                'emotion': p.emotion,
                'progress_delta': p.progress_delta,
                'created_at': p.created_at.isoformat()
            }
            for p in progress_entries
        ]
    
    def _goal_to_dict(self, goal: GoalModel) -> Dict:
        """Convert GoalModel to dict."""
        return {
            'id': str(goal.id),
            'title': goal.title,
            'description': goal.description,
            'category': goal.category,
            'status': goal.status,
            'progress_percentage': goal.progress_percentage,
            'target_date': goal.target_date.isoformat() if goal.target_date else None,
            'created_at': goal.created_at.isoformat(),
            'updated_at': goal.updated_at.isoformat(),
            'completed_at': goal.completed_at.isoformat() if goal.completed_at else None,
            'last_mentioned_at': goal.last_mentioned_at.isoformat() if goal.last_mentioned_at else None,
            'mention_count': goal.mention_count,
            'check_in_frequency': goal.check_in_frequency,
            'last_check_in': goal.last_check_in.isoformat() if goal.last_check_in else None,
            'milestones': goal.milestones or [],
            'progress_notes': goal.progress_notes or [],
            'motivation': goal.motivation,
            'obstacles': goal.obstacles or []
        }

