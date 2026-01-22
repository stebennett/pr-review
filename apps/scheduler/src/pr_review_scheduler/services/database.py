"""Database service for the scheduler.

This module provides functions for querying schedules and caching PR data.
It defines read-only copies of the database models from web-be to avoid
cross-package dependencies.
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pr_review_shared.encryption import DecryptionError, decrypt_token
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from pr_review_scheduler.config import get_settings

logger = logging.getLogger(__name__)

# SQLAlchemy declarative base for models
Base = declarative_base()

# Module-level engine cache
_engine: Engine | None = None


def utcnow() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid4())


# -----------------------------------------------------------------------------
# Database Models (read-only mirrors of web-be models)
# -----------------------------------------------------------------------------


class User(Base):
    """User model for storing GitHub user information.

    This is a read-only mirror of the User model in web-be.
    """

    __tablename__ = "users"

    id = Column(String, primary_key=True)
    github_username = Column(String, nullable=False)
    github_access_token = Column(String, nullable=False)
    email = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def __repr__(self) -> str:
        """Return string representation of the user."""
        return f"<User(id={self.id}, username={self.github_username})>"


class NotificationSchedule(Base):
    """Notification schedule for sending PR summaries via email.

    This is a read-only mirror of the NotificationSchedule model in web-be.
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
        lazy="joined",
    )
    user = relationship("User", lazy="joined")
    cached_pull_requests = relationship(
        "CachedPullRequest",
        back_populates="schedule",
    )

    def __repr__(self) -> str:
        """Return string representation of the schedule."""
        return f"<NotificationSchedule(id={self.id}, name={self.name})>"


class ScheduleRepository(Base):
    """Repository included in a notification schedule.

    This is a read-only mirror of the ScheduleRepository model in web-be.
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

    def __repr__(self) -> str:
        """Return string representation of the schedule repository."""
        return f"<ScheduleRepository(org={self.organization}, repo={self.repository})>"


class CachedPullRequest(Base):
    """Cached pull request data from scheduled job runs.

    This is a read-only mirror of the CachedPullRequest model in web-be.
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

    def __repr__(self) -> str:
        """Return string representation of the cached pull request."""
        return (
            f"<CachedPullRequest(org={self.organization}, "
            f"repo={self.repository}, pr={self.pr_number})>"
        )


# -----------------------------------------------------------------------------
# Engine and Session Management
# -----------------------------------------------------------------------------


