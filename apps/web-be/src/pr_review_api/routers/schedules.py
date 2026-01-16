"""Schedules router for managing notification schedules.

This module provides CRUD endpoints for managing notification schedules
that define when and what PR notifications should be sent to users.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pr_review_shared import encrypt_token
from sqlalchemy.orm import Session

from pr_review_api.config import Settings, get_settings
from pr_review_api.database import get_db
from pr_review_api.dependencies import get_current_user
from pr_review_api.models.schedule import NotificationSchedule, ScheduleRepository
from pr_review_api.models.user import User
from pr_review_api.schemas.schedule import (
    PATOrganization,
    PATOrganizationsData,
    PATOrganizationsResponse,
    PATPreviewRequest,
    PATRepositoriesData,
    PATRepositoriesRequest,
    PATRepositoriesResponse,
    PATRepository,
    RepositoryRef,
    ScheduleCreate,
    ScheduleData,
    ScheduleResponse,
    SchedulesData,
    SchedulesResponse,
    ScheduleUpdate,
    SingleScheduleResponse,
)
from pr_review_api.services.github import GitHubAPIService, get_github_api_service

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


async def _validate_pat_and_repositories(
    pat: str,
    repositories: list[RepositoryRef],
    github_service: GitHubAPIService,
) -> None:
    """Validate PAT and repository access before saving a schedule.

    Args:
        pat: GitHub Personal Access Token to validate.
        repositories: List of repositories to check access for.
        github_service: GitHub API service instance.

    Raises:
        HTTPException: 400 if PAT is invalid, missing scopes, or can't access repos.
    """
    # Validate PAT
    pat_result = await github_service.validate_pat(pat)

    if not pat_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PAT_VALIDATION_FAILED",
                "message": pat_result.error_message or "Invalid GitHub Personal Access Token",
            },
        )

    # Check for missing scopes (classic PATs only)
    if pat_result.missing_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PAT_MISSING_SCOPES",
                "message": "The provided GitHub PAT is missing required scopes",
                "missing_scopes": pat_result.missing_scopes,
                "required_scopes": list(github_service.REQUIRED_PAT_SCOPES),
            },
        )

    # Validate repository access
    access_result = await github_service.validate_repository_access(pat, repositories)

    if access_result.inaccessible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PAT_REPOSITORY_ACCESS_DENIED",
                "message": "The provided GitHub PAT cannot access one or more repositories",
                "inaccessible_repositories": [
                    {
                        "organization": repo.organization,
                        "repository": repo.repository,
                        "reason": repo.reason,
                    }
                    for repo in access_result.inaccessible
                ],
            },
        )


def _schedule_to_response(schedule: NotificationSchedule) -> ScheduleResponse:
    """Convert a NotificationSchedule model to a ScheduleResponse.

    Args:
        schedule: The database model to convert.

    Returns:
        ScheduleResponse with repositories extracted.
    """
    repositories = [
        RepositoryRef(organization=repo.organization, repository=repo.repository)
        for repo in schedule.repositories
    ]
    return ScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        cron_expression=schedule.cron_expression,
        repositories=repositories,
        is_active=schedule.is_active,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.get("", response_model=SchedulesResponse)
async def list_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SchedulesResponse:
    """List all notification schedules for the current user.

    Args:
        current_user: Current authenticated user from JWT.
        db: Database session.

    Returns:
        SchedulesResponse with list of user's schedules.
    """
    schedules = (
        db.query(NotificationSchedule).filter(NotificationSchedule.user_id == current_user.id).all()
    )

    schedule_responses = [_schedule_to_response(s) for s in schedules]

    return SchedulesResponse(data=SchedulesData(schedules=schedule_responses))


@router.post("", response_model=SingleScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    github_service: GitHubAPIService = Depends(get_github_api_service),
) -> SingleScheduleResponse:
    """Create a new notification schedule.

    Validates the GitHub PAT and repository access before encrypting
    and storing the schedule with its repository entries.

    Args:
        schedule_data: Schedule creation data.
        current_user: Current authenticated user from JWT.
        db: Database session.
        settings: Application settings for encryption key.
        github_service: GitHub API service for PAT validation.

    Returns:
        SingleScheduleResponse with the created schedule.

    Raises:
        HTTPException: 400 if PAT is invalid, missing scopes, or can't access repos.
    """
    # Validate PAT and repository access before saving
    await _validate_pat_and_repositories(
        schedule_data.github_pat,
        schedule_data.repositories,
        github_service,
    )

    # Encrypt the GitHub PAT before storing
    encrypted_pat = encrypt_token(schedule_data.github_pat, settings.encryption_key)

    # Create the schedule
    schedule = NotificationSchedule(
        user_id=current_user.id,
        name=schedule_data.name,
        cron_expression=schedule_data.cron_expression,
        github_pat=encrypted_pat,
        is_active=schedule_data.is_active,
    )
    db.add(schedule)
    db.flush()  # Get the schedule ID

    # Create repository associations
    for repo_ref in schedule_data.repositories:
        repo = ScheduleRepository(
            schedule_id=schedule.id,
            organization=repo_ref.organization,
            repository=repo_ref.repository,
        )
        db.add(repo)

    db.commit()
    db.refresh(schedule)

    return SingleScheduleResponse(data=ScheduleData(schedule=_schedule_to_response(schedule)))


@router.get("/{schedule_id}", response_model=SingleScheduleResponse)
async def get_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SingleScheduleResponse:
    """Get a specific notification schedule by ID.

    Args:
        schedule_id: The schedule ID to retrieve.
        current_user: Current authenticated user from JWT.
        db: Database session.

    Returns:
        SingleScheduleResponse with the requested schedule.

    Raises:
        HTTPException: 404 if schedule not found or doesn't belong to user.
    """
    schedule = (
        db.query(NotificationSchedule)
        .filter(
            NotificationSchedule.id == schedule_id,
            NotificationSchedule.user_id == current_user.id,
        )
        .first()
    )

    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    return SingleScheduleResponse(data=ScheduleData(schedule=_schedule_to_response(schedule)))


@router.put("/{schedule_id}", response_model=SingleScheduleResponse)
async def update_schedule(
    schedule_id: str,
    schedule_data: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    github_service: GitHubAPIService = Depends(get_github_api_service),
) -> SingleScheduleResponse:
    """Update a notification schedule.

    Supports partial updates - only provided fields are updated.
    If github_pat is provided, it will be validated and encrypted before storing.
    If repositories is provided, it replaces all existing associations.

    Args:
        schedule_id: The schedule ID to update.
        schedule_data: Schedule update data.
        current_user: Current authenticated user from JWT.
        db: Database session.
        settings: Application settings for encryption key.
        github_service: GitHub API service for PAT validation.

    Returns:
        SingleScheduleResponse with the updated schedule.

    Raises:
        HTTPException: 404 if schedule not found or doesn't belong to user.
        HTTPException: 400 if PAT is invalid, missing scopes, or can't access repos.
    """
    schedule = (
        db.query(NotificationSchedule)
        .filter(
            NotificationSchedule.id == schedule_id,
            NotificationSchedule.user_id == current_user.id,
        )
        .first()
    )

    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    # Validate PAT if a new one is provided
    if schedule_data.github_pat is not None:
        # Determine which repositories to validate against
        repos_to_validate = schedule_data.repositories
        if repos_to_validate is None:
            # Use existing repositories if not updating them
            repos_to_validate = [
                RepositoryRef(organization=r.organization, repository=r.repository)
                for r in schedule.repositories
            ]

        await _validate_pat_and_repositories(
            schedule_data.github_pat,
            repos_to_validate,
            github_service,
        )

    # Update provided fields
    if schedule_data.name is not None:
        schedule.name = schedule_data.name
    if schedule_data.cron_expression is not None:
        schedule.cron_expression = schedule_data.cron_expression
    if schedule_data.github_pat is not None:
        schedule.github_pat = encrypt_token(schedule_data.github_pat, settings.encryption_key)
    if schedule_data.is_active is not None:
        schedule.is_active = schedule_data.is_active

    # Replace repositories if provided
    if schedule_data.repositories is not None:
        # Delete existing repositories
        db.query(ScheduleRepository).filter(ScheduleRepository.schedule_id == schedule_id).delete()

        # Create new repository associations
        for repo_ref in schedule_data.repositories:
            repo = ScheduleRepository(
                schedule_id=schedule.id,
                organization=repo_ref.organization,
                repository=repo_ref.repository,
            )
            db.add(repo)

    db.commit()
    db.refresh(schedule)

    return SingleScheduleResponse(data=ScheduleData(schedule=_schedule_to_response(schedule)))


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a notification schedule.

    Cascade deletes associated repository entries.

    Args:
        schedule_id: The schedule ID to delete.
        current_user: Current authenticated user from JWT.
        db: Database session.

    Raises:
        HTTPException: 404 if schedule not found or doesn't belong to user.
    """
    schedule = (
        db.query(NotificationSchedule)
        .filter(
            NotificationSchedule.id == schedule_id,
            NotificationSchedule.user_id == current_user.id,
        )
        .first()
    )

    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    db.delete(schedule)
    db.commit()


