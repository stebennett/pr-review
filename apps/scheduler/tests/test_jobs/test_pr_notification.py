"""Tests for the PR notification job."""

from unittest.mock import AsyncMock, MagicMock, patch

from pr_review_scheduler.jobs import pr_notification


class TestRunNotificationJob:
    """Tests for run_notification_job function."""

    def test_run_notification_job_with_prs(self):
        """Test job sends email when PRs are found."""
        # Mock schedule data
        mock_schedule = {
            "id": "schedule-123",
            "user_id": "user-456",
            "user_email": "user@example.com",
            "name": "Daily PR Review",
            "cron_expression": "0 9 * * 1-5",
            "github_pat": "ghp_test_token",
            "is_active": True,
            "repositories": [
                {"organization": "myorg", "repository": "frontend"},
                {"organization": "myorg", "repository": "backend"},
            ],
        }

        # Mock PR data
        mock_prs_frontend = [
            {
                "number": 1,
                "title": "Feature A",
                "author": "dev1",
                "author_avatar_url": "https://github.com/dev1.png",
                "labels": "[]",
                "checks_status": "pass",
                "html_url": "https://github.com/myorg/frontend/pull/1",
                "created_at": "2024-01-15T10:00:00Z",
                "organization": "myorg",
                "repository": "frontend",
            },
            {
                "number": 2,
                "title": "Feature B",
                "author": "dev2",
                "author_avatar_url": "https://github.com/dev2.png",
                "labels": "[]",
                "checks_status": "pending",
                "html_url": "https://github.com/myorg/frontend/pull/2",
                "created_at": "2024-01-16T10:00:00Z",
                "organization": "myorg",
                "repository": "frontend",
            },
        ]
        mock_prs_backend = [
            {
                "number": 10,
                "title": "Bug fix",
                "author": "dev3",
                "author_avatar_url": "https://github.com/dev3.png",
                "labels": '["bug"]',
                "checks_status": "fail",
                "html_url": "https://github.com/myorg/backend/pull/10",
                "created_at": "2024-01-17T10:00:00Z",
                "organization": "myorg",
                "repository": "backend",
            },
        ]

        mock_settings = MagicMock()
        mock_settings.application_url = "http://localhost:5173"

        with patch(
            "pr_review_scheduler.jobs.pr_notification.get_schedule_by_id",
            return_value=mock_schedule,
        ) as mock_get_schedule, patch(
            "pr_review_scheduler.jobs.pr_notification.get_repository_pull_requests",
            new_callable=AsyncMock,
        ) as mock_get_prs, patch(
            "pr_review_scheduler.jobs.pr_notification.cache_pull_requests",
        ) as mock_cache, patch(
            "pr_review_scheduler.jobs.pr_notification.send_notification_email",
            return_value=True,
        ) as mock_send_email, patch(
            "pr_review_scheduler.jobs.pr_notification.format_pr_summary_email",
            return_value=("Subject", "Body"),
        ) as mock_format, patch(
            "pr_review_scheduler.jobs.pr_notification.get_settings",
            return_value=mock_settings,
        ):
            # Setup mock to return different PRs for different repos
            mock_get_prs.side_effect = [mock_prs_frontend, mock_prs_backend]

            pr_notification.run_notification_job("schedule-123")

            # Verify schedule was looked up
            mock_get_schedule.assert_called_once_with("schedule-123")

            # Verify PRs were fetched for each repository
            assert mock_get_prs.call_count == 2

            # Verify PRs were cached
            mock_cache.assert_called_once()
            cache_call_args = mock_cache.call_args
            assert cache_call_args[0][0] == "schedule-123"
            assert len(cache_call_args[0][1]) == 3  # 2 frontend + 1 backend PRs

            # Verify email was formatted and sent
            mock_format.assert_called_once()
            format_call_args = mock_format.call_args
            assert format_call_args[0][0] == {
                "myorg/frontend": 2,
                "myorg/backend": 1,
            }

            mock_send_email.assert_called_once_with(
                "user@example.com", "Subject", "Body"
            )

    def test_run_notification_job_no_prs(self):
        """Test job skips email when no PRs are found."""
        mock_schedule = {
            "id": "schedule-123",
            "user_id": "user-456",
            "user_email": "user@example.com",
            "name": "Daily PR Review",
            "cron_expression": "0 9 * * 1-5",
            "github_pat": "ghp_test_token",
            "is_active": True,
            "repositories": [
                {"organization": "myorg", "repository": "frontend"},
            ],
        }

        with patch(
            "pr_review_scheduler.jobs.pr_notification.get_schedule_by_id",
            return_value=mock_schedule,
        ), patch(
            "pr_review_scheduler.jobs.pr_notification.get_repository_pull_requests",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            "pr_review_scheduler.jobs.pr_notification.cache_pull_requests",
        ) as mock_cache, patch(
            "pr_review_scheduler.jobs.pr_notification.send_notification_email",
        ) as mock_send_email:
            pr_notification.run_notification_job("schedule-123")

            # Verify cache was NOT called (no PRs to cache)
            mock_cache.assert_not_called()

            # Verify email was NOT sent
            mock_send_email.assert_not_called()

    def test_run_notification_job_schedule_not_found(self):
        """Test job handles missing schedule gracefully."""
        with patch(
            "pr_review_scheduler.jobs.pr_notification.get_schedule_by_id",
            return_value=None,
        ) as mock_get_schedule, patch(
            "pr_review_scheduler.jobs.pr_notification.get_repository_pull_requests",
            new_callable=AsyncMock,
        ) as mock_get_prs, patch(
            "pr_review_scheduler.jobs.pr_notification.send_notification_email",
        ) as mock_send_email:
            pr_notification.run_notification_job("non-existent-schedule")

            # Verify schedule lookup was attempted
            mock_get_schedule.assert_called_once_with("non-existent-schedule")

            # Verify no PRs were fetched or emails sent
            mock_get_prs.assert_not_called()
            mock_send_email.assert_not_called()

    def test_run_notification_job_no_email(self):
        """Test job logs warning when user has no email configured."""
        mock_schedule = {
            "id": "schedule-123",
            "user_id": "user-456",
            "user_email": None,  # No email configured
            "name": "Daily PR Review",
            "cron_expression": "0 9 * * 1-5",
            "github_pat": "ghp_test_token",
            "is_active": True,
            "repositories": [
                {"organization": "myorg", "repository": "frontend"},
            ],
        }

        mock_prs = [
            {
                "number": 1,
                "title": "Feature A",
                "author": "dev1",
                "author_avatar_url": "https://github.com/dev1.png",
                "labels": "[]",
                "checks_status": "pass",
                "html_url": "https://github.com/myorg/frontend/pull/1",
                "created_at": "2024-01-15T10:00:00Z",
                "organization": "myorg",
                "repository": "frontend",
            },
        ]

        mock_settings = MagicMock()
        mock_settings.application_url = "http://localhost:5173"

        with patch(
            "pr_review_scheduler.jobs.pr_notification.get_schedule_by_id",
            return_value=mock_schedule,
        ), patch(
            "pr_review_scheduler.jobs.pr_notification.get_repository_pull_requests",
            new_callable=AsyncMock,
            return_value=mock_prs,
        ), patch(
            "pr_review_scheduler.jobs.pr_notification.cache_pull_requests",
        ) as mock_cache, patch(
            "pr_review_scheduler.jobs.pr_notification.send_notification_email",
        ) as mock_send_email, patch(
            "pr_review_scheduler.jobs.pr_notification.get_settings",
            return_value=mock_settings,
        ):
            pr_notification.run_notification_job("schedule-123")

            # PRs should still be cached even without email
            mock_cache.assert_called_once()

            # Email should NOT be sent (no email address)
            mock_send_email.assert_not_called()

    def test_run_notification_job_empty_email(self):
        """Test job logs warning when user has empty email string."""
        mock_schedule = {
            "id": "schedule-123",
            "user_id": "user-456",
            "user_email": "",  # Empty email string
            "name": "Daily PR Review",
            "cron_expression": "0 9 * * 1-5",
            "github_pat": "ghp_test_token",
            "is_active": True,
            "repositories": [
                {"organization": "myorg", "repository": "frontend"},
            ],
        }

        mock_prs = [
            {
                "number": 1,
                "title": "Feature A",
                "author": "dev1",
                "author_avatar_url": "https://github.com/dev1.png",
                "labels": "[]",
                "checks_status": "pass",
                "html_url": "https://github.com/myorg/frontend/pull/1",
                "created_at": "2024-01-15T10:00:00Z",
                "organization": "myorg",
                "repository": "frontend",
            },
        ]

        mock_settings = MagicMock()
        mock_settings.application_url = "http://localhost:5173"

        with patch(
            "pr_review_scheduler.jobs.pr_notification.get_schedule_by_id",
            return_value=mock_schedule,
        ), patch(
            "pr_review_scheduler.jobs.pr_notification.get_repository_pull_requests",
            new_callable=AsyncMock,
            return_value=mock_prs,
        ), patch(
            "pr_review_scheduler.jobs.pr_notification.cache_pull_requests",
        ) as mock_cache, patch(
            "pr_review_scheduler.jobs.pr_notification.send_notification_email",
        ) as mock_send_email, patch(
            "pr_review_scheduler.jobs.pr_notification.get_settings",
            return_value=mock_settings,
        ):
            pr_notification.run_notification_job("schedule-123")

            # PRs should still be cached even without email
            mock_cache.assert_called_once()

            # Email should NOT be sent (empty email address)
            mock_send_email.assert_not_called()

    def test_run_notification_job_multiple_repos_partial_failure(self):
        """Test job continues when some repos fail to fetch PRs."""
        mock_schedule = {
            "id": "schedule-123",
            "user_id": "user-456",
            "user_email": "user@example.com",
            "name": "Daily PR Review",
            "cron_expression": "0 9 * * 1-5",
            "github_pat": "ghp_test_token",
            "is_active": True,
            "repositories": [
                {"organization": "myorg", "repository": "frontend"},
                {"organization": "myorg", "repository": "backend"},
            ],
        }

        mock_prs = [
            {
                "number": 1,
                "title": "Feature A",
                "author": "dev1",
                "author_avatar_url": "https://github.com/dev1.png",
                "labels": "[]",
                "checks_status": "pass",
                "html_url": "https://github.com/myorg/frontend/pull/1",
                "created_at": "2024-01-15T10:00:00Z",
                "organization": "myorg",
                "repository": "frontend",
            },
        ]

        mock_settings = MagicMock()
        mock_settings.application_url = "http://localhost:5173"

        with patch(
            "pr_review_scheduler.jobs.pr_notification.get_schedule_by_id",
            return_value=mock_schedule,
        ), patch(
            "pr_review_scheduler.jobs.pr_notification.get_repository_pull_requests",
            new_callable=AsyncMock,
        ) as mock_get_prs, patch(
            "pr_review_scheduler.jobs.pr_notification.cache_pull_requests",
        ) as mock_cache, patch(
            "pr_review_scheduler.jobs.pr_notification.send_notification_email",
            return_value=True,
        ) as mock_send_email, patch(
            "pr_review_scheduler.jobs.pr_notification.format_pr_summary_email",
            return_value=("Subject", "Body"),
        ), patch(
            "pr_review_scheduler.jobs.pr_notification.get_settings",
            return_value=mock_settings,
        ):
            # First repo returns PRs, second returns empty (simulating error handled gracefully)
            mock_get_prs.side_effect = [mock_prs, []]

            pr_notification.run_notification_job("schedule-123")

            # Verify both repos were attempted
            assert mock_get_prs.call_count == 2

            # Verify PRs from successful repo were cached
            mock_cache.assert_called_once()
            cache_call_args = mock_cache.call_args
            assert len(cache_call_args[0][1]) == 1

            # Verify email was sent
            mock_send_email.assert_called_once()
