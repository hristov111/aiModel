"""Tests for authentication and JWT functionality."""

import pytest
from datetime import datetime, timedelta
from app.core.auth import (
    create_jwt_token,
    validate_jwt_token,
    decode_jwt_token,
    generate_api_key,
    validate_api_key
)
from app.core.config import settings


class TestJWTAuthentication:
    """Test JWT token creation and validation."""
    
    def test_create_jwt_token(self):
        """Test JWT token creation."""
        user_id = "test_user_123"
        token = create_jwt_token(user_id, expires_in_hours=1)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_validate_jwt_token_valid(self):
        """Test validating a valid JWT token."""
        user_id = "test_user_123"
        token = create_jwt_token(user_id, expires_in_hours=1)
        
        validated_user_id = validate_jwt_token(token)
        
        assert validated_user_id == user_id
    
    def test_validate_jwt_token_expired(self):
        """Test validating an expired JWT token."""
        user_id = "test_user_123"
        
        # Create token with negative expiration (already expired)
        import jwt
        from datetime import datetime, timedelta
        
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        
        expired_token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        validated_user_id = validate_jwt_token(expired_token)
        
        assert validated_user_id is None
    
    def test_validate_jwt_token_invalid_signature(self):
        """Test validating JWT token with invalid signature."""
        user_id = "test_user_123"
        
        # Create token with wrong secret
        import jwt
        from datetime import datetime, timedelta
        
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        
        invalid_token = jwt.encode(
            payload,
            "wrong-secret-key",
            algorithm=settings.jwt_algorithm
        )
        
        validated_user_id = validate_jwt_token(invalid_token)
        
        assert validated_user_id is None
    
    def test_decode_jwt_token(self):
        """Test decoding JWT token payload."""
        user_id = "test_user_123"
        token = create_jwt_token(user_id, expires_in_hours=1)
        
        payload = decode_jwt_token(token)
        
        assert payload is not None
        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_jwt_token_with_custom_expiration(self):
        """Test creating JWT token with custom expiration."""
        user_id = "test_user_123"
        expires_in_hours = 48
        
        token = create_jwt_token(user_id, expires_in_hours=expires_in_hours)
        payload = decode_jwt_token(token)
        
        assert payload is not None
        
        # Check expiration is approximately correct (within 1 minute tolerance)
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + timedelta(hours=expires_in_hours)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        
        assert time_diff < 60  # Within 1 minute


class TestAPIKeyAuthentication:
    """Test API key generation and validation."""
    
    def test_generate_api_key(self):
        """Test API key generation."""
        user_id = "test_user"
        api_key = generate_api_key(user_id)
        
        assert api_key is not None
        assert api_key.startswith(f"user_{user_id}_")
        assert len(api_key) > len(f"user_{user_id}_")
    
    def test_validate_api_key_valid(self):
        """Test validating a valid API key."""
        user_id = "alice"
        api_key = generate_api_key(user_id)
        
        validated_user_id = validate_api_key(api_key)
        
        assert validated_user_id == user_id
    
    def test_validate_api_key_invalid_format(self):
        """Test validating API key with invalid format."""
        invalid_keys = [
            "invalid",
            "user_",
            "notakey",
            "",
            "key_alice_123"
        ]
        
        for key in invalid_keys:
            validated_user_id = validate_api_key(key)
            assert validated_user_id is None
    
    def test_api_key_uniqueness(self):
        """Test that generated API keys are unique."""
        user_id = "test_user"
        keys = [generate_api_key(user_id) for _ in range(10)]
        
        # All keys should be unique
        assert len(keys) == len(set(keys))


class TestProductionValidation:
    """Test production configuration validation."""
    
    def test_production_validation_errors(self):
        """Test that production validation catches security issues."""
        # This would be tested with environment variables
        # Just ensure the validation function exists
        from app.core.config import Settings
        
        test_settings = Settings()
        
        # Should have validation method
        assert hasattr(test_settings, 'validate_production_settings')
        assert callable(test_settings.validate_production_settings)


@pytest.mark.asyncio
class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""
    
    async def test_create_token_endpoint(self, client):
        """Test token creation endpoint."""
        response = await client.post(
            "/auth/token",
            json={
                "user_id": "test_user",
                "expires_in_hours": 24
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == "test_user"
        assert data["expires_in"] == 24 * 3600
    
    async def test_validate_token_endpoint_valid(self, client):
        """Test token validation endpoint with valid token."""
        # First create a token
        create_response = await client.post(
            "/auth/token",
            json={"user_id": "test_user"}
        )
        token = create_response.json()["access_token"]
        
        # Then validate it
        response = await client.post(
            "/auth/validate",
            json={"token": token}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is True
        assert data["user_id"] == "test_user"
        assert data["error"] is None
    
    async def test_validate_token_endpoint_invalid(self, client):
        """Test token validation endpoint with invalid token."""
        response = await client.post(
            "/auth/validate",
            json={"token": "invalid.token.here"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is False
        assert data["user_id"] is None
        assert data["error"] is not None