@router.post("/pat/organizations", response_model=PATOrganizationsResponse)
async def preview_pat_organizations(
    request: PATPreviewRequest,
    current_user: User = Depends(get_current_user),
    github_service: GitHubAPIService = Depends(get_github_api_service),
) -> PATOrganizationsResponse:
    """Preview organizations accessible with a GitHub PAT.

    Validates the PAT and returns the list of organizations/accounts
    that can be accessed with it.

    Args:
        request: Request containing the GitHub PAT.
        current_user: Current authenticated user from JWT.
        github_service: GitHub API service instance.

    Returns:
        PATOrganizationsResponse with list of accessible organizations.

    Raises:
        HTTPException: 400 if PAT is invalid or missing required scopes.
    """
    # Validate PAT first
    pat_result = await github_service.validate_pat(request.github_pat)

    if not pat_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PAT_VALIDATION_FAILED",
                "message": pat_result.error_message or "Invalid GitHub Personal Access Token",
            },
        )

    if pat_result.missing_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "PAT_MISSING_SCOPES",
                "message": "The provided GitHub PAT is missing required scopes",
                "missing_scopes": pat_result.missing_scopes,
                "required_scopes": list(github_service.REQUIRED_PAT_SCOPES),
            },
        )

    # Fetch organizations accessible with this PAT
    organizations, _ = await github_service.get_user_organizations(request.github_pat)

    return PATOrganizationsResponse(
        data=PATOrganizationsData(
            organizations=[
                PATOrganization(
                    id=org.id,
                    login=org.login,
                    avatar_url=org.avatar_url,
                )
                for org in organizations
            ],
            username=pat_result.username or "",
        )
    )


