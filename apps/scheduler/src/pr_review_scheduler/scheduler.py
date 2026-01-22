"""APScheduler setup and management.

This module provides the scheduler instance and functions for managing
scheduled notification jobs.
"""

import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from pr_review_scheduler.jobs.pr_notification import run_notification_job

if TYPE_CHECKING:
    from apscheduler.job import Job

logger = logging.getLogger(__name__)


def create_scheduler() -> BackgroundScheduler:
    """Create and configure the APScheduler instance.

    Returns:
        Configured BackgroundScheduler instance.
    """
    scheduler = BackgroundScheduler(
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 60,
        }
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


def get_job(scheduler: BackgroundScheduler, job_id: str) -> "Job | None":
    """Get a job by ID.

    Args:
        scheduler: The scheduler instance.
        job_id: The job ID to look up.

    Returns:
        The job if found, None otherwise.
    """
    return scheduler.get_job(job_id)


def remove_job(scheduler: BackgroundScheduler, job_id: str) -> None:
    """Remove a job by ID.

    Args:
        scheduler: The scheduler instance.
        job_id: The job ID to remove.
    """
    job = scheduler.get_job(job_id)
    if job:
        scheduler.remove_job(job_id)
        logger.info("Removed job: %s", job_id)


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

    # Parse cron expression into CronTrigger
    trigger = CronTrigger.from_crontab(cron_expression)

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
