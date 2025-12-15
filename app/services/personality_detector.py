"""Detect personality preferences from natural language."""

import re
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class PersonalityDetector:
    """
    Detects personality preferences from user messages.
    
    Allows users to configure AI personality using natural language like:
    - "Be like a wise mentor"
    - "I want you to be more enthusiastic"
    - "Act like a supportive friend"
    """
    
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
    
    def detect(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Detect personality configuration from message.
        
        Args:
            message: User message
            
        Returns:
            Dict with detected personality config or None
        """
        if not message or len(message.strip()) < 5:
            return None
        
        message_lower = message.lower()
        config = {}
        
        # Detect archetype
        archetype = self._detect_archetype(message_lower)
        if archetype:
            config['archetype'] = archetype
            logger.info(f"Detected archetype: {archetype}")
        
        # Detect trait adjustments
        traits = self._detect_traits(message_lower)
        if traits:
            config['traits'] = traits
            logger.info(f"Detected trait adjustments: {traits}")
        
        # Detect behavior toggles
        behaviors = self._detect_behaviors(message_lower)
        if behaviors:
            config['behaviors'] = behaviors
            logger.info(f"Detected behavior changes: {behaviors}")
        
        # Detect relationship type
        relationship = self._detect_relationship(message_lower)
        if relationship:
            config['relationship_type'] = relationship
            logger.info(f"Detected relationship type: {relationship}")
        
        # Detect custom instructions
        if any(phrase in message_lower for phrase in ['i want you to', 'you should', 'please']):
            config['custom_instructions'] = message
        
        return config if config else None
    
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

