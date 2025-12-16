"""Application configuration using Pydantic Settings."""

import os
import secrets as secrets_module
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LM Studio Configuration
    lm_studio_base_url: str = "http://localhost:1234/v1"
    lm_studio_model_name: str = "local-model"
    lm_studio_temperature: float = 0.7
    lm_studio_max_tokens: int = 150  # Shorter responses for faster generation
    
    # Database Configuration
    postgres_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_companion"
    postgres_pool_size: int = 10
    postgres_max_overflow: int = 20
    
    # Redis Configuration (optional, for distributed deployments)
    redis_url: str = ""  # e.g., "redis://localhost:6379/0"
    redis_enabled: bool = False  # Enable Redis-based short-term memory
    
    # Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # Memory Configuration
    short_term_memory_size: int = 10
    long_term_memory_top_k: int = 5
    memory_similarity_threshold: float = 0.2  # Lowered for better recall (embedding similarities are typically low)
    memory_extraction_min_turns: int = 3
    memory_extraction_method: str = "hybrid"  # Options: "llm", "heuristic", "hybrid"
    
    # AI Detection Methods (AI Chaining)
    emotion_detection_method: str = "hybrid"  # Options: "llm", "pattern", "hybrid"
    goal_detection_method: str = "hybrid"  # Options: "llm", "pattern", "hybrid"
    personality_detection_method: str = "hybrid"  # Options: "llm", "pattern", "hybrid"
    memory_categorization_method: str = "hybrid"  # Options: "llm", "pattern", "hybrid"
    contradiction_detection_method: str = "hybrid"  # Options: "llm", "pattern", "hybrid"
    
    # System Configuration
    system_persona: str = "a helpful, knowledgeable AI assistant with memory of past conversations"
    rate_limit_requests_per_minute: int = 30
    
    # Authentication
    require_authentication: bool = True  # Set to False for development without auth
    jwt_secret_key: str = "change-this-in-production"  # For JWT tokens
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    
    # Logging
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        env = os.getenv("ENVIRONMENT", "development").lower()
        return env in ("production", "prod")
    
    def validate_production_settings(self) -> None:
        """
        Validate that production settings are properly configured.
        Raises ValueError if critical security settings are misconfigured.
        """
        if not self.is_production:
            return
        
        errors = []
        
        # Check JWT secret is not default
        if self.jwt_secret_key == "change-this-in-production":
            errors.append(
                "JWT_SECRET_KEY is using default value! "
                "Set a strong random key: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        # Check JWT secret strength
        if len(self.jwt_secret_key) < 32:
            errors.append(
                f"JWT_SECRET_KEY is too short ({len(self.jwt_secret_key)} chars). "
                "Use at least 32 characters for production."
            )
        
        # Check authentication is enabled
        if not self.require_authentication:
            errors.append(
                "REQUIRE_AUTHENTICATION must be 'true' in production! "
                "Never disable authentication in production."
            )
        
        # Warn about weak database passwords
        if "postgres:postgres@" in self.postgres_url.lower():
            logger.warning(
                "⚠️  WARNING: Database URL contains default 'postgres' password. "
                "Use strong passwords in production!"
            )
        
        # Check CORS is not too permissive
        if "*" in self.cors_origins:
            errors.append(
                "CORS_ORIGINS cannot contain '*' in production! "
                "Specify exact allowed origins."
            )
        
        if errors:
            error_msg = "\n❌ PRODUCTION CONFIGURATION ERRORS:\n" + "\n".join(f"  • {e}" for e in errors)
            raise ValueError(error_msg)
        
        logger.info("✅ Production configuration validated successfully")


# Global settings instance
settings = Settings()

# Validate production settings on import
if settings.is_production:
    settings.validate_production_settings()

