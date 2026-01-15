"""Models for notification schedules and their associated repositories."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import backref, relationship

from pr_review_api.database import Base


def utcnow() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid4())


class NotificationSchedule(Base):
    """Notification schedule for sending PR summaries via email.

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the users table.
        name: Human-readable name for the schedule.
        cron_expression: Cron expression defining when notifications are sent.
        github_pat: Encrypted GitHub Personal Access Token for API access.
        is_active: Whether this schedule is currently active.
        created_at: Timestamp when the schedule was created.
        updated_at: Timestamp when the schedule was last updated.
        repositories: List of repositories to include in notifications.
        user: Reference to the owning User.
    """

    __tablename__ = "notification_schedules"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    cron_expression = Column(String, nullable=False)
    github_pat = Column(String, nullable=False)  # Encrypted
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    repositories = relationship(
        "ScheduleRepository",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )
    user = relationship(
        "User",
        backref=backref("schedules", passive_deletes=True),
    )
    cached_pull_requests = relationship(
        "CachedPullRequest",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return string representation of the schedule."""
        return f"<NotificationSchedule(id={self.id}, name={self.name})>"


class ScheduleRepository(Base):
    """Repository included in a notification schedule.

    Attributes:
        id: UUID primary key.
        schedule_id: Foreign key to the notification_schedules table.
        organization: GitHub organization name.
        repository: GitHub repository name.
        schedule: Reference to the parent NotificationSchedule.
    """

    __tablename__ = "schedule_repositories"

    id = Column(String, primary_key=True, default=generate_uuid)
    schedule_id = Column(
        String,
        ForeignKey("notification_schedules.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization = Column(String, nullable=False)
    repository = Column(String, nullable=False)

    schedule = relationship("NotificationSchedule", back_populates="repositories")

    __table_args__ = (
        UniqueConstraint("schedule_id", "organization", "repository", name="uq_schedule_org_repo"),
    )

    def __repr__(self) -> str:
        """Return string representation of the schedule repository."""
        return (
            f"<ScheduleRepository(id={self.id}, org={self.organization}, repo={self.repository})>"
        )
