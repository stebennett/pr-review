"""Settings router for managing user settings.

This module provides endpoints for reading and updating user settings,
specifically the email address used for notifications.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from pr_review_api.database import get_db
from pr_review_api.dependencies import get_current_user
from pr_review_api.models.user import User
from pr_review_api.schemas.settings import (
    SettingsAPIResponse,
    SettingsData,
    SettingsResponse,
    SettingsUpdate,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsAPIResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
) -> SettingsAPIResponse:
    """Get the current user's settings.

    Args:
        current_user: Current authenticated user from JWT.

    Returns:
        SettingsAPIResponse with user's email address.
    """
    return SettingsAPIResponse(
        data=SettingsData(settings=SettingsResponse(email=current_user.email))
    )


@router.put("", response_model=SettingsAPIResponse)
async def update_settings(
    settings_data: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SettingsAPIResponse:
    """Update the current user's settings.

    Args:
        settings_data: New settings values.
        current_user: Current authenticated user from JWT.
        db: Database session.

    Returns:
        SettingsAPIResponse with updated settings.

    Raises:
        HTTPException: 422 if email format is invalid.
    """
    # Update the user's email
    current_user.email = settings_data.email
    db.commit()
    db.refresh(current_user)

    return SettingsAPIResponse(
        data=SettingsData(settings=SettingsResponse(email=current_user.email))
    )
