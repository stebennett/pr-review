"""GitHub API service for the scheduler.

This module provides functions for fetching pull request data from GitHub.
"""

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


async def get_repository_pull_requests(
    access_token: str,
    organization: str,
    repository: str,
) -> list[dict[str, Any]]:
    """Fetch open pull requests for a repository.

    Args:
        access_token: GitHub Personal Access Token.
        organization: GitHub organization name.
        repository: Repository name.

    Returns:
        List of pull request data dictionaries with keys:
        - number: PR number
        - title: PR title
        - author: GitHub username of the author
        - author_avatar_url: URL to author's avatar
        - labels: JSON string of label names
        - checks_status: 'pass', 'fail', or 'pending'
        - html_url: URL to the PR on GitHub
        - created_at: ISO timestamp of PR creation
        - organization: Organization name
        - repository: Repository name
    """
    logger.info("Fetching PRs for %s/%s", organization, repository)

    url = f"{GITHUB_API_BASE}/repos/{organization}/{repository}/pulls"
    headers = {
        **GITHUB_HEADERS,
        "Authorization": f"Bearer {access_token}",
    }
    params = {
        "state": "open",
        "per_page": 100,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()

            prs_data = response.json()

            result = []
            for pr in prs_data:
                # Get the SHA from the PR head
                sha = pr.get("head", {}).get("sha", "")

                # Get checks status for this PR
                checks_status = await get_pull_request_checks(
                    access_token, organization, repository, sha
                )

                # Extract label names as a JSON string
                labels = [label.get("name", "") for label in pr.get("labels", [])]
                labels_json = json.dumps(labels)

                # Build the PR data dictionary
                pr_data = {
                    "number": pr.get("number"),
                    "title": pr.get("title", ""),
                    "author": pr.get("user", {}).get("login", ""),
                    "author_avatar_url": pr.get("user", {}).get("avatar_url", ""),
                    "labels": labels_json,
                    "checks_status": checks_status,
                    "html_url": pr.get("html_url", ""),
                    "created_at": pr.get("created_at", ""),
                    "organization": organization,
                    "repository": repository,
                }
                result.append(pr_data)

            logger.info(
                "Found %d open PRs for %s/%s", len(result), organization, repository
            )
            return result

    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP error fetching PRs for %s/%s: %s", organization, repository, e
        )
        return []
    except httpx.ConnectError as e:
        logger.error(
            "Connection error fetching PRs for %s/%s: %s", organization, repository, e
        )
        return []
    except Exception as e:
        logger.error(
            "Unexpected error fetching PRs for %s/%s: %s", organization, repository, e
        )
        return []


async def get_pull_request_checks(
    access_token: str,
    organization: str,
    repository: str,
    sha: str,
) -> str:
    """Get the checks status for a pull request.

    Args:
        access_token: GitHub Personal Access Token.
        organization: GitHub organization name.
        repository: Repository name.
        sha: Commit SHA to get check runs for.

    Returns:
        Checks status: 'pass', 'fail', or 'pending'.
        Returns 'pending' on errors.
    """
    logger.debug("Fetching checks for %s/%s commit %s", organization, repository, sha)

    url = f"{GITHUB_API_BASE}/repos/{organization}/{repository}/commits/{sha}/check-runs"
    headers = {
        **GITHUB_HEADERS,
        "Authorization": f"Bearer {access_token}",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            check_runs = data.get("check_runs", [])

            # No checks means pass
            if not check_runs:
                return "pass"

            # Aggregate status: any failure -> "fail", any pending -> "pending", else "pass"
            has_failure = False
            has_pending = False

            for check in check_runs:
                status = check.get("status", "")
                conclusion = check.get("conclusion")

                # Check for failure (conclusion is 'failure' or similar)
                if conclusion in ("failure", "cancelled", "timed_out", "action_required"):
                    has_failure = True

                # Check for pending (status is not 'completed' or conclusion is None)
                if status != "completed" or conclusion is None:
                    has_pending = True

            # Priority: failure > pending > pass
            if has_failure:
                return "fail"
            if has_pending:
                return "pending"
            return "pass"

    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP error fetching checks for %s/%s: %s", organization, repository, e
        )
        return "pending"
    except httpx.ConnectError as e:
        logger.error(
            "Connection error fetching checks for %s/%s: %s", organization, repository, e
        )
        return "pending"
    except Exception as e:
        logger.error(
            "Unexpected error fetching checks for %s/%s: %s", organization, repository, e
        )
        return "pending"
