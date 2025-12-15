"""Advanced emotion detection service with confidence scoring."""

import re
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class DetectedEmotion:
    """Represents a detected emotion with metadata."""
    
    def __init__(
        self,
        emotion: str,
        confidence: float,
        indicators: List[str],
        intensity: str = "medium"
    ):
        self.emotion = emotion
        self.confidence = confidence  # 0.0 to 1.0
        self.indicators = indicators  # ['keyword', 'emoji', 'phrase']
        self.intensity = intensity  # low, medium, high
        self.detected_at = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "emotion": self.emotion,
            "confidence": self.confidence,
            "indicators": self.indicators,
            "intensity": self.intensity,
            "detected_at": self.detected_at.isoformat()
        }


class EmotionDetector:
    """
    Advanced emotion detection from text messages.
    
    Supports 12+ emotions with confidence scoring, intensity levels,
    and multiple detection methods (keywords, emojis, phrases, context).
    """
    
    # Comprehensive emotion patterns with weights
    EMOTIONS = {
        'sad': {
            'keywords': {
                'sad': 0.8, 'depressed': 0.9, 'down': 0.7, 'upset': 0.7,
                'crying': 0.9, 'unhappy': 0.8, 'miserable': 0.9, 'heartbroken': 1.0,
                'lonely': 0.8, 'hurt': 0.7, 'devastated': 1.0, 'grief': 0.9,
                'mourning': 0.9, 'sorrow': 0.8
            },
            'emojis': {
                '😢': 0.9, '😭': 1.0, '😔': 0.8, '😞': 0.8, '💔': 0.9,
                '😿': 0.8, '🥺': 0.7, '😣': 0.7
            },
            'phrases': [
                (r"i('m| am) (so |really |very |)sad", 0.9),
                (r"feel(ing|s|) (so |really |)(down|depressed)", 0.9),
                (r"can't stop (crying|thinking about)", 0.9),
                (r"my (heart|life) (is |feels |)broken", 1.0),
                (r"(just |)lost (my|someone|a)", 0.9),
                (r"passed away|died", 0.9)
            ],
            'response_tone': 'supportive_empathetic'
        },
        
        'angry': {
            'keywords': {
                'angry': 0.9, 'furious': 1.0, 'mad': 0.8, 'pissed': 0.9,
                'outraged': 1.0, 'livid': 1.0, 'rage': 1.0, 'hate': 0.8,
                'disgusted': 0.8, 'infuriated': 1.0
            },
            'emojis': {
                '😠': 0.9, '😡': 1.0, '🤬': 1.0, '😤': 0.8, '💢': 0.9,
                '🔥': 0.7, '👿': 0.9
            },
            'phrases': [
                (r"i('m| am) (so |really |)angry", 0.9),
                (r"this is (ridiculous|bullshit|unacceptable)", 1.0),
                (r"(I |i)(hate|can't stand) (this|it|that)", 0.9),
                (r"makes me (so |)angry", 0.9),
                (r"fed up|sick of", 0.8)
            ],
            'response_tone': 'calm_deescalating'
        },
        
        'frustrated': {
            'keywords': {
                'frustrated': 0.9, 'annoyed': 0.8, 'irritated': 0.8,
                'struggling': 0.7, 'stuck': 0.7, 'overwhelmed': 0.8,
                'tired': 0.6, 'exhausted': 0.7, 'stressed': 0.7
            },
            'emojis': {
                '😤': 0.9, '😒': 0.8, '🙄': 0.7, '😫': 0.8, '😩': 0.8,
                '🤦': 0.8
            },
            'phrases': [
                (r"(so |really |)frustrated", 0.9),
                (r"nothing (is |)working", 0.8),
                (r"tried (everything|for hours)", 0.8),
                (r"can't (figure|get|make) (it|this) (out|to work)", 0.8),
                (r"been (trying|working) (on this |)for (hours|days)", 0.9)
            ],
            'response_tone': 'patient_supportive'
        },
        
        'happy': {
            'keywords': {
                'happy': 0.9, 'great': 0.7, 'wonderful': 0.8, 'amazing': 0.9,
                'fantastic': 0.9, 'awesome': 0.8, 'love': 0.7, 'perfect': 0.8,
                'delighted': 0.9, 'pleased': 0.7, 'content': 0.7, 'joyful': 0.9
            },
            'emojis': {
                '😊': 0.8, '😃': 0.9, '😄': 0.9, '😁': 0.9, '🙂': 0.7,
                '☺️': 0.8, '😌': 0.7
            },
            'phrases': [
                (r"i('m| am) (so |really |)happy", 0.9),
                (r"this is (great|wonderful|amazing)", 0.8),
                (r"feel(ing|s|) (great|wonderful|happy)", 0.8),
                (r"love (this|it|that)", 0.7)
            ],
            'response_tone': 'warm_positive'
        },
        
        'excited': {
            'keywords': {
                'excited': 1.0, 'thrilled': 1.0, 'pumped': 0.9, 'stoked': 0.9,
                'psyched': 0.9, 'eager': 0.8, 'enthusiastic': 0.9, 'omg': 0.8,
                'yay': 0.9, 'woohoo': 1.0
            },
            'emojis': {
                '🎉': 1.0, '🎊': 1.0, '🥳': 1.0, '😆': 0.8, '✨': 0.7,
                '🎈': 0.7, '🙌': 0.8, '👏': 0.7, '💪': 0.7
            },
            'phrases': [
                (r"(so |really |)excited", 1.0),
                (r"can't wait", 0.9),
                (r"(just |)got (the |)(job|offer|promotion|news)", 0.9),
                (r"this is (incredible|unbelievable)", 0.9),
                (r"omg|oh my god", 0.8)
            ],
            'response_tone': 'enthusiastic_celebratory'
        },
        
        'anxious': {
            'keywords': {
                'worried': 0.9, 'nervous': 0.9, 'anxious': 1.0, 'scared': 0.9,
                'afraid': 0.9, 'concerned': 0.7, 'terrified': 1.0, 'panic': 1.0,
                'stress': 0.8, 'overwhelmed': 0.8, 'uncertain': 0.7
            },
            'emojis': {
                '😰': 1.0, '😨': 0.9, '😟': 0.8, '😓': 0.8, '😥': 0.8,
                '🥶': 0.7
            },
            'phrases': [
                (r"i('m| am) (so |really |)worried", 0.9),
                (r"(feeling|feel) anxious", 1.0),
                (r"(what if|scared that)", 0.8),
                (r"don't know (what to|how to)", 0.7),
                (r"(having|getting) (a |)panic (attack|)", 1.0)
            ],
            'response_tone': 'calm_reassuring'
        },
        
        'confused': {
            'keywords': {
                'confused': 0.9, 'lost': 0.7, 'puzzled': 0.8, 'baffled': 0.9,
                'perplexed': 0.8, 'unclear': 0.7, 'bewildered': 0.9
            },
            'emojis': {
                '😕': 0.9, '😵': 0.8, '🤔': 0.7, '😖': 0.8, '🤷': 0.8
            },
            'phrases': [
                (r"(so |really |)confused", 0.9),
                (r"don't understand", 0.8),
                (r"what (do you|does (this|that)) mean", 0.7),
                (r"(not|doesn't) make sense", 0.8),
                (r"(can you|could you) explain", 0.6)
            ],
            'response_tone': 'clear_patient'
        },
        
        'grateful': {
            'keywords': {
                'thank': 0.8, 'thanks': 0.8, 'grateful': 1.0, 'appreciate': 0.9,
                'thankful': 0.9, 'blessed': 0.8, 'fortunate': 0.7
            },
            'emojis': {
                '🙏': 1.0, '🤗': 0.8, '💝': 0.7, '🎁': 0.6, '❤️': 0.6
            },
            'phrases': [
                (r"thank you (so much|very much|)", 0.9),
                (r"(really |)appreciate (it|this|that|your help)", 0.9),
                (r"you('re| are) (the |)best", 0.8),
                (r"(so |)grateful", 1.0)
            ],
            'response_tone': 'warm_humble'
        },
        
        'disappointed': {
            'keywords': {
                'disappointed': 1.0, 'letdown': 0.9, 'failed': 0.8,
                'didn\'t work': 0.7, 'expected': 0.6, 'hoped': 0.6
            },
            'emojis': {
                '😞': 0.9, '😔': 0.8, '😟': 0.7, '😢': 0.7
            },
            'phrases': [
                (r"(so |really |)disappointed", 1.0),
                (r"(didn't|did not) (work out|go well)", 0.8),
                (r"expected (more|better)", 0.8),
                (r"let(ting| ) me down", 0.9)
            ],
            'response_tone': 'encouraging_supportive'
        },
        
        'proud': {
            'keywords': {
                'proud': 1.0, 'accomplished': 0.9, 'achieved': 0.8,
                'succeeded': 0.9, 'did it': 0.7, 'made it': 0.7
            },
            'emojis': {
                '💪': 0.8, '🏆': 0.9, '🎯': 0.7, '⭐': 0.7, '👍': 0.6
            },
            'phrases': [
                (r"(so |really |)proud", 1.0),
                (r"(finally |just |)accomplished", 0.9),
                (r"(finally |just |)(did|finished|completed) it", 0.8),
                (r"succeeded|made it", 0.8)
            ],
            'response_tone': 'celebratory_affirming'
        },
        
        'lonely': {
            'keywords': {
                'lonely': 1.0, 'alone': 0.8, 'isolated': 0.9,
                'nobody': 0.7, 'empty': 0.7, 'abandoned': 0.9
            },
            'emojis': {
                '😔': 0.8, '😞': 0.8, '🥺': 0.9, '💔': 0.7
            },
            'phrases': [
                (r"(so |really |)lonely", 1.0),
                (r"feel(ing|) alone", 0.9),
                (r"nobody (cares|understands)", 0.9),
                (r"(have |got )no(body| one)", 0.8)
            ],
            'response_tone': 'warm_companionable'
        },
        
        'hopeful': {
            'keywords': {
                'hopeful': 1.0, 'optimistic': 0.9, 'looking forward': 0.8,
                'hoping': 0.8, 'maybe': 0.5, 'possible': 0.6
            },
            'emojis': {
                '🤞': 0.9, '🌟': 0.7, '✨': 0.7, '🌈': 0.8, '☀️': 0.6
            },
            'phrases': [
                (r"(feeling |)hopeful", 1.0),
                (r"things (will|might) (get |)better", 0.8),
                (r"looking forward to", 0.8),
                (r"(fingers |)crossed", 0.7)
            ],
            'response_tone': 'encouraging_optimistic'
        }
    }
    
    # Intensity amplifiers
    INTENSITY_MODIFIERS = {
        'high': ['so', 'very', 'really', 'extremely', 'incredibly', 'super', 'absolutely'],
        'low': ['a bit', 'somewhat', 'kind of', 'kinda', 'slightly', 'a little']
    }
    
    def detect(self, message: str) -> Optional[DetectedEmotion]:
        """
        Detect emotion from message with confidence scoring.
        
        Args:
            message: User message text
            
        Returns:
            DetectedEmotion object or None if no strong emotion detected
        """
        if not message or len(message.strip()) < 3:
            return None
        
        message_lower = message.lower()
        emotion_scores = defaultdict(lambda: {'score': 0.0, 'indicators': []})
        
        # Detect emotions using multiple methods
        for emotion_name, patterns in self.EMOTIONS.items():
            # 1. Keyword matching
            for keyword, weight in patterns['keywords'].items():
                if re.search(r'\b' + keyword + r'\b', message_lower):
                    emotion_scores[emotion_name]['score'] += weight * 0.4
                    emotion_scores[emotion_name]['indicators'].append('keyword')
            
            # 2. Emoji matching
            for emoji, weight in patterns['emojis'].items():
                if emoji in message:
                    emotion_scores[emotion_name]['score'] += weight * 0.5
                    emotion_scores[emotion_name]['indicators'].append('emoji')
            
            # 3. Phrase matching
            for pattern, weight in patterns['phrases']:
                if re.search(pattern, message_lower):
                    emotion_scores[emotion_name]['score'] += weight * 0.6
                    emotion_scores[emotion_name]['indicators'].append('phrase')
        
        # Find strongest emotion
        if not emotion_scores:
            return None
        
        best_emotion = max(emotion_scores.items(), key=lambda x: x[1]['score'])
        emotion_name, data = best_emotion
        
        # Threshold: only return if confidence > 0.3
        if data['score'] < 0.3:
            return None
        
        # Normalize confidence to 0-1
        confidence = min(data['score'], 1.0)
        
        # Detect intensity
        intensity = self._detect_intensity(message_lower)
        
        # Deduplicate indicators
        indicators = list(set(data['indicators']))
        
        logger.info(f"Detected emotion: {emotion_name} (confidence: {confidence:.2f}, intensity: {intensity})")
        
        return DetectedEmotion(
            emotion=emotion_name,
            confidence=confidence,
            indicators=indicators,
            intensity=intensity
        )
    
    def _detect_intensity(self, message: str) -> str:
        """Detect emotion intensity from amplifiers."""
        for modifier in self.INTENSITY_MODIFIERS['high']:
            if modifier in message:
                return 'high'
        
        for modifier in self.INTENSITY_MODIFIERS['low']:
            if modifier in message:
                return 'low'
        
        return 'medium'
    
    def get_response_tone(self, emotion: str) -> str:
        """Get recommended response tone for detected emotion."""
        if emotion in self.EMOTIONS:
            return self.EMOTIONS[emotion].get('response_tone', 'balanced')
        return 'balanced'
    
    def analyze_emotion_trend(self, emotion_history: List[Dict]) -> Dict:
        """
        Analyze emotion trends from history.
        
        Args:
            emotion_history: List of emotion dicts with 'emotion' and 'detected_at'
            
        Returns:
            {
                'dominant_emotion': 'sad',
                'emotion_distribution': {'sad': 0.6, 'angry': 0.4},
                'recent_trend': 'declining',  # improving, stable, declining
                'needs_attention': True
            }
        """
        if not emotion_history:
            return {
                'dominant_emotion': None,
                'emotion_distribution': {},
                'recent_trend': 'stable',
                'needs_attention': False
            }
        
        # Count emotions
        emotion_counts = defaultdict(int)
        for entry in emotion_history:
            emotion_counts[entry['emotion']] += 1
        
        total = len(emotion_history)
        emotion_distribution = {
            emotion: count / total 
            for emotion, count in emotion_counts.items()
        }
        
        # Find dominant
        dominant = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else None
        
        # Analyze trend (last 5 vs previous 5)
        if len(emotion_history) >= 10:
            recent = emotion_history[-5:]
            previous = emotion_history[-10:-5]
            
            negative_emotions = {'sad', 'angry', 'frustrated', 'anxious', 'disappointed', 'lonely'}
            
            recent_negative = sum(1 for e in recent if e['emotion'] in negative_emotions)
            previous_negative = sum(1 for e in previous if e['emotion'] in negative_emotions)
            
            if recent_negative < previous_negative:
                trend = 'improving'
            elif recent_negative > previous_negative:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        # Check if needs attention (multiple negative emotions)
        recent_negative = sum(
            1 for e in emotion_history[-5:] 
            if e['emotion'] in {'sad', 'angry', 'anxious', 'lonely'}
        )
        needs_attention = recent_negative >= 3
        
        return {
            'dominant_emotion': dominant,
            'emotion_distribution': emotion_distribution,
            'recent_trend': trend,
            'needs_attention': needs_attention
        }

