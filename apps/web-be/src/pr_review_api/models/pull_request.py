"""Model for cached pull request data."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from pr_review_api.database import Base


def utcnow() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid4())


class CachedPullRequest(Base):
    """Cached pull request data from scheduled job runs.

    Stores PR information fetched during scheduled notification jobs
    for potential display and debugging purposes.

    Attributes:
        id: UUID primary key.
        schedule_id: Foreign key to the notification_schedules table.
        organization: GitHub organization name.
        repository: GitHub repository name.
        pr_number: Pull request number.
        title: Pull request title.
        author: PR author username.
        author_avatar_url: URL to author's GitHub avatar.
        labels: JSON string of label data.
        checks_status: Status of PR checks ('pass', 'fail', 'pending').
        html_url: URL to the pull request on GitHub.
        created_at: When the PR was created on GitHub.
        cached_at: When this data was cached.
        schedule: Reference to the parent NotificationSchedule.
    """

    __tablename__ = "cached_pull_requests"

    id = Column(String, primary_key=True, default=generate_uuid)
    schedule_id = Column(
        String,
        ForeignKey("notification_schedules.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization = Column(String, nullable=False)
    repository = Column(String, nullable=False)
    pr_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    author_avatar_url = Column(String, nullable=True)
    labels = Column(String, nullable=True)  # JSON array
    checks_status = Column(String, nullable=True)  # 'pass', 'fail', 'pending'
    html_url = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    cached_at = Column(DateTime, default=utcnow)

    schedule = relationship("NotificationSchedule", back_populates="cached_pull_requests")

    __table_args__ = (
        UniqueConstraint(
            "schedule_id",
            "organization",
            "repository",
            "pr_number",
            name="uq_schedule_org_repo_pr",
        ),
    )

    def __repr__(self) -> str:
        """Return string representation of the cached pull request."""
        return (
            f"<CachedPullRequest(id={self.id}, org={self.organization}, "
            f"repo={self.repository}, pr={self.pr_number})>"
        )
