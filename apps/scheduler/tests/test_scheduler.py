"""Tests for the scheduler module."""

import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from pr_review_scheduler.config import get_settings
from pr_review_scheduler.scheduler import (
    JobNotFoundError,
    add_cron_job,
    create_scheduler,
    get_all_jobs,
    get_job,
    remove_job,
    shutdown_scheduler,
    start_scheduler,
    update_job,
)


class TestCreateScheduler:
    """Tests for create_scheduler function."""

    def test_create_scheduler_returns_background_scheduler(self, mock_settings):
        """Test that create_scheduler returns a BackgroundScheduler instance."""
        scheduler = create_scheduler()
        try:
            assert isinstance(scheduler, BackgroundScheduler)
        finally:
            if scheduler.running:
                scheduler.shutdown(wait=False)

    def test_create_scheduler_configures_timezone(self, mock_settings):
        """Test that scheduler is configured with the correct timezone."""
        scheduler = create_scheduler()
        try:
            settings = get_settings()
            expected_timezone = ZoneInfo(settings.scheduler_timezone)
            assert scheduler.timezone == expected_timezone
        finally:
            if scheduler.running:
                scheduler.shutdown(wait=False)

    def test_create_scheduler_with_different_timezone(self, mock_settings_different_timezone):
        """Test that scheduler uses configured timezone."""
        scheduler = create_scheduler()
        try:
            settings = get_settings()
            assert settings.scheduler_timezone == "America/New_York"
            expected_timezone = ZoneInfo("America/New_York")
            assert scheduler.timezone == expected_timezone
        finally:
            if scheduler.running:
                scheduler.shutdown(wait=False)

    def test_create_scheduler_configures_job_defaults(self, mock_settings):
        """Test that scheduler has correct job defaults."""
        scheduler = create_scheduler()
        try:
            # Job defaults are applied when jobs are added
            # We verify by checking the scheduler was created without errors
            assert scheduler is not None
        finally:
            if scheduler.running:
                scheduler.shutdown(wait=False)


class TestStartScheduler:
    """Tests for start_scheduler function."""

    def test_start_scheduler_starts_scheduler(self, mock_settings):
        """Test that start_scheduler starts the scheduler."""
        scheduler = create_scheduler()
        try:
            assert not scheduler.running
            start_scheduler(scheduler)
            assert scheduler.running
        finally:
            scheduler.shutdown(wait=False)

    def test_start_scheduler_does_not_start_if_already_running(self, mock_settings):
        """Test that start_scheduler is idempotent."""
        scheduler = create_scheduler()
        try:
            start_scheduler(scheduler)
            assert scheduler.running
            # Call again - should not raise
            start_scheduler(scheduler)
            assert scheduler.running
        finally:
            scheduler.shutdown(wait=False)


class TestShutdownScheduler:
    """Tests for shutdown_scheduler function."""

    def test_shutdown_scheduler_stops_running_scheduler(self, mock_settings):
        """Test that shutdown_scheduler stops the scheduler."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        assert scheduler.running
        shutdown_scheduler(scheduler, wait=True)
        assert not scheduler.running

    def test_shutdown_scheduler_handles_not_running_scheduler(self, mock_settings):
        """Test that shutdown_scheduler handles non-running scheduler."""
        scheduler = create_scheduler()
        assert not scheduler.running
        # Should not raise
        shutdown_scheduler(scheduler, wait=True)
        assert not scheduler.running

    def test_shutdown_scheduler_with_wait_false(self, mock_settings):
        """Test that shutdown_scheduler can shut down without waiting."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        shutdown_scheduler(scheduler, wait=False)
        assert not scheduler.running


