"""Pytest configuration and fixtures for scheduler tests."""

import pytest

from pr_review_scheduler.config import get_settings


@pytest.fixture
def mock_settings(monkeypatch):
    """Provide mock settings for tests."""
    # Clear the cached settings
    get_settings.cache_clear()

    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
    monkeypatch.setenv("SMTP2GO_HOST", "mail.smtp2go.com")
    monkeypatch.setenv("SMTP2GO_PORT", "587")
    monkeypatch.setenv("SMTP2GO_USERNAME", "test-user")
    monkeypatch.setenv("SMTP2GO_PASSWORD", "test-password")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "test@example.com")
    monkeypatch.setenv("APPLICATION_URL", "http://localhost:5173")
    monkeypatch.setenv("SCHEDULER_TIMEZONE", "UTC")
    monkeypatch.setenv("SCHEDULER_EXECUTOR_POOL_SIZE", "5")

    yield

    # Clear the cache after the test
    get_settings.cache_clear()


@pytest.fixture
def mock_settings_different_timezone(monkeypatch):
    """Provide mock settings with a different timezone for tests."""
    # Clear the cached settings
    get_settings.cache_clear()

    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
    monkeypatch.setenv("SMTP2GO_HOST", "mail.smtp2go.com")
    monkeypatch.setenv("SMTP2GO_PORT", "587")
    monkeypatch.setenv("SMTP2GO_USERNAME", "test-user")
    monkeypatch.setenv("SMTP2GO_PASSWORD", "test-password")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "test@example.com")
    monkeypatch.setenv("APPLICATION_URL", "http://localhost:5173")
    monkeypatch.setenv("SCHEDULER_TIMEZONE", "America/New_York")
    monkeypatch.setenv("SCHEDULER_EXECUTOR_POOL_SIZE", "3")

    yield

    # Clear the cache after the test
    get_settings.cache_clear()
