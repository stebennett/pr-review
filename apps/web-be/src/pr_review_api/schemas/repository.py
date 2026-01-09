"""Repository schemas for GitHub API responses."""

from pydantic import BaseModel


class Repository(BaseModel):
    """GitHub repository.

    Attributes:
        id: GitHub repository ID.
        name: Repository name (without owner).
        full_name: Full repository name (owner/repo).
    """

    id: str
    name: str
    full_name: str
