"""Organizations router for listing user's GitHub organizations.

This module provides an endpoint for fetching the authenticated user's
GitHub organizations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from httpx import HTTPStatusError
from pr_review_shared import decrypt_token

from pr_review_api.config import Settings, get_settings
from pr_review_api.dependencies import get_current_user
from pr_review_api.models.user import User
from pr_review_api.schemas import OrganizationsData, OrganizationsResponse
from pr_review_api.services.github import GitHubAPIService, get_github_api_service

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.get("", response_model=OrganizationsResponse)
async def list_organizations(
    current_user: User = Depends(get_current_user),
    github_service: GitHubAPIService = Depends(get_github_api_service),
    settings: Settings = Depends(get_settings),
) -> OrganizationsResponse:
    """List organizations the authenticated user has access to.

    Fetches the user's GitHub organizations using their stored access token.

    Args:
        current_user: Current authenticated user from JWT.
        github_service: GitHub API service for fetching organizations.
        settings: Application settings for decryption key.

    Returns:
        OrganizationsResponse with list of organizations.

    Raises:
        HTTPException: 500 if GitHub API call fails.
    """
    # Decrypt the user's GitHub access token
    access_token = decrypt_token(
        current_user.github_access_token,
        settings.encryption_key,
    )

    try:
        organizations, _ = await github_service.get_user_organizations(access_token)
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub access token is invalid or expired",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch organizations from GitHub",
        )

    return OrganizationsResponse(data=OrganizationsData(organizations=organizations))
