"""Rate limiting utilities."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


# Create rate limiter instance
limiter = Limiter(key_func=get_remote_address)


def get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key from request.
    
    Uses remote address by default, but can be customized
    to use API keys, user IDs, etc.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Rate limit key string
    """
    return get_remote_address(request)

