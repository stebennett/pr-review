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
    RepositoryRef,
    ScheduleCreate,
    ScheduleData,
    ScheduleResponse,
    SchedulesData,
    SchedulesResponse,
    ScheduleUpdate,
    SingleScheduleResponse,
)

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


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
        db.query(NotificationSchedule)
        .filter(NotificationSchedule.user_id == current_user.id)
        .all()
    )

    schedule_responses = [_schedule_to_response(s) for s in schedules]

    return SchedulesResponse(data=SchedulesData(schedules=schedule_responses))


@router.post("", response_model=SingleScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SingleScheduleResponse:
    """Create a new notification schedule.

    Encrypts the GitHub PAT before storing and creates associated
    repository entries.

    Args:
        schedule_data: Schedule creation data.
        current_user: Current authenticated user from JWT.
        db: Database session.
        settings: Application settings for encryption key.

    Returns:
        SingleScheduleResponse with the created schedule.
    """
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

    return SingleScheduleResponse(
        data=ScheduleData(schedule=_schedule_to_response(schedule))
    )


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

    return SingleScheduleResponse(
        data=ScheduleData(schedule=_schedule_to_response(schedule))
    )


@router.put("/{schedule_id}", response_model=SingleScheduleResponse)
async def update_schedule(
    schedule_id: str,
    schedule_data: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SingleScheduleResponse:
    """Update a notification schedule.

    Supports partial updates - only provided fields are updated.
    If github_pat is provided, it will be encrypted before storing.
    If repositories is provided, it replaces all existing associations.

    Args:
        schedule_id: The schedule ID to update.
        schedule_data: Schedule update data.
        current_user: Current authenticated user from JWT.
        db: Database session.
        settings: Application settings for encryption key.

    Returns:
        SingleScheduleResponse with the updated schedule.

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
        db.query(ScheduleRepository).filter(
            ScheduleRepository.schedule_id == schedule_id
        ).delete()

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

    return SingleScheduleResponse(
        data=ScheduleData(schedule=_schedule_to_response(schedule))
    )


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