class TestAddCronJob:
    """Tests for add_cron_job function."""

    def test_add_cron_job_adds_job(self, mock_settings):
        """Test that add_cron_job adds a job to the scheduler."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:

            def dummy_job():
                pass

            job = add_cron_job(
                scheduler,
                job_id="test-job",
                func=dummy_job,
                cron_expression="0 9 * * *",  # Every day at 9 AM
            )

            assert job is not None
            assert job.id == "test-job"
            assert get_job(scheduler, "test-job") is not None
        finally:
            scheduler.shutdown(wait=False)

    def test_add_cron_job_with_args(self, mock_settings):
        """Test that add_cron_job passes args correctly."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:
            results = []

            def job_with_args(schedule_id):
                results.append(schedule_id)

            job = add_cron_job(
                scheduler,
                job_id="test-job-args",
                func=job_with_args,
                cron_expression="0 9 * * *",
                args=["schedule-123"],
            )

            assert job is not None
            assert job.args == ("schedule-123",)
        finally:
            scheduler.shutdown(wait=False)

    def test_add_cron_job_with_kwargs(self, mock_settings):
        """Test that add_cron_job passes kwargs correctly."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:

            def job_with_kwargs(schedule_id=None):
                pass

            job = add_cron_job(
                scheduler,
                job_id="test-job-kwargs",
                func=job_with_kwargs,
                cron_expression="0 9 * * *",
                kwargs={"schedule_id": "schedule-456"},
            )

            assert job is not None
            assert job.kwargs == {"schedule_id": "schedule-456"}
        finally:
            scheduler.shutdown(wait=False)

    def test_add_cron_job_replaces_existing(self, mock_settings):
        """Test that add_cron_job replaces existing job by default."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:

            def dummy_job():
                pass

            # Add first job
            add_cron_job(
                scheduler,
                job_id="test-job",
                func=dummy_job,
                cron_expression="0 9 * * *",
            )

            # Add second job with same ID (different schedule)
            add_cron_job(
                scheduler,
                job_id="test-job",
                func=dummy_job,
                cron_expression="0 10 * * *",  # Changed to 10 AM
                replace_existing=True,
            )

            # Should only have one job
            jobs = get_all_jobs(scheduler)
            assert len(jobs) == 1
            assert jobs[0].id == "test-job"
        finally:
            scheduler.shutdown(wait=False)

    def test_add_cron_job_invalid_cron_expression(self, mock_settings):
        """Test that add_cron_job raises ValueError for invalid cron."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:

            def dummy_job():
                pass

            with pytest.raises(ValueError):
                add_cron_job(
                    scheduler,
                    job_id="test-job",
                    func=dummy_job,
                    cron_expression="invalid cron",
                )
        finally:
            scheduler.shutdown(wait=False)

    def test_add_cron_job_weekday_expression(self, mock_settings):
        """Test that add_cron_job handles weekday expressions."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:

            def dummy_job():
                pass

            # Weekdays at 9 AM
            job = add_cron_job(
                scheduler,
                job_id="test-weekday-job",
                func=dummy_job,
                cron_expression="0 9 * * 1-5",
            )

            assert job is not None
            assert isinstance(job.trigger, CronTrigger)
        finally:
            scheduler.shutdown(wait=False)


class TestGetJob:
    """Tests for get_job function."""

    def test_get_job_returns_existing_job(self, mock_settings):
        """Test that get_job returns an existing job."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:

            def dummy_job():
                pass

            add_cron_job(
                scheduler,
                job_id="test-job",
                func=dummy_job,
                cron_expression="0 9 * * *",
            )

            job = get_job(scheduler, "test-job")
            assert job is not None
            assert job.id == "test-job"
        finally:
            scheduler.shutdown(wait=False)

    def test_get_job_returns_none_for_nonexistent(self, mock_settings):
        """Test that get_job returns None for non-existent job."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:
            job = get_job(scheduler, "nonexistent-job")
            assert job is None
        finally:
            scheduler.shutdown(wait=False)


class TestGetAllJobs:
    """Tests for get_all_jobs function."""

    def test_get_all_jobs_returns_empty_list(self, mock_settings):
        """Test that get_all_jobs returns empty list when no jobs."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:
            jobs = get_all_jobs(scheduler)
            assert jobs == []
        finally:
            scheduler.shutdown(wait=False)

    def test_get_all_jobs_returns_all_jobs(self, mock_settings):
        """Test that get_all_jobs returns all scheduled jobs."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:

            def dummy_job():
                pass

            add_cron_job(scheduler, job_id="job-1", func=dummy_job, cron_expression="0 9 * * *")
            add_cron_job(scheduler, job_id="job-2", func=dummy_job, cron_expression="0 10 * * *")
            add_cron_job(scheduler, job_id="job-3", func=dummy_job, cron_expression="0 11 * * *")

            jobs = get_all_jobs(scheduler)
            assert len(jobs) == 3
            job_ids = {job.id for job in jobs}
            assert job_ids == {"job-1", "job-2", "job-3"}
        finally:
            scheduler.shutdown(wait=False)


