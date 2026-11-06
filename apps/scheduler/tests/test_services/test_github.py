"""Tests for the GitHub API service."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from pr_review_scheduler.services import github


class TestGetRepositoryPullRequests:
    """Tests for get_repository_pull_requests function."""

    @pytest.mark.asyncio
    async def test_get_repository_pull_requests(self):
        """Test successful fetch of pull requests with checks."""
        # Mock PR response from GitHub API
        mock_pr_response = [
            {
                "number": 123,
                "title": "Add new feature",
                "user": {
                    "login": "testuser",
                    "avatar_url": "https://github.com/testuser.png",
                },
                "labels": [
                    {"name": "enhancement"},
                    {"name": "ready-for-review"},
                ],
                "html_url": "https://github.com/myorg/myrepo/pull/123",
                "created_at": "2024-01-15T10:00:00Z",
                "head": {
                    "sha": "abc123def456",
                },
            },
            {
                "number": 124,
                "title": "Fix bug",
                "user": {
                    "login": "otheruser",
                    "avatar_url": "https://github.com/otheruser.png",
                },
                "labels": [],
                "html_url": "https://github.com/myorg/myrepo/pull/124",
                "created_at": "2024-01-16T14:30:00Z",
                "head": {
                    "sha": "def456abc789",
                },
            },
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_pr_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            # Also mock get_pull_request_checks
            with patch.object(
                github, "get_pull_request_checks", new_callable=AsyncMock
            ) as mock_checks:
                mock_checks.side_effect = ["pass", "pending"]

                result = await github.get_repository_pull_requests(
                    access_token="ghp_test_token",
                    organization="myorg",
                    repository="myrepo",
                )

        assert len(result) == 2

        # Verify first PR
        assert result[0]["number"] == 123
        assert result[0]["title"] == "Add new feature"
        assert result[0]["author"] == "testuser"
        assert result[0]["author_avatar_url"] == "https://github.com/testuser.png"
        assert result[0]["labels"] == '["enhancement", "ready-for-review"]'
        assert result[0]["checks_status"] == "pass"
        assert result[0]["html_url"] == "https://github.com/myorg/myrepo/pull/123"
        assert result[0]["created_at"] == "2024-01-15T10:00:00Z"
        assert result[0]["organization"] == "myorg"
        assert result[0]["repository"] == "myrepo"

        # Verify second PR
        assert result[1]["number"] == 124
        assert result[1]["title"] == "Fix bug"
        assert result[1]["author"] == "otheruser"
        assert result[1]["labels"] == "[]"
        assert result[1]["checks_status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_repository_pull_requests_empty(self):
        """Test fetch returns empty list when no PRs exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await github.get_repository_pull_requests(
                access_token="ghp_test_token",
                organization="myorg",
                repository="myrepo",
            )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_repository_pull_requests_handles_error(self):
        """Test fetch returns empty list on HTTP error."""
        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )

            result = await github.get_repository_pull_requests(
                access_token="ghp_test_token",
                organization="nonexistent",
                repository="repo",
            )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_repository_pull_requests_handles_connection_error(self):
        """Test fetch returns empty list on connection error."""
        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")

            result = await github.get_repository_pull_requests(
                access_token="ghp_test_token",
                organization="myorg",
                repository="myrepo",
            )

        assert result == []


class TestGetPullRequestChecks:
    """Tests for get_pull_request_checks function."""

    @pytest.mark.asyncio
    async def test_get_pull_request_checks_pass(self):
        """Test checks return 'pass' when all checks succeed."""
        mock_check_runs_response = {
            "total_count": 3,
            "check_runs": [
                {"conclusion": "success", "status": "completed"},
                {"conclusion": "success", "status": "completed"},
                {"conclusion": "success", "status": "completed"},
            ],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_check_runs_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await github.get_pull_request_checks(
                access_token="ghp_test_token",
                organization="myorg",
                repository="myrepo",
                sha="abc123def456",
            )

        assert result == "pass"

    @pytest.mark.asyncio
    async def test_get_pull_request_checks_fail(self):
        """Test checks return 'fail' when any check fails."""
        mock_check_runs_response = {
            "total_count": 3,
            "check_runs": [
                {"conclusion": "success", "status": "completed"},
                {"conclusion": "failure", "status": "completed"},
                {"conclusion": "success", "status": "completed"},
            ],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_check_runs_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await github.get_pull_request_checks(
                access_token="ghp_test_token",
                organization="myorg",
                repository="myrepo",
                sha="abc123def456",
            )

        assert result == "fail"

    @pytest.mark.asyncio
    async def test_get_pull_request_checks_pending(self):
        """Test checks return 'pending' when any check is in progress."""
        mock_check_runs_response = {
            "total_count": 3,
            "check_runs": [
                {"conclusion": "success", "status": "completed"},
                {"conclusion": None, "status": "in_progress"},
                {"conclusion": "success", "status": "completed"},
            ],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_check_runs_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await github.get_pull_request_checks(
                access_token="ghp_test_token",
                organization="myorg",
                repository="myrepo",
                sha="abc123def456",
            )

        assert result == "pending"

    @pytest.mark.asyncio
    async def test_get_pull_request_checks_no_checks(self):
        """Test checks return 'pass' when no checks exist."""
        mock_check_runs_response = {
            "total_count": 0,
            "check_runs": [],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_check_runs_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await github.get_pull_request_checks(
                access_token="ghp_test_token",
                organization="myorg",
                repository="myrepo",
                sha="abc123def456",
            )

        assert result == "pass"

    @pytest.mark.asyncio
    async def test_get_pull_request_checks_handles_error(self):
        """Test checks return 'pending' on error."""
        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "Server Error",
                request=MagicMock(),
                response=MagicMock(status_code=500),
            )

            result = await github.get_pull_request_checks(
                access_token="ghp_test_token",
                organization="myorg",
                repository="myrepo",
                sha="abc123def456",
            )

        assert result == "pending"

    @pytest.mark.asyncio
    async def test_get_pull_request_checks_fail_takes_priority_over_pending(self):
        """Test checks return 'fail' even when some are pending if any failed."""
        mock_check_runs_response = {
            "total_count": 3,
            "check_runs": [
                {"conclusion": "failure", "status": "completed"},
                {"conclusion": None, "status": "in_progress"},
                {"conclusion": "success", "status": "completed"},
            ],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_check_runs_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await github.get_pull_request_checks(
                access_token="ghp_test_token",
                organization="myorg",
                repository="myrepo",
                sha="abc123def456",
            )

        assert result == "fail"
