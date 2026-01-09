"""Organization schemas for GitHub API responses."""

from pydantic import BaseModel


class Organization(BaseModel):
    """GitHub organization.

    Attributes:
        id: GitHub organization ID.
        login: Organization login name.
        avatar_url: URL to organization's avatar.
    """

    id: str
    login: str
    avatar_url: str | None = None
