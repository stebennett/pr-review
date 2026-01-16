"""Tests for GitHub OAuth and API services."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from pr_review_api.services.github import GitHubAPIService


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


class TestGitHubAPIService:
    """Tests for GitHubAPIService."""

    @pytest.fixture
    def service(self):
        """Create a GitHubAPIService instance."""
        return GitHubAPIService()

    @pytest.fixture
    def mock_rate_limit_headers(self):
        """Create mock rate limit headers."""
        return {
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Reset": "1704110400",  # 2024-01-01 12:00:00 UTC
        }

    def _create_mock_response(self, json_data, headers=None):
        """Helper to create a mock HTTP response."""
        mock_response = MagicMock()
        mock_response.json.return_value = json_data
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = headers or {
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Reset": "1704110400",
        }
        return mock_response

    def _create_mock_client(self, response):
        """Helper to create a mock async HTTP client."""
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        return mock_client

    # Tests for get_user_organizations

    @pytest.mark.asyncio
    async def test_get_user_organizations_success(self, service):
        """Should fetch and parse user organizations plus personal account."""
        mock_user = {
            "id": 999,
            "login": "testuser",
            "avatar_url": "https://example.com/user-avatar.png",
        }
        mock_orgs = [
            {"id": 123, "login": "my-org", "avatar_url": "https://example.com/avatar1.png"},
            {"id": 456, "login": "other-org", "avatar_url": "https://example.com/avatar2.png"},
        ]

        mock_user_response = self._create_mock_response(mock_user)
        mock_orgs_response = self._create_mock_response(mock_orgs)

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=[mock_user_response, mock_orgs_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            orgs, rate_limit = await service.get_user_organizations("test_token")

            # Should include personal account first, then organizations
            assert len(orgs) == 3
            assert orgs[0].id == "999"
            assert orgs[0].login == "testuser"
            assert orgs[0].avatar_url == "https://example.com/user-avatar.png"
            assert orgs[1].id == "123"
            assert orgs[1].login == "my-org"
            assert orgs[2].id == "456"
            assert orgs[2].login == "other-org"
            assert rate_limit.remaining == 4999

    @pytest.mark.asyncio
    async def test_get_user_organizations_empty(self, service):
        """Should return personal account when user has no organizations."""
        mock_user = {
            "id": 999,
            "login": "testuser",
            "avatar_url": "https://example.com/user-avatar.png",
        }

        mock_user_response = self._create_mock_response(mock_user)
        mock_orgs_response = self._create_mock_response([])

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=[mock_user_response, mock_orgs_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            orgs, rate_limit = await service.get_user_organizations("test_token")

            # Should still include personal account
            assert len(orgs) == 1
            assert orgs[0].id == "999"
            assert orgs[0].login == "testuser"
            assert rate_limit.remaining == 4999

    @pytest.mark.asyncio
    async def test_get_user_organizations_auth_error(self, service):
        """Should raise on authentication failure."""

        async def mock_get(*args, **kwargs):
            response = MagicMock()
            response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Unauthorized", request=MagicMock(), response=MagicMock(status_code=401)
            )
            return response

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)  # Don't suppress exceptions
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await service.get_user_organizations("invalid_token")

    # Tests for get_organization_repositories

    @pytest.mark.asyncio
    async def test_get_organization_repositories_success(self, service):
        """Should fetch and parse organization repositories."""
        mock_repos = [
            {"id": 789, "name": "repo-1", "full_name": "my-org/repo-1"},
            {"id": 101112, "name": "repo-2", "full_name": "my-org/repo-2"},
        ]

        mock_response = self._create_mock_response(mock_repos)

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = self._create_mock_client(mock_response)
            mock_client_class.return_value = mock_client

            repos, rate_limit = await service.get_organization_repositories("test_token", "my-org")

            assert len(repos) == 2
            assert repos[0].id == "789"
            assert repos[0].name == "repo-1"
            assert repos[0].full_name == "my-org/repo-1"
            assert rate_limit.remaining == 4999

            # Verify correct URL was called
            call_args = mock_client.get.call_args
            assert "my-org" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_organization_repositories_with_pagination_params(self, service):
        """Should include pagination and sort parameters."""
        mock_response = self._create_mock_response([])

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = self._create_mock_client(mock_response)
            mock_client_class.return_value = mock_client

            await service.get_organization_repositories("test_token", "my-org")

            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["per_page"] == 100
            assert call_args[1]["params"]["sort"] == "updated"

    @pytest.mark.asyncio
    async def test_get_organization_repositories_fallback_to_user_endpoint(self, service):
        """Should fallback to user repos endpoint when org endpoint returns 404."""
        mock_repos = [
            {"id": 789, "name": "personal-repo", "full_name": "testuser/personal-repo"},
        ]

        # First response: 404 for org endpoint
        mock_404_response = MagicMock()
        mock_404_response.status_code = 404

        # Second response: success for user endpoint
        mock_repos_response = self._create_mock_response(mock_repos)
        mock_repos_response.status_code = 200

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=[mock_404_response, mock_repos_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            repos, rate_limit = await service.get_organization_repositories(
                "test_token", "testuser"
            )

            assert len(repos) == 1
            assert repos[0].name == "personal-repo"
            assert repos[0].full_name == "testuser/personal-repo"

            # Verify both endpoints were called
            assert mock_client.get.call_count == 2

    # Tests for get_repository_pull_requests

    @pytest.mark.asyncio
    async def test_get_repository_pull_requests_success(self, service):
        """Should fetch and parse pull requests with check status."""
        mock_prs = [
            {
                "number": 123,
                "title": "Add feature",
                "user": {"login": "octocat", "avatar_url": "https://example.com/avatar.png"},
                "labels": [{"name": "enhancement", "color": "84b6eb"}],
                "html_url": "https://github.com/my-org/repo/pull/123",
                "created_at": "2024-01-10T08:00:00Z",
                "head": {"sha": "abc123"},
            }
        ]

        mock_check_runs = {"check_runs": [{"status": "completed", "conclusion": "success"}]}

        mock_prs_response = self._create_mock_response(mock_prs)
        mock_checks_response = self._create_mock_response(mock_check_runs)

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=[mock_prs_response, mock_checks_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            prs, rate_limit = await service.get_repository_pull_requests(
                "test_token", "my-org", "repo"
            )

            assert len(prs) == 1
            assert prs[0].number == 123
            assert prs[0].title == "Add feature"
            assert prs[0].author.username == "octocat"
            assert len(prs[0].labels) == 1
            assert prs[0].labels[0].name == "enhancement"
            assert prs[0].checks_status == "pass"

    @pytest.mark.asyncio
    async def test_get_repository_pull_requests_with_failed_checks(self, service):
        """Should return 'fail' status when checks fail."""
        mock_prs = [
            {
                "number": 123,
                "title": "Add feature",
                "user": {"login": "octocat", "avatar_url": None},
                "labels": [],
                "html_url": "https://github.com/my-org/repo/pull/123",
                "created_at": "2024-01-10T08:00:00Z",
                "head": {"sha": "abc123"},
            }
        ]

        mock_check_runs = {
            "check_runs": [
                {"status": "completed", "conclusion": "success"},
                {"status": "completed", "conclusion": "failure"},
            ]
        }

        mock_prs_response = self._create_mock_response(mock_prs)
        mock_checks_response = self._create_mock_response(mock_check_runs)

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=[mock_prs_response, mock_checks_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            prs, _ = await service.get_repository_pull_requests("test_token", "my-org", "repo")

            assert prs[0].checks_status == "fail"

    @pytest.mark.asyncio
    async def test_get_repository_pull_requests_with_pending_checks(self, service):
        """Should return 'pending' status when checks are in progress."""
        mock_prs = [
            {
                "number": 123,
                "title": "Add feature",
                "user": {"login": "octocat", "avatar_url": None},
                "labels": [],
                "html_url": "https://github.com/my-org/repo/pull/123",
                "created_at": "2024-01-10T08:00:00Z",
                "head": {"sha": "abc123"},
            }
        ]

        mock_check_runs = {
            "check_runs": [
                {"status": "completed", "conclusion": "success"},
                {"status": "in_progress", "conclusion": None},
            ]
        }

        mock_prs_response = self._create_mock_response(mock_prs)
        mock_checks_response = self._create_mock_response(mock_check_runs)

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=[mock_prs_response, mock_checks_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            prs, _ = await service.get_repository_pull_requests("test_token", "my-org", "repo")

            assert prs[0].checks_status == "pending"

    @pytest.mark.asyncio
    async def test_get_repository_pull_requests_no_checks(self, service):
        """Should return 'pending' status when no checks exist."""
        mock_prs = [
            {
                "number": 123,
                "title": "Add feature",
                "user": {"login": "octocat", "avatar_url": None},
                "labels": [],
                "html_url": "https://github.com/my-org/repo/pull/123",
                "created_at": "2024-01-10T08:00:00Z",
                "head": {"sha": "abc123"},
            }
        ]

        mock_check_runs = {"check_runs": []}

        mock_prs_response = self._create_mock_response(mock_prs)
        mock_checks_response = self._create_mock_response(mock_check_runs)

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=[mock_prs_response, mock_checks_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            prs, _ = await service.get_repository_pull_requests("test_token", "my-org", "repo")

            assert prs[0].checks_status == "pending"

    @pytest.mark.asyncio
    async def test_get_repository_pull_requests_checks_api_error(self, service):
        """Should return 'pending' when check API fails."""
        mock_prs = [
            {
                "number": 123,
                "title": "Add feature",
                "user": {"login": "octocat", "avatar_url": None},
                "labels": [],
                "html_url": "https://github.com/my-org/repo/pull/123",
                "created_at": "2024-01-10T08:00:00Z",
                "head": {"sha": "abc123"},
            }
        ]

        mock_prs_response = self._create_mock_response(mock_prs)

        mock_checks_response = MagicMock()
        mock_checks_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=MagicMock(status_code=404)
        )

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=[mock_prs_response, mock_checks_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            prs, _ = await service.get_repository_pull_requests("test_token", "my-org", "repo")

            # Should still return PRs, with pending status due to check failure
            assert len(prs) == 1
            assert prs[0].checks_status == "pending"

    # Tests for get_pull_request_checks

    @pytest.mark.asyncio
    async def test_get_pull_request_checks_pass(self, service):
        """Should return 'pass' when all checks succeed."""
        mock_pr = {"head": {"sha": "abc123"}}
        mock_check_runs = {
            "check_runs": [
                {"status": "completed", "conclusion": "success"},
                {"status": "completed", "conclusion": "success"},
            ]
        }

        mock_pr_response = self._create_mock_response(mock_pr)
        mock_checks_response = self._create_mock_response(mock_check_runs)

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=[mock_pr_response, mock_checks_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            status, rate_limit = await service.get_pull_request_checks(
                "test_token", "my-org", "repo", 123
            )

            assert status == "pass"
            assert rate_limit.remaining == 4999

    @pytest.mark.asyncio
    async def test_get_pull_request_checks_fail(self, service):
        """Should return 'fail' when any check fails."""
        mock_pr = {"head": {"sha": "abc123"}}
        mock_check_runs = {
            "check_runs": [
                {"status": "completed", "conclusion": "success"},
                {"status": "completed", "conclusion": "cancelled"},
            ]
        }

        mock_pr_response = self._create_mock_response(mock_pr)
        mock_checks_response = self._create_mock_response(mock_check_runs)

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=[mock_pr_response, mock_checks_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            status, _ = await service.get_pull_request_checks("test_token", "my-org", "repo", 123)

            assert status == "fail"

    @pytest.mark.asyncio
    async def test_get_pull_request_checks_timed_out(self, service):
        """Should return 'fail' when check times out."""
        mock_pr = {"head": {"sha": "abc123"}}
        mock_check_runs = {"check_runs": [{"status": "completed", "conclusion": "timed_out"}]}

        mock_pr_response = self._create_mock_response(mock_pr)
        mock_checks_response = self._create_mock_response(mock_check_runs)

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=[mock_pr_response, mock_checks_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            status, _ = await service.get_pull_request_checks("test_token", "my-org", "repo", 123)

            assert status == "fail"

    # Tests for rate limit parsing

    def test_parse_rate_limit(self, service):
        """Should correctly parse rate limit headers."""
        mock_response = MagicMock()
        mock_response.headers = {
            "X-RateLimit-Remaining": "4500",
            "X-RateLimit-Reset": "1704110400",
        }

        rate_limit = service._parse_rate_limit(mock_response)

        assert rate_limit.remaining == 4500
        assert rate_limit.reset_at == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    def test_parse_rate_limit_missing_headers(self, service):
        """Should handle missing rate limit headers."""
        mock_response = MagicMock()
        mock_response.headers = {}

        rate_limit = service._parse_rate_limit(mock_response)

        assert rate_limit.remaining == 0
        assert rate_limit.reset_at == datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC)

    # Tests for request headers

    def test_get_headers_includes_authorization(self, service):
        """Should include Bearer token in Authorization header."""
        headers = service._get_headers("my_token")

        assert headers["Authorization"] == "Bearer my_token"
        assert headers["Accept"] == "application/vnd.github+json"
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"

    # Tests for PAT validation

    @pytest.mark.asyncio
    async def test_validate_pat_valid_token_with_scopes(self, service):
        """Should validate a valid PAT with required scopes."""
        mock_user = {"id": 12345, "login": "testuser"}

        mock_response = MagicMock()
        mock_response.json.return_value = mock_user
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"X-OAuth-Scopes": "read:org, repo, read:user"}

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await service.validate_pat("ghp_valid_token")

            assert result.is_valid is True
            assert result.username == "testuser"
            assert "read:org" in result.scopes
            assert "repo" in result.scopes
            assert result.missing_scopes == []
            assert result.error_message is None

    @pytest.mark.asyncio
    async def test_validate_pat_missing_scopes(self, service):
        """Should detect missing required scopes."""
        mock_user = {"id": 12345, "login": "testuser"}

        mock_response = MagicMock()
        mock_response.json.return_value = mock_user
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"X-OAuth-Scopes": "read:user"}  # Missing read:org and repo

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await service.validate_pat("ghp_limited_token")

            assert result.is_valid is True
            assert result.username == "testuser"
            assert "read:org" in result.missing_scopes
            assert "repo" in result.missing_scopes

    @pytest.mark.asyncio
    async def test_validate_pat_fine_grained_token(self, service):
        """Should handle fine-grained PAT without scopes header."""
        mock_user = {"id": 12345, "login": "testuser"}

        mock_response = MagicMock()
        mock_response.json.return_value = mock_user
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {}  # Fine-grained PATs don't have X-OAuth-Scopes

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await service.validate_pat("github_pat_fine_grained")

            assert result.is_valid is True
            assert result.username == "testuser"
            assert result.scopes == []
            assert result.missing_scopes == []  # Can't check scopes for fine-grained PATs

    @pytest.mark.asyncio
    async def test_validate_pat_invalid_token(self, service):
        """Should return invalid result for unauthorized token."""

        async def mock_get(*args, **kwargs):
            response = MagicMock()
            response.status_code = 401
            response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Unauthorized", request=MagicMock(), response=response
            )
            return response

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = await service.validate_pat("invalid_token")

            assert result.is_valid is False
            assert result.username is None
            assert "Invalid or expired" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_pat_api_error(self, service):
        """Should handle GitHub API errors."""

        async def mock_get(*args, **kwargs):
            response = MagicMock()
            response.status_code = 500
            response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server Error", request=MagicMock(), response=response
            )
            return response

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = await service.validate_pat("some_token")

            assert result.is_valid is False
            assert "500" in result.error_message

    # Tests for repository access validation

    @pytest.mark.asyncio
    async def test_validate_repository_access_all_accessible(self, service):
        """Should return all repos as accessible when access is granted."""
        from pr_review_api.schemas import RepositoryRef

        repos = [
            RepositoryRef(organization="my-org", repository="repo-1"),
            RepositoryRef(organization="my-org", repository="repo-2"),
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await service.validate_repository_access("valid_token", repos)

            assert len(result.accessible) == 2
            assert len(result.inaccessible) == 0

    @pytest.mark.asyncio
    async def test_validate_repository_access_some_inaccessible(self, service):
        """Should correctly identify inaccessible repos."""
        from pr_review_api.schemas import RepositoryRef

        repos = [
            RepositoryRef(organization="my-org", repository="repo-1"),
            RepositoryRef(organization="my-org", repository="private-repo"),
        ]

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200

        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=[mock_response_200, mock_response_404])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await service.validate_repository_access("valid_token", repos)

            assert len(result.accessible) == 1
            assert result.accessible[0].repository == "repo-1"
            assert len(result.inaccessible) == 1
            assert result.inaccessible[0].repository == "private-repo"
            assert "not found" in result.inaccessible[0].reason.lower()

    @pytest.mark.asyncio
    async def test_validate_repository_access_forbidden(self, service):
        """Should handle 403 forbidden response."""
        from pr_review_api.schemas import RepositoryRef

        repos = [RepositoryRef(organization="my-org", repository="repo-1")]

        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await service.validate_repository_access("valid_token", repos)

            assert len(result.accessible) == 0
            assert len(result.inaccessible) == 1
            assert "forbidden" in result.inaccessible[0].reason.lower()

    @pytest.mark.asyncio
    async def test_validate_repository_access_connection_error(self, service):
        """Should handle connection errors gracefully."""
        from pr_review_api.schemas import RepositoryRef

        repos = [RepositoryRef(organization="my-org", repository="repo-1")]

        with patch("pr_review_api.services.github.httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await service.validate_repository_access("valid_token", repos)

            assert len(result.accessible) == 0
            assert len(result.inaccessible) == 1
            assert "connection" in result.inaccessible[0].reason.lower()
