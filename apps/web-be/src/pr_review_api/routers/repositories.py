"""Repositories router for listing organization repositories.

This module provides an endpoint for fetching repositories within a
GitHub organization.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from httpx import HTTPStatusError
from pr_review_shared import decrypt_token

from pr_review_api.config import Settings, get_settings
from pr_review_api.dependencies import get_current_user
from pr_review_api.models.user import User
from pr_review_api.schemas import RepositoriesData, RepositoriesResponse
from pr_review_api.services.github import GitHubAPIService, get_github_api_service

router = APIRouter(prefix="/api/organizations", tags=["repositories"])


@router.get("/{org}/repositories", response_model=RepositoriesResponse)
async def list_repositories(
    org: str,
    current_user: User = Depends(get_current_user),
    github_service: GitHubAPIService = Depends(get_github_api_service),
    settings: Settings = Depends(get_settings),
) -> RepositoriesResponse:
    """List repositories in an organization.

    Fetches the organization's repositories using the user's stored access token.

    Args:
        org: Organization login name.
        current_user: Current authenticated user from JWT.
        github_service: GitHub API service for fetching repositories.
        settings: Application settings for decryption key.

    Returns:
        RepositoriesResponse with list of repositories.

    Raises:
        HTTPException: 401 if GitHub token is invalid.
        HTTPException: 404 if organization is not found.
        HTTPException: 502 if GitHub API call fails.
    """
    # Decrypt the user's GitHub access token
    access_token = decrypt_token(
        current_user.github_access_token,
        settings.encryption_key,
    )

    try:
        repositories, _ = await github_service.get_organization_repositories(access_token, org)
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub access token is invalid or expired",
            )
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{org}' not found",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch repositories from GitHub",
        )

    return RepositoriesResponse(data=RepositoriesData(repositories=repositories))
