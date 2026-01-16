"""Schedule schemas for request and response models."""

from datetime import datetime

from pydantic import BaseModel, Field


class RepositoryRef(BaseModel):
    """Reference to a GitHub repository.

    Attributes:
        organization: GitHub organization name.
        repository: GitHub repository name.
    """

    organization: str = Field(..., min_length=1)
    repository: str = Field(..., min_length=1)


class ScheduleCreate(BaseModel):
    """Request body for creating a notification schedule.

    Attributes:
        name: Human-readable name for the schedule.
        cron_expression: Cron expression defining when notifications are sent.
        github_pat: GitHub Personal Access Token for API access.
        repositories: List of repositories to include in notifications.
        is_active: Whether the schedule should be active immediately.
    """

    name: str = Field(..., min_length=1, max_length=255)
    cron_expression: str = Field(..., min_length=1)
    github_pat: str = Field(..., min_length=1)
    repositories: list[RepositoryRef] = Field(..., min_length=1)
    is_active: bool = True


class ScheduleUpdate(BaseModel):
    """Request body for updating a notification schedule.

    All fields are optional to allow partial updates.

    Attributes:
        name: Human-readable name for the schedule.
        cron_expression: Cron expression defining when notifications are sent.
        github_pat: GitHub Personal Access Token (only updated if provided).
        repositories: List of repositories (replaces all existing if provided).
        is_active: Whether the schedule is active.
    """

    name: str | None = Field(None, min_length=1, max_length=255)
    cron_expression: str | None = Field(None, min_length=1)
    github_pat: str | None = Field(None, min_length=1)
    repositories: list[RepositoryRef] | None = None
    is_active: bool | None = None


class ScheduleResponse(BaseModel):
    """Response for a single notification schedule.

    Note: The GitHub PAT is never included in responses.

    Attributes:
        id: Unique identifier for the schedule.
        name: Human-readable name for the schedule.
        cron_expression: Cron expression defining when notifications are sent.
        repositories: List of repositories included in notifications.
        is_active: Whether the schedule is active.
        created_at: When the schedule was created.
        updated_at: When the schedule was last updated.
    """

    id: str
    name: str
    cron_expression: str
    repositories: list[RepositoryRef]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SchedulesData(BaseModel):
    """Container for schedules list.

    Attributes:
        schedules: List of notification schedules.
    """

    schedules: list[ScheduleResponse]


class SchedulesResponse(BaseModel):
    """API response wrapper for schedules list endpoint.

    Attributes:
        data: Container with list of schedules.
    """

    data: SchedulesData


class ScheduleData(BaseModel):
    """Container for single schedule.

    Attributes:
        schedule: The notification schedule.
    """

    schedule: ScheduleResponse


class SingleScheduleResponse(BaseModel):
    """API response wrapper for single schedule endpoint.

    Attributes:
        data: Container with the schedule.
    """

    data: ScheduleData
