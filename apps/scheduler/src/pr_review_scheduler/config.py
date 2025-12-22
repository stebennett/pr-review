"""Application configuration using pydantic-settings.

This module provides centralized configuration management for the PR-Review Scheduler.
Settings are loaded from environment variables with sensible defaults.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        database_url: SQLite database connection URL.
        encryption_key: Fernet key for decrypting PATs.
        smtp2go_host: SMTP2GO server hostname.
        smtp2go_port: SMTP2GO server port.
        smtp2go_username: SMTP2GO username.
        smtp2go_password: SMTP2GO password.
        email_from_address: Sender email address.
        application_url: Base URL of the application (for email links).
        schedule_poll_interval: Seconds between schedule DB polls.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "sqlite:///./pr_review.db"

    # Encryption
    encryption_key: str = ""

    # SMTP2GO
    smtp2go_host: str = ""
    smtp2go_port: int = 587
    smtp2go_username: str = ""
    smtp2go_password: str = ""

    # Email
    email_from_address: str = ""

    # Application
    application_url: str = "http://localhost:5173"

    # Scheduler
    schedule_poll_interval: int = 60


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings instance loaded from environment variables.
    """
    return Settings()
