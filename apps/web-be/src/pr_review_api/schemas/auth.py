"""Authentication schemas for request and response models."""

from pydantic import BaseModel


class LoginResponse(BaseModel):
    """Response from /api/auth/login endpoint.

    Attributes:
        url: GitHub OAuth authorization URL to redirect the user to.
    """

    url: str


class UserResponse(BaseModel):
    """User information response.

    Attributes:
        id: GitHub user ID.
        username: GitHub username.
        email: User's email address (may be None if private).
        avatar_url: URL to user's GitHub avatar.
    """

    id: str
    username: str
    email: str | None = None
    avatar_url: str | None = None


class TokenResponse(BaseModel):
    """JWT token response.

    Attributes:
        access_token: JWT access token.
        token_type: Token type (always "bearer").
    """

    access_token: str
    token_type: str = "bearer"
