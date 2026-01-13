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


class RepositoriesData(BaseModel):
    """Container for repositories list.

    Attributes:
        repositories: List of repositories.
    """

    repositories: list[Repository]


class RepositoriesResponse(BaseModel):
    """API response wrapper for repositories endpoint.

    Attributes:
        data: Container with list of repositories.
    """

    data: RepositoriesData
