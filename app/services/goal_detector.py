"""Goal detection from natural language with AI chaining."""

import re
import json
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoalDetector:
    """
    Detects goals and goal-related mentions from user messages.
    
    Supports multiple detection methods:
    - Pattern-based (regex matching)
    - LLM-based (AI chaining for intelligent detection)
    - Hybrid (LLM with pattern fallback)
    
    Can identify:
    - New goal declarations (explicit and implicit)
    - Progress updates
    - Obstacles/setbacks
    - Completions
    - Goal mentions
    """
    
    def __init__(self, llm_client=None, method: str = None):
        """
        Initialize goal detector.
        
        Args:
            llm_client: Optional LLM client for AI-based detection
            method: Detection method ("llm", "pattern", "hybrid"). Defaults to config setting.
        """
        self.llm_client = llm_client
        self.method = method or settings.goal_detection_method.lower()
        logger.info(f"GoalDetector initialized with method: {self.method}")
    
    # Goal declaration patterns
    GOAL_PATTERNS = {
        'explicit': [
            r'(my goal|my dream|my aspiration) is to',
            r'i want to (learn|achieve|accomplish|become|get|reach)',
            r'i\'m (planning|hoping|trying|working) to',
            r'i\'d like to',
            r'i need to',
            r'i should',
            r'i will',
            r'i\'m going to',
            r'by (next year|2024|2025|the end of)',
            r'i\'m aiming (to|for)',
            r'i aspire to',
            r'i\'m determined to',
            r'my intention is to'
        ],
        'implicit': [
            r'(starting|beginning|committing to)',
            r'(working on|focusing on) .*(goal|project|learning)',
            r'decided to',
            r'(planning|preparing) for'
        ]
    }
    
    # Progress indicators
    PROGRESS_PATTERNS = {
        'positive': [
            r'(made|making) (good |great |)progress',
            r'(finished|completed|done with)',
            r'(finally |just |)(achieved|accomplished|did|reached)',
            r'(getting|got) (better|closer|good) at',
            r'(improved|improving)',
            r'(successful|succeeded) (in|at|with)',
            r'(mastered|learned)',
            r'milestone',
            r'breakthrough',
            r'on track',
            r'ahead of schedule'
        ],
        'negative': [
            r'(struggling|stuck|having trouble) (with|on)',
            r'(not making|no) progress',
            r'(behind|falling behind) (on|schedule)',
            r'(difficult|hard|challenging)',
            r'(obstacle|setback|problem)',
            r'(can\'t (seem to|figure out))',
            r'frustrated (with|by)',
            r'gave up (on|)',
            r'abandoned',
            r'too hard',
            r'off track'
        ],
        'neutral': [
            r'(still working|continuing) (on|with)',
            r'(currently|right now) (learning|practicing|studying)',
            r'(been|was) (working|practicing|studying)',
            r'spent .* (hours|minutes|time) (on|)',
            r'(today|yesterday|this week) i (worked|practiced|studied)'
        ]
    }
    
    # Completion indicators
    COMPLETION_PATTERNS = [
        r'(finally |just |)(finished|completed|accomplished|achieved)',
        r'(reached|hit|met) (my |the |)goal',
        r'(done|finished) with',
        r'mission accomplished',
        r'goal (achieved|completed|met)',
        r'(successfully|finally) (became|got|reached|earned)',
        r'proud to (say|announce)',
        r'excited to (share|announce)'
    ]
    
    # Time reference patterns
    TIME_PATTERNS = {
        'deadline': [
            r'by (next year|2024|2025|january|february|march|april|may|june|july|august|september|october|november|december)',
            r'in (\d+) (days|weeks|months|years)',
            r'by (the end of|end of)',
            r'before (next|)',
            r'within (\d+)'
        ]
    }
    
    # Category indicators
    CATEGORY_PATTERNS = {
        'learning': [
            r'learn|study|practice|course|class|tutorial|training|education|skill',
            r'(reading|read) (book|article)',
            r'(certification|certificate|degree|diploma)',
            r'(programming|coding|language|spanish|french|german|chinese|japanese)'
        ],
        'health': [
            r'(lose|gain) weight',
            r'(exercise|workout|gym|fitness|running|jogging)',
            r'(diet|nutrition|eating|healthy)',
            r'(sleep|rest|meditation|yoga)',
            r'(mental health|therapy|wellness)',
            r'(quit|stop) (smoking|drinking)',
            r'(pounds|kg|lbs|miles|km)'
        ],
        'career': [
            r'(job|career|work|employment)',
            r'(promotion|raise|salary)',
            r'(interview|application|resume)',
            r'(start|launch) (business|company|startup)',
            r'(networking|professional)',
            r'(skills|experience) for (work|job|career)'
        ],
        'financial': [
            r'(save|saving|savings)',
            r'(invest|investment|stocks|crypto)',
            r'(budget|budgeting|money)',
            r'(debt|loan|mortgage)',
            r'(dollars|euros|\$|€|£)',
            r'(financial|finance|economy)',
            r'(emergency fund|retirement)'
        ],
        'personal': [
            r'(relationship|dating|marriage)',
            r'(family|friends|social)',
            r'(hobby|interest|passion)',
            r'(travel|trip|vacation)',
            r'(move|moving|relocate)',
            r'(organize|declutter|clean)'
        ],
        'creative': [
            r'(write|writing|novel|book|story)',
            r'(paint|painting|draw|drawing|art)',
            r'(music|song|instrument|guitar|piano)',
            r'(create|make|build) (art|music|project)',
            r'(photography|photo)',
            r'(design|designer)'
        ],
        'social': [
            r'(make|meet) (friends|people)',
            r'(social|socialize|socializing)',
            r'(community|volunteer|volunteering)',
            r'(network|networking)',
            r'(relationship|relationships)',
            r'(communicate|communication)'
        ]
    }
    
    async def detect_goal(self, message: str, context: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Detect if message contains a new goal declaration using configured method.
        
        Args:
            message: User message
            context: Optional list of previous messages for context
        
        Returns:
            {
                'title': 'Learn Spanish',
                'category': 'learning',
                'confidence': 0.85,
                'commitment_level': 0.9,
                'target_date': '2025-12-31',
                'motivation': 'for my trip to Spain'
            }
        """
        # Choose detection method
        if self.method == "llm":
            return await self._detect_goal_with_llm(message, context)
        elif self.method == "pattern":
            return self._detect_goal_with_patterns(message)
        else:  # hybrid (default)
            # Try LLM first
            llm_result = await self._detect_goal_with_llm(message, context)
            if llm_result and llm_result.get('confidence', 0) >= 0.6:
                logger.debug(f"Using LLM goal detection (confidence: {llm_result['confidence']:.2f})")
                return llm_result
            # Fallback to patterns
            logger.debug("LLM goal detection low confidence or failed, falling back to pattern matching")
            return self._detect_goal_with_patterns(message)
    
    def _detect_goal_with_patterns(self, message: str) -> Optional[Dict]:
        """
        Detect goal using pattern matching (original method).
        
        Returns:
            Goal dict or None
        """
        message_lower = message.lower()
        
        # Check for goal patterns
        is_goal = False
        confidence = 0.0
        
        for pattern in self.GOAL_PATTERNS['explicit']:
            if re.search(pattern, message_lower):
                is_goal = True
                confidence = 0.9
                break
        
        if not is_goal:
            for pattern in self.GOAL_PATTERNS['implicit']:
                if re.search(pattern, message_lower):
                    is_goal = True
                    confidence = 0.6
                    break
        
        if not is_goal:
            return None
        
        # Extract goal details
        category = self._detect_category(message_lower)
        target_date = self._extract_target_date(message_lower)
        title = self._extract_goal_title(message)
        
        return {
            'title': title,
            'category': category,
            'confidence': confidence,
            'commitment_level': confidence,  # Use confidence as commitment for patterns
            'target_date': target_date,
            'raw_message': message
        }
    
    async def _detect_goal_with_llm(self, message: str, context: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Detect goal using LLM (AI chaining for intelligent detection).
        
        Args:
            message: User message
            context: Optional list of previous messages
            
        Returns:
            Goal dict or None
        """
        if not self.llm_client:
            logger.debug("LLM client not available for goal detection")
            return None
        
        # Build context string
        context_str = ""
        if context and len(context) > 0:
            context_str = "\nPrevious messages:\n" + "\n".join(f"- {msg}" for msg in context[-3:])
        
        prompt = f"""Analyze if this message contains a goal, aspiration, or intention.

Current message: "{message}"{context_str}

Identify:
1. Is this a goal/aspiration/intention? (explicit or implicit)
2. What is the goal?
3. How committed is the user? (0.0-1.0)
4. What category does it belong to?
5. Any target timeframe?
6. Any motivation mentioned?

Consider:
- Explicit goals: "I want to learn Spanish", "My goal is to..."
- Implicit goals: "I should probably exercise more", "I've been thinking about..."
- Commitment level: Serious intention vs casual mention
- Context from previous messages

Categories:
learning, health, career, financial, personal, creative, social

Return ONLY valid JSON:
{{
  "is_goal": true,
  "title": "brief, clear goal statement",
  "category": "learning",
  "confidence": 0.0-1.0,
  "commitment_level": 0.0-1.0,
  "target_timeframe": "short-term|medium-term|long-term|none",
  "target_date": "YYYY-MM-DD or null",
  "motivation": "why they want this or null",
  "reasoning": "why this is/isn't a goal"
}}

If NOT a goal, return: {{"is_goal": false, "confidence": 0.0}}

JSON:"""
        
        try:
            response = await self.llm_client.chat([
                {"role": "system", "content": "You are a goal detection expert. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ])
            
            # Parse JSON response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                logger.warning("No JSON found in LLM goal response")
                return None
            
            result = json.loads(json_match.group())
            
            # Validate result
            if not result.get('is_goal') or result.get('confidence', 0) < 0.3:
                return None
            
            title = result.get('title', '').strip()
            if not title or len(title) < 3:
                logger.warning("LLM returned invalid goal title")
                return None
            
            category = result.get('category', 'personal').lower()
            confidence = float(result.get('confidence', 0.5))
            commitment_level = float(result.get('commitment_level', confidence))
            
            logger.info(
                f"LLM detected goal: '{title}' (category: {category}, "
                f"confidence: {confidence:.2f}, commitment: {commitment_level:.2f})"
            )
            
            return {
                'title': title,
                'category': category,
                'confidence': min(confidence, 1.0),
                'commitment_level': min(commitment_level, 1.0),
                'target_date': result.get('target_date'),
                'motivation': result.get('motivation'),
                'target_timeframe': result.get('target_timeframe', 'none'),
                'raw_message': message,
                'detection_method': 'llm'
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM goal JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM goal detection failed: {e}")
            return None
    
    def detect_progress_mention(
        self,
        message: str,
        existing_goals: List[Dict]
    ) -> List[Dict]:
        """
        Detect mentions of existing goals in the message.
        
        Args:
            message: User message
            existing_goals: List of user's active goals
            
        Returns:
            List of {goal_id, progress_type, sentiment, content}
        """
        mentions = []
        message_lower = message.lower()
        
        for goal in existing_goals:
            # Check if goal is mentioned
            goal_keywords = self._extract_keywords(goal['title'])
            
            match_score = sum(
                1 for keyword in goal_keywords
                if keyword.lower() in message_lower
            )
            
            if match_score > 0:
                # Determine progress type
                progress_type, sentiment = self._analyze_progress_sentiment(message_lower)
                
                mentions.append({
                    'goal_id': goal['id'],
                    'goal_title': goal['title'],
                    'progress_type': progress_type,
                    'sentiment': sentiment,
                    'content': message,
                    'match_score': match_score / len(goal_keywords)
                })
        
        return mentions
    
    def detect_completion(self, message: str) -> bool:
        """Check if message indicates goal completion."""
        message_lower = message.lower()
        
        for pattern in self.COMPLETION_PATTERNS:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def _detect_category(self, message: str) -> str:
        """Detect goal category from message content."""
        category_scores = {}
        
        for category, patterns in self.CATEGORY_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message):
                    score += 1
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return 'personal'  # Default
    
    def _extract_target_date(self, message: str) -> Optional[str]:
        """Extract target date from message."""
        # Try to find explicit dates
        for pattern in self.TIME_PATTERNS['deadline']:
            match = re.search(pattern, message)
            if match:
                # Parse and return ISO date
                # Simplified - would need proper date parsing
                return None  # Placeholder
        
        return None
    
    def _extract_goal_title(self, message: str) -> str:
        """Extract a clean goal title from message."""
        # Remove common prefixes
        cleaned = re.sub(
            r'^(my goal is to|i want to|i\'m planning to|i\'d like to|i need to|i should|i will|i\'m going to)\s+',
            '',
            message.lower()
        )
        
        # Take first sentence or up to 100 chars
        cleaned = cleaned.split('.')[0]
        if len(cleaned) > 100:
            cleaned = cleaned[:97] + '...'
        
        # Capitalize first letter
        return cleaned.capitalize()
    
    def _extract_keywords(self, title: str) -> List[str]:
        """Extract key words from goal title for matching."""
        # Remove common words
        stop_words = {'i', 'me', 'my', 'the', 'a', 'an', 'to', 'for', 'in', 'on', 'at', 'by'}
        
        words = title.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        return keywords
    
    def _analyze_progress_sentiment(self, message: str) -> Tuple[str, str]:
        """
        Analyze progress type and sentiment.
        
        Returns:
            (progress_type, sentiment)
        """
        # Check for positive progress
        for pattern in self.PROGRESS_PATTERNS['positive']:
            if re.search(pattern, message):
                return 'update', 'positive'
        
        # Check for negative progress
        for pattern in self.PROGRESS_PATTERNS['negative']:
            if re.search(pattern, message):
                return 'setback', 'negative'
        
        # Check for neutral progress
        for pattern in self.PROGRESS_PATTERNS['neutral']:
            if re.search(pattern, message):
                return 'mention', 'neutral'
        
        # Check for completion
        if self.detect_completion(message):
            return 'completion', 'positive'
        
        return 'mention', 'neutral'
    
    def extract_obstacles(self, message: str) -> Optional[str]:
        """Extract mentioned obstacles from message."""
        obstacle_patterns = [
            r'(problem|issue|challenge|obstacle|difficulty) (is|with|:)',
            r'(struggling|stuck) (with|on|because)',
            r'(can\'t|cannot) .* because',
            r'(too|very) (hard|difficult|challenging)'
        ]
        
        for pattern in obstacle_patterns:
            if re.search(pattern, message.lower()):
                # Extract the context around the pattern
                return message  # Simplified - would extract specific obstacle
        
        return None
    
    def extract_motivation(self, message: str) -> Optional[str]:
        """Extract motivation from message."""
        motivation_patterns = [
            r'because',
            r'so that',
            r'in order to',
            r'for my',
            r'to help',
            r'want to .* because'
        ]
        
        for pattern in motivation_patterns:
            if re.search(pattern, message.lower()):
                return message  # Simplified - would extract specific motivation
        
        return None

