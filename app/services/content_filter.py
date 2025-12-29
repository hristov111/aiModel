"""Content filter service for detecting explicit/NSFW content."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ContentFilter:
    """
    Service for detecting explicit/NSFW content in text.
    
    Uses pattern-based detection with context awareness to identify
    explicit content that should be handled by the uncensored local model.
    """
    
    # Explicit content indicators
    EXPLICIT_KEYWORDS = [
        # Sexual content
        r'\b(sex|sexual|porn|pornography|xxx|nsfw|explicit)\b',
        r'\b(erotic|arousal|orgasm|masturbat|genitals?)\b',
        r'\b(intercourse|penetration|fellatio|cunnilingus)\b',
        r'\b(nude|naked|strip|undress)\b',
        
        # Adult themes
        r'\b(adult content|mature content|18\+|r-rated|x-rated)\b',
        r'\b(fetish|kink|bdsm)\b',
        
        # Explicit language (strong indicators)
        r'\b(fuck|shit|cock|pussy|dick|penis|vagina|breast|tits?|ass)\b',
        
        # Request for explicit content
        r'\b(write|create|generate|tell me).{0,30}(sex|explicit|nsfw|adult)\b',
        r'\b(roleplay|role-play).{0,30}(sexual|explicit|adult)\b',
    ]
    
    # Context phrases that indicate explicit intent
    EXPLICIT_CONTEXTS = [
        r'make it (more |)explicit',
        r'(be |get |)more sexual',
        r'add (some |)sexual (content|elements|themes)',
        r'(describe|write|create).{0,30}(sexual|explicit|nsfw)',
        r'without (censorship|restrictions|filters)',
        r'uncensored',
        r'no (limits|boundaries|restrictions)',
    ]
    
    # False positive prevention - medical/clinical terms
    CLINICAL_CONTEXT = [
        r'\b(medical|clinical|doctor|patient|diagnosis|treatment|health|anatomy)\b',
        r'\b(examination|procedure|symptom|condition|disease)\b',
        r'\b(therapy|counseling|mental health)\b',
    ]
    
    def __init__(self, sensitivity: str = "medium"):
        """
        Initialize content filter.
        
        Args:
            sensitivity: Detection sensitivity ("low", "medium", "high")
        """
        self.sensitivity = sensitivity
        logger.info(f"ContentFilter initialized with sensitivity: {sensitivity}")
    
    def is_explicit(self, text: str) -> bool:
        """
        Check if text contains explicit content.
        
        Args:
            text: Text to check
            
        Returns:
            True if explicit content detected, False otherwise
        """
        if not text or len(text.strip()) < 3:
            return False
        
        text_lower = text.lower()
        
        # Check for clinical/medical context first (avoid false positives)
        is_clinical = self._is_clinical_context(text_lower)
        if is_clinical:
            logger.debug("Clinical context detected, not marking as explicit")
            return False
        
        # Count explicit indicators
        explicit_score = 0
        indicators_found = []
        
        # Check explicit keywords
        for pattern in self.EXPLICIT_KEYWORDS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                explicit_score += len(matches)
                indicators_found.append(f"keyword: {matches[0]}")
        
        # Check explicit contexts (weighted higher)
        for pattern in self.EXPLICIT_CONTEXTS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                explicit_score += 3  # Context phrases weighted higher
                indicators_found.append(f"context: {pattern[:30]}")
        
        # Determine threshold based on sensitivity
        thresholds = {
            "low": 5,      # More permissive
            "medium": 3,   # Balanced
            "high": 1      # More strict
        }
        threshold = thresholds.get(self.sensitivity, 3)
        
        is_explicit = explicit_score >= threshold
        
        if is_explicit:
            logger.info(
                f"Explicit content detected (score: {explicit_score}/{threshold}). "
                f"Indicators: {', '.join(indicators_found[:3])}"
            )
        
        return is_explicit
    
    def _is_clinical_context(self, text: str) -> bool:
        """
        Check if text is in a clinical/medical context.
        
        Args:
            text: Text to check (lowercase)
            
        Returns:
            True if clinical context detected
        """
        for pattern in self.CLINICAL_CONTEXT:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def get_sensitivity_description(self) -> str:
        """Get description of current sensitivity level."""
        descriptions = {
            "low": "Permissive - only flags very explicit content",
            "medium": "Balanced - flags moderately explicit content",
            "high": "Strict - flags potentially explicit content"
        }
        return descriptions.get(self.sensitivity, "Unknown")


# Global content filter instance
_content_filter: Optional[ContentFilter] = None


def get_content_filter(sensitivity: str = "medium") -> ContentFilter:
    """
    Get or create global content filter instance.
    
    Args:
        sensitivity: Detection sensitivity
        
    Returns:
        ContentFilter instance
    """
    global _content_filter
    if _content_filter is None:
        _content_filter = ContentFilter(sensitivity=sensitivity)
    return _content_filter



