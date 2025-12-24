"""Application configuration using pydantic-settings.

This module provides centralized configuration management for the PR-Review API.
Settings are loaded from environment variables with sensible defaults.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        database_url: SQLite database connection URL.
        github_client_id: GitHub OAuth App client ID.
        github_client_secret: GitHub OAuth App client secret.
        github_redirect_uri: OAuth callback URL.
        jwt_secret_key: Secret key for JWT signing.
        jwt_algorithm: JWT algorithm (default: HS256).
        jwt_expiration_hours: JWT token expiration in hours.
        encryption_key: Fernet key for encrypting secrets.
        cors_origins: Comma-separated list of allowed CORS origins.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///./pr_review.db"

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = ""

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Encryption
    encryption_key: str = ""

    # CORS
    cors_origins: str = "http://localhost:5173"

    # Frontend URL for OAuth callback redirect
    frontend_url: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse cors_origins string into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings instance loaded from environment variables.
    """
    return Settings()
