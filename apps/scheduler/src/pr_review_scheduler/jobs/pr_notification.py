"""Pull Request notification job.

This module contains the job that fetches open PRs and sends notification emails.
"""

import asyncio
import logging
from typing import Any

from pr_review_scheduler.config import get_settings
from pr_review_scheduler.services.database import cache_pull_requests, get_schedule_by_id
from pr_review_scheduler.services.email import format_pr_summary_email, send_notification_email
from pr_review_scheduler.services.github import get_repository_pull_requests

logger = logging.getLogger(__name__)


def run_notification_job(schedule_id: str) -> None:
    """Execute the PR notification job for a schedule.

    This job:
    1. Loads the schedule from the database
    2. Decrypts the GitHub PAT
    3. Fetches open PRs for each repository in the schedule
    4. Caches the PR data in the database
    5. Sends a summary email if there are open PRs

    Args:
        schedule_id: The ID of the schedule to process.
    """
    logger.info("Running notification job for schedule: %s", schedule_id)

    # 1. Load schedule from database (PAT is already decrypted)
    schedule = get_schedule_by_id(schedule_id)

    if schedule is None:
        logger.error("Schedule not found: %s", schedule_id)
        return

    # 2. Get the decrypted PAT from the schedule
    github_pat = schedule["github_pat"]
    repositories = schedule.get("repositories", [])
    user_email = schedule.get("user_email")

    # 3. Fetch PRs from GitHub for each repository concurrently
    all_prs: list[dict[str, Any]] = []
    pr_counts: dict[str, int] = {}

    if repositories:
        # Log the repositories we are about to fetch PRs for
        for repo in repositories:
            logger.info("Fetching PRs for %s/%s", repo["organization"], repo["repository"])

        async def _fetch_all_prs() -> list[list[dict[str, Any]]]:
            tasks = [
                get_repository_pull_requests(
                    github_pat, repo["organization"], repo["repository"]
                )
                for repo in repositories
            ]
            return await asyncio.gather(*tasks)

        # Fetch all repositories concurrently with a single event loop
        prs_results = asyncio.run(_fetch_all_prs())

        for repo, prs in zip(repositories, prs_results):
            org = repo["organization"]
            repo_name = repo["repository"]
            repo_full_name = f"{org}/{repo_name}"

            if prs:
                all_prs.extend(prs)
                pr_counts[repo_full_name] = len(prs)
                logger.info("Found %d PRs in %s", len(prs), repo_full_name)
            else:
                logger.info("No open PRs found in %s", repo_full_name)

    # 4. If PRs found, cache them and send email
    if all_prs:
        logger.info("Total PRs found: %d across %d repositories", len(all_prs), len(pr_counts))

        # Cache the PRs
        cache_pull_requests(schedule_id, all_prs)

        # 5. Send email if user has email configured
        if not user_email:
            logger.warning(
                "No email configured for schedule %s (user_id: %s). "
                "Skipping email notification.",
                schedule_id,
                schedule.get("user_id"),
            )
        else:
            settings = get_settings()
            subject, body = format_pr_summary_email(pr_counts, settings.application_url)

            logger.info("Sending notification email to %s", user_email)
            send_notification_email(user_email, subject, body)
    else:
        logger.info(
            "No open PRs found for schedule %s. Skipping email notification.",
            schedule_id,
        )

    logger.info("Notification job completed for schedule: %s", schedule_id)
