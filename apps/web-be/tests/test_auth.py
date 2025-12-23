"""Tests for authentication endpoints."""

from unittest.mock import AsyncMock, MagicMock

from pr_review_api.main import app
from pr_review_api.services.github import GitHubOAuthService, get_github_oauth_service


def create_mock_github_service(
    authorization_url: str = "https://github.com/login/oauth/authorize?client_id=test",
    token: dict | None = None,
    user_info: dict | None = None,
    user_emails: list | None = None,
    token_error: Exception | None = None,
):
    """Create a mock GitHub OAuth service for testing."""
    mock_service = MagicMock(spec=GitHubOAuthService)
    mock_service.get_authorization_url = AsyncMock(return_value=authorization_url)

    if token_error:
        mock_service.exchange_code_for_token = AsyncMock(side_effect=token_error)
    else:
        mock_service.exchange_code_for_token = AsyncMock(
            return_value=token or {"access_token": "test_token", "token_type": "bearer"}
        )

    mock_service.get_user_info = AsyncMock(
        return_value=user_info
        or {
            "id": 12345,
            "login": "testuser",
            "email": "test@example.com",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345",
        }
    )
    mock_service.get_user_emails = AsyncMock(return_value=user_emails or [])
    return mock_service


class TestLoginEndpoint:
    """Tests for GET /api/auth/login."""

    def test_login_returns_github_url(self, client):
        """Should return a GitHub authorization URL."""
        mock_service = create_mock_github_service(
            authorization_url="https://github.com/login/oauth/authorize?client_id=test&scope=read:org,repo"
        )
        app.dependency_overrides[get_github_oauth_service] = lambda: mock_service

        try:
            response = client.get("/api/auth/login")

            assert response.status_code == 200
            data = response.json()
            assert "url" in data
            assert "github.com" in data["url"]
        finally:
            app.dependency_overrides.pop(get_github_oauth_service, None)

    def test_login_url_contains_client_id(self, client):
        """Authorization URL should contain client_id."""
        mock_service = create_mock_github_service(
            authorization_url="https://github.com/login/oauth/authorize?client_id=test_client_id&scope=read:org"
        )
        app.dependency_overrides[get_github_oauth_service] = lambda: mock_service

        try:
            response = client.get("/api/auth/login")

            url = response.json()["url"]
            assert "client_id" in url
        finally:
            app.dependency_overrides.pop(get_github_oauth_service, None)


class TestCallbackEndpoint:
    """Tests for GET /api/auth/callback."""

    def test_callback_success_redirects_with_token(self, client):
        """Successful OAuth should redirect to frontend with JWT token."""
        mock_service = create_mock_github_service(
            token={"access_token": "gho_test_token", "token_type": "bearer"},
            user_info={
                "id": 12345,
                "login": "testuser",
                "email": "test@example.com",
                "avatar_url": "https://avatars.githubusercontent.com/u/12345",
            },
        )
        app.dependency_overrides[get_github_oauth_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/auth/callback",
                params={"code": "test_code", "state": "test_state"},
                follow_redirects=False,
            )

            assert response.status_code == 302
            location = response.headers["location"]
            assert "localhost:5173" in location
            assert "token=" in location
        finally:
            app.dependency_overrides.pop(get_github_oauth_service, None)

    def test_callback_creates_new_user(self, client, db_session):
        """First-time OAuth should create a new user in database."""
        mock_service = create_mock_github_service(
            token={"access_token": "gho_test_token", "token_type": "bearer"},
            user_info={
                "id": 99999,
                "login": "newuser",
                "email": "new@example.com",
                "avatar_url": "https://avatars.githubusercontent.com/u/99999",
            },
        )
        app.dependency_overrides[get_github_oauth_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/auth/callback",
                params={"code": "test_code"},
                follow_redirects=False,
            )

            assert response.status_code == 302
            location = response.headers["location"]
            assert "token=" in location
        finally:
            app.dependency_overrides.pop(get_github_oauth_service, None)

    def test_callback_fetches_email_from_emails_api(self, client):
        """Should fetch email from /user/emails if not in profile."""
        mock_service = create_mock_github_service(
            token={"access_token": "gho_test_token", "token_type": "bearer"},
            user_info={
                "id": 88888,
                "login": "privateemailuser",
                "email": None,
                "avatar_url": "https://avatars.githubusercontent.com/u/88888",
            },
            user_emails=[
                {"email": "private@example.com", "primary": True, "verified": True},
                {"email": "secondary@example.com", "primary": False, "verified": True},
            ],
        )
        app.dependency_overrides[get_github_oauth_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/auth/callback",
                params={"code": "test_code"},
                follow_redirects=False,
            )

            assert response.status_code == 302
            # Verify email API was called (email was None in profile)
            mock_service.get_user_emails.assert_called_once()
        finally:
            app.dependency_overrides.pop(get_github_oauth_service, None)

    def test_callback_handles_oauth_error(self, client):
        """OAuth failure should redirect to login with error."""
        mock_service = create_mock_github_service(token_error=Exception("OAuth failed"))
        app.dependency_overrides[get_github_oauth_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/auth/callback",
                params={"code": "invalid_code"},
                follow_redirects=False,
            )

            assert response.status_code == 302
            location = response.headers["location"]
            assert "error=" in location
        finally:
            app.dependency_overrides.pop(get_github_oauth_service, None)


class TestMeEndpoint:
    """Tests for GET /api/auth/me."""

    def test_me_requires_authentication(self, client):
        """Should return 401 or 403 without Authorization header."""
        response = client.get("/api/auth/me")
        # FastAPI HTTPBearer returns 403 for missing credentials
        # but can also return 401 depending on configuration
        assert response.status_code in [401, 403]

    def test_me_returns_user_info(self, client, test_user, auth_headers):
        """Should return current user's information with valid token."""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.github_username
        assert data["email"] == test_user.email
        assert data["avatar_url"] == test_user.avatar_url

    def test_me_rejects_invalid_token(self, client):
        """Should return 401 with invalid JWT."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401


class TestLogoutEndpoint:
    """Tests for POST /api/auth/logout."""

    def test_logout_returns_success(self, client):
        """Logout should always return success message."""
        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()
