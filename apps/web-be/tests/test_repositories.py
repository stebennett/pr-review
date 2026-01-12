"""Tests for repositories endpoint."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
from pr_review_shared import encrypt_token

from pr_review_api.config import get_settings
from pr_review_api.main import app
from pr_review_api.schemas import RateLimitInfo, Repository
from pr_review_api.services.github import GitHubAPIService, get_github_api_service


def create_mock_github_api_service(
    repositories: list[Repository] | None = None,
    rate_limit: RateLimitInfo | None = None,
    error: Exception | None = None,
) -> MagicMock:
    """Create a mock GitHub API service for testing.

    Args:
        repositories: List of repositories to return.
        rate_limit: Rate limit info to return.
        error: Exception to raise instead of returning data.

    Returns:
        Mock GitHubAPIService instance.
    """
    mock_service = MagicMock(spec=GitHubAPIService)

    if error:
        mock_service.get_organization_repositories = AsyncMock(side_effect=error)
    else:
        repos = repositories or []
        rl = rate_limit or RateLimitInfo(
            remaining=4999, reset_at=datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC)
        )
        mock_service.get_organization_repositories = AsyncMock(return_value=(repos, rl))

    return mock_service


class TestListRepositories:
    """Tests for GET /api/organizations/{org}/repositories."""

    def test_requires_authentication(self, client):
        """Should return 401/403 without Authorization header."""
        response = client.get("/api/organizations/my-org/repositories")
        # FastAPI HTTPBearer returns 403 for missing credentials
        assert response.status_code in [401, 403]

    def test_returns_empty_list_when_no_repositories(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return empty list when organization has no repositories."""
        # Ensure settings override is set
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Update test user with properly encrypted token
        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        mock_service = create_mock_github_api_service(repositories=[])
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get("/api/organizations/my-org/repositories", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert "repositories" in data["data"]
            assert data["data"]["repositories"] == []
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_returns_repositories_list(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return list of repositories from GitHub API."""
        # Ensure settings override is set
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Update test user with properly encrypted token
        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        repos = [
            Repository(
                id="67890",
                name="my-repo",
                full_name="my-org/my-repo",
            ),
            Repository(
                id="11111",
                name="another-repo",
                full_name="my-org/another-repo",
            ),
        ]
        mock_service = create_mock_github_api_service(repositories=repos)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get("/api/organizations/my-org/repositories", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert "repositories" in data["data"]
            assert len(data["data"]["repositories"]) == 2

            repo1 = data["data"]["repositories"][0]
            assert repo1["id"] == "67890"
            assert repo1["name"] == "my-repo"
            assert repo1["full_name"] == "my-org/my-repo"

            repo2 = data["data"]["repositories"][1]
            assert repo2["id"] == "11111"
            assert repo2["name"] == "another-repo"
            assert repo2["full_name"] == "my-org/another-repo"
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_handles_github_api_401_error(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return 401 when GitHub token is invalid."""
        # Ensure settings override is set
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("invalid_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        # Create a mock HTTP 401 response
        mock_response = MagicMock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )
        mock_service = create_mock_github_api_service(error=error)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get("/api/organizations/my-org/repositories", headers=auth_headers)

            assert response.status_code == 401
            data = response.json()
            assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_handles_github_api_404_error(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return 404 when organization is not found."""
        # Ensure settings override is set
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        # Create a mock HTTP 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=mock_response,
        )
        mock_service = create_mock_github_api_service(error=error)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/organizations/nonexistent-org/repositories", headers=auth_headers
            )

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
            assert "nonexistent-org" in data["detail"]
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_handles_github_api_server_error(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return 502 when GitHub API returns server error."""
        # Ensure settings override is set
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        # Create a mock HTTP 500 response
        mock_response = MagicMock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=mock_response,
        )
        mock_service = create_mock_github_api_service(error=error)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get("/api/organizations/my-org/repositories", headers=auth_headers)

            assert response.status_code == 502
            data = response.json()
            assert "failed" in data["detail"].lower()
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_rejects_invalid_jwt_token(self, client):
        """Should return 401 with invalid JWT token."""
        response = client.get(
            "/api/organizations/my-org/repositories",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    def test_response_format_matches_specification(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return response matching API specification format."""
        # Ensure settings override is set
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        repos = [
            Repository(
                id="67890",
                name="my-repo",
                full_name="my-org/my-repo",
            ),
        ]
        mock_service = create_mock_github_api_service(repositories=repos)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get("/api/organizations/my-org/repositories", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()

            # Verify top-level structure
            assert "data" in data
            assert isinstance(data["data"], dict)

            # Verify repositories structure
            assert "repositories" in data["data"]
            assert isinstance(data["data"]["repositories"], list)

            # Verify repository object structure
            repo = data["data"]["repositories"][0]
            assert "id" in repo
            assert "name" in repo
            assert "full_name" in repo
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)
