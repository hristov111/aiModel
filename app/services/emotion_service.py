"""Service for managing emotion detection and history tracking."""

import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import EmotionHistoryModel
from app.services.emotion_detector import EmotionDetector, DetectedEmotion

logger = logging.getLogger(__name__)


class EmotionService:
    """Manages emotion detection, storage, and analysis."""
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize emotion service.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
        self.detector = EmotionDetector()
    
    async def detect_and_store(
        self,
        user_id: UUID,
        message: str,
        conversation_id: Optional[UUID] = None
    ) -> Optional[DetectedEmotion]:
        """
        Detect emotion from message and store in history.
        
        Args:
            user_id: User ID
            message: User message text
            conversation_id: Optional conversation ID
            
        Returns:
            DetectedEmotion object or None
        """
        # Detect emotion
        emotion = self.detector.detect(message)
        
        if not emotion:
            return None
        
        # Store in database
        try:
            snippet = message[:100] if len(message) > 100 else message
            
            emotion_record = EmotionHistoryModel(
                user_id=user_id,
                conversation_id=conversation_id,
                emotion=emotion.emotion,
                confidence=emotion.confidence,
                intensity=emotion.intensity,
                indicators=emotion.indicators,
                message_snippet=snippet,
                detected_at=emotion.detected_at
            )
            
            self.db.add(emotion_record)
            await self.db.commit()
            
            logger.info(
                f"Stored emotion for user {user_id}: {emotion.emotion} "
                f"(confidence: {emotion.confidence:.2f})"
            )
            
            return emotion
            
        except Exception as e:
            logger.error(f"Failed to store emotion: {e}")
            await self.db.rollback()
            # Don't fail the whole request if emotion storage fails
            return emotion
    
    async def get_recent_emotions(
        self,
        user_id: UUID,
        limit: int = 10,
        days: int = 30
    ) -> List[Dict]:
        """
        Get recent emotion history for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of emotions to return
            days: Look back this many days
            
        Returns:
            List of emotion dictionaries
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = (
            select(EmotionHistoryModel)
            .where(
                EmotionHistoryModel.user_id == user_id,
                EmotionHistoryModel.detected_at >= cutoff_date
            )
            .order_by(desc(EmotionHistoryModel.detected_at))
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        emotions = result.scalars().all()
        
        return [
            {
                'emotion': e.emotion,
                'confidence': e.confidence,
                'intensity': e.intensity,
                'indicators': e.indicators,
                'message_snippet': e.message_snippet,
                'detected_at': e.detected_at.isoformat(),
                'conversation_id': str(e.conversation_id) if e.conversation_id else None
            }
            for e in emotions
        ]
    
    async def get_emotion_trends(
        self,
        user_id: UUID,
        days: int = 30
    ) -> Dict:
        """
        Analyze emotion trends for a user.
        
        Args:
            user_id: User ID
            days: Analyze emotions from this many days back
            
        Returns:
            Trend analysis dictionary
        """
        # Get recent emotions
        recent_emotions = await self.get_recent_emotions(
            user_id=user_id,
            limit=50,
            days=days
        )
        
        # Use detector's analysis
        analysis = self.detector.analyze_emotion_trend(recent_emotions)
        
        return analysis
    
    async def get_emotion_statistics(
        self,
        user_id: UUID,
        days: int = 30
    ) -> Dict:
        """
        Get detailed emotion statistics for a user.
        
        Args:
            user_id: User ID
            days: Look back this many days
            
        Returns:
            Statistics dictionary with counts and percentages
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Count emotions by type
        stmt = (
            select(
                EmotionHistoryModel.emotion,
                func.count(EmotionHistoryModel.id).label('count'),
                func.avg(EmotionHistoryModel.confidence).label('avg_confidence')
            )
            .where(
                EmotionHistoryModel.user_id == user_id,
                EmotionHistoryModel.detected_at >= cutoff_date
            )
            .group_by(EmotionHistoryModel.emotion)
            .order_by(desc('count'))
        )
        
        result = await self.db.execute(stmt)
        emotion_counts = result.all()
        
        # Calculate statistics
        total = sum(row.count for row in emotion_counts)
        
        if total == 0:
            return {
                'total_emotions_detected': 0,
                'period_days': days,
                'emotions': []
            }
        
        emotions_data = [
            {
                'emotion': row.emotion,
                'count': row.count,
                'percentage': (row.count / total) * 100,
                'avg_confidence': round(row.avg_confidence, 2)
            }
            for row in emotion_counts
        ]
        
        # Categorize emotions
        positive_emotions = {'happy', 'excited', 'grateful', 'proud', 'hopeful'}
        negative_emotions = {'sad', 'angry', 'frustrated', 'anxious', 'disappointed', 'lonely'}
        neutral_emotions = {'confused'}
        
        positive_count = sum(
            e['count'] for e in emotions_data 
            if e['emotion'] in positive_emotions
        )
        negative_count = sum(
            e['count'] for e in emotions_data 
            if e['emotion'] in negative_emotions
        )
        neutral_count = sum(
            e['count'] for e in emotions_data 
            if e['emotion'] in neutral_emotions
        )
        
        return {
            'total_emotions_detected': total,
            'period_days': days,
            'emotions': emotions_data,
            'sentiment_breakdown': {
                'positive': {
                    'count': positive_count,
                    'percentage': (positive_count / total) * 100 if total > 0 else 0
                },
                'negative': {
                    'count': negative_count,
                    'percentage': (negative_count / total) * 100 if total > 0 else 0
                },
                'neutral': {
                    'count': neutral_count,
                    'percentage': (neutral_count / total) * 100 if total > 0 else 0
                }
            }
        }
    
    async def clear_emotion_history(
        self,
        user_id: UUID,
        conversation_id: Optional[UUID] = None
    ) -> int:
        """
        Clear emotion history for a user or specific conversation.
        
        Args:
            user_id: User ID
            conversation_id: Optional conversation ID to clear specific conversation
            
        Returns:
            Number of emotions deleted
        """
        from sqlalchemy import delete
        
        if conversation_id:
            stmt = delete(EmotionHistoryModel).where(
                EmotionHistoryModel.user_id == user_id,
                EmotionHistoryModel.conversation_id == conversation_id
            )
        else:
            stmt = delete(EmotionHistoryModel).where(
                EmotionHistoryModel.user_id == user_id
            )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        deleted_count = result.rowcount
        logger.info(f"Cleared {deleted_count} emotions for user {user_id}")
        
        return deleted_count

