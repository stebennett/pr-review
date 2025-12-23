"""User model for storing GitHub user information."""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String

from pr_review_api.database import Base


def utcnow() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class User(Base):
    """User model for storing GitHub user information.

    Attributes:
        id: GitHub user ID (primary key).
        github_username: GitHub username/login.
        github_access_token: Encrypted GitHub OAuth access token.
        email: User's email address (may be None if private).
        avatar_url: URL to user's GitHub avatar.
        created_at: Timestamp when the user was first created.
        updated_at: Timestamp when the user was last updated.
    """

    __tablename__ = "users"

    id = Column(String, primary_key=True)  # GitHub user ID
    github_username = Column(String, nullable=False)
    github_access_token = Column(String, nullable=False)  # Encrypted
    email = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def __repr__(self) -> str:
        """Return string representation of the user."""
        return f"<User(id={self.id}, username={self.github_username})>"