def _get_engine() -> Engine:
    """Get or create the database engine.

    Returns:
        SQLAlchemy Engine instance configured for the database.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},  # Required for SQLite
        )
    return _engine


def _get_session() -> Session:
    """Create a new database session.

    Returns:
        A new SQLAlchemy Session instance.
    """
    engine = _get_engine()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_factory()


def _schedule_to_dict(schedule: NotificationSchedule, decrypted_pat: str) -> dict[str, Any]:
    """Convert a NotificationSchedule to a dictionary.

    Args:
        schedule: The schedule model instance.
        decrypted_pat: The decrypted GitHub PAT.

    Returns:
        Dictionary representation of the schedule.
    """
    return {
        "id": schedule.id,
        "user_id": schedule.user_id,
        "user_email": schedule.user.email if schedule.user else None,
        "name": schedule.name,
        "cron_expression": schedule.cron_expression,
        "github_pat": decrypted_pat,
        "is_active": schedule.is_active,
        "repositories": [
            {
                "organization": repo.organization,
                "repository": repo.repository,
            }
            for repo in schedule.repositories
        ],
    }


# -----------------------------------------------------------------------------
# Query Functions
# -----------------------------------------------------------------------------


def get_active_schedules() -> list[dict[str, Any]]:
    """Get all active notification schedules from the database.

    Queries for active schedules, joins with repositories, and decrypts PATs.
    Schedules with decryption errors are logged and skipped.

    Returns:
        List of active schedule dictionaries with decrypted PAT and repositories.
    """
    settings = get_settings()
    logger.debug("Fetching active schedules from %s", settings.database_url)

    session = _get_session()
    try:
        schedules = (
            session.query(NotificationSchedule)
            .filter(NotificationSchedule.is_active == True)  # noqa: E712
            .all()
        )

        result = []
        for schedule in schedules:
            try:
                decrypted_pat = decrypt_token(schedule.github_pat, settings.encryption_key)
                result.append(_schedule_to_dict(schedule, decrypted_pat))
            except DecryptionError as e:
                logger.error(
                    "Failed to decrypt PAT for schedule %s: %s. Skipping schedule.",
                    schedule.id,
                    e,
                )
                continue
            except Exception as e:
                logger.error(
                    "Unexpected error processing schedule %s: %s. Skipping schedule.",
                    schedule.id,
                    e,
                )
                continue

        logger.debug("Found %d active schedules", len(result))
        return result
    finally:
        session.close()


def get_schedule_by_id(schedule_id: str) -> dict[str, Any] | None:
    """Get a specific schedule by ID.

    Args:
        schedule_id: The schedule ID to look up.

    Returns:
        Schedule dictionary if found, None otherwise.
    """
    logger.debug("Fetching schedule: %s", schedule_id)

    settings = get_settings()
    session = _get_session()
    try:
        schedule = (
            session.query(NotificationSchedule)
            .filter(NotificationSchedule.id == schedule_id)
            .first()
        )

        if schedule is None:
            return None

        try:
            decrypted_pat = decrypt_token(schedule.github_pat, settings.encryption_key)
            return _schedule_to_dict(schedule, decrypted_pat)
        except DecryptionError as e:
            logger.error(
                "Failed to decrypt PAT for schedule %s: %s",
                schedule_id,
                e,
            )
            return None
    finally:
        session.close()


def get_user_email(user_id: str) -> str | None:
    """Get a user's email address.

    Args:
        user_id: The user ID to look up.

    Returns:
        User's email address if found, None otherwise.
    """
    logger.debug("Fetching email for user: %s", user_id)

    session = _get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()

        if user is None:
            return None

        return user.email
    finally:
        session.close()


def get_all_schedule_ids() -> list[str]:
    """Get all schedule IDs (both active and inactive).

    Returns:
        List of all schedule IDs.
    """
    logger.debug("Fetching all schedule IDs")

    session = _get_session()
    try:
        schedules = session.query(NotificationSchedule.id).all()
        return [schedule.id for schedule in schedules]
    finally:
        session.close()


def cache_pull_requests(
    schedule_id: str,
    pull_requests: list[dict[str, Any]],
) -> None:
    """Cache fetched pull requests in the database.

    Replaces any existing cached PRs for the schedule.

    Args:
        schedule_id: The schedule ID.
        pull_requests: List of PR data dicts with keys:
            number, title, author, author_avatar_url, labels,
            checks_status, html_url, created_at, organization, repository
    """
    logger.debug("Caching %d PRs for schedule: %s", len(pull_requests), schedule_id)

    session = _get_session()
    try:
        # Delete existing cached PRs for this schedule
        session.query(CachedPullRequest).filter_by(schedule_id=schedule_id).delete()

        # Insert new PRs
        for pr in pull_requests:
            cached_pr = CachedPullRequest(
                id=str(uuid4()),
                schedule_id=schedule_id,
                organization=pr["organization"],
                repository=pr["repository"],
                pr_number=pr["number"],
                title=pr["title"],
                author=pr["author"],
                author_avatar_url=pr.get("author_avatar_url"),
                labels=pr.get("labels"),
                checks_status=pr.get("checks_status"),
                html_url=pr["html_url"],
                created_at=pr["created_at"],
            )
            session.add(cached_pr)

        session.commit()
        logger.info("Cached %d PRs for schedule: %s", len(pull_requests), schedule_id)
    except Exception as e:
        session.rollback()
        logger.error("Error caching PRs for schedule %s: %s", schedule_id, e)
        raise
    finally:
        session.close()
