"""Tests for JWT service."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from pr_review_api.services.jwt import TokenError, create_access_token, verify_token


class TestJWTService:
    """Tests for JWT service functions."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for JWT operations."""
        settings = MagicMock()
        settings.jwt_secret_key = "test_secret_key_for_jwt_testing"
        settings.jwt_algorithm = "HS256"
        settings.jwt_expiration_hours = 24
        return settings

    def test_create_access_token_returns_string(self, mock_settings):
        """Should return a JWT token string."""
        with patch("pr_review_api.services.jwt.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            token = create_access_token(user_id="12345")

            assert isinstance(token, str)
            assert len(token) > 0
            # JWT tokens have 3 parts separated by dots
            assert token.count(".") == 2

    def test_create_access_token_encodes_user_id(self, mock_settings):
        """Token payload should contain user ID in sub claim."""
        with patch("pr_review_api.services.jwt.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            token = create_access_token(user_id="12345")
            payload = verify_token(token)

            assert payload["sub"] == "12345"

    def test_create_access_token_includes_expiration(self, mock_settings):
        """Token should include expiration time."""
        with patch("pr_review_api.services.jwt.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            token = create_access_token(user_id="12345")
            payload = verify_token(token)

            assert "exp" in payload
            # Expiration should be in the future
            exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
            assert exp_time > datetime.now(UTC)

    def test_create_access_token_includes_issued_at(self, mock_settings):
        """Token should include issued at time."""
        with patch("pr_review_api.services.jwt.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            token = create_access_token(user_id="12345")
            payload = verify_token(token)

            assert "iat" in payload

    def test_verify_token_returns_payload(self, mock_settings):
        """Should decode and return token payload."""
        with patch("pr_review_api.services.jwt.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            token = create_access_token(user_id="12345")
            payload = verify_token(token)

            assert isinstance(payload, dict)
            assert "sub" in payload
            assert "exp" in payload
            assert "iat" in payload

    def test_verify_token_rejects_invalid_token(self, mock_settings):
        """Should raise TokenError for invalid tokens."""
        with patch("pr_review_api.services.jwt.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            with pytest.raises(TokenError):
                verify_token("invalid.token.here")

    def test_verify_token_rejects_wrong_secret(self, mock_settings):
        """Should raise TokenError when token was signed with different secret."""
        with patch("pr_review_api.services.jwt.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            # Create token with one secret
            token = create_access_token(user_id="12345")

            # Try to verify with different secret
            mock_settings.jwt_secret_key = "different_secret_key"

            with pytest.raises(TokenError):
                verify_token(token)

    def test_verify_token_rejects_expired_token(self, mock_settings):
        """Should raise TokenError for expired tokens."""
        with patch("pr_review_api.services.jwt.get_settings") as mock_get_settings:
            # Set expiration to -1 hours (already expired)
            mock_settings.jwt_expiration_hours = -1
            mock_get_settings.return_value = mock_settings

            token = create_access_token(user_id="12345")

            with pytest.raises(TokenError):
                verify_token(token)
