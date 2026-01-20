"""Tests for the config module."""

from pr_review_scheduler.config import Settings, get_settings


class TestSettings:
    """Tests for the Settings class."""

    def test_custom_settings_from_env(self, monkeypatch):
        """Test that settings are loaded from environment variables."""
        get_settings.cache_clear()

        monkeypatch.setenv("DATABASE_URL", "sqlite:///./custom.db")
        monkeypatch.setenv("ENCRYPTION_KEY", "custom-key")
        monkeypatch.setenv("SMTP2GO_HOST", "custom.smtp2go.com")
        monkeypatch.setenv("SMTP2GO_PORT", "465")
        monkeypatch.setenv("SMTP2GO_USERNAME", "custom-user")
        monkeypatch.setenv("SMTP2GO_PASSWORD", "custom-pass")
        monkeypatch.setenv("EMAIL_FROM_ADDRESS", "custom@example.com")
        monkeypatch.setenv("APPLICATION_URL", "https://custom.app.com")
        monkeypatch.setenv("SCHEDULE_POLL_INTERVAL", "120")
        monkeypatch.setenv("SCHEDULER_TIMEZONE", "Europe/London")
        monkeypatch.setenv("SCHEDULER_EXECUTOR_POOL_SIZE", "20")

        settings = Settings()

        assert settings.database_url == "sqlite:///./custom.db"
        assert settings.encryption_key == "custom-key"
        assert settings.smtp2go_host == "custom.smtp2go.com"
        assert settings.smtp2go_port == 465
        assert settings.smtp2go_username == "custom-user"
        assert settings.smtp2go_password == "custom-pass"
        assert settings.email_from_address == "custom@example.com"
        assert settings.application_url == "https://custom.app.com"
        assert settings.schedule_poll_interval == 120
        assert settings.scheduler_timezone == "Europe/London"
        assert settings.scheduler_executor_pool_size == 20

        get_settings.cache_clear()


class TestGetSettings:
    """Tests for the get_settings function."""

    def test_get_settings_returns_settings_instance(self, mock_settings):
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self, mock_settings):
        """Test that get_settings returns the same cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_get_settings_cache_can_be_cleared(self, monkeypatch):
        """Test that the settings cache can be cleared."""
        get_settings.cache_clear()

        monkeypatch.setenv("SCHEDULER_TIMEZONE", "UTC")
        settings1 = get_settings()
        assert settings1.scheduler_timezone == "UTC"

        get_settings.cache_clear()

        monkeypatch.setenv("SCHEDULER_TIMEZONE", "Asia/Tokyo")
        settings2 = get_settings()
        assert settings2.scheduler_timezone == "Asia/Tokyo"

        get_settings.cache_clear()
