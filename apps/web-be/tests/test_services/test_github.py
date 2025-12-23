"""Tests for GitHub OAuth service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGitHubOAuthService:
    """Tests for GitHubOAuthService."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for the service."""
        settings = MagicMock()
        settings.github_client_id = "test_client_id"
        settings.github_client_secret = "test_client_secret"
        settings.github_redirect_uri = "http://localhost:8000/api/auth/callback"
        return settings

    @pytest.fixture
    def service(self, mock_settings):
        """Create a GitHubOAuthService with mocked settings."""
        with patch("pr_review_api.services.github.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            from pr_review_api.services.github import GitHubOAuthService

            return GitHubOAuthService()

    @pytest.mark.asyncio
    async def test_get_authorization_url_includes_required_params(self, service):
        """Should generate authorization URL with required parameters."""
        with patch.object(service.client, "get_authorization_url", new_callable=AsyncMock) as mock:
            mock.return_value = (
                "https://github.com/login/oauth/authorize"
                "?client_id=test_client_id"
                "&redirect_uri=http://localhost:8000/api/auth/callback"
                "&scope=read:org+repo+read:user+user:email"
                "&state=test_state"
            )

            url = await service.get_authorization_url(state="test_state")

            assert "github.com" in url
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_authorization_url_includes_scopes(self, service):
        """Authorization URL should include required scopes."""
        # Verify the service has the correct scopes configured
        assert "read:org" in service.SCOPES
        assert "repo" in service.SCOPES
        assert "read:user" in service.SCOPES
        assert "user:email" in service.SCOPES

    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self, service):
        """Should exchange authorization code for access token."""
        mock_token = {"access_token": "gho_test_token", "token_type": "bearer"}

        with patch.object(service.client, "get_access_token", new_callable=AsyncMock) as mock:
            mock.return_value = mock_token

            result = await service.exchange_code_for_token("test_code")

            assert result == mock_token
            mock.assert_called_once_with(
                code="test_code",
                redirect_uri=service.redirect_uri,
            )

    @pytest.mark.asyncio
    async def test_get_user_info(self, service):
        """Should fetch user info from GitHub API."""
        mock_user = {
            "id": 12345,
            "login": "testuser",
            "email": "test@example.com",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345",
        }

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_user
            mock_response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await service.get_user_info("test_access_token")

            assert result == mock_user
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "https://api.github.com/user" in call_args[0]
            assert "Bearer test_access_token" in call_args[1]["headers"]["Authorization"]

    @pytest.mark.asyncio
    async def test_get_user_emails(self, service):
        """Should fetch user emails from GitHub API."""
        mock_emails = [
            {"email": "primary@example.com", "primary": True, "verified": True},
            {"email": "secondary@example.com", "primary": False, "verified": True},
        ]

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_emails
            mock_response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await service.get_user_emails("test_access_token")

            assert result == mock_emails
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "https://api.github.com/user/emails" in call_args[0]
