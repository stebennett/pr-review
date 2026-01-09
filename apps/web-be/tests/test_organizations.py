"""Tests for organizations endpoint."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
from pr_review_shared import encrypt_token

from pr_review_api.config import get_settings
from pr_review_api.main import app
from pr_review_api.schemas import Organization, RateLimitInfo
from pr_review_api.services.github import GitHubAPIService, get_github_api_service


def create_mock_github_api_service(
    organizations: list[Organization] | None = None,
    rate_limit: RateLimitInfo | None = None,
    error: Exception | None = None,
) -> MagicMock:
    """Create a mock GitHub API service for testing.

    Args:
        organizations: List of organizations to return.
        rate_limit: Rate limit info to return.
        error: Exception to raise instead of returning data.

    Returns:
        Mock GitHubAPIService instance.
    """
    mock_service = MagicMock(spec=GitHubAPIService)

    if error:
        mock_service.get_user_organizations = AsyncMock(side_effect=error)
    else:
        orgs = organizations or []
        rl = rate_limit or RateLimitInfo(
            remaining=4999, reset_at=datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC)
        )
        mock_service.get_user_organizations = AsyncMock(return_value=(orgs, rl))

    return mock_service


class TestListOrganizations:
    """Tests for GET /api/organizations."""

    def test_requires_authentication(self, client):
        """Should return 401/403 without Authorization header."""
        response = client.get("/api/organizations")
        # FastAPI HTTPBearer returns 403 for missing credentials
        assert response.status_code in [401, 403]

    def test_returns_empty_list_when_no_organizations(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return empty list when user has no organizations."""
        # Ensure settings override is set (auth_headers fixture may reset it)
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Update test user with properly encrypted token
        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        mock_service = create_mock_github_api_service(organizations=[])
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get("/api/organizations", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert "organizations" in data["data"]
            assert data["data"]["organizations"] == []
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_returns_organizations_list(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return list of organizations from GitHub API."""
        # Ensure settings override is set
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Update test user with properly encrypted token
        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        orgs = [
            Organization(
                id="12345",
                login="my-org",
                avatar_url="https://avatars.githubusercontent.com/u/12345",
            ),
            Organization(
                id="67890",
                login="another-org",
                avatar_url="https://avatars.githubusercontent.com/u/67890",
            ),
        ]
        mock_service = create_mock_github_api_service(organizations=orgs)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get("/api/organizations", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert "organizations" in data["data"]
            assert len(data["data"]["organizations"]) == 2

            org1 = data["data"]["organizations"][0]
            assert org1["id"] == "12345"
            assert org1["login"] == "my-org"
            assert "avatars.githubusercontent.com" in org1["avatar_url"]

            org2 = data["data"]["organizations"][1]
            assert org2["id"] == "67890"
            assert org2["login"] == "another-org"
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_handles_organization_without_avatar(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should handle organizations with null avatar_url."""
        # Ensure settings override is set
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        orgs = [
            Organization(id="12345", login="no-avatar-org", avatar_url=None),
        ]
        mock_service = create_mock_github_api_service(organizations=orgs)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get("/api/organizations", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            org = data["data"]["organizations"][0]
            assert org["id"] == "12345"
            assert org["login"] == "no-avatar-org"
            assert org["avatar_url"] is None
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
            response = client.get("/api/organizations", headers=auth_headers)

            assert response.status_code == 401
            data = response.json()
            assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()
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
            response = client.get("/api/organizations", headers=auth_headers)

            assert response.status_code == 502
            data = response.json()
            assert "failed" in data["detail"].lower()
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_rejects_invalid_jwt_token(self, client):
        """Should return 401 with invalid JWT token."""
        response = client.get(
            "/api/organizations",
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

        orgs = [
            Organization(
                id="12345",
                login="my-org",
                avatar_url="https://avatars.githubusercontent.com/u/12345",
            ),
        ]
        mock_service = create_mock_github_api_service(organizations=orgs)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get("/api/organizations", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()

            # Verify top-level structure
            assert "data" in data
            assert isinstance(data["data"], dict)

            # Verify organizations structure
            assert "organizations" in data["data"]
            assert isinstance(data["data"]["organizations"], list)

            # Verify organization object structure
            org = data["data"]["organizations"][0]
            assert "id" in org
            assert "login" in org
            assert "avatar_url" in org
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)
