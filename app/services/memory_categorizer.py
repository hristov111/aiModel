"""Memory categorization and entity extraction."""

import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MemoryCategorizer:
    """
    Categorizes memories and extracts entities (people, places, topics).
    
    Categories:
    - personal_fact: Facts about the user (age, job, location, etc.)
    - preference: User preferences (likes, dislikes, favorites)
    - goal: User goals and aspirations
    - event: Past events and experiences
    - relationship: Information about people in user's life
    - challenge: Struggles, problems, obstacles
    - achievement: Accomplishments, wins, successes
    - knowledge: General knowledge user wants to remember
    - instruction: How user wants AI to behave
    """
    
    # Category detection patterns
    CATEGORY_PATTERNS = {
        'personal_fact': [
            r'(i am|i\'m|my name is) ',
            r'i (work|live|study) (at|in|as)',
            r'i have a? (job|career|degree|certification)',
            r'(my age|i\'m \d+ years old)',
            r'(my birthday|born (in|on))',
            r'(my (hometown|city|country))',
            r'(single|married|divorced|in a relationship)'
        ],
        'preference': [
            r'i (like|love|enjoy|prefer)',
            r'i (hate|dislike|can\'t stand)',
            r'(my favorite|i\'m a fan of)',
            r'i (always|never|usually) (eat|drink|watch|read|listen)',
            r'i prefer .* (over|to|instead of)',
            r'(allergic to|vegetarian|vegan)'
        ],
        'goal': [
            r'i want to',
            r'i\'m (planning|hoping|trying) to',
            r'(my goal|my dream) is',
            r'i\'m working (on|toward)',
            r'i aspire to',
            r'i\'d like to (learn|achieve|accomplish)',
            r'by (next year|2024|2025)',
            r'(saving up for|planning to buy)'
        ],
        'event': [
            r'(yesterday|last (week|month|year))',
            r'(i went to|i visited|i traveled)',
            r'(happened|occurred) (yesterday|recently)',
            r'(remember when|back when)',
            r'(i met|i saw|i did)',
            r'(celebration|party|wedding|funeral)',
            r'(graduated|got married|had a baby)'
        ],
        'relationship': [
            r'(my (wife|husband|partner|boyfriend|girlfriend))',
            r'(my (mom|dad|mother|father|parent))',
            r'(my (son|daughter|child|kid))',
            r'(my (brother|sister|sibling))',
            r'(my (friend|colleague|boss|coworker))',
            r'(named|called) [A-Z][a-z]+',
            r'[A-Z][a-z]+ (is|works|lives|said|thinks)',
            r'(family|relatives|in-laws)'
        ],
        'challenge': [
            r'(struggling|having trouble|difficulty) with',
            r'(problem|issue|challenge) (with|is)',
            r'(can\'t (seem to|figure out))',
            r'(frustrated|stuck|overwhelmed) (with|by)',
            r'(worry|worried|anxious) about',
            r'(health (issue|problem)|medical)',
            r'(financial (trouble|stress))',
            r'(relationship (problem|issue))'
        ],
        'achievement': [
            r'(got|received|earned) (a|the|my) (promotion|raise|award)',
            r'(finished|completed|accomplished)',
            r'(proud|excited) (of|about)',
            r'(won|achieved|succeeded)',
            r'(milestone|breakthrough)',
            r'(certificate|degree|diploma)',
            r'(personal record|new high)'
        ],
        'knowledge': [
            r'(did you know|fun fact)',
            r'(learned|discovered|found out) that',
            r'(research shows|studies indicate)',
            r'(according to|based on)',
            r'(defined as|means that)',
            r'(formula|equation|method) (for|is)'
        ],
        'instruction': [
            r'(remember|don\'t forget) to',
            r'(always|never) (call|refer|mention) me',
            r'when (i say|i mention)',
            r'(respond|reply|answer) with',
            r'(your role is|you should)',
            r'(make sure to|be sure to)'
        ]
    }
    
    def categorize(
        self,
        memory_content: str,
        memory_type: Optional[str] = None
    ) -> str:
        """
        Categorize a memory based on its content.
        
        Args:
            memory_content: The memory text
            memory_type: Existing type hint (fact, preference, etc.)
            
        Returns:
            Category string
        """
        content_lower = memory_content.lower()
        
        # Score each category
        category_scores = {}
        for category, patterns in self.CATEGORY_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    score += 1
            if score > 0:
                category_scores[category] = score
        
        # Use existing memory_type as hint
        if memory_type:
            type_category_map = {
                'preference': 'preference',
                'goal': 'goal',
                'fact': 'personal_fact',
                'event': 'event',
                'instruction': 'instruction'
            }
            if memory_type in type_category_map:
                category = type_category_map[memory_type]
                if category in category_scores:
                    category_scores[category] += 2  # Boost existing type
                else:
                    category_scores[category] = 2
        
        # Return highest scoring category or default
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])[0]
            return best_category
        
        return 'knowledge'  # Default category
    
    def extract_entities(self, memory_content: str) -> Dict[str, List[str]]:
        """
        Extract entities from memory content.
        
        Returns:
            {
                'people': ['Alice', 'Bob'],
                'places': ['Paris', 'Tokyo'],
                'topics': ['python', 'machine learning'],
                'dates': ['2024-01-15', 'next week']
            }
        """
        entities = {
            'people': [],
            'places': [],
            'topics': [],
            'dates': []
        }
        
        # Extract people (proper names in context)
        people_patterns = [
            r'(?:my |)(?:friend|colleague|boss|partner|wife|husband|brother|sister|son|daughter|mom|dad|mother|father) (?:named |called |)([A-Z][a-z]+)',
            r'([A-Z][a-z]+) (?:is|was|said|thinks|works|lives)',
            r'(?:met|saw|talked to|called|messaged) ([A-Z][a-z]+)'
        ]
        
        for pattern in people_patterns:
            matches = re.findall(pattern, memory_content)
            entities['people'].extend(matches)
        
        # Remove common words that might be misidentified
        common_words = {'Today', 'Tomorrow', 'Yesterday', 'Next', 'Last', 'This', 
                       'That', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                       'Friday', 'Saturday', 'Sunday', 'January', 'February',
                       'March', 'April', 'May', 'June', 'July', 'August',
                       'September', 'October', 'November', 'December'}
        entities['people'] = [p for p in entities['people'] if p not in common_words]
        
        # Extract places (cities, countries - simple pattern)
        place_patterns = [
            r'(?:in|at|from|to|visit|traveled to|living in) ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'([A-Z][a-z]+) is (?:beautiful|amazing|lovely|nice)'
        ]
        
        for pattern in place_patterns:
            matches = re.findall(pattern, memory_content)
            # Filter out people names
            places = [m for m in matches if m not in entities['people']]
            entities['places'].extend(places)
        
        # Extract topics (technical terms, interests)
        # Look for lowercase technical terms or repeated words
        words = memory_content.lower().split()
        # Topics are words that appear with context indicators
        topic_indicators = ['learn', 'study', 'interest', 'hobby', 'about', 'using', 
                          'programming', 'language', 'framework', 'tool']
        
        for i, word in enumerate(words):
            if any(ind in words[max(0,i-3):i+3] for ind in topic_indicators):
                if len(word) > 4 and word.isalpha():
                    entities['topics'].append(word)
        
        # Extract dates
        date_patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',  # ISO format
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}(?:st|nd|rd|th)?,? \d{4}\b',
            r'\b(?:next|last) (?:week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\byesterday|today|tomorrow\b',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, memory_content, re.IGNORECASE)
            entities['dates'].extend(matches)
        
        # Deduplicate and clean
        for key in entities:
            entities[key] = list(set(entities[key]))
            # Remove empty strings
            entities[key] = [e for e in entities[key] if e.strip()]
        
        return entities
    
    def is_similar_topic(
        self,
        entities1: Dict[str, List[str]],
        entities2: Dict[str, List[str]]
    ) -> Tuple[bool, float]:
        """
        Check if two memories have similar topics/entities.
        
        Returns:
            (is_similar, similarity_score)
        """
        if not entities1 or not entities2:
            return False, 0.0
        
        score = 0.0
        max_score = 0.0
        
        # Compare people
        if entities1['people'] and entities2['people']:
            people1 = set(entities1['people'])
            people2 = set(entities2['people'])
            overlap = len(people1 & people2)
            if overlap > 0:
                score += overlap * 0.4  # People overlap is very important
            max_score += 0.4
        
        # Compare places
        if entities1['places'] and entities2['places']:
            places1 = set(entities1['places'])
            places2 = set(entities2['places'])
            overlap = len(places1 & places2)
            if overlap > 0:
                score += overlap * 0.2
            max_score += 0.2
        
        # Compare topics
        if entities1['topics'] and entities2['topics']:
            topics1 = set(entities1['topics'])
            topics2 = set(entities2['topics'])
            overlap = len(topics1 & topics2)
            if overlap > 0:
                score += overlap * 0.3
            max_score += 0.3
        
        # Compare dates
        if entities1['dates'] and entities2['dates']:
            dates1 = set(entities1['dates'])
            dates2 = set(entities2['dates'])
            overlap = len(dates1 & dates2)
            if overlap > 0:
                score += overlap * 0.1
            max_score += 0.1
        
        if max_score == 0:
            return False, 0.0
        
        similarity = score / max_score if max_score > 0 else 0.0
        is_similar = similarity > 0.3
        
        return is_similar, similarity
    
    def get_category_description(self, category: str) -> str:
        """Get human-readable description of category."""
        descriptions = {
            'personal_fact': 'Facts about you (name, job, location, etc.)',
            'preference': 'Your likes, dislikes, and preferences',
            'goal': 'Your goals and aspirations',
            'event': 'Past events and experiences',
            'relationship': 'Information about people in your life',
            'challenge': 'Problems, struggles, and obstacles',
            'achievement': 'Accomplishments and successes',
            'knowledge': 'General knowledge and facts',
            'instruction': 'How you want the AI to behave'
        }
        return descriptions.get(category, 'Uncategorized memory')

