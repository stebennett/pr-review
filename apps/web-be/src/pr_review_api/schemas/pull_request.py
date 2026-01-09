"""Pull request schemas for GitHub API responses."""

from datetime import datetime

from pydantic import BaseModel


class Author(BaseModel):
    """Pull request author.

    Attributes:
        username: GitHub username.
        avatar_url: URL to author's avatar.
    """

    username: str
    avatar_url: str | None = None


class Label(BaseModel):
    """Pull request label.

    Attributes:
        name: Label name.
        color: Label color (hex without #).
    """

    name: str
    color: str


class PullRequest(BaseModel):
    """GitHub pull request.

    Attributes:
        number: PR number.
        title: PR title.
        author: PR author information.
        labels: List of labels attached to the PR.
        checks_status: Aggregate check status ('pass', 'fail', 'pending').
        html_url: URL to the PR on GitHub.
        created_at: When the PR was created.
    """

    number: int
    title: str
    author: Author
    labels: list[Label]
    checks_status: str  # 'pass', 'fail', 'pending'
    html_url: str
    created_at: datetime
