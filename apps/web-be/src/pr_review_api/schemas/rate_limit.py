"""Rate limit schemas for GitHub API responses."""

from datetime import datetime

from pydantic import BaseModel


class RateLimitInfo(BaseModel):
    """GitHub API rate limit information.

    Attributes:
        remaining: Number of requests remaining in the current rate limit window.
        reset_at: When the rate limit will reset (UTC).
    """

    remaining: int
    reset_at: datetime
