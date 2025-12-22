"""Pytest configuration and fixtures for scheduler tests."""

import pytest


@pytest.fixture
def mock_settings(monkeypatch):
    """Provide mock settings for tests."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key")
    monkeypatch.setenv("SMTP2GO_HOST", "mail.smtp2go.com")
    monkeypatch.setenv("SMTP2GO_PORT", "587")
    monkeypatch.setenv("SMTP2GO_USERNAME", "test-user")
    monkeypatch.setenv("SMTP2GO_PASSWORD", "test-password")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "test@example.com")
    monkeypatch.setenv("APPLICATION_URL", "http://localhost:5173")
