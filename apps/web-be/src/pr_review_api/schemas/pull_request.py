"""Pull request schemas for GitHub API responses."""

from datetime import datetime

from pydantic import BaseModel

from pr_review_api.schemas.rate_limit import RateLimitInfo


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


class PullRequestsData(BaseModel):
    """Container for pull requests list.

    Attributes:
        pulls: List of pull requests.
    """

    pulls: list[PullRequest]


class PullRequestsMeta(BaseModel):
    """Metadata for pull requests response.

    Attributes:
        rate_limit: GitHub API rate limit information.
    """

    rate_limit: RateLimitInfo


class PullRequestsResponse(BaseModel):
    """API response wrapper for pull requests endpoint.

    Attributes:
        data: Container with list of pull requests.
        meta: Response metadata including rate limit info.
    """

    data: PullRequestsData
    meta: PullRequestsMeta


class RefreshData(BaseModel):
    """Container for refresh response data.

    Attributes:
        message: Success message.
    """

    message: str


class RefreshMeta(BaseModel):
    """Metadata for refresh response.

    Attributes:
        rate_limit: GitHub API rate limit information.
    """

    rate_limit: RateLimitInfo


class RefreshResponse(BaseModel):
    """API response wrapper for refresh endpoint.

    Attributes:
        data: Container with success message.
        meta: Response metadata including rate limit info.
    """

    data: RefreshData
    meta: RefreshMeta
