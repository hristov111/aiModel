"""Custom exceptions for the AI Companion Service."""


class AICompanionException(Exception):
    """Base exception for all AI Companion errors."""
    pass


class LLMConnectionError(AICompanionException):
    """Raised when unable to connect to LLM service."""
    pass


class LLMResponseError(AICompanionException):
    """Raised when LLM returns an invalid response."""
    pass


class EmbeddingGenerationError(AICompanionException):
    """Raised when embedding generation fails."""
    pass


class MemoryRetrievalError(AICompanionException):
    """Raised when memory retrieval fails."""
    pass


class MemoryStorageError(AICompanionException):
    """Raised when memory storage fails."""
    pass


class ConversationNotFoundError(AICompanionException):
    """Raised when conversation ID is not found."""
    pass


class InvalidRequestError(AICompanionException):
    """Raised when request validation fails."""
    pass

