"""Tests for schedule synchronization."""

from unittest.mock import MagicMock, patch

import pytest

from pr_review_scheduler.sync import sync_schedules


@pytest.fixture
def mock_scheduler():
    """Create a mock scheduler with common methods."""
    scheduler = MagicMock()
    scheduler.get_jobs.return_value = []
    return scheduler


class TestSyncSchedules:
    """Tests for sync_schedules function."""

    @patch("pr_review_scheduler.sync.remove_job")
    @patch("pr_review_scheduler.sync.add_notification_job")
    @patch("pr_review_scheduler.sync.get_all_schedule_ids")
    @patch("pr_review_scheduler.sync.get_active_schedules")
    def test_sync_schedules_adds_new_jobs(
        self,
        mock_get_active,
        mock_get_all_ids,
        mock_add_job,
        mock_remove_job,
        mock_scheduler,
    ):
        """Test that new schedules are added as jobs."""
        # Setup: One active schedule, no existing jobs
        mock_get_active.return_value = [
            {
                "id": "schedule-1",
                "cron_expression": "0 9 * * 1-5",
                "name": "Test Schedule",
            }
        ]
        mock_get_all_ids.return_value = ["schedule-1"]
        mock_scheduler.get_jobs.return_value = []

        # Execute
        sync_schedules(mock_scheduler)

        # Verify: Job was added
        mock_add_job.assert_called_once_with(mock_scheduler, "schedule-1", "0 9 * * 1-5")
        mock_remove_job.assert_not_called()

    @patch("pr_review_scheduler.sync.remove_job")
    @patch("pr_review_scheduler.sync.add_notification_job")
    @patch("pr_review_scheduler.sync.get_all_schedule_ids")
    @patch("pr_review_scheduler.sync.get_active_schedules")
    def test_sync_schedules_removes_deleted_jobs(
        self,
        mock_get_active,
        mock_get_all_ids,
        mock_add_job,
        mock_remove_job,
        mock_scheduler,
    ):
        """Test that deleted schedules have their jobs removed."""
        # Setup: No active schedules, but a job exists for a deleted schedule
        mock_get_active.return_value = []
        mock_get_all_ids.return_value = []  # Schedule was deleted from DB

        existing_job = MagicMock()
        existing_job.id = "deleted-schedule"
        mock_scheduler.get_jobs.return_value = [existing_job]

        # Execute
        sync_schedules(mock_scheduler)

        # Verify: Job was removed
        mock_remove_job.assert_called_once_with(mock_scheduler, "deleted-schedule")
        mock_add_job.assert_not_called()

    @patch("pr_review_scheduler.sync.remove_job")
    @patch("pr_review_scheduler.sync.add_notification_job")
    @patch("pr_review_scheduler.sync.get_all_schedule_ids")
    @patch("pr_review_scheduler.sync.get_active_schedules")
    def test_sync_schedules_removes_inactive_jobs(
        self,
        mock_get_active,
        mock_get_all_ids,
        mock_add_job,
        mock_remove_job,
        mock_scheduler,
    ):
        """Test that inactive schedules have their jobs removed."""
        # Setup: Schedule exists but is inactive
        mock_get_active.return_value = []  # No active schedules
        mock_get_all_ids.return_value = ["inactive-schedule"]  # But schedule exists

        existing_job = MagicMock()
        existing_job.id = "inactive-schedule"
        mock_scheduler.get_jobs.return_value = [existing_job]

        # Execute
        sync_schedules(mock_scheduler)

        # Verify: Job was removed because schedule is inactive
        mock_remove_job.assert_called_once_with(mock_scheduler, "inactive-schedule")
        mock_add_job.assert_not_called()

    @patch("pr_review_scheduler.sync.remove_job")
    @patch("pr_review_scheduler.sync.add_notification_job")
    @patch("pr_review_scheduler.sync.get_all_schedule_ids")
    @patch("pr_review_scheduler.sync.get_active_schedules")
    def test_sync_schedules_updates_existing_jobs(
        self,
        mock_get_active,
        mock_get_all_ids,
        mock_add_job,
        mock_remove_job,
        mock_scheduler,
    ):
        """Test that existing jobs are updated if cron changed."""
        # Setup: Active schedule with a job that already exists
        mock_get_active.return_value = [
            {
                "id": "schedule-1",
                "cron_expression": "0 10 * * 1-5",  # Changed from 9 to 10
                "name": "Test Schedule",
            }
        ]
        mock_get_all_ids.return_value = ["schedule-1"]

        existing_job = MagicMock()
        existing_job.id = "schedule-1"
        mock_scheduler.get_jobs.return_value = [existing_job]

        # Execute
        sync_schedules(mock_scheduler)

        # Verify: Job was re-added (add_notification_job handles replacement)
        mock_add_job.assert_called_once_with(mock_scheduler, "schedule-1", "0 10 * * 1-5")
        # remove_job should NOT be called separately - add_notification_job handles it
        mock_remove_job.assert_not_called()

    @patch("pr_review_scheduler.sync.remove_job")
    @patch("pr_review_scheduler.sync.add_notification_job")
    @patch("pr_review_scheduler.sync.get_all_schedule_ids")
    @patch("pr_review_scheduler.sync.get_active_schedules")
    def test_sync_schedules_handles_multiple_schedules(
        self,
        mock_get_active,
        mock_get_all_ids,
        mock_add_job,
        mock_remove_job,
        mock_scheduler,
    ):
        """Test syncing multiple schedules at once."""
        # Setup: Two active schedules, one deleted, one inactive
        mock_get_active.return_value = [
            {"id": "schedule-1", "cron_expression": "0 9 * * *", "name": "Active 1"},
            {"id": "schedule-2", "cron_expression": "0 10 * * *", "name": "Active 2"},
        ]
        mock_get_all_ids.return_value = ["schedule-1", "schedule-2", "schedule-3"]

        # Existing jobs: schedule-1 (active), schedule-3 (inactive), schedule-4 (deleted)
        job1 = MagicMock()
        job1.id = "schedule-1"
        job3 = MagicMock()
        job3.id = "schedule-3"
        job4 = MagicMock()
        job4.id = "schedule-4"
        mock_scheduler.get_jobs.return_value = [job1, job3, job4]

        # Execute
        sync_schedules(mock_scheduler)

        # Verify: Both active schedules added/updated
        assert mock_add_job.call_count == 2

        # Verify: Jobs for schedule-3 (inactive) and schedule-4 (deleted) removed
        assert mock_remove_job.call_count == 2
        removed_ids = [call[0][1] for call in mock_remove_job.call_args_list]
        assert "schedule-3" in removed_ids
        assert "schedule-4" in removed_ids

    @patch("pr_review_scheduler.sync.remove_job")
    @patch("pr_review_scheduler.sync.add_notification_job")
    @patch("pr_review_scheduler.sync.get_all_schedule_ids")
    @patch("pr_review_scheduler.sync.get_active_schedules")
    def test_sync_schedules_no_changes_needed(
        self,
        mock_get_active,
        mock_get_all_ids,
        mock_add_job,
        mock_remove_job,
        mock_scheduler,
    ):
        """Test sync when schedules haven't changed still re-syncs jobs."""
        # Setup: One active schedule that already has a job
        mock_get_active.return_value = [
            {"id": "schedule-1", "cron_expression": "0 9 * * *", "name": "Test"}
        ]
        mock_get_all_ids.return_value = ["schedule-1"]

        existing_job = MagicMock()
        existing_job.id = "schedule-1"
        mock_scheduler.get_jobs.return_value = [existing_job]

        # Execute
        sync_schedules(mock_scheduler)

        # Verify: Job is still re-added (idempotent behavior)
        mock_add_job.assert_called_once()
        mock_remove_job.assert_not_called()
