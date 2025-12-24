"""JWT service for token generation and validation.

This module provides functions for creating and verifying JWT tokens
used for authentication in the PR-Review application.
"""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from pr_review_api.config import get_settings


class TokenError(Exception):
    """Exception raised for token-related errors."""

    pass


def create_access_token(user_id: str) -> str:
    """Create a JWT access token for the given user.

    Args:
        user_id: GitHub user ID to encode in the token.

    Returns:
        Encoded JWT token string.
    """
    settings = get_settings()

    now = datetime.now(UTC)
    expire = now + timedelta(hours=settings.jwt_expiration_hours)

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token.

    Args:
        token: JWT token string to verify.

    Returns:
        Decoded token payload dictionary containing:
        - sub: User ID
        - iat: Issued at timestamp
        - exp: Expiration timestamp

    Raises:
        TokenError: If the token is invalid, expired, or malformed.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        raise TokenError(f"Invalid token: {e}") from e
