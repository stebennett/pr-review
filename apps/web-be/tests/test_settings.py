"""Tests for settings endpoints."""

from pr_review_api.config import get_settings
from pr_review_api.main import app
from pr_review_api.models.user import User


class TestGetSettings:
    """Tests for GET /api/settings."""

    def test_requires_authentication(self, client):
        """Should return 401/403 without Authorization header."""
        response = client.get("/api/settings")
        # FastAPI HTTPBearer returns 403 for missing credentials
        assert response.status_code in [401, 403]

    def test_returns_user_email_when_set(self, client, test_user, auth_headers, test_settings):
        """Should return user's email address when it is set."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        response = client.get("/api/settings", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "settings" in data["data"]
        assert data["data"]["settings"]["email"] == "test@example.com"

    def test_returns_null_email_when_not_set(self, client, db_session, auth_headers, test_settings):
        """Should return null email when user has no email set."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Create a user without email
        user_no_email = User(
            id="67890",
            github_username="noemail_user",
            github_access_token="encrypted_token",
            email=None,
            avatar_url=None,
        )
        db_session.add(user_no_email)
        db_session.commit()

        # Create token for this user
        from pr_review_api.services.jwt import create_access_token

        token = create_access_token(user_id=user_no_email.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/settings", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["settings"]["email"] is None


class TestUpdateSettings:
    """Tests for PUT /api/settings."""

    def test_requires_authentication(self, client):
        """Should return 401/403 without Authorization header."""
        response = client.put("/api/settings", json={"email": "new@example.com"})
        # FastAPI HTTPBearer returns 403 for missing credentials
        assert response.status_code in [401, 403]

    def test_updates_email_successfully(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should update user's email address."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"email": "newemail@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["settings"]["email"] == "newemail@example.com"

        # Verify persisted to database
        db_session.refresh(test_user)
        assert test_user.email == "newemail@example.com"

    def test_clears_email_with_null(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should allow clearing email by setting to null."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"email": None},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["settings"]["email"] is None

        # Verify persisted to database
        db_session.refresh(test_user)
        assert test_user.email is None

    def test_rejects_invalid_email_format(self, client, test_user, auth_headers, test_settings):
        """Should return 422 for invalid email format."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"email": "not-a-valid-email"},
        )

        assert response.status_code == 422

    def test_rejects_email_without_domain(self, client, test_user, auth_headers, test_settings):
        """Should return 422 for email without domain."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"email": "user@"},
        )

        assert response.status_code == 422

    def test_rejects_email_without_at_symbol(self, client, test_user, auth_headers, test_settings):
        """Should return 422 for email without @ symbol."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"email": "userexample.com"},
        )

        assert response.status_code == 422

    def test_accepts_valid_email_formats(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should accept various valid email formats."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user@subdomain.example.com",
        ]

        for email in valid_emails:
            response = client.put(
                "/api/settings",
                headers=auth_headers,
                json={"email": email},
            )

            assert response.status_code == 200, f"Failed for email: {email}"
            data = response.json()
            assert data["data"]["settings"]["email"] == email

    def test_persists_changes_to_database(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should persist email changes to the database."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        new_email = "persisted@example.com"
        response = client.put(
            "/api/settings",
            headers=auth_headers,
            json={"email": new_email},
        )

        assert response.status_code == 200

        # Expire cached objects and fetch user fresh from database
        db_session.expire_all()
        db_user = db_session.query(User).filter(User.id == test_user.id).first()
        assert db_user.email == new_email
