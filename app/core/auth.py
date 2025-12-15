"""Authentication and authorization utilities."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import secrets
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from app.models.database import UserModel
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


async def get_current_user_id(
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Extract user ID from request headers.
    
    Supports multiple authentication methods:
    1. X-API-Key header (simple API key authentication)
    2. X-User-Id header (for development/testing)
    3. Authorization header (Bearer token - for future JWT implementation)
    
    Args:
        x_api_key: API key from X-API-Key header
        x_user_id: User ID from X-User-Id header (dev mode)
        authorization: Bearer token from Authorization header
        
    Returns:
        User ID string
        
    Raises:
        HTTPException: If authentication fails
    """
    # Method 1: X-User-Id header (development mode)
    # WARNING: Only use in development! Not secure for production.
    if x_user_id:
        logger.debug(f"Authenticated user via X-User-Id: {x_user_id}")
        return x_user_id
    
    # Method 2: X-API-Key header (simple API key)
    if x_api_key:
        user_id = validate_api_key(x_api_key)
        if user_id:
            logger.debug(f"Authenticated user via API key: {user_id}")
            return user_id
    
    # Method 3: Authorization Bearer token (JWT - for future implementation)
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        user_id = validate_jwt_token(token)
        if user_id:
            logger.debug(f"Authenticated user via JWT: {user_id}")
            return user_id
    
    # No valid authentication found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide X-User-Id, X-API-Key, or Authorization header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def validate_api_key(api_key: str) -> Optional[str]:
    """
    Validate API key and return user ID.
    
    Simple implementation for demonstration.
    In production, store API keys in database with proper hashing.
    
    Args:
        api_key: API key to validate
        
    Returns:
        User ID if valid, None otherwise
    """
    # Simple format: "user_<user_id>_<random>"
    # Example: "user_alice_a1b2c3d4"
    
    if not api_key or not api_key.startswith("user_"):
        return None
    
    parts = api_key.split("_")
    if len(parts) >= 2:
        user_id = parts[1]
        logger.debug(f"Extracted user_id from API key: {user_id}")
        return user_id
    
    return None


def validate_jwt_token(token: str) -> Optional[str]:
    """
    Validate JWT token and return user ID.
    
    Implements proper JWT validation with:
    - Signature verification
    - Expiration checking
    - Algorithm verification (prevents 'none' algorithm attack)
    
    Args:
        token: JWT token
        
    Returns:
        User ID if valid, None otherwise
    """
    try:
        # Decode and verify JWT token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "require": ["exp", "sub"]  # Require expiration and subject (user_id)
            }
        )
        
        # Extract user_id from 'sub' (subject) claim
        user_id = payload.get("sub")
        
        if not user_id:
            logger.warning("JWT token missing 'sub' claim")
            return None
        
        logger.debug(f"Successfully validated JWT for user: {user_id}")
        return user_id
        
    except ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error validating JWT: {e}", exc_info=True)
        return None


def generate_api_key(user_id: str) -> str:
    """
    Generate a simple API key for a user.
    
    Format: user_<user_id>_<random_string>
    
    Args:
        user_id: User identifier
        
    Returns:
        Generated API key
    """
    random_suffix = secrets.token_urlsafe(16)
    return f"user_{user_id}_{random_suffix}"


def create_jwt_token(
    user_id: str,
    expires_in_hours: Optional[int] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT token for a user.
    
    Args:
        user_id: User identifier
        expires_in_hours: Token expiration time in hours (default: from settings)
        additional_claims: Optional additional claims to include in token
        
    Returns:
        Encoded JWT token
    """
    if expires_in_hours is None:
        expires_in_hours = settings.jwt_expiration_hours
    
    # Calculate expiration time
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=expires_in_hours)
    
    # Build token payload
    payload = {
        "sub": user_id,  # Subject (user_id)
        "iat": now,  # Issued at
        "exp": expires_at,  # Expiration
        "type": "access_token"
    }
    
    # Add any additional claims
    if additional_claims:
        payload.update(additional_claims)
    
    # Encode and sign the token
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    logger.debug(f"Created JWT token for user {user_id}, expires in {expires_in_hours}h")
    
    return token


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT token without validation (use validate_jwt_token for auth).
    Useful for debugging and inspecting tokens.
    
    Args:
        token: JWT token
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False}
        )
        return payload
    except Exception as e:
        logger.error(f"Failed to decode JWT token: {e}")
        return None


async def ensure_user_exists(
    session: AsyncSession,
    user_id: str,
    email: Optional[str] = None,
    display_name: Optional[str] = None
) -> UserModel:
    """
    Ensure user exists in database, create if not.
    
    Args:
        session: Database session
        user_id: External user ID
        email: Optional email
        display_name: Optional display name
        
    Returns:
        UserModel instance
    """
    # Try to find existing user
    result = await session.execute(
        select(UserModel).where(UserModel.external_user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        # Create new user
        user = UserModel(
            external_user_id=user_id,
            email=email,
            display_name=display_name or user_id
        )
        session.add(user)
        await session.flush()
        logger.info(f"Created new user: {user_id}")
    
    return user


async def verify_conversation_ownership(
    session: AsyncSession,
    conversation_id,
    user_id: str
) -> bool:
    """
    Verify that a conversation belongs to a user.
    
    Args:
        session: Database session
        conversation_id: Conversation UUID
        user_id: External user ID
        
    Returns:
        True if user owns conversation
        
    Raises:
        HTTPException: If conversation not found or unauthorized
    """
    from app.models.database import ConversationModel
    
    result = await session.execute(
        select(ConversationModel)
        .join(UserModel)
        .where(ConversationModel.id == conversation_id)
        .where(UserModel.external_user_id == user_id)
    )
    conversation = result.scalar_one_or_none()
    
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or you don't have access"
        )
    
    return True