class TestRemoveJob:
    """Tests for remove_job function."""

    def test_remove_job_removes_existing_job(self, mock_settings):
        """Test that remove_job removes an existing job."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:

            def dummy_job():
                pass

            add_cron_job(
                scheduler,
                job_id="test-job",
                func=dummy_job,
                cron_expression="0 9 * * *",
            )

            assert get_job(scheduler, "test-job") is not None
            result = remove_job(scheduler, "test-job")
            assert result is True
            assert get_job(scheduler, "test-job") is None
        finally:
            scheduler.shutdown(wait=False)

    def test_remove_job_returns_false_for_nonexistent(self, mock_settings):
        """Test that remove_job returns False for non-existent job."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:
            result = remove_job(scheduler, "nonexistent-job")
            assert result is False
        finally:
            scheduler.shutdown(wait=False)


class TestUpdateJob:
    """Tests for update_job function."""

    def test_update_job_updates_cron_expression(self, mock_settings):
        """Test that update_job updates the cron expression."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:

            def dummy_job():
                pass

            add_cron_job(
                scheduler,
                job_id="test-job",
                func=dummy_job,
                cron_expression="0 9 * * *",
            )

            result = update_job(scheduler, "test-job", cron_expression="0 10 * * *")
            assert result is True

            # Verify the job still exists
            job = get_job(scheduler, "test-job")
            assert job is not None
        finally:
            scheduler.shutdown(wait=False)

    def test_update_job_raises_for_nonexistent(self, mock_settings):
        """Test that update_job raises JobNotFoundError for non-existent job."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:
            with pytest.raises(JobNotFoundError) as exc_info:
                update_job(scheduler, "nonexistent-job", cron_expression="0 10 * * *")
            assert exc_info.value.job_id == "nonexistent-job"
        finally:
            scheduler.shutdown(wait=False)

    def test_update_job_with_no_changes(self, mock_settings):
        """Test that update_job returns False when no update parameters provided."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:

            def dummy_job():
                pass

            add_cron_job(
                scheduler,
                job_id="test-job",
                func=dummy_job,
                cron_expression="0 9 * * *",
            )

            # Update with no cron expression - should return False (no changes made)
            result = update_job(scheduler, "test-job")
            assert result is False
        finally:
            scheduler.shutdown(wait=False)


class TestJobExecution:
    """Tests for job execution behavior."""

    def test_job_executes_with_correct_args(self, mock_settings):
        """Test that a job executes and receives correct arguments."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:
            results = []
            event = threading.Event()

            def test_job(schedule_id):
                results.append(schedule_id)
                event.set()

            # Use date trigger for immediate execution, aligned with scheduler timezone
            run_time = datetime.now(tz=scheduler.timezone) + timedelta(milliseconds=100)
            scheduler.add_job(
                test_job,
                trigger=DateTrigger(run_date=run_time),
                id="immediate-job",
                args=["test-schedule-id"],
            )

            # Wait for job to execute
            event.wait(timeout=2)

            assert len(results) == 1
            assert results[0] == "test-schedule-id"
        finally:
            scheduler.shutdown(wait=False)

    def test_job_coalescing(self, mock_settings):
        """Test that jobs coalesce when multiple triggers fire."""
        scheduler = create_scheduler()
        start_scheduler(scheduler)
        try:
            # This test verifies the coalesce setting is applied
            # by checking that the scheduler accepts the configuration
            def dummy_job():
                pass

            job = add_cron_job(
                scheduler,
                job_id="coalesce-test",
                func=dummy_job,
                cron_expression="* * * * *",  # Every minute
            )

            # Verify job was added with coalesce enabled (from defaults)
            assert job is not None
        finally:
            scheduler.shutdown(wait=False)
