"""Advanced content classification system with multi-layered detection."""

import re
import logging
import unicodedata
import asyncio
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
import json

if TYPE_CHECKING:
    from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ContentLabel(str, Enum):
    """Content risk labels for routing decisions."""
    SAFE = "SAFE"
    SUGGESTIVE = "SUGGESTIVE"
    EXPLICIT_CONSENSUAL_ADULT = "EXPLICIT_CONSENSUAL_ADULT"
    EXPLICIT_FETISH = "EXPLICIT_FETISH"
    NONCONSENSUAL = "NONCONSENSUAL"
    MINOR_RISK = "MINOR_RISK"


@dataclass
class ClassificationResult:
    """Result of content classification."""
    label: ContentLabel
    confidence: float  # 0.0 to 1.0
    indicators: List[str]  # What triggered this classification
    normalized_text: str  # Normalized version of input
    layer_results: Dict[str, any]  # Results from each detection layer


class ContentClassifier:
    """
    Multi-layered content classification system.
    
    Implements 4-layer detection:
    1. Normalization (unicode, leetspeak, emoji, spacing)
    2. Fast rules (explicit anatomy, age indicators, coercion)
    3. Pattern-based classifier (core detection)
    4. LLM judge (optional, for borderline cases)
    """
    
    # Layer 1: Normalization mappings
    LEETSPEAK_MAP = {
        '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's',
        '7': 't', '8': 'b', '@': 'a', '$': 's', '!': 'i',
    }
    
    EMOJI_MAP = {
        '🍆': 'penis', '🍑': 'butt', '💦': 'cum', '👅': 'tongue',
        '🔥': 'hot', '😈': 'naughty', '💋': 'kiss', '🍌': 'penis',
        '🥵': 'horny', '😏': 'suggestive', '💕': 'love', '❤️': 'love',
        '🛏️': 'bed', '🌶️': 'spicy', '🔞': 'adult',
    }
    
    # Layer 2: Fast rules - IMMEDIATE escalation
    AGE_INDICATORS = [
        r'\b(teens?|teenagers?|underage|minors?|children|child|kids?|young|youth)\b',
        r'\b(school|student|high school|middle school|elementary)\b',
        r'\b(barely legal|just turned 18|fresh 18)\b',
        r'\b(\d+)[\s-]?(year|yr)[\s-]?old\b',  # Age mentions
        r'\b(loli|shota|pedo|pedophile)\b',
    ]
    
    COERCION_INDICATORS = [
        r'\b(forced|rape|assault|molest|abuse)\b',
        r'\b(drugged|drunk|unconscious|passed out|sleeping)\b',
        r'\b(coerce|manipulate|blackmail|threaten)\b',
        r'\b(non[\s-]?consensual|against will|without consent)\b',
        r'\b(kidnap|capture|trap|restrain)\b',
    ]
    
    # Layer 3: Pattern-based classification
    EXPLICIT_ANATOMY = [
        r'\b(penis|cock|dick|shaft|balls|testicles)\b',
        r'\b(vagina|pussy|cunt|clit|labia)\b',
        r'\b(breasts?|tits?|nipples?|boobs)\b',
        r'\b(ass|anus|butthole|asshole)\b',
        r'\b(genitals?|privates)\b',
    ]
    
    SEXUAL_ACTS = [
        r'\b(sex|intercourse|penetration|fucking)\b',
        r'\b(blowjob|fellatio|cunnilingus|oral sex)\b',
        r'\b(masturbat|jerk off|handjob|fingering)\b',
        r'\b(orgasm|climax|cum|ejaculat)\b',
        r'\b(anal|vaginal|oral)\b',
    ]
    
    FETISH_INDICATORS = [
        r'\b(bdsm|bondage|domination|submission|sadism|masochism)\b',
        r'\b(fetish|kink|kinky)\b',
        r'\b(slave|master|mistress|dom|sub)\b',
        r'\b(whip|chain|collar|leash|gag)\b',
        r'\b(humiliation|degradation|torture)\b',
        r'\b(feet|foot fetish|worship)\b',
        r'\b(latex|leather|rubber)\b',
    ]
    
    SUGGESTIVE_CONTENT = [
        r'\b(flirt|flirty|seduce|tease|arousal)\b',
        r'\b(sexy|hot|attractive|beautiful|gorgeous|charming|handsome)\b',
        r'\b(kiss|touch|caress|embrace|hug|cuddle)\b',
        r'\b(desire|lust|passion|romance|romantic)\b',
        r'\b(intimate|intimacy|sensual)\b',
        r'\b(naked|nude|undress|strip)\b',
        r'\b(bedroom|fantasies|fantasy)\b',
    ]
    
    EXPLICIT_REQUESTS = [
        r'\b(write|create|generate|describe|tell me).{0,40}(sex|explicit|nsfw|porn)\b',
        r'\b(roleplay|role[\s-]?play).{0,40}(sexual|explicit|adult|nsfw)\b',
        r'\b(erotic|adult) (story|content|scene|roleplay)\b',
        r'\b(make it|be|get) (more )?(explicit|sexual|dirty|nasty)\b',
        r'\b(bedroom|sexual) (activities|activity|things)\b',
    ]
    
    # Clinical/medical context (false positive prevention)
    CLINICAL_CONTEXT = [
        r'\b(medical|clinical|doctor|patient|diagnosis|treatment)\b',
        r'\b(examination|procedure|symptom|condition|disease)\b',
        r'\b(therapy|counseling|health|anatomy|biology)\b',
        r'\b(education|educational|textbook|academic)\b',
    ]
    
    # Layer 4: LLM Judge Configuration
    LLM_CONFIDENCE_THRESHOLD = 0.7  # Use LLM if pattern confidence below this
    
    # System prompt for LLM judge
    LLM_SYSTEM_PROMPT = """You are a content safety classifier. Your job is to classify messages into one of 6 categories.

CRITICAL RULES:
1. MINOR_RISK - ALWAYS flag if ANY mention of minors, age ambiguity, "teen", "school", "young"
2. NONCONSENSUAL - ALWAYS flag if ANY coercion, force, "rape", "drugged", "against will"
3. Be strict on safety - when in doubt, choose the MORE restrictive category
4. Consider context and nuance - not just keywords

Categories (in order of restriction):
1. SAFE - Normal conversation, appropriate content
2. SUGGESTIVE - Romantic, flirty, compliments, but not explicit
3. EXPLICIT_CONSENSUAL_ADULT - Clear sexual content between adults
4. EXPLICIT_FETISH - BDSM, kink, fetish content with consent
5. NONCONSENSUAL - Non-consensual, forced, coerced (ALWAYS REFUSE)
6. MINOR_RISK - Any age ambiguity or minor mentions (ALWAYS REFUSE)

Respond with JSON only, no other text:
{
  "label": "CATEGORY_NAME",
  "confidence": 0.0-1.0,
  "reasoning": "1-2 sentence explanation"
}"""
    
    def __init__(self, llm_client: Optional['LLMClient'] = None, enable_llm_judge: bool = True):
        """
        Initialize content classifier.
        
        Args:
            llm_client: Optional LLM client for Layer 4 judge
            enable_llm_judge: Enable LLM judge for borderline cases
        """
        self.llm_client = llm_client
        self.enable_llm_judge = enable_llm_judge and llm_client is not None
        self.llm_cache = {}  # Cache LLM results
        
        if self.enable_llm_judge:
            logger.info("ContentClassifier initialized with 4-layer detection (LLM judge enabled)")
        else:
            logger.info("ContentClassifier initialized with 3-layer detection (LLM judge disabled)")
    
    def classify(self, text: str) -> ClassificationResult:
        """
        Classify content through multi-layered detection.
        
        Args:
            text: Input text to classify
            
        Returns:
            ClassificationResult with label, confidence, and details
        """
        if not text or len(text.strip()) < 3:
            return ClassificationResult(
                label=ContentLabel.SAFE,
                confidence=1.0,
                indicators=[],
                normalized_text=text,
                layer_results={}
            )
        
        # Layer 1: Normalize
        normalized = self._normalize_text(text)
        layer_results = {"normalized": normalized}
        
        # Layer 2: Fast rules (immediate escalation)
        minor_risk_score, minor_indicators = self._check_minor_risk(normalized)
        if minor_risk_score > 0:
            logger.warning(f"MINOR_RISK detected: {minor_indicators}")
            return ClassificationResult(
                label=ContentLabel.MINOR_RISK,
                confidence=1.0,
                indicators=minor_indicators,
                normalized_text=normalized,
                layer_results={"minor_risk": minor_indicators}
            )
        
        coercion_score, coercion_indicators = self._check_coercion(normalized)
        if coercion_score > 0:
            logger.warning(f"NONCONSENSUAL detected: {coercion_indicators}")
            return ClassificationResult(
                label=ContentLabel.NONCONSENSUAL,
                confidence=1.0,
                indicators=coercion_indicators,
                normalized_text=normalized,
                layer_results={"coercion": coercion_indicators}
            )
        
        # Check for clinical context (avoid false positives)
        if self._is_clinical_context(normalized):
            logger.debug("Clinical context detected, marking as SAFE")
            return ClassificationResult(
                label=ContentLabel.SAFE,
                confidence=0.9,
                indicators=["clinical_context"],
                normalized_text=normalized,
                layer_results={"clinical": True}
            )
        
        # Layer 3: Pattern-based classification
        classification = self._pattern_classify(normalized)
        layer_results.update(classification["details"])
        
        # Layer 4: LLM Judge (for borderline cases)
        if self.enable_llm_judge and self._should_use_llm_judge(classification):
            logger.info(
                f"Pattern confidence {classification['confidence']:.2f} triggers LLM judge"
            )
            
            try:
                # Run async LLM call in a new event loop or use existing one
                try:
                    # Try to get existing loop
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, we can't use asyncio.run()
                        # Use run_coroutine_threadsafe or create task
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, self._llm_judge(normalized, classification))
                            llm_result = future.result(timeout=10)  # 10 second timeout
                    else:
                        llm_result = asyncio.run(self._llm_judge(normalized, classification))
                except RuntimeError:
                    # No event loop, create one
                    llm_result = asyncio.run(self._llm_judge(normalized, classification))
                
                if llm_result:
                    # Blend LLM result with pattern result
                    classification = self._blend_results(classification, llm_result)
                    layer_results["llm_judge"] = llm_result
                    logger.info(
                        f"LLM judge result: {llm_result['label']} "
                        f"(confidence: {llm_result['confidence']:.2f})"
                    )
            except Exception as e:
                logger.warning(f"LLM judge failed, using pattern result: {e}")
        
        return ClassificationResult(
            label=classification["label"],
            confidence=classification["confidence"],
            indicators=classification["indicators"],
            normalized_text=normalized,
            layer_results=layer_results
        )
    
    def _normalize_text(self, text: str) -> str:
        """
        Layer 1: Normalize text to catch obfuscation attempts.
        
        Handles:
        - Unicode normalization (NFKC)
        - Leetspeak mapping
        - Emoji mapping
        - Spacing tricks
        """
        # Unicode normalization
        text = unicodedata.normalize('NFKC', text)
        
        # Emoji mapping
        for emoji, word in self.EMOJI_MAP.items():
            text = text.replace(emoji, f" {word} ")
        
        # Collapse multiple spaces to single space
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Leetspeak mapping
        for leet, char in self.LEETSPEAK_MAP.items():
            text = text.replace(leet, char)
        
        # Lowercase for matching (do this before spacing removal)
        text = text.lower()
        
        # Remove single-letter spacing tricks (s e x -> sex, p o r n -> porn)
        # Handle sequences of 2-4 single letters separated by spaces
        text = re.sub(r'\b([a-z])\s+([a-z])\s+([a-z])\s+([a-z])\b', r'\1\2\3\4', text)  # 4 letters
        text = re.sub(r'\b([a-z])\s+([a-z])\s+([a-z])\b', r'\1\2\3', text)  # 3 letters
        text = re.sub(r'\b([a-z])\s+([a-z])\b', r'\1\2', text)  # 2 letters
        
        return text
    
    def _check_minor_risk(self, text: str) -> Tuple[int, List[str]]:
        """
        Layer 2: Check for age-related risk indicators.
        
        Returns:
            (score, indicators) - score > 0 means MINOR_RISK detected
        """
        indicators = []
        
        for pattern in self.AGE_INDICATORS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                indicators.append(f"age_indicator: {matches[0]}")
        
        return len(indicators), indicators
    
    def _check_coercion(self, text: str) -> Tuple[int, List[str]]:
        """
        Layer 2: Check for coercion/non-consensual indicators.
        
        Returns:
            (score, indicators) - score > 0 means NONCONSENSUAL detected
        """
        indicators = []
        
        for pattern in self.COERCION_INDICATORS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                indicators.append(f"coercion: {matches[0]}")
        
        return len(indicators), indicators
    
    def _is_clinical_context(self, text: str) -> bool:
        """Check if text is in clinical/medical context."""
        for pattern in self.CLINICAL_CONTEXT:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _pattern_classify(self, text: str) -> Dict:
        """
        Layer 3: Pattern-based classification.
        
        Returns dict with label, confidence, indicators, and details.
        """
        scores = {
            "anatomy": 0,
            "sexual_acts": 0,
            "fetish": 0,
            "suggestive": 0,
            "explicit_request": 0,
        }
        
        all_indicators = []
        
        # Check explicit anatomy
        for pattern in self.EXPLICIT_ANATOMY:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                scores["anatomy"] += len(matches)
                all_indicators.append(f"anatomy: {matches[0]}")
        
        # Check sexual acts
        for pattern in self.SEXUAL_ACTS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                scores["sexual_acts"] += len(matches)
                all_indicators.append(f"sexual_act: {matches[0]}")
        
        # Check fetish indicators
        for pattern in self.FETISH_INDICATORS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                scores["fetish"] += len(matches)
                all_indicators.append(f"fetish: {matches[0]}")
        
        # Check suggestive content
        for pattern in self.SUGGESTIVE_CONTENT:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                scores["suggestive"] += len(matches)
                all_indicators.append(f"suggestive: {matches[0]}")
        
        # Check explicit requests (weighted higher)
        for pattern in self.EXPLICIT_REQUESTS:
            if re.search(pattern, text, re.IGNORECASE):
                scores["explicit_request"] += 3
                all_indicators.append(f"explicit_request")
        
        # Determine classification based on scores
        total_explicit = scores["anatomy"] + scores["sexual_acts"]
        total_fetish = scores["fetish"]
        total_suggestive = scores["suggestive"]
        explicit_request = scores["explicit_request"]
        
        # Classification logic
        if total_fetish >= 1:
            return {
                "label": ContentLabel.EXPLICIT_FETISH,
                "confidence": min(0.65 + (total_fetish * 0.15), 1.0),
                "indicators": all_indicators[:5],
                "details": {"scores": scores}
            }
        
        if total_explicit >= 3 or explicit_request >= 3:
            return {
                "label": ContentLabel.EXPLICIT_CONSENSUAL_ADULT,
                "confidence": min(0.7 + (total_explicit * 0.05), 1.0),
                "indicators": all_indicators[:5],
                "details": {"scores": scores}
            }
        
        if total_explicit >= 1 or explicit_request >= 1:
            return {
                "label": ContentLabel.EXPLICIT_CONSENSUAL_ADULT,
                "confidence": 0.6,
                "indicators": all_indicators[:5],
                "details": {"scores": scores}
            }
        
        if total_suggestive >= 2:
            return {
                "label": ContentLabel.SUGGESTIVE,
                "confidence": min(0.6 + (total_suggestive * 0.1), 0.9),
                "indicators": all_indicators[:5],
                "details": {"scores": scores}
            }
        
        # Default to SAFE
        return {
            "label": ContentLabel.SAFE,
            "confidence": 0.95,
            "indicators": [],
            "details": {"scores": scores}
        }
    
    def _should_use_llm_judge(self, classification: Dict) -> bool:
        """
        Determine if LLM judge should be used.
        
        Args:
            classification: Pattern classification result
            
        Returns:
            True if LLM judge should be used
        """
        # Condition 1: Low confidence
        if classification["confidence"] < self.LLM_CONFIDENCE_THRESHOLD:
            return True
        
        # Condition 2: Multiple indicators with mixed signals
        scores = classification["details"]["scores"]
        active_categories = sum(1 for v in scores.values() if v > 0)
        if active_categories >= 3:
            return True
        
        # Condition 3: Borderline explicit (score = 1-2)
        total_explicit = scores["anatomy"] + scores["sexual_acts"]
        if 1 <= total_explicit <= 2:
            return True
        
        # Condition 4: Borderline suggestive (score = 1)
        if scores["suggestive"] == 1:
            return True
        
        return False
    
    async def _llm_judge(self, text: str, pattern_result: Dict) -> Optional[Dict]:
        """
        Use LLM to classify borderline content.
        
        Args:
            text: Normalized text
            pattern_result: Pattern classification result
            
        Returns:
            LLM classification result or None if failed
        """
        # Check cache
        cache_key = hash(text)
        if cache_key in self.llm_cache:
            logger.debug("LLM judge cache hit")
            return self.llm_cache[cache_key]
        
        # Build prompt
        prompt = self._build_llm_prompt(text, pattern_result)
        
        try:
            # Call LLM
            response = await self.llm_client.chat([
                {"role": "system", "content": self.LLM_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ])
            
            # Parse JSON response
            # Try to extract JSON from response (in case LLM adds extra text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = json.loads(response)
            
            # Validate
            if self._validate_llm_result(result):
                self.llm_cache[cache_key] = result
                return result
            else:
                logger.warning(f"Invalid LLM result: {result}")
                return None
            
        except json.JSONDecodeError as e:
            logger.warning(f"LLM judge JSON parse error: {e}, response: {response[:100]}")
            return None
        except Exception as e:
            logger.warning(f"LLM judge error: {e}")
            return None
    
    def _build_llm_prompt(self, text: str, pattern_result: Dict) -> str:
        """
        Build classification prompt for LLM.
        
        Args:
            text: Normalized text
            pattern_result: Pattern classification result
            
        Returns:
            Prompt string
        """
        return f"""Classify this message into exactly ONE category:

Message: "{text}"

Pattern analysis suggests: {pattern_result['label'].value} (confidence: {pattern_result['confidence']:.2f})
Indicators: {', '.join(pattern_result['indicators'][:3]) if pattern_result['indicators'] else 'none'}

Respond with JSON only:
{{
  "label": "CATEGORY_NAME",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""
    
    def _validate_llm_result(self, result: Dict) -> bool:
        """
        Validate LLM classification result.
        
        Args:
            result: LLM result dict
            
        Returns:
            True if valid
        """
        if not isinstance(result, dict):
            return False
        
        if "label" not in result or "confidence" not in result:
            return False
        
        # Check if label is valid
        try:
            ContentLabel[result["label"]]
        except KeyError:
            logger.warning(f"Invalid label from LLM: {result['label']}")
            return False
        
        # Check confidence range
        if not (0.0 <= result["confidence"] <= 1.0):
            return False
        
        return True
    
    def _blend_results(self, pattern_result: Dict, llm_result: Dict) -> Dict:
        """
        Blend pattern and LLM results.
        
        Args:
            pattern_result: Pattern classification result
            llm_result: LLM classification result
            
        Returns:
            Blended classification result
        """
        # Convert label string to ContentLabel
        llm_label = ContentLabel[llm_result["label"]]
        
        # If LLM is highly confident, trust it
        if llm_result["confidence"] > 0.85:
            logger.info(f"LLM high confidence ({llm_result['confidence']:.2f}), using LLM result")
            return {
                "label": llm_label,
                "confidence": llm_result["confidence"],
                "indicators": pattern_result["indicators"] + [f"llm: {llm_result.get('reasoning', 'verified')}"],
                "details": {
                    **pattern_result["details"],
                    "llm": llm_result,
                    "source": "llm"
                }
            }
        
        # If LLM agrees with pattern, boost confidence
        if llm_label == pattern_result["label"]:
            logger.info(f"LLM agrees with pattern, boosting confidence")
            return {
                **pattern_result,
                "confidence": min(pattern_result["confidence"] + 0.2, 1.0),
                "indicators": pattern_result["indicators"] + ["llm: confirmed"],
                "details": {
                    **pattern_result["details"],
                    "llm": llm_result,
                    "source": "blended"
                }
            }
        
        # If disagree, compare risk levels (prefer safer option)
        pattern_risk = self._get_risk_level(pattern_result["label"])
        llm_risk = self._get_risk_level(llm_label)
        
        if llm_risk > pattern_risk:
            # LLM says riskier - be cautious
            logger.info(f"LLM identifies higher risk ({llm_label.value} vs {pattern_result['label'].value})")
            return {
                "label": llm_label,
                "confidence": (pattern_result["confidence"] + llm_result["confidence"]) / 2,
                "indicators": pattern_result["indicators"] + [f"llm: {llm_result.get('reasoning', 'escalated')}"],
                "details": {
                    **pattern_result["details"],
                    "llm": llm_result,
                    "source": "llm_override"
                }
            }
        
        # Pattern says riskier - trust pattern (avoid false negatives)
        logger.info(f"Pattern identifies higher risk, keeping pattern result")
        return {
            **pattern_result,
            "indicators": pattern_result["indicators"] + [f"llm: {llm_result.get('reasoning', 'disagreed')}"],
            "details": {
                **pattern_result["details"],
                "llm": llm_result,
                "source": "pattern"
            }
        }
    
    def _get_risk_level(self, label: ContentLabel) -> int:
        """
        Get risk level for a content label.
        
        Args:
            label: Content label
            
        Returns:
            Risk level (0-5)
        """
        risk_levels = {
            ContentLabel.SAFE: 0,
            ContentLabel.SUGGESTIVE: 1,
            ContentLabel.EXPLICIT_CONSENSUAL_ADULT: 2,
            ContentLabel.EXPLICIT_FETISH: 3,
            ContentLabel.NONCONSENSUAL: 4,
            ContentLabel.MINOR_RISK: 5,
        }
        return risk_levels.get(label, 0)


# Global classifier instance
_classifier: Optional[ContentClassifier] = None


def get_content_classifier(llm_client: Optional['LLMClient'] = None, enable_llm_judge: bool = False) -> ContentClassifier:
    """
    Get or create global content classifier instance.
    
    Args:
        llm_client: Optional LLM client for Layer 4 judge
        enable_llm_judge: Enable LLM judge for borderline cases
    
    Returns:
        ContentClassifier instance
    """
    global _classifier
    if _classifier is None:
        _classifier = ContentClassifier(llm_client=llm_client, enable_llm_judge=enable_llm_judge)
    return _classifier

