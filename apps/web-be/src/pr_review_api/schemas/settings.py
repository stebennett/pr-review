"""Settings schemas for request and response models."""

from pydantic import BaseModel, EmailStr


class SettingsResponse(BaseModel):
    """Response for user settings.

    Attributes:
        email: User's notification email address (may be None if not set).
    """

    email: str | None


class SettingsData(BaseModel):
    """Container for settings data.

    Attributes:
        settings: The user settings.
    """

    settings: SettingsResponse


class SettingsAPIResponse(BaseModel):
    """API response wrapper for settings endpoint.

    Attributes:
        data: Container with the settings.
    """

    data: SettingsData


class SettingsUpdate(BaseModel):
    """Request body for updating user settings.

    Attributes:
        email: New email address for the user (use None to clear).
    """

    email: EmailStr | None = None
