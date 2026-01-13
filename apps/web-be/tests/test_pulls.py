"""Tests for pull requests endpoint."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
from pr_review_shared import encrypt_token

from pr_review_api.config import get_settings
from pr_review_api.main import app
from pr_review_api.schemas import Author, Label, PullRequest, RateLimitInfo
from pr_review_api.services.github import GitHubAPIService, get_github_api_service


def create_mock_github_api_service(
    pull_requests: list[PullRequest] | None = None,
    rate_limit: RateLimitInfo | None = None,
    error: Exception | None = None,
) -> MagicMock:
    """Create a mock GitHub API service for testing.

    Args:
        pull_requests: List of pull requests to return.
        rate_limit: Rate limit info to return.
        error: Exception to raise instead of returning data.

    Returns:
        Mock GitHubAPIService instance.
    """
    mock_service = MagicMock(spec=GitHubAPIService)

    if error:
        mock_service.get_repository_pull_requests = AsyncMock(side_effect=error)
    else:
        prs = pull_requests or []
        rl = rate_limit or RateLimitInfo(
            remaining=4999, reset_at=datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC)
        )
        mock_service.get_repository_pull_requests = AsyncMock(return_value=(prs, rl))

    return mock_service


def create_sample_pull_request(
    number: int = 123,
    title: str = "Add new feature",
    username: str = "octocat",
    checks_status: str = "pass",
) -> PullRequest:
    """Create a sample pull request for testing.

    Args:
        number: PR number.
        title: PR title.
        username: Author username.
        checks_status: Check status ('pass', 'fail', 'pending').

    Returns:
        PullRequest instance.
    """
    return PullRequest(
        number=number,
        title=title,
        author=Author(
            username=username,
            avatar_url=f"https://avatars.githubusercontent.com/u/{number}",
        ),
        labels=[
            Label(name="enhancement", color="84b6eb"),
            Label(name="high-priority", color="ff0000"),
        ],
        checks_status=checks_status,
        html_url=f"https://github.com/my-org/my-repo/pull/{number}",
        created_at=datetime(2024, 1, 10, 8, 0, 0, tzinfo=UTC),
    )


class TestListPullRequests:
    """Tests for GET /api/organizations/{org}/repositories/{repo}/pulls."""

    def test_requires_authentication(self, client):
        """Should return 401/403 without Authorization header."""
        response = client.get("/api/organizations/my-org/repositories/my-repo/pulls")
        # FastAPI HTTPBearer returns 403 for missing credentials
        assert response.status_code in [401, 403]

    def test_returns_empty_list_when_no_pull_requests(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return empty list when repository has no open PRs."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        mock_service = create_mock_github_api_service(pull_requests=[])
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/organizations/my-org/repositories/my-repo/pulls",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert "pulls" in data["data"]
            assert data["data"]["pulls"] == []
            assert "meta" in data
            assert "rate_limit" in data["meta"]
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_returns_pull_requests_list(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return list of pull requests from GitHub API."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        prs = [
            create_sample_pull_request(number=123, title="Add new feature", checks_status="pass"),
            create_sample_pull_request(number=456, title="Fix bug", checks_status="fail"),
        ]
        mock_service = create_mock_github_api_service(pull_requests=prs)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/organizations/my-org/repositories/my-repo/pulls",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert "pulls" in data["data"]
            assert len(data["data"]["pulls"]) == 2

            pr1 = data["data"]["pulls"][0]
            assert pr1["number"] == 123
            assert pr1["title"] == "Add new feature"
            assert pr1["checks_status"] == "pass"

            pr2 = data["data"]["pulls"][1]
            assert pr2["number"] == 456
            assert pr2["title"] == "Fix bug"
            assert pr2["checks_status"] == "fail"
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_returns_rate_limit_info(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return rate limit information in response meta."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        rate_limit = RateLimitInfo(
            remaining=4500, reset_at=datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC)
        )
        mock_service = create_mock_github_api_service(pull_requests=[], rate_limit=rate_limit)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/organizations/my-org/repositories/my-repo/pulls",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "meta" in data
            assert "rate_limit" in data["meta"]
            assert data["meta"]["rate_limit"]["remaining"] == 4500
            assert "reset_at" in data["meta"]["rate_limit"]
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_returns_pull_request_with_checks_status_pass(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return PR with checks_status 'pass' when all checks succeed."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        prs = [create_sample_pull_request(checks_status="pass")]
        mock_service = create_mock_github_api_service(pull_requests=prs)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/organizations/my-org/repositories/my-repo/pulls",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["pulls"][0]["checks_status"] == "pass"
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_returns_pull_request_with_checks_status_fail(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return PR with checks_status 'fail' when any check fails."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        prs = [create_sample_pull_request(checks_status="fail")]
        mock_service = create_mock_github_api_service(pull_requests=prs)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/organizations/my-org/repositories/my-repo/pulls",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["pulls"][0]["checks_status"] == "fail"
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_returns_pull_request_with_checks_status_pending(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return PR with checks_status 'pending' when checks are in progress."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        prs = [create_sample_pull_request(checks_status="pending")]
        mock_service = create_mock_github_api_service(pull_requests=prs)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/organizations/my-org/repositories/my-repo/pulls",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["pulls"][0]["checks_status"] == "pending"
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_handles_github_api_401_error(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return 401 when GitHub token is invalid."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("invalid_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

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
            response = client.get(
                "/api/organizations/my-org/repositories/my-repo/pulls",
                headers=auth_headers,
            )

            assert response.status_code == 401
            data = response.json()
            assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_handles_github_api_404_error(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return 404 when repository is not found."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

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
                "/api/organizations/my-org/repositories/nonexistent-repo/pulls",
                headers=auth_headers,
            )

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
            assert "my-org/nonexistent-repo" in data["detail"]
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_handles_github_api_server_error(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return 502 when GitHub API returns server error."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

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
            response = client.get(
                "/api/organizations/my-org/repositories/my-repo/pulls",
                headers=auth_headers,
            )

            assert response.status_code == 502
            data = response.json()
            assert "failed" in data["detail"].lower()
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_rejects_invalid_jwt_token(self, client):
        """Should return 401 with invalid JWT token."""
        response = client.get(
            "/api/organizations/my-org/repositories/my-repo/pulls",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    def test_response_format_matches_specification(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return response matching API specification format."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        prs = [create_sample_pull_request()]
        mock_service = create_mock_github_api_service(pull_requests=prs)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/organizations/my-org/repositories/my-repo/pulls",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()

            # Verify top-level structure
            assert "data" in data
            assert isinstance(data["data"], dict)
            assert "meta" in data
            assert isinstance(data["meta"], dict)

            # Verify pulls structure
            assert "pulls" in data["data"]
            assert isinstance(data["data"]["pulls"], list)

            # Verify pull request object structure
            pr = data["data"]["pulls"][0]
            assert "number" in pr
            assert "title" in pr
            assert "author" in pr
            assert "username" in pr["author"]
            assert "avatar_url" in pr["author"]
            assert "labels" in pr
            assert "checks_status" in pr
            assert "html_url" in pr
            assert "created_at" in pr

            # Verify labels structure
            assert len(pr["labels"]) > 0
            label = pr["labels"][0]
            assert "name" in label
            assert "color" in label

            # Verify meta structure
            assert "rate_limit" in data["meta"]
            assert "remaining" in data["meta"]["rate_limit"]
            assert "reset_at" in data["meta"]["rate_limit"]
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_returns_pull_requests_with_labels(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return PRs with correctly formatted labels."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        prs = [create_sample_pull_request()]
        mock_service = create_mock_github_api_service(pull_requests=prs)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/organizations/my-org/repositories/my-repo/pulls",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            labels = data["data"]["pulls"][0]["labels"]
            assert len(labels) == 2
            assert labels[0]["name"] == "enhancement"
            assert labels[0]["color"] == "84b6eb"
            assert labels[1]["name"] == "high-priority"
            assert labels[1]["color"] == "ff0000"
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)

    def test_returns_pull_requests_with_author_info(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return PRs with author username and avatar URL."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        encrypted_token = encrypt_token("test_access_token", test_settings.encryption_key)
        test_user.github_access_token = encrypted_token
        db_session.commit()

        prs = [create_sample_pull_request(username="octocat")]
        mock_service = create_mock_github_api_service(pull_requests=prs)
        app.dependency_overrides[get_github_api_service] = lambda: mock_service

        try:
            response = client.get(
                "/api/organizations/my-org/repositories/my-repo/pulls",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            author = data["data"]["pulls"][0]["author"]
            assert author["username"] == "octocat"
            assert "avatar_url" in author
            assert author["avatar_url"] is not None
        finally:
            app.dependency_overrides.pop(get_github_api_service, None)
