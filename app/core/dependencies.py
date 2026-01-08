"""Dependency injection for FastAPI."""

from typing import AsyncGenerator, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user_id, ensure_user_exists
from app.core.config import settings
from app.repositories.vector_store import VectorStoreRepository
from app.utils.embeddings import get_embedding_generator, EmbeddingGenerator
from app.services.llm_client import get_llm_client, LLMClient
from app.services.short_term_memory import get_conversation_buffer, ConversationBuffer
from app.services.long_term_memory import LongTermMemoryService
from app.services.prompt_builder import PromptBuilder
from app.services.chat_service import ChatService
from app.services.user_preference_service import UserPreferenceService
from app.services.emotion_service import EmotionService
from app.services.personality_service import PersonalityService
from app.services.personality_cache import PersonalityCache
from app.models.database import UserModel


# Singletons
_personality_cache: Optional[PersonalityCache] = None

def get_embedding_generator_dep() -> EmbeddingGenerator:
    """Get embedding generator dependency."""
    return get_embedding_generator()


def get_llm_client_dep() -> LLMClient:
    """Get LLM client dependency (defaults to OpenAI)."""
    return get_llm_client(provider="openai")


def get_conversation_buffer_dep() -> ConversationBuffer:
    """Get conversation buffer dependency."""
    return get_conversation_buffer()


def get_prompt_builder_dep() -> PromptBuilder:
    """Get prompt builder dependency."""
    return PromptBuilder()


def get_personality_cache_dep() -> Optional[PersonalityCache]:
    """Get personality cache dependency (Redis-based singleton)."""
    global _personality_cache
    if _personality_cache is None and settings.redis_enabled and settings.redis_url:
        _personality_cache = PersonalityCache(redis_url=settings.redis_url)
    return _personality_cache


# Database-dependent services
def get_vector_store(
    db: AsyncSession = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client_dep)
) -> VectorStoreRepository:
    """Get vector store repository dependency."""
    return VectorStoreRepository(db, llm_client=llm_client)


def get_long_term_memory(
    vector_store: VectorStoreRepository = Depends(get_vector_store),
    embedding_generator: EmbeddingGenerator = Depends(get_embedding_generator_dep),
    llm_client: LLMClient = Depends(get_llm_client_dep)
) -> LongTermMemoryService:
    """Get long-term memory service dependency."""
    return LongTermMemoryService(
        vector_store=vector_store,
        embedding_generator=embedding_generator,
        llm_client=llm_client  # ✅ ENABLED: Use LLM for intelligent memory extraction
    )


def get_preference_service(
    db: AsyncSession = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client_dep)
) -> UserPreferenceService:
    """Get user preference service dependency."""
    return UserPreferenceService(db, llm_client=llm_client)


def get_emotion_service(
    db: AsyncSession = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client_dep)
) -> EmotionService:
    """Get emotion service dependency."""
    return EmotionService(db, llm_client=llm_client)


def get_personality_service(
    db: AsyncSession = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client_dep),
    cache: Optional[PersonalityCache] = Depends(get_personality_cache_dep)
) -> PersonalityService:
    """Get personality service dependency with Redis caching."""
    return PersonalityService(db, llm_client=llm_client, cache=cache)


def get_goal_service(
    db: AsyncSession = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client_dep)
):
    """Get goal service dependency."""
    from app.services.goal_service import GoalService
    return GoalService(db, llm_client=llm_client)


def get_chat_service(
    conversation_buffer: ConversationBuffer = Depends(get_conversation_buffer_dep),
    long_term_memory: LongTermMemoryService = Depends(get_long_term_memory),
    prompt_builder: PromptBuilder = Depends(get_prompt_builder_dep),
    llm_client: LLMClient = Depends(get_llm_client_dep),
    preference_service: UserPreferenceService = Depends(get_preference_service),
    emotion_service: EmotionService = Depends(get_emotion_service),
    personality_service: PersonalityService = Depends(get_personality_service),
    goal_service = Depends(get_goal_service)
) -> ChatService:
    """Get chat service dependency."""
    return ChatService(
        conversation_buffer=conversation_buffer,
        long_term_memory=long_term_memory,
        prompt_builder=prompt_builder,
        llm_client=llm_client,
        preference_service=preference_service,
        emotion_service=emotion_service,
        personality_service=personality_service,
        goal_service=goal_service
    )

