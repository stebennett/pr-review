"""Pull requests router for listing repository PRs.

This module provides endpoints for fetching open pull requests
for a specific repository within an organization and refreshing PR data.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from httpx import HTTPStatusError
from pr_review_shared import decrypt_token

from pr_review_api.config import Settings, get_settings
from pr_review_api.dependencies import get_current_user
from pr_review_api.models.user import User
from pr_review_api.schemas.pull_request import (
    PullRequestsData,
    PullRequestsMeta,
    PullRequestsResponse,
    RefreshData,
    RefreshMeta,
    RefreshResponse,
)
from pr_review_api.services.github import GitHubAPIService, get_github_api_service

router = APIRouter(prefix="/api/organizations", tags=["pulls"])

# Separate router for refresh endpoint with different prefix
refresh_router = APIRouter(prefix="/api/pulls", tags=["pulls"])


@router.get(
    "/{org}/repositories/{repo}/pulls",
    response_model=PullRequestsResponse,
)
async def list_pull_requests(
    org: str,
    repo: str,
    current_user: User = Depends(get_current_user),
    github_service: GitHubAPIService = Depends(get_github_api_service),
    settings: Settings = Depends(get_settings),
) -> PullRequestsResponse:
    """List open pull requests for a repository.

    Fetches open PRs including their check statuses using the user's
    stored access token.

    Args:
        org: Organization login name.
        repo: Repository name.
        current_user: Current authenticated user from JWT.
        github_service: GitHub API service for fetching pull requests.
        settings: Application settings for decryption key.

    Returns:
        PullRequestsResponse with list of pull requests and rate limit info.

    Raises:
        HTTPException: 401 if GitHub token is invalid.
        HTTPException: 404 if organization or repository is not found.
        HTTPException: 502 if GitHub API call fails.
    """
    # Decrypt the user's GitHub access token
    access_token = decrypt_token(
        current_user.github_access_token,
        settings.encryption_key,
    )

    try:
        pull_requests, rate_limit = await github_service.get_repository_pull_requests(
            access_token, org, repo
        )
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub access token is invalid or expired",
            )
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository '{org}/{repo}' not found",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch pull requests from GitHub",
        )

    return PullRequestsResponse(
        data=PullRequestsData(pulls=pull_requests),
        meta=PullRequestsMeta(rate_limit=rate_limit),
    )


@refresh_router.post(
    "/refresh",
    response_model=RefreshResponse,
)
async def refresh_pull_requests(
    current_user: User = Depends(get_current_user),
    github_service: GitHubAPIService = Depends(get_github_api_service),
    settings: Settings = Depends(get_settings),
) -> RefreshResponse:
    """Trigger a refresh of PR data and return rate limit info.

    This endpoint validates the user's GitHub token and returns the current
    rate limit status. The actual data refresh happens client-side via
    React Query cache invalidation.

    Args:
        current_user: Current authenticated user from JWT.
        github_service: GitHub API service for checking rate limit.
        settings: Application settings for decryption key.

    Returns:
        RefreshResponse with success message and rate limit info.

    Raises:
        HTTPException: 401 if GitHub token is invalid.
        HTTPException: 429 if rate limit is exceeded.
        HTTPException: 502 if GitHub API call fails.
    """
    # Decrypt the user's GitHub access token
    access_token = decrypt_token(
        current_user.github_access_token,
        settings.encryption_key,
    )

    try:
        rate_limit = await github_service.get_rate_limit(access_token)
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub access token is invalid or expired",
            )
        if e.response.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="GitHub API rate limit exceeded",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to check rate limit from GitHub",
        )

    # Check if rate limit is exceeded
    if rate_limit.remaining == 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="GitHub API rate limit exceeded",
            headers={"X-RateLimit-Reset": rate_limit.reset_at.isoformat()},
        )

    return RefreshResponse(
        data=RefreshData(message="Refresh initiated successfully"),
        meta=RefreshMeta(rate_limit=rate_limit),
    )
