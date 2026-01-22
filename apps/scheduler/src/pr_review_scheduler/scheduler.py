"""APScheduler setup and management.

This module provides the scheduler instance and functions for managing
scheduled notification jobs.
"""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from pr_review_scheduler.config import get_settings
from pr_review_scheduler.jobs.pr_notification import run_notification_job

if TYPE_CHECKING:
    from apscheduler.job import Job

logger = logging.getLogger(__name__)


class JobNotFoundError(Exception):
    """Raised when a job is not found in the scheduler."""

    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id}")


def create_scheduler() -> BackgroundScheduler:
    """Create and configure the APScheduler instance.

    Configures the scheduler with:
    - ThreadPoolExecutor for concurrent job execution
    - Timezone from settings (default: UTC)
    - Job defaults for coalescing, max instances, and misfire handling

    Returns:
        Configured BackgroundScheduler instance.
    """
    settings = get_settings()
    timezone = ZoneInfo(settings.scheduler_timezone)

    executors = {"default": ThreadPoolExecutor(max_workers=settings.scheduler_executor_pool_size)}

    job_defaults = {
        # Combine multiple pending runs into one when a job couldn't be executed on time
        "coalesce": True,
        # Maximum number of concurrent instances of this job
        "max_instances": 1,
        # How many seconds late a job can still be triggered (after scheduled time)
        "misfire_grace_time": 60,
    }

    scheduler = BackgroundScheduler(
        executors=executors,
        job_defaults=job_defaults,
        timezone=timezone,
    )

    logger.info(
        "Created scheduler with timezone=%s, executor_pool_size=%d",
        settings.scheduler_timezone,
        settings.scheduler_executor_pool_size,
    )

    return scheduler


def start_scheduler(scheduler: BackgroundScheduler) -> None:
    """Start the scheduler.

    Args:
        scheduler: The scheduler instance to start.
    """
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def shutdown_scheduler(scheduler: BackgroundScheduler, wait: bool = True) -> None:
    """Gracefully shutdown the scheduler.

    Args:
        scheduler: The scheduler instance to shutdown.
        wait: Whether to wait for running jobs to complete.
    """
    if scheduler.running:
        scheduler.shutdown(wait=wait)
        logger.info("Scheduler shut down")


def add_cron_job(
    scheduler: BackgroundScheduler,
    job_id: str,
    func: Callable[..., Any],
    cron_expression: str,
    args: list[Any] | None = None,
    kwargs: dict[str, Any] | None = None,
    replace_existing: bool = True,
) -> "Job":
    """Add a cron-based job to the scheduler.

    Args:
        scheduler: The scheduler instance.
        job_id: Unique identifier for the job.
        func: The function to execute.
        cron_expression: Standard 5-field cron expression (minute hour day month weekday).
        args: Positional arguments to pass to the function.
        kwargs: Keyword arguments to pass to the function.
        replace_existing: If True, replace any existing job with the same ID.

    Returns:
        The created Job instance.

    Raises:
        ValueError: If the cron expression is invalid.
    """
    settings = get_settings()
    timezone = ZoneInfo(settings.scheduler_timezone)

    trigger = CronTrigger.from_crontab(cron_expression, timezone=timezone)

    job = scheduler.add_job(
        func,
        trigger=trigger,
        id=job_id,
        args=args or [],
        kwargs=kwargs or {},
        replace_existing=replace_existing,
    )

    logger.info("Added cron job: %s with expression '%s'", job_id, cron_expression)
    return job


def get_job(scheduler: BackgroundScheduler, job_id: str) -> "Job | None":
    """Get a job by ID.

    Args:
        scheduler: The scheduler instance.
        job_id: The job ID to look up.

    Returns:
        The job if found, None otherwise.
    """
    return scheduler.get_job(job_id)


def get_all_jobs(scheduler: BackgroundScheduler) -> list["Job"]:
    """Get all scheduled jobs.

    Args:
        scheduler: The scheduler instance.

    Returns:
        List of all scheduled jobs.
    """
    return scheduler.get_jobs()


def remove_job(scheduler: BackgroundScheduler, job_id: str) -> bool:
    """Remove a job by ID.

    Args:
        scheduler: The scheduler instance.
        job_id: The job ID to remove.

    Returns:
        True if the job was removed, False if it didn't exist.
    """
    job = scheduler.get_job(job_id)
    if job:
        scheduler.remove_job(job_id)
        logger.info("Removed job: %s", job_id)
        return True
    return False


def update_job(
    scheduler: BackgroundScheduler,
    job_id: str,
    cron_expression: str | None = None,
) -> bool:
    """Update an existing job's schedule.

    Args:
        scheduler: The scheduler instance.
        job_id: The job ID to update.
        cron_expression: New cron expression (if provided).

    Returns:
        True if the job was updated, False if no update parameters were provided.

    Raises:
        JobNotFoundError: If the job with the given ID does not exist.
    """
    job = scheduler.get_job(job_id)
    if not job:
        raise JobNotFoundError(job_id)

    if not cron_expression:
        logger.info("No update parameters provided for job %s; no changes made", job_id)
        return False

    settings = get_settings()
    timezone = ZoneInfo(settings.scheduler_timezone)
    trigger = CronTrigger.from_crontab(cron_expression, timezone=timezone)
    job.reschedule(trigger)
    logger.info("Updated job %s with new expression '%s'", job_id, cron_expression)

    return True


def add_notification_job(
    scheduler: BackgroundScheduler,
    schedule_id: str,
    cron_expression: str,
) -> "Job":
    """Add a notification job with a cron schedule.

    If a job with the same schedule_id already exists, it will be replaced.

    Args:
        scheduler: The scheduler instance.
        schedule_id: Unique identifier for the schedule (used as job ID).
        cron_expression: Cron expression for the job schedule (e.g., "0 9 * * 1-5").

    Returns:
        The created job instance.
    """
    # Remove existing job if present (allows replacement)
    remove_job(scheduler, schedule_id)

    settings = get_settings()
    timezone = ZoneInfo(settings.scheduler_timezone)

    # Parse cron expression into CronTrigger
    trigger = CronTrigger.from_crontab(cron_expression, timezone=timezone)

    # Add the job
    job = scheduler.add_job(
        run_notification_job,
        trigger=trigger,
        id=schedule_id,
        args=[schedule_id],
        name=f"PR notification for schedule {schedule_id}",
    )

    logger.info("Added notification job: %s with cron: %s", schedule_id, cron_expression)
    return job
