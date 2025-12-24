"""Content routing system with model switching and prompt management."""

import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

from app.services.content_classifier import ContentLabel, ClassificationResult
from app.services.llm_client import LLMClient, LMStudioClient, OpenAIClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelRoute(str, Enum):
    """Model routing destinations."""
    NORMAL = "NORMAL"  # Safe content
    ROMANCE = "ROMANCE"  # Suggestive/flirty content
    EXPLICIT = "EXPLICIT"  # Consensual adult explicit content
    FETISH = "FETISH"  # Fetish content with tighter guardrails
    REFUSAL = "REFUSAL"  # Non-consensual content
    HARD_REFUSAL = "HARD_REFUSAL"  # Minor risk content


@dataclass
class RouteConfig:
    """Configuration for a specific route."""
    model_route: ModelRoute
    client_type: str  # "openai" or "local"
    model_name: Optional[str]
    temperature: float
    max_tokens: int
    system_prompt: str


class ContentRouter:
    """
    Routes content to appropriate models based on classification.
    
    Implements:
    - Model switching based on content type
    - Separate system prompts per route
    - Refusal handling for prohibited content
    """
    
    # Route mapping: ContentLabel -> ModelRoute
    ROUTE_MAP = {
        ContentLabel.SAFE: ModelRoute.NORMAL,
        ContentLabel.SUGGESTIVE: ModelRoute.ROMANCE,
        ContentLabel.EXPLICIT_CONSENSUAL_ADULT: ModelRoute.EXPLICIT,
        ContentLabel.EXPLICIT_FETISH: ModelRoute.FETISH,
        ContentLabel.NONCONSENSUAL: ModelRoute.REFUSAL,
        ContentLabel.MINOR_RISK: ModelRoute.HARD_REFUSAL,
    }
    
    # System prompts for each route
    SYSTEM_PROMPTS = {
        ModelRoute.NORMAL: """You are a helpful, knowledgeable AI assistant with memory of past conversations.
Be friendly, supportive, and engaging. Maintain appropriate boundaries.""",
        
        ModelRoute.ROMANCE: """You are a warm, flirtatious AI companion with memory of past conversations.
You can engage in romantic and suggestive conversation while maintaining respect and consent.
Be playful and charming, but always respectful. Keep things tasteful and consensual.""",
        
        ModelRoute.EXPLICIT: """You are an adult AI companion for consensual explicit conversations.

RULES:
- Adults only - all participants must be 18+
- Explicit anatomical language is allowed
- Maintain enthusiastic consent at all times
- NO coercion, degradation, or non-consensual content
- NO illegal content of any kind
- Maintain character boundaries and respect limits
- If anything feels non-consensual, stop immediately

Be open and direct while maintaining safety and consent.""",
        
        ModelRoute.FETISH: """You are an adult AI companion for consensual fetish/kink exploration.

STRICT RULES:
- Adults only - all participants must be 18+
- Explicit content allowed within narrow, consensual scope
- HARD FILTERS for:
  * Permanent harm or injury
  * Extreme humiliation or degradation
  * Power imbalance exploitation
  * Non-consensual acts
  * Illegal content
- Maintain SSC (Safe, Sane, Consensual) or RACK (Risk-Aware Consensual Kink) principles
- Check in on comfort and boundaries regularly
- Stop immediately if consent is unclear

Be open within these strict boundaries.""",
        
        ModelRoute.REFUSAL: """I cannot engage with content involving non-consensual activities, coercion, or force.

I'm happy to have other conversations with you. What else can I help you with?""",
        
        ModelRoute.HARD_REFUSAL: """I cannot engage with any content involving minors or age-ambiguous scenarios.

This is a hard boundary for safety and legal reasons. I'm happy to help with other topics.""",
    }
    
    def __init__(self):
        """Initialize content router."""
        self.routes: Dict[ModelRoute, RouteConfig] = self._build_routes()
        self.clients: Dict[str, LLMClient] = {}
        logger.info("ContentRouter initialized with model switching")
    
    def _build_routes(self) -> Dict[ModelRoute, RouteConfig]:
        """Build route configurations."""
        routes = {
            ModelRoute.NORMAL: RouteConfig(
                model_route=ModelRoute.NORMAL,
                client_type="openai",
                model_name=settings.openai_model_name,
                temperature=0.7,
                max_tokens=2000,
                system_prompt=self.SYSTEM_PROMPTS[ModelRoute.NORMAL],
            ),
            ModelRoute.ROMANCE: RouteConfig(
                model_route=ModelRoute.ROMANCE,
                client_type="openai",
                model_name=settings.openai_model_name,
                temperature=0.8,  # Slightly more creative
                max_tokens=2000,
                system_prompt=self.SYSTEM_PROMPTS[ModelRoute.ROMANCE],
            ),
            ModelRoute.EXPLICIT: RouteConfig(
                model_route=ModelRoute.EXPLICIT,
                client_type="local",  # Use uncensored local model
                model_name=settings.lm_studio_model_name,
                temperature=0.8,
                max_tokens=2000,
                system_prompt=self.SYSTEM_PROMPTS[ModelRoute.EXPLICIT],
            ),
            ModelRoute.FETISH: RouteConfig(
                model_route=ModelRoute.FETISH,
                client_type="local",  # Use uncensored local model
                model_name=settings.lm_studio_model_name,
                temperature=0.7,  # More controlled
                max_tokens=1500,  # Shorter responses
                system_prompt=self.SYSTEM_PROMPTS[ModelRoute.FETISH],
            ),
            ModelRoute.REFUSAL: RouteConfig(
                model_route=ModelRoute.REFUSAL,
                client_type="openai",  # Use safe model for refusals
                model_name=settings.openai_model_name,
                temperature=0.5,
                max_tokens=200,
                system_prompt=self.SYSTEM_PROMPTS[ModelRoute.REFUSAL],
            ),
            ModelRoute.HARD_REFUSAL: RouteConfig(
                model_route=ModelRoute.HARD_REFUSAL,
                client_type="openai",  # Use safe model for refusals
                model_name=settings.openai_model_name,
                temperature=0.5,
                max_tokens=200,
                system_prompt=self.SYSTEM_PROMPTS[ModelRoute.HARD_REFUSAL],
            ),
        }
        return routes
    
    def route(self, classification: ClassificationResult) -> ModelRoute:
        """
        Determine route based on classification.
        
        Args:
            classification: Classification result
            
        Returns:
            ModelRoute to use
        """
        route = self.ROUTE_MAP.get(classification.label, ModelRoute.NORMAL)
        
        logger.info(
            f"Routing {classification.label} (confidence: {classification.confidence:.2f}) "
            f"to {route}"
        )
        
        return route
    
    def get_client(self, route: ModelRoute) -> LLMClient:
        """
        Get or create LLM client for route.
        
        Args:
            route: Model route
            
        Returns:
            LLMClient instance
        """
        config = self.routes[route]
        cache_key = f"{config.client_type}_{config.model_name}"
        
        if cache_key not in self.clients:
            if config.client_type == "local":
                self.clients[cache_key] = LMStudioClient(
                    model_name=config.model_name,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )
            else:  # openai
                self.clients[cache_key] = OpenAIClient(
                    model_name=config.model_name,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )
            
            logger.info(f"Created {config.client_type} client for route {route}")
        
        return self.clients[cache_key]
    
    def get_system_prompt(self, route: ModelRoute) -> str:
        """
        Get system prompt for route.
        
        Args:
            route: Model route
            
        Returns:
            System prompt string
        """
        return self.routes[route].system_prompt
    
    def should_refuse(self, route: ModelRoute) -> bool:
        """
        Check if route should refuse to generate.
        
        Args:
            route: Model route
            
        Returns:
            True if should refuse
        """
        return route in (ModelRoute.REFUSAL, ModelRoute.HARD_REFUSAL)
    
    def get_refusal_message(self, route: ModelRoute) -> str:
        """
        Get refusal message for route.
        
        Args:
            route: Model route
            
        Returns:
            Refusal message
        """
        return self.SYSTEM_PROMPTS.get(route, "I cannot assist with this request.")


# Global router instance
_router: Optional[ContentRouter] = None


def get_content_router() -> ContentRouter:
    """
    Get or create global content router instance.
    
    Returns:
        ContentRouter instance
    """
    global _router
    if _router is None:
        _router = ContentRouter()
    return _router

