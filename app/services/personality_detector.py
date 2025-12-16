"""Detect personality preferences from natural language with AI chaining."""

import re
import json
import logging
from typing import Dict, Optional, Any, List

from app.core.config import settings

logger = logging.getLogger(__name__)


class PersonalityDetector:
    """
    Detects personality preferences from user messages.
    
    Supports multiple detection methods:
    - Pattern-based (regex matching)
    - LLM-based (AI chaining for intelligent detection)
    - Hybrid (LLM with pattern fallback)
    
    Allows users to configure AI personality using natural language like:
    - "Be like a wise mentor"
    - "I want you to be more enthusiastic"
    - "Act like a supportive friend"
    - "I need someone who really gets me" (AI chaining detects this!)
    """
    
    def __init__(self, llm_client=None, method: str = None):
        """
        Initialize personality detector.
        
        Args:
            llm_client: Optional LLM client for AI-based detection
            method: Detection method ("llm", "pattern", "hybrid"). Defaults to config.
        """
        self.llm_client = llm_client
        self.method = method or settings.personality_detection_method.lower()
        logger.info(f"PersonalityDetector initialized with method: {self.method}")
    
    # Archetype detection patterns
    ARCHETYPE_PATTERNS = {
        'wise_mentor': [
            r'(be |act |)like a (wise |)mentor',
            r'guide me|be my guide',
            r'(wise|thoughtful) (advisor|mentor)',
            r'help me (grow|learn|develop)',
            r'challenge me',
            r'teacher.*(wisdom|guide)'
        ],
        'supportive_friend': [
            r'(be |act |)like a (good |best |supportive |)friend',
            r'just (listen|be there)',
            r'(warm|caring) (friend|companion)',
            r'(support|encourage) me',
            r'don\'?t judge( me|)',
            r'be (understanding|compassionate)'
        ],
        'professional_coach': [
            r'(be |act |)like a (professional |)coach',
            r'hold me accountable',
            r'focus on (my |)goals',
            r'help me (achieve|accomplish|reach)',
            r'(push|motivate) me',
            r'results?.?oriented'
        ],
        'creative_partner': [
            r'(be |act |)like a creative partner',
            r'brainstorm( with me|)',
            r'explore ideas',
            r'(creative|imaginative) (thinking|collaboration)',
            r'let\'?s create',
            r'think outside the box'
        ],
        'calm_therapist': [
            r'(be |act |)like a (calm |)therapist',
            r'help me process',
            r'(safe|judgment.?free) space',
            r'listen (without judgment|patiently)',
            r'help me understand (my |)(feelings|emotions)',
            r'(therapeutic|counseling)'
        ],
        'enthusiastic_cheerleader': [
            r'(be |act |)like a cheerleader',
            r'(be my|) biggest fan',
            r'celebrate (with me|everything)',
            r'(super |very |)enthusiastic',
            r'(hype|pump) me up',
            r'keep my spirits high'
        ],
        'pragmatic_advisor': [
            r'(be |act |)like a (pragmatic |practical |)advisor',
            r'(straight|straight.?forward|direct) advice',
            r'no.?nonsense',
            r'(practical|realistic) (solutions|approach)',
            r'(logical|rational) (thinking|advice)',
            r'get to the point'
        ],
        'curious_student': [
            r'(be |act |)like a (curious |)student',
            r'learn (with|alongside) me',
            r'ask (lots of |)questions',
            r'(explore|discover) together',
            r'(curious|inquisitive)',
            r'let\'?s (explore|investigate)'
        ],
        'girlfriend': [
            r'(be |act |)like (my |a |)girlfriend',
            r'be my (romantic |)partner',
            r'(romantic|affectionate) (companion|relationship)',
            r'talk to me like (a girlfriend|we\'?re dating)',
            r'(loving|caring) girlfriend',
            r'be (romantic|affectionate)',
            r'treat me like (your boyfriend|we\'?re together)'
        ]
    }
    
    # Trait adjustment patterns (increase/decrease traits)
    TRAIT_PATTERNS = {
        'humor_level': {
            'increase': [
                r'be (more |)humor(ous|)', r'(make |tell )(more |)(jokes|funny)',
                r'(add |use )(more |)humor', r'be (funnier|playful)',
                r'lighten( the mood| up|)', r'don\'?t be so serious'
            ],
            'decrease': [
                r'(be |)more serious', r'(less|no) (humor|jokes)',
                r'stop (joking|being funny)', r'(be |)professional'
            ]
        },
        'formality_level': {
            'increase': [
                r'(be |)more formal', r'(be |)more professional',
                r'use proper (language|grammar)', r'(be |)polite',
                r'(be |)respectful', r'less casual'
            ],
            'decrease': [
                r'(be |)more casual', r'(be |)less formal',
                r'(loosen|relax) up', r'be (chill|relaxed)',
                r'use (slang|casual language)', r'(be |)informal'
            ]
        },
        'enthusiasm_level': {
            'increase': [
                r'(be |)more (enthusiastic|energetic|excited)',
                r'show more (energy|excitement)', r'(be |)livelier',
                r'more (passion|enthusiasm)', r'pump up the energy'
            ],
            'decrease': [
                r'(be |)more (calm|reserved|measured)',
                r'tone down( the energy|)', r'(be |)less (excited|enthusiastic)',
                r'(be |)more subdued', r'(relax|calm) (down|)'
            ]
        },
        'empathy_level': {
            'increase': [
                r'(be |)more (empathetic|compassionate|understanding)',
                r'show more (empathy|compassion)', r'(be |)sensitive',
                r'understand (my |)feelings', r'(be |)caring'
            ],
            'decrease': [
                r'(be |)more (logical|rational|objective)',
                r'less (emotional|empathetic)', r'focus on (logic|facts)',
                r'(be |)more analytical', r'less feelings'
            ]
        },
        'directness_level': {
            'increase': [
                r'(be |)more (direct|straightforward|blunt)',
                r'just (tell|give) me (the truth|straight)',
                r'don\'?t (sugarcoat|beat around)', r'(be |)honest',
                r'cut to the chase', r'(be |)frank'
            ],
            'decrease': [
                r'(be |)more (gentle|tactful|diplomatic)',
                r'(be |)softer', r'less (direct|blunt|harsh)',
                r'(be |)more careful', r'(be |)nicer'
            ]
        },
        'curiosity_level': {
            'increase': [
                r'ask (more|lots of) questions',
                r'(be |)more (curious|inquisitive)',
                r'(explore|dig) deeper', r'(be |)curious'
            ],
            'decrease': [
                r'(stop |)asking so many questions',
                r'less (curious|inquisitive)', r'(be |)less nosy',
                r'(just |)answer( my questions|)'
            ]
        },
        'supportiveness_level': {
            'increase': [
                r'(be |)more (supportive|encouraging)',
                r'(be my|give me) support', r'encourage me',
                r'(be |)more positive', r'(believe|support) in me'
            ],
            'decrease': [
                r'challenge me (more|)', r'(be |)more critical',
                r'(be |)tough(er|)', r'push (me |)harder',
                r'less (supportive|encouraging)'
            ]
        },
        'playfulness_level': {
            'increase': [
                r'(be |)more (playful|fun)',
                r'(have |add )more fun', r'(be |)less serious',
                r'(be |)more (creative|imaginative)'
            ],
            'decrease': [
                r'(be |)more serious', r'less (playful|silly)',
                r'(be |)more focused', r'(stop |)playing around'
            ]
        }
    }
    
    # Behavior toggle patterns
    BEHAVIOR_PATTERNS = {
        'asks_questions': {
            'enable': [
                r'ask( me|) (more |)(questions|)', r'(be |)curious',
                r'inquire( about|)', r'(be |)inquisitive'
            ],
            'disable': [
                r'(stop |don\'?t )ask(ing|) (so many |)questions',
                r'(just |)answer( my questions|)', r'no (more |)questions'
            ]
        },
        'uses_examples': {
            'enable': [
                r'(give|use|provide) (more |)examples',
                r'show me examples', r'(illustrate|demonstrate)'
            ],
            'disable': [
                r'(no|skip|less) examples', r'(just |)explain (directly|simply)',
                r'(stop |)giving examples'
            ]
        },
        'shares_opinions': {
            'enable': [
                r'share your (opinions|thoughts|views)',
                r'what do you think', r'give( me|) your (opinion|perspective)',
                r'(be |)opinionated'
            ],
            'disable': [
                r'(don\'?t|no) (share |)(your |)(opinions|thoughts)',
                r'(just |)stick to facts', r'(be |)objective',
                r'(stay |be |)neutral'
            ]
        },
        'challenges_user': {
            'enable': [
                r'challenge me', r'push me (harder|)',
                r'(be |)tough(er|) on me', r'(don\'?t|) hold back',
                r'(be |)critical'
            ],
            'disable': [
                r'(stop |don\'?t )challeng(e|ing) me',
                r'(be |)less (critical|tough)', r'(be |)more supportive',
                r'(stop |)pushing( me|)'
            ]
        },
        'celebrates_wins': {
            'enable': [
                r'celebrate (with me|my wins)',
                r'acknowledge (my |)achievements',
                r'(be |)happy for me', r'(share|join) my (joy|excitement)'
            ],
            'disable': [
                r'(don\'?t|no need to) celebrate',
                r'(just |)move on', r'(stay |be |)focused',
                r'(skip|no) celebrations'
            ]
        }
    }
    
    # Relationship type patterns
    RELATIONSHIP_PATTERNS = {
        'friend': [r'(be |act like a |)friend', r'(like |)buddies', r'peers'],
        'mentor': [r'(be |act like a |)mentor', r'teacher', r'guide'],
        'coach': [r'(be |act like a |)coach', r'trainer'],
        'therapist': [r'(be |act like a |)therapist', r'counselor'],
        'partner': [r'(be |act like a |)partner', r'collaborate', r'work together'],
        'advisor': [r'(be |act like an |)advisor', r'consultant'],
        'assistant': [r'(be |act like an |)assistant', r'helper', r'support']
    }
    
    async def detect(self, message: str, context: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Detect personality configuration from message using configured method.
        
        Args:
            message: User message
            context: Optional conversation context
            
        Returns:
            Dict with detected personality config or None
        """
        if not message or len(message.strip()) < 5:
            return None
        
        # Choose detection method
        if self.method == "llm":
            return await self._detect_with_llm(message, context)
        elif self.method == "pattern":
            return self._detect_with_patterns(message)
        else:  # hybrid (default)
            # Try LLM first
            llm_result = await self._detect_with_llm(message, context)
            if llm_result and len(llm_result) > 0:
                logger.debug(f"Using LLM personality detection")
                return llm_result
            # Fallback to patterns
            logger.debug("LLM detection returned nothing, falling back to patterns")
            return self._detect_with_patterns(message)
    
    def _detect_with_patterns(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Detect personality using pattern matching (original method).
        
        Args:
            message: User message
            
        Returns:
            Dict with personality config or None
        """
        message_lower = message.lower()
        config = {}
        
        # Detect archetype
        archetype = self._detect_archetype(message_lower)
        if archetype:
            config['archetype'] = archetype
            logger.info(f"Pattern detected archetype: {archetype}")
        
        # Detect trait adjustments
        traits = self._detect_traits(message_lower)
        if traits:
            config['traits'] = traits
            logger.info(f"Pattern detected trait adjustments: {traits}")
        
        # Detect behavior toggles
        behaviors = self._detect_behaviors(message_lower)
        if behaviors:
            config['behaviors'] = behaviors
            logger.info(f"Pattern detected behavior changes: {behaviors}")
        
        # Detect relationship type
        relationship = self._detect_relationship(message_lower)
        if relationship:
            config['relationship_type'] = relationship
            logger.info(f"Pattern detected relationship type: {relationship}")
        
        # Detect custom instructions
        if any(phrase in message_lower for phrase in ['i want you to', 'you should', 'please']):
            config['custom_instructions'] = message
        
        return config if config else None
    
    async def _detect_with_llm(self, message: str, context: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Detect personality configuration using LLM (AI chaining).
        
        Args:
            message: User message
            context: Optional conversation context
            
        Returns:
            Dict with personality config or None
        """
        if not self.llm_client:
            logger.debug("LLM client not available for personality detection")
            return None
        
        # Build context string
        context_str = ""
        if context and len(context) > 0:
            context_str = "\nRecent conversation:\n" + "\n".join(f"- {msg}" for msg in context[-3:])
        
        prompt = f"""Analyze if this message contains personality or communication style preferences for an AI assistant.

Current message: "{message}"{context_str}

Identify:
1. Personality archetype (if mentioned)
2. Trait adjustments (0-10 scales)
3. Behavioral preferences
4. Relationship type
5. Custom instructions

Available archetypes:
- wise_mentor: Thoughtful advisor who challenges and guides
- supportive_friend: Warm, caring, non-judgmental listener
- professional_coach: Results-oriented, holds accountable
- creative_partner: Brainstorms, explores ideas together
- calm_therapist: Patient, helps process emotions
- enthusiastic_cheerleader: Energetic supporter, celebrates wins
- pragmatic_advisor: Direct, practical, no-nonsense advice
- curious_student: Learns alongside, asks questions
- girlfriend: Romantic, affectionate companion

Traits (0-10 scales):
- humor_level: 0=serious, 10=very humorous
- formality_level: 0=casual, 10=very formal
- enthusiasm_level: 0=reserved, 10=very enthusiastic
- empathy_level: 0=logical, 10=highly empathetic
- directness_level: 0=indirect, 10=very direct
- curiosity_level: 0=passive, 10=very curious
- supportiveness_level: 0=challenging, 10=highly supportive
- playfulness_level: 0=serious, 10=very playful

Behaviors (true/false):
- asks_questions: Should AI ask questions?
- uses_examples: Should AI give examples?
- shares_opinions: Should AI share opinions?
- challenges_user: Should AI challenge/push user?
- celebrates_wins: Should AI celebrate achievements?

Relationship types:
friend, mentor, coach, therapist, partner, advisor, assistant, girlfriend

Return ONLY valid JSON:
{{
  "archetype": "archetype_name or null",
  "traits": {{
    "trait_name": 0-10 value
  }},
  "behaviors": {{
    "behavior_name": true/false
  }},
  "relationship_type": "type or null",
  "custom_instructions": "any specific requests or null",
  "confidence": 0.0-1.0,
  "reasoning": "why this was detected"
}}

If NO personality preferences detected, return: {{"confidence": 0.0}}

JSON:"""
        
        try:
            response = await self.llm_client.chat([
                {"role": "system", "content": "You are a personality configuration expert. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ])
            
            # Parse JSON response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                logger.warning("No JSON found in LLM personality response")
                return None
            
            result = json.loads(json_match.group())
            
            # Validate result
            confidence = result.get('confidence', 0)
            if confidence < 0.3:
                return None
            
            # Build config from result
            config = {}
            
            if result.get('archetype'):
                config['archetype'] = result['archetype']
            
            if result.get('traits'):
                # Validate trait values are 0-10
                valid_traits = {}
                for trait, value in result['traits'].items():
                    if isinstance(value, (int, float)) and 0 <= value <= 10:
                        valid_traits[trait] = int(value)
                if valid_traits:
                    config['traits'] = valid_traits
            
            if result.get('behaviors'):
                # Validate boolean values
                valid_behaviors = {}
                for behavior, value in result['behaviors'].items():
                    if isinstance(value, bool):
                        valid_behaviors[behavior] = value
                if valid_behaviors:
                    config['behaviors'] = valid_behaviors
            
            if result.get('relationship_type'):
                config['relationship_type'] = result['relationship_type']
            
            if result.get('custom_instructions'):
                config['custom_instructions'] = result['custom_instructions']
            
            if config:
                logger.info(
                    f"LLM detected personality config: {list(config.keys())} "
                    f"(confidence: {confidence:.2f})"
                )
                return config
            
            return None
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM personality JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM personality detection failed: {e}")
            return None
    
    def _detect_archetype(self, message: str) -> Optional[str]:
        """Detect personality archetype."""
        for archetype, patterns in self.ARCHETYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return archetype
        return None
    
    def _detect_traits(self, message: str) -> Dict[str, int]:
        """Detect trait adjustments."""
        adjustments = {}
        
        for trait, directions in self.TRAIT_PATTERNS.items():
            # Check increase patterns
            for pattern in directions['increase']:
                if re.search(pattern, message, re.IGNORECASE):
                    adjustments[trait] = 8  # Set to high value
                    break
            
            # Check decrease patterns
            if trait not in adjustments:
                for pattern in directions['decrease']:
                    if re.search(pattern, message, re.IGNORECASE):
                        adjustments[trait] = 3  # Set to low value
                        break
        
        return adjustments
    
    def _detect_behaviors(self, message: str) -> Dict[str, bool]:
        """Detect behavior toggles."""
        toggles = {}
        
        for behavior, directions in self.BEHAVIOR_PATTERNS.items():
            # Check enable patterns
            for pattern in directions['enable']:
                if re.search(pattern, message, re.IGNORECASE):
                    toggles[behavior] = True
                    break
            
            # Check disable patterns
            if behavior not in toggles:
                for pattern in directions['disable']:
                    if re.search(pattern, message, re.IGNORECASE):
                        toggles[behavior] = False
                        break
        
        return toggles
    
    def _detect_relationship(self, message: str) -> Optional[str]:
        """Detect relationship type."""
        for rel_type, patterns in self.RELATIONSHIP_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return rel_type
        return None

