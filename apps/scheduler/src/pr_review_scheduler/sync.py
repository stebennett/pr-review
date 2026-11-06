"""Schedule synchronization module.

This module provides functions for synchronizing database schedules
with APScheduler jobs.
"""

import logging
from typing import TYPE_CHECKING

from pr_review_scheduler.scheduler import add_notification_job, remove_job
from pr_review_scheduler.services.database import get_active_schedules, get_all_schedule_ids

if TYPE_CHECKING:
    from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


def sync_schedules(scheduler: "BackgroundScheduler") -> None:
    """Synchronize database schedules with APScheduler jobs.

    This function performs the following:
    1. Get active schedules from database
    2. Get all schedule IDs (to detect deleted schedules)
    3. Get current jobs from scheduler
    4. For each active schedule: add/update job
    5. For each current job not in active schedules:
       - If schedule was deleted (not in all_schedule_ids): remove job
       - If schedule was deactivated (in all_ids but not active): remove job

    Args:
        scheduler: The APScheduler BackgroundScheduler instance.
    """
    # Get active schedules from database
    active_schedules = get_active_schedules()
    active_schedule_ids = {schedule["id"] for schedule in active_schedules}

    # Get all schedule IDs to detect deleted vs deactivated
    all_schedule_ids = set(get_all_schedule_ids())

    # Get current jobs from scheduler
    current_jobs = scheduler.get_jobs()
    current_job_ids = {job.id for job in current_jobs}

    logger.debug(
        "Syncing schedules: %d active, %d total in DB, %d current jobs",
        len(active_schedule_ids),
        len(all_schedule_ids),
        len(current_job_ids),
    )

    # Add/update jobs for active schedules
    for schedule in active_schedules:
        schedule_id = schedule["id"]
        cron_expression = schedule["cron_expression"]

        # add_notification_job handles both add and update (replaces if exists)
        add_notification_job(scheduler, schedule_id, cron_expression)

    # Remove jobs for schedules that are no longer active
    for job in current_jobs:
        job_id = job.id

        if job_id not in active_schedule_ids:
            # Job exists but schedule is not active
            if job_id not in all_schedule_ids:
                # Schedule was deleted from database
                logger.info("Removing job for deleted schedule: %s", job_id)
            else:
                # Schedule exists but is inactive
                logger.info("Removing job for inactive schedule: %s", job_id)

            remove_job(scheduler, job_id)