@router.post("/pat/repositories", response_model=PATRepositoriesResponse)
async def preview_pat_repositories(
    request: PATRepositoriesRequest,
    current_user: User = Depends(get_current_user),
    github_service: GitHubAPIService = Depends(get_github_api_service),
) -> PATRepositoriesResponse:
    """Preview repositories accessible with a GitHub PAT for an organization.

    Fetches the list of repositories in the specified organization
    that can be accessed with the provided PAT.

    Args:
        request: Request containing the GitHub PAT and organization.
        current_user: Current authenticated user from JWT.
        github_service: GitHub API service instance.

    Returns:
        PATRepositoriesResponse with list of accessible repositories.

    Raises:
        HTTPException: 400 if PAT is invalid.
        HTTPException: 404 if organization not found.
    """
    # Fetch repositories for the organization
    try:
        repositories, _ = await github_service.get_organization_repositories(
            request.github_pat, request.organization
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "FETCH_REPOSITORIES_FAILED",
                "message": f"Failed to fetch repositories for organization '{request.organization}'",
            },
        )

    return PATRepositoriesResponse(
        data=PATRepositoriesData(
            repositories=[
                PATRepository(
                    id=repo.id,
                    name=repo.name,
                    full_name=repo.full_name,
                )
                for repo in repositories
            ]
        )
    )
