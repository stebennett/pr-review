"""Tests for scheduler setup and management."""

from apscheduler.triggers.cron import CronTrigger

from pr_review_scheduler.scheduler import (
    add_notification_job,
    create_scheduler,
    get_job,
    remove_job,
    shutdown_scheduler,
    start_scheduler,
)


def test_create_scheduler():
    """Test that scheduler is created with correct configuration."""
    scheduler = create_scheduler()
    assert scheduler is not None
    assert not scheduler.running


def test_start_and_shutdown_scheduler():
    """Test starting and stopping the scheduler."""
    scheduler = create_scheduler()
    start_scheduler(scheduler)
    assert scheduler.running
    shutdown_scheduler(scheduler, wait=False)
    assert not scheduler.running


def test_add_notification_job():
    """Test adding a notification job with cron expression."""
    scheduler = create_scheduler()
    start_scheduler(scheduler)

    try:
        job = add_notification_job(
            scheduler,
            schedule_id="test-schedule-123",
            cron_expression="0 9 * * 1-5",  # 9am weekdays
        )

        assert job is not None
        assert job.id == "test-schedule-123"
        assert isinstance(job.trigger, CronTrigger)

        # Verify job can be retrieved
        retrieved = get_job(scheduler, "test-schedule-123")
        assert retrieved is not None
        assert retrieved.id == job.id
    finally:
        shutdown_scheduler(scheduler, wait=False)


def test_add_notification_job_replaces_existing():
    """Test that adding a job with same ID replaces existing."""
    scheduler = create_scheduler()
    start_scheduler(scheduler)

    try:
        add_notification_job(scheduler, "test-123", "0 9 * * *")
        add_notification_job(scheduler, "test-123", "0 10 * * *")  # Different time

        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "test-123"
    finally:
        shutdown_scheduler(scheduler, wait=False)


def test_remove_nonexistent_job_no_error():
    """Test that removing a nonexistent job doesn't raise."""
    scheduler = create_scheduler()
    start_scheduler(scheduler)

    try:
        # Should not raise
        remove_job(scheduler, "nonexistent-job-id")
    finally:
        shutdown_scheduler(scheduler, wait=False)
