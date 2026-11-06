# Phase 6: Scheduler Service Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the background scheduler service that fetches PRs and sends notification emails on configured schedules.

**Architecture:** The scheduler uses APScheduler to run cron-based jobs. It loads active schedules from the database, creates jobs for each, and polls for changes every 60 seconds. Each job fetches PRs via the GitHub API using the schedule's decrypted PAT, caches results, and sends email summaries via SMTP2GO.

**Tech Stack:** Python, APScheduler, SQLAlchemy, httpx (GitHub API), smtplib (SMTP2GO), pr_review_shared (encryption)

---

## Prerequisites

Before starting, ensure:
1. The scheduler skeleton exists in `apps/scheduler/`
2. Database models exist in `apps/web-be/` (NotificationSchedule, ScheduleRepository, CachedPullRequest, User)
3. The shared encryption package exists at `shared/python/pr_review_shared/`

---

## Task 6.1: Enhance APScheduler Setup

**Goal:** The scheduler.py already has basic setup. We need to add job management functions for loading schedules.

**Files:**
- Modify: `apps/scheduler/src/pr_review_scheduler/scheduler.py`
- Test: `apps/scheduler/tests/test_scheduler.py`

**Step 1: Write the failing test for add_notification_job**

```python
# apps/scheduler/tests/test_scheduler.py
"""Tests for scheduler setup and management."""

import pytest
from apscheduler.triggers.cron import CronTrigger

from pr_review_scheduler.scheduler import (
    add_notification_job,
    create_scheduler,
    get_job,
    remove_job,
    shutdown_scheduler,
    start_scheduler,
)


def test_create_scheduler():
    """Test that scheduler is created with correct configuration."""
    scheduler = create_scheduler()
    assert scheduler is not None
    assert not scheduler.running


def test_start_and_shutdown_scheduler():
    """Test starting and stopping the scheduler."""
    scheduler = create_scheduler()
    start_scheduler(scheduler)
    assert scheduler.running
    shutdown_scheduler(scheduler, wait=False)
    assert not scheduler.running


def test_add_notification_job():
    """Test adding a notification job with cron expression."""
    scheduler = create_scheduler()
    start_scheduler(scheduler)

    try:
        job = add_notification_job(
            scheduler,
            schedule_id="test-schedule-123",
            cron_expression="0 9 * * 1-5",  # 9am weekdays
        )

        assert job is not None
        assert job.id == "test-schedule-123"
        assert isinstance(job.trigger, CronTrigger)

        # Verify job can be retrieved
        retrieved = get_job(scheduler, "test-schedule-123")
        assert retrieved is not None
        assert retrieved.id == job.id
    finally:
        shutdown_scheduler(scheduler, wait=False)


def test_add_notification_job_replaces_existing():
    """Test that adding a job with same ID replaces existing."""
    scheduler = create_scheduler()
    start_scheduler(scheduler)

    try:
        add_notification_job(scheduler, "test-123", "0 9 * * *")
        add_notification_job(scheduler, "test-123", "0 10 * * *")  # Different time

        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "test-123"
    finally:
        shutdown_scheduler(scheduler, wait=False)


def test_remove_nonexistent_job_no_error():
    """Test that removing a nonexistent job doesn't raise."""
    scheduler = create_scheduler()
    start_scheduler(scheduler)

    try:
        # Should not raise
        remove_job(scheduler, "nonexistent-job-id")
    finally:
        shutdown_scheduler(scheduler, wait=False)
```

**Step 2: Run test to verify it fails**

Run: `cd apps/scheduler && pytest tests/test_scheduler.py -v`
Expected: FAIL with "cannot import name 'add_notification_job'"

**Step 3: Write minimal implementation**

```python
# apps/scheduler/src/pr_review_scheduler/scheduler.py
"""APScheduler setup and management.

This module provides the scheduler instance and functions for managing
scheduled notification jobs.
"""

import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from pr_review_scheduler.jobs.pr_notification import run_notification_job

if TYPE_CHECKING:
    from apscheduler.job import Job

logger = logging.getLogger(__name__)


def create_scheduler() -> BackgroundScheduler:
    """Create and configure the APScheduler instance.

    Returns:
        Configured BackgroundScheduler instance.
    """
    scheduler = BackgroundScheduler(
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 60,
        }
    )
    return scheduler


def start_scheduler(scheduler: BackgroundScheduler) -> None:
    """Start the scheduler.

    Args:
        scheduler: The scheduler instance to start.
    """
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def shutdown_scheduler(scheduler: BackgroundScheduler, wait: bool = True) -> None:
    """Gracefully shutdown the scheduler.

    Args:
        scheduler: The scheduler instance to shutdown.
        wait: Whether to wait for running jobs to complete.
    """
    if scheduler.running:
        scheduler.shutdown(wait=wait)
        logger.info("Scheduler shut down")


def get_job(scheduler: BackgroundScheduler, job_id: str) -> "Job | None":
    """Get a job by ID.

    Args:
        scheduler: The scheduler instance.
        job_id: The job ID to look up.

    Returns:
        The job if found, None otherwise.
    """
    return scheduler.get_job(job_id)


def remove_job(scheduler: BackgroundScheduler, job_id: str) -> None:
    """Remove a job by ID.

    Args:
        scheduler: The scheduler instance.
        job_id: The job ID to remove.
    """
    job = scheduler.get_job(job_id)
    if job:
        scheduler.remove_job(job_id)
        logger.info("Removed job: %s", job_id)


def add_notification_job(
    scheduler: BackgroundScheduler,
    schedule_id: str,
    cron_expression: str,
) -> "Job":
    """Add or replace a notification job for a schedule.

    Args:
        scheduler: The scheduler instance.
        schedule_id: The schedule ID (used as job ID).
        cron_expression: Cron expression for job timing (e.g., "0 9 * * 1-5").

    Returns:
        The created/updated Job instance.
    """
    # Remove existing job if present
    existing = scheduler.get_job(schedule_id)
    if existing:
        scheduler.remove_job(schedule_id)
        logger.info("Replacing existing job: %s", schedule_id)

    # Create cron trigger from expression
    trigger = CronTrigger.from_crontab(cron_expression)

    # Add the job
    job = scheduler.add_job(
        run_notification_job,
        trigger=trigger,
        id=schedule_id,
        args=[schedule_id],
        name=f"PR Notification: {schedule_id}",
    )
    logger.info("Added notification job: %s with cron '%s'", schedule_id, cron_expression)
    return job
```

**Step 4: Run test to verify it passes**

Run: `cd apps/scheduler && pytest tests/test_scheduler.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/scheduler/src/pr_review_scheduler/scheduler.py apps/scheduler/tests/test_scheduler.py
git commit -m "feat(scheduler): add notification job management to APScheduler setup (Task 6.1)"
```

---

## Task 6.2: Implement Schedule Loading from Database

**Goal:** Create database service to query schedules and their repositories, decrypt PATs, and sync jobs.

**Files:**
- Create: `apps/scheduler/src/pr_review_scheduler/database.py` (new module for SQLAlchemy setup)
- Modify: `apps/scheduler/src/pr_review_scheduler/services/database.py`
- Test: `apps/scheduler/tests/test_services/test_database.py`

**Step 1: Create the database module for SQLAlchemy setup**

```python
# apps/scheduler/src/pr_review_scheduler/database.py
"""Database configuration for the scheduler.

This module sets up SQLAlchemy connection to the same database used by web-be.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from pr_review_scheduler.config import get_settings

# Get settings
settings = get_settings()

# SQLite requires check_same_thread=False for multi-threaded access
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_session() -> Session:
    """Get a new database session.

    Returns:
        SQLAlchemy Session instance.

    Note:
        Caller is responsible for closing the session.
    """
    return SessionLocal()
```

**Step 2: Write the failing test for database service**

```python
# apps/scheduler/tests/test_services/__init__.py
"""Test services package."""
```

```python
# apps/scheduler/tests/test_services/test_database.py
"""Tests for database service."""

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean, UniqueConstraint, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from pr_review_shared.encryption import encrypt_token, generate_encryption_key

# Create test database models (mirrors web-be models)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    github_username = Column(String, nullable=False)
    github_access_token = Column(String, nullable=False)
    email = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))


class NotificationSchedule(Base):
    __tablename__ = "notification_schedules"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    cron_expression = Column(String, nullable=False)
    github_pat = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    repositories = relationship("ScheduleRepository", back_populates="schedule", cascade="all, delete-orphan")


class ScheduleRepository(Base):
    __tablename__ = "schedule_repositories"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    schedule_id = Column(String, ForeignKey("notification_schedules.id", ondelete="CASCADE"), nullable=False)
    organization = Column(String, nullable=False)
    repository = Column(String, nullable=False)
    schedule = relationship("NotificationSchedule", back_populates="repositories")
    __table_args__ = (UniqueConstraint("schedule_id", "organization", "repository"),)


class CachedPullRequest(Base):
    __tablename__ = "cached_pull_requests"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    schedule_id = Column(String, ForeignKey("notification_schedules.id", ondelete="CASCADE"), nullable=False)
    organization = Column(String, nullable=False)
    repository = Column(String, nullable=False)
    pr_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    author_avatar_url = Column(String, nullable=True)
    labels = Column(String, nullable=True)
    checks_status = Column(String, nullable=True)
    html_url = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    cached_at = Column(DateTime, default=lambda: datetime.now(UTC))
    __table_args__ = (UniqueConstraint("schedule_id", "organization", "repository", "pr_number"),)


@pytest.fixture
def encryption_key():
    """Generate a test encryption key."""
    return generate_encryption_key()


@pytest.fixture
def db_session(encryption_key, monkeypatch):
    """Create an in-memory database with test data."""
    # Set environment variables
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("ENCRYPTION_KEY", encryption_key)
    monkeypatch.setenv("SMTP2GO_HOST", "mail.smtp2go.com")
    monkeypatch.setenv("SMTP2GO_USERNAME", "test")
    monkeypatch.setenv("SMTP2GO_PASSWORD", "test")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "test@example.com")

    # Clear cached settings
    from pr_review_scheduler.config import get_settings
    get_settings.cache_clear()

    # Create engine and tables
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Create test user
    user = User(
        id="user-123",
        github_username="testuser",
        github_access_token=encrypt_token("oauth-token", encryption_key),
        email="test@example.com",
    )
    session.add(user)

    # Create active schedule with repositories
    active_schedule = NotificationSchedule(
        id="schedule-active-1",
        user_id="user-123",
        name="Daily PR Check",
        cron_expression="0 9 * * 1-5",
        github_pat=encrypt_token("ghp_active_pat_123", encryption_key),
        is_active=True,
    )
    active_schedule.repositories.append(
        ScheduleRepository(organization="my-org", repository="repo-1")
    )
    active_schedule.repositories.append(
        ScheduleRepository(organization="my-org", repository="repo-2")
    )
    session.add(active_schedule)

    # Create inactive schedule
    inactive_schedule = NotificationSchedule(
        id="schedule-inactive-1",
        user_id="user-123",
        name="Disabled Schedule",
        cron_expression="0 10 * * *",
        github_pat=encrypt_token("ghp_inactive_pat", encryption_key),
        is_active=False,
    )
    session.add(inactive_schedule)

    session.commit()

    yield session, engine, encryption_key

    session.close()


def test_get_active_schedules(db_session, monkeypatch):
    """Test fetching active schedules with repositories."""
    session, engine, encryption_key = db_session

    # Patch the database module to use our test engine
    from pr_review_scheduler.services import database as db_module
    monkeypatch.setattr(db_module, "_get_engine", lambda: engine)

    from pr_review_scheduler.services.database import get_active_schedules

    schedules = get_active_schedules()

    assert len(schedules) == 1
    schedule = schedules[0]
    assert schedule["id"] == "schedule-active-1"
    assert schedule["name"] == "Daily PR Check"
    assert schedule["cron_expression"] == "0 9 * * 1-5"
    assert schedule["user_id"] == "user-123"
    assert schedule["user_email"] == "test@example.com"
    # PAT should be decrypted
    assert schedule["github_pat"] == "ghp_active_pat_123"
    # Repositories should be included
    assert len(schedule["repositories"]) == 2
    repo_names = [(r["organization"], r["repository"]) for r in schedule["repositories"]]
    assert ("my-org", "repo-1") in repo_names
    assert ("my-org", "repo-2") in repo_names


def test_get_schedule_by_id(db_session, monkeypatch):
    """Test fetching a specific schedule by ID."""
    session, engine, encryption_key = db_session

    from pr_review_scheduler.services import database as db_module
    monkeypatch.setattr(db_module, "_get_engine", lambda: engine)

    from pr_review_scheduler.services.database import get_schedule_by_id

    # Existing schedule
    schedule = get_schedule_by_id("schedule-active-1")
    assert schedule is not None
    assert schedule["name"] == "Daily PR Check"

    # Non-existent schedule
    schedule = get_schedule_by_id("nonexistent")
    assert schedule is None


def test_get_user_email(db_session, monkeypatch):
    """Test fetching user email address."""
    session, engine, encryption_key = db_session

    from pr_review_scheduler.services import database as db_module
    monkeypatch.setattr(db_module, "_get_engine", lambda: engine)

    from pr_review_scheduler.services.database import get_user_email

    email = get_user_email("user-123")
    assert email == "test@example.com"

    email = get_user_email("nonexistent")
    assert email is None


def test_get_all_schedule_ids(db_session, monkeypatch):
    """Test fetching all schedule IDs (active and inactive)."""
    session, engine, encryption_key = db_session

    from pr_review_scheduler.services import database as db_module
    monkeypatch.setattr(db_module, "_get_engine", lambda: engine)

    from pr_review_scheduler.services.database import get_all_schedule_ids

    ids = get_all_schedule_ids()
    assert "schedule-active-1" in ids
    assert "schedule-inactive-1" in ids
```

**Step 3: Run test to verify it fails**

Run: `cd apps/scheduler && pytest tests/test_services/test_database.py -v`
Expected: FAIL (functions not implemented)

**Step 4: Write the implementation**

```python
# apps/scheduler/src/pr_review_scheduler/services/database.py
"""Database service for the scheduler.

This module provides functions for querying schedules and caching PR data.
"""

import logging
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from pr_review_scheduler.config import get_settings
from pr_review_shared.encryption import decrypt_token

logger = logging.getLogger(__name__)

# Database models (mirrors web-be models for read access)
Base = declarative_base()


class User(Base):
    """User model for reading user data."""

    __tablename__ = "users"
    id = Column(String, primary_key=True)
    github_username = Column(String, nullable=False)
    github_access_token = Column(String, nullable=False)
    email = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class NotificationSchedule(Base):
    """Schedule model for reading schedule data."""

    __tablename__ = "notification_schedules"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    cron_expression = Column(String, nullable=False)
    github_pat = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    repositories = relationship("ScheduleRepository", back_populates="schedule")
    user = relationship("User")


class ScheduleRepository(Base):
    """Repository model for reading repository associations."""

    __tablename__ = "schedule_repositories"
    id = Column(String, primary_key=True)
    schedule_id = Column(String, ForeignKey("notification_schedules.id", ondelete="CASCADE"), nullable=False)
    organization = Column(String, nullable=False)
    repository = Column(String, nullable=False)
    schedule = relationship("NotificationSchedule", back_populates="repositories")
    __table_args__ = (UniqueConstraint("schedule_id", "organization", "repository"),)


class CachedPullRequest(Base):
    """Cached PR model for storing/reading PR data."""

    __tablename__ = "cached_pull_requests"
    id = Column(String, primary_key=True)
    schedule_id = Column(String, ForeignKey("notification_schedules.id", ondelete="CASCADE"), nullable=False)
    organization = Column(String, nullable=False)
    repository = Column(String, nullable=False)
    pr_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    author_avatar_url = Column(String, nullable=True)
    labels = Column(String, nullable=True)
    checks_status = Column(String, nullable=True)
    html_url = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    cached_at = Column(DateTime)
    __table_args__ = (UniqueConstraint("schedule_id", "organization", "repository", "pr_number"),)


# Engine caching
_engine = None


def _get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(settings.database_url, connect_args=connect_args, echo=False)
    return _engine


def _get_session() -> Session:
    """Get a new database session."""
    engine = _get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def get_active_schedules() -> list[dict[str, Any]]:
    """Get all active notification schedules from the database.

    Returns:
        List of active schedule dictionaries with decrypted PATs.
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
            except Exception as e:
                logger.error("Failed to decrypt PAT for schedule %s: %s", schedule.id, e)
                continue

            result.append({
                "id": schedule.id,
                "user_id": schedule.user_id,
                "user_email": schedule.user.email if schedule.user else None,
                "name": schedule.name,
                "cron_expression": schedule.cron_expression,
                "github_pat": decrypted_pat,
                "is_active": schedule.is_active,
                "repositories": [
                    {"organization": repo.organization, "repository": repo.repository}
                    for repo in schedule.repositories
                ],
            })

        logger.info("Found %d active schedules", len(result))
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
    settings = get_settings()
    logger.debug("Fetching schedule: %s", schedule_id)

    session = _get_session()
    try:
        schedule = session.query(NotificationSchedule).filter_by(id=schedule_id).first()
        if not schedule:
            return None

        try:
            decrypted_pat = decrypt_token(schedule.github_pat, settings.encryption_key)
        except Exception as e:
            logger.error("Failed to decrypt PAT for schedule %s: %s", schedule_id, e)
            return None

        return {
            "id": schedule.id,
            "user_id": schedule.user_id,
            "user_email": schedule.user.email if schedule.user else None,
            "name": schedule.name,
            "cron_expression": schedule.cron_expression,
            "github_pat": decrypted_pat,
            "is_active": schedule.is_active,
            "repositories": [
                {"organization": repo.organization, "repository": repo.repository}
                for repo in schedule.repositories
            ],
        }
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
        user = session.query(User).filter_by(id=user_id).first()
        return user.email if user else None
    finally:
        session.close()


def get_all_schedule_ids() -> set[str]:
    """Get all schedule IDs (active and inactive).

    Returns:
        Set of all schedule IDs.
    """
    session = _get_session()
    try:
        schedules = session.query(NotificationSchedule.id).all()
        return {s.id for s in schedules}
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
        pull_requests: List of PR data to cache.
    """
    logger.debug("Caching %d PRs for schedule: %s", len(pull_requests), schedule_id)

    # Implementation in Task 6.6
    pass
```

**Step 5: Run test to verify it passes**

Run: `cd apps/scheduler && pytest tests/test_services/test_database.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add apps/scheduler/src/pr_review_scheduler/services/database.py apps/scheduler/tests/test_services/
git commit -m "feat(scheduler): implement database service for schedule loading (Task 6.2)"
```

---

## Task 6.3: Implement PR Fetching Job

**Goal:** Create the notification job that fetches PRs from GitHub and prepares email.

**Files:**
- Modify: `apps/scheduler/src/pr_review_scheduler/services/github.py`
- Modify: `apps/scheduler/src/pr_review_scheduler/jobs/pr_notification.py`
- Test: `apps/scheduler/tests/test_services/test_github.py`
- Test: `apps/scheduler/tests/test_jobs/test_pr_notification.py`

**Step 1: Write the failing test for GitHub service**

```python
# apps/scheduler/tests/test_services/test_github.py
"""Tests for GitHub API service."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch

from pr_review_scheduler.services.github import (
    get_repository_pull_requests,
    get_pull_request_checks,
)


@pytest.mark.asyncio
async def test_get_repository_pull_requests():
    """Test fetching open pull requests for a repository."""
    mock_prs = [
        {
            "number": 1,
            "title": "Add feature X",
            "user": {"login": "user1", "avatar_url": "https://avatar1.png"},
            "labels": [{"name": "enhancement", "color": "84b6eb"}],
            "html_url": "https://github.com/org/repo/pull/1",
            "created_at": "2024-01-10T08:00:00Z",
            "head": {"sha": "abc123"},
        },
        {
            "number": 2,
            "title": "Fix bug Y",
            "user": {"login": "user2", "avatar_url": "https://avatar2.png"},
            "labels": [],
            "html_url": "https://github.com/org/repo/pull/2",
            "created_at": "2024-01-11T09:00:00Z",
            "head": {"sha": "def456"},
        },
    ]

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock PR list response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_prs
        mock_response.raise_for_status = AsyncMock()
        mock_client.get.return_value = mock_response

        prs = await get_repository_pull_requests("test-token", "my-org", "my-repo")

        assert len(prs) == 2
        assert prs[0]["number"] == 1
        assert prs[0]["title"] == "Add feature X"
        assert prs[0]["author"] == "user1"
        assert prs[0]["author_avatar_url"] == "https://avatar1.png"
        assert prs[0]["html_url"] == "https://github.com/org/repo/pull/1"


@pytest.mark.asyncio
async def test_get_repository_pull_requests_empty():
    """Test fetching PRs returns empty list when none exist."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.raise_for_status = AsyncMock()
        mock_client.get.return_value = mock_response

        prs = await get_repository_pull_requests("test-token", "my-org", "my-repo")

        assert prs == []


@pytest.mark.asyncio
async def test_get_repository_pull_requests_handles_error():
    """Test that API errors are handled gracefully."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=None, response=mock_response
        )
        mock_client.get.return_value = mock_response

        prs = await get_repository_pull_requests("test-token", "my-org", "my-repo")

        # Should return empty list on error, not raise
        assert prs == []


@pytest.mark.asyncio
async def test_get_pull_request_checks_pass():
    """Test fetching checks status - all pass."""
    mock_checks = {
        "check_runs": [
            {"status": "completed", "conclusion": "success"},
            {"status": "completed", "conclusion": "success"},
        ]
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_checks
        mock_response.raise_for_status = AsyncMock()
        mock_client.get.return_value = mock_response

        status = await get_pull_request_checks("token", "org", "repo", "sha123")

        assert status == "pass"


@pytest.mark.asyncio
async def test_get_pull_request_checks_fail():
    """Test fetching checks status - one failure."""
    mock_checks = {
        "check_runs": [
            {"status": "completed", "conclusion": "success"},
            {"status": "completed", "conclusion": "failure"},
        ]
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_checks
        mock_response.raise_for_status = AsyncMock()
        mock_client.get.return_value = mock_response

        status = await get_pull_request_checks("token", "org", "repo", "sha123")

        assert status == "fail"


@pytest.mark.asyncio
async def test_get_pull_request_checks_pending():
    """Test fetching checks status - some pending."""
    mock_checks = {
        "check_runs": [
            {"status": "completed", "conclusion": "success"},
            {"status": "in_progress", "conclusion": None},
        ]
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_checks
        mock_response.raise_for_status = AsyncMock()
        mock_client.get.return_value = mock_response

        status = await get_pull_request_checks("token", "org", "repo", "sha123")

        assert status == "pending"
```

**Step 2: Run test to verify it fails**

Run: `cd apps/scheduler && pytest tests/test_services/test_github.py -v`
Expected: FAIL

**Step 3: Write the GitHub service implementation**

```python
# apps/scheduler/src/pr_review_scheduler/services/github.py
"""GitHub API service for the scheduler.

This module provides functions for fetching pull request data from GitHub.
"""

import json
import logging
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _get_headers(access_token: str) -> dict[str, str]:
    """Build headers for GitHub API requests."""
    return {
        **GITHUB_HEADERS,
        "Authorization": f"Bearer {access_token}",
    }


async def get_repository_pull_requests(
    access_token: str,
    organization: str,
    repository: str,
) -> list[dict[str, Any]]:
    """Fetch open pull requests for a repository.

    Args:
        access_token: GitHub Personal Access Token.
        organization: GitHub organization name.
        repository: Repository name.

    Returns:
        List of pull request data dictionaries.
    """
    logger.info("Fetching PRs for %s/%s", organization, repository)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{organization}/{repository}/pulls",
                headers=_get_headers(access_token),
                params={"state": "open", "per_page": 100},
            )
            response.raise_for_status()
            prs_data = response.json()

            result = []
            for pr in prs_data:
                # Get check status for this PR
                checks_status = await get_pull_request_checks(
                    access_token, organization, repository, pr["head"]["sha"]
                )

                result.append({
                    "number": pr["number"],
                    "title": pr["title"],
                    "author": pr["user"]["login"],
                    "author_avatar_url": pr["user"].get("avatar_url"),
                    "labels": json.dumps([
                        {"name": label["name"], "color": label["color"]}
                        for label in pr.get("labels", [])
                    ]),
                    "checks_status": checks_status,
                    "html_url": pr["html_url"],
                    "created_at": datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00")),
                    "organization": organization,
                    "repository": repository,
                })

            logger.info("Found %d open PRs for %s/%s", len(result), organization, repository)
            return result

    except httpx.HTTPStatusError as e:
        logger.error("GitHub API error for %s/%s: %s", organization, repository, e)
        return []
    except Exception as e:
        logger.error("Error fetching PRs for %s/%s: %s", organization, repository, e)
        return []


async def get_pull_request_checks(
    access_token: str,
    organization: str,
    repository: str,
    sha: str,
) -> str:
    """Get the checks status for a commit.

    Args:
        access_token: GitHub Personal Access Token.
        organization: GitHub organization name.
        repository: Repository name.
        sha: Commit SHA to check.

    Returns:
        Checks status: 'pass', 'fail', or 'pending'.
    """
    logger.debug("Fetching checks for %s/%s@%s", organization, repository, sha[:7])

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{organization}/{repository}/commits/{sha}/check-runs",
                headers=_get_headers(access_token),
            )
            response.raise_for_status()

            data = response.json()
            check_runs = data.get("check_runs", [])

            if not check_runs:
                return "pending"

            has_failure = False
            has_pending = False

            for check in check_runs:
                status = check.get("status")
                conclusion = check.get("conclusion")

                if status != "completed":
                    has_pending = True
                elif conclusion in ("failure", "cancelled", "timed_out"):
                    has_failure = True

            if has_failure:
                return "fail"
            if has_pending:
                return "pending"
            return "pass"

    except httpx.HTTPStatusError:
        logger.warning("Could not fetch check status for %s/%s@%s", organization, repository, sha[:7])
        return "pending"
    except Exception as e:
        logger.error("Error fetching checks: %s", e)
        return "pending"
```

**Step 4: Run test to verify GitHub service passes**

Run: `cd apps/scheduler && pytest tests/test_services/test_github.py -v`
Expected: PASS

**Step 5: Write the failing test for notification job**

```python
# apps/scheduler/tests/test_jobs/__init__.py
"""Test jobs package."""
```

```python
# apps/scheduler/tests/test_jobs/test_pr_notification.py
"""Tests for PR notification job."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from pr_review_scheduler.jobs.pr_notification import run_notification_job


@pytest.fixture
def mock_schedule():
    """Create a mock schedule."""
    return {
        "id": "schedule-123",
        "user_id": "user-456",
        "user_email": "test@example.com",
        "name": "Daily PR Check",
        "cron_expression": "0 9 * * 1-5",
        "github_pat": "ghp_test_token_123",
        "is_active": True,
        "repositories": [
            {"organization": "my-org", "repository": "repo-1"},
            {"organization": "my-org", "repository": "repo-2"},
        ],
    }


@pytest.fixture
def mock_prs():
    """Create mock PR data."""
    return [
        {
            "number": 1,
            "title": "Add feature",
            "author": "user1",
            "author_avatar_url": "https://avatar.png",
            "labels": "[]",
            "checks_status": "pass",
            "html_url": "https://github.com/org/repo/pull/1",
            "created_at": datetime.now(UTC),
            "organization": "my-org",
            "repository": "repo-1",
        },
    ]


def test_run_notification_job_with_prs(mock_schedule, mock_prs, monkeypatch):
    """Test job sends email when PRs are found."""
    monkeypatch.setenv("APPLICATION_URL", "http://localhost:5173")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-key")
    monkeypatch.setenv("SMTP2GO_HOST", "mail.smtp2go.com")
    monkeypatch.setenv("SMTP2GO_USERNAME", "test")
    monkeypatch.setenv("SMTP2GO_PASSWORD", "test")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "test@example.com")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    # Clear cached settings
    from pr_review_scheduler.config import get_settings
    get_settings.cache_clear()

    with patch("pr_review_scheduler.jobs.pr_notification.get_schedule_by_id") as mock_get_schedule, \
         patch("pr_review_scheduler.jobs.pr_notification.get_repository_pull_requests") as mock_get_prs, \
         patch("pr_review_scheduler.jobs.pr_notification.cache_pull_requests") as mock_cache, \
         patch("pr_review_scheduler.jobs.pr_notification.send_notification_email") as mock_send_email, \
         patch("pr_review_scheduler.jobs.pr_notification.format_pr_summary_email") as mock_format:

        mock_get_schedule.return_value = mock_schedule
        mock_get_prs.return_value = mock_prs
        mock_format.return_value = ("[PR-Review] Summary", "Email body")
        mock_send_email.return_value = True

        # Run the job (need to handle async)
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            run_notification_job.__wrapped__("schedule-123")
        ) if hasattr(run_notification_job, '__wrapped__') else run_notification_job("schedule-123")

        # Verify schedule was loaded
        mock_get_schedule.assert_called_once_with("schedule-123")

        # Verify PRs were fetched for each repo
        assert mock_get_prs.call_count == 2

        # Verify email was sent
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert call_args[0][0] == "test@example.com"


def test_run_notification_job_no_prs(mock_schedule, monkeypatch):
    """Test job does not send email when no PRs found."""
    monkeypatch.setenv("APPLICATION_URL", "http://localhost:5173")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-key")
    monkeypatch.setenv("SMTP2GO_HOST", "mail.smtp2go.com")
    monkeypatch.setenv("SMTP2GO_USERNAME", "test")
    monkeypatch.setenv("SMTP2GO_PASSWORD", "test")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "test@example.com")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    from pr_review_scheduler.config import get_settings
    get_settings.cache_clear()

    with patch("pr_review_scheduler.jobs.pr_notification.get_schedule_by_id") as mock_get_schedule, \
         patch("pr_review_scheduler.jobs.pr_notification.get_repository_pull_requests") as mock_get_prs, \
         patch("pr_review_scheduler.jobs.pr_notification.send_notification_email") as mock_send_email:

        mock_get_schedule.return_value = mock_schedule
        mock_get_prs.return_value = []  # No PRs

        run_notification_job("schedule-123")

        # Verify email was NOT sent
        mock_send_email.assert_not_called()


def test_run_notification_job_schedule_not_found(monkeypatch):
    """Test job handles missing schedule gracefully."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-key")
    monkeypatch.setenv("SMTP2GO_HOST", "mail.smtp2go.com")
    monkeypatch.setenv("SMTP2GO_USERNAME", "test")
    monkeypatch.setenv("SMTP2GO_PASSWORD", "test")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "test@example.com")

    from pr_review_scheduler.config import get_settings
    get_settings.cache_clear()

    with patch("pr_review_scheduler.jobs.pr_notification.get_schedule_by_id") as mock_get_schedule:
        mock_get_schedule.return_value = None

        # Should not raise
        run_notification_job("nonexistent-schedule")


def test_run_notification_job_no_email(mock_schedule, mock_prs, monkeypatch):
    """Test job handles missing user email gracefully."""
    monkeypatch.setenv("APPLICATION_URL", "http://localhost:5173")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-key")
    monkeypatch.setenv("SMTP2GO_HOST", "mail.smtp2go.com")
    monkeypatch.setenv("SMTP2GO_USERNAME", "test")
    monkeypatch.setenv("SMTP2GO_PASSWORD", "test")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "test@example.com")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    from pr_review_scheduler.config import get_settings
    get_settings.cache_clear()

    schedule_no_email = {**mock_schedule, "user_email": None}

    with patch("pr_review_scheduler.jobs.pr_notification.get_schedule_by_id") as mock_get_schedule, \
         patch("pr_review_scheduler.jobs.pr_notification.get_repository_pull_requests") as mock_get_prs, \
         patch("pr_review_scheduler.jobs.pr_notification.send_notification_email") as mock_send_email:

        mock_get_schedule.return_value = schedule_no_email
        mock_get_prs.return_value = mock_prs

        run_notification_job("schedule-123")

        # Email should NOT be sent when user has no email
        mock_send_email.assert_not_called()
```

**Step 6: Write the notification job implementation**

```python
# apps/scheduler/src/pr_review_scheduler/jobs/pr_notification.py
"""Pull Request notification job.

This module contains the job that fetches open PRs and sends notification emails.
"""

import asyncio
import logging
from typing import Any

from pr_review_scheduler.config import get_settings
from pr_review_scheduler.services.database import (
    cache_pull_requests,
    get_schedule_by_id,
)
from pr_review_scheduler.services.email import (
    format_pr_summary_email,
    send_notification_email,
)
from pr_review_scheduler.services.github import get_repository_pull_requests

logger = logging.getLogger(__name__)


def run_notification_job(schedule_id: str) -> None:
    """Execute the PR notification job for a schedule.

    This job:
    1. Loads the schedule from the database
    2. Fetches open PRs for each repository in the schedule
    3. Caches the PR data in the database
    4. Sends a summary email if there are open PRs

    Args:
        schedule_id: The ID of the schedule to process.
    """
    logger.info("Running notification job for schedule: %s", schedule_id)

    # Load schedule from database
    schedule = get_schedule_by_id(schedule_id)
    if not schedule:
        logger.error("Schedule not found: %s", schedule_id)
        return

    # Get settings
    settings = get_settings()
    github_pat = schedule["github_pat"]
    repositories = schedule["repositories"]
    user_email = schedule["user_email"]

    # Fetch PRs for each repository
    all_prs: list[dict[str, Any]] = []
    repo_pr_counts: dict[str, int] = {}

    for repo in repositories:
        org = repo["organization"]
        repo_name = repo["repository"]
        full_name = f"{org}/{repo_name}"

        try:
            # Run async function in sync context
            prs = asyncio.get_event_loop().run_until_complete(
                get_repository_pull_requests(github_pat, org, repo_name)
            )

            if prs:
                all_prs.extend(prs)
                repo_pr_counts[full_name] = len(prs)
                logger.info("Found %d PRs for %s", len(prs), full_name)
            else:
                logger.info("No open PRs for %s", full_name)
        except Exception as e:
            logger.error("Error fetching PRs for %s: %s", full_name, e)

    # Cache PRs in database
    if all_prs:
        try:
            cache_pull_requests(schedule_id, all_prs)
        except Exception as e:
            logger.error("Error caching PRs: %s", e)

    # Send email if PRs found and user has email configured
    if all_prs and user_email:
        try:
            subject, body = format_pr_summary_email(repo_pr_counts, settings.application_url)
            success = send_notification_email(user_email, subject, body)
            if success:
                logger.info("Sent notification email to %s", user_email)
            else:
                logger.error("Failed to send notification email to %s", user_email)
        except Exception as e:
            logger.error("Error sending email: %s", e)
    elif all_prs and not user_email:
        logger.warning("PRs found but user has no email configured for schedule %s", schedule_id)
    else:
        logger.info("No open PRs found for schedule %s, skipping email", schedule_id)

    logger.info("Notification job completed for schedule: %s", schedule_id)
```

**Step 7: Run tests to verify notification job passes**

Run: `cd apps/scheduler && pytest tests/test_jobs/test_pr_notification.py -v`
Expected: PASS

**Step 8: Commit**

```bash
git add apps/scheduler/src/pr_review_scheduler/services/github.py \
        apps/scheduler/src/pr_review_scheduler/jobs/pr_notification.py \
        apps/scheduler/tests/test_services/test_github.py \
        apps/scheduler/tests/test_jobs/
git commit -m "feat(scheduler): implement PR fetching job and GitHub service (Task 6.3)"
```

---

## Task 6.4: Implement Email Sending via SMTP2GO

**Goal:** Implement the actual SMTP email sending functionality.

**Files:**
- Modify: `apps/scheduler/src/pr_review_scheduler/services/email.py`
- Test: `apps/scheduler/tests/test_services/test_email.py`

**Step 1: Write the failing test for email service**

```python
# apps/scheduler/tests/test_services/test_email.py
"""Tests for email service."""

import pytest
from unittest.mock import patch, MagicMock

from pr_review_scheduler.services.email import (
    format_pr_summary_email,
    send_notification_email,
)


def test_format_pr_summary_email():
    """Test email formatting."""
    repositories = {
        "org/repo-1": 3,
        "org/repo-2": 1,
    }
    application_url = "http://localhost:5173"

    subject, body = format_pr_summary_email(repositories, application_url)

    assert subject == "[PR-Review] Open Pull Requests Summary"
    assert "You have open pull requests that need attention." in body
    assert "org/repo-1: 3 open PRs" in body
    assert "org/repo-2: 1 open PR" in body  # Singular
    assert "View details: http://localhost:5173/" in body
    assert "http://localhost:5173/settings" in body


def test_format_pr_summary_email_single_pr():
    """Test email formatting with single PR."""
    repositories = {"org/repo": 1}

    subject, body = format_pr_summary_email(repositories, "http://test.com")

    assert "1 open PR" in body  # Singular
    assert "1 open PRs" not in body


def test_send_notification_email_success(monkeypatch):
    """Test successful email sending."""
    monkeypatch.setenv("SMTP2GO_HOST", "mail.smtp2go.com")
    monkeypatch.setenv("SMTP2GO_PORT", "587")
    monkeypatch.setenv("SMTP2GO_USERNAME", "test-user")
    monkeypatch.setenv("SMTP2GO_PASSWORD", "test-password")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "noreply@test.com")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-key")
    monkeypatch.setenv("APPLICATION_URL", "http://localhost:5173")

    from pr_review_scheduler.config import get_settings
    get_settings.cache_clear()

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = send_notification_email(
            "recipient@example.com",
            "Test Subject",
            "Test Body",
        )

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test-user", "test-password")
        mock_server.sendmail.assert_called_once()


def test_send_notification_email_smtp_error(monkeypatch):
    """Test email sending handles SMTP errors."""
    monkeypatch.setenv("SMTP2GO_HOST", "mail.smtp2go.com")
    monkeypatch.setenv("SMTP2GO_PORT", "587")
    monkeypatch.setenv("SMTP2GO_USERNAME", "test-user")
    monkeypatch.setenv("SMTP2GO_PASSWORD", "test-password")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "noreply@test.com")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-key")
    monkeypatch.setenv("APPLICATION_URL", "http://localhost:5173")

    from pr_review_scheduler.config import get_settings
    get_settings.cache_clear()

    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__.side_effect = Exception("Connection failed")

        result = send_notification_email(
            "recipient@example.com",
            "Test Subject",
            "Test Body",
        )

        assert result is False
```

**Step 2: Run test to verify it fails**

Run: `cd apps/scheduler && pytest tests/test_services/test_email.py -v`
Expected: FAIL

**Step 3: Write the email service implementation**

```python
# apps/scheduler/src/pr_review_scheduler/services/email.py
"""Email service for sending notifications via SMTP2GO.

This module provides functions for sending PR notification emails.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pr_review_scheduler.config import get_settings

logger = logging.getLogger(__name__)


def send_notification_email(
    to_address: str,
    subject: str,
    body: str,
) -> bool:
    """Send a notification email via SMTP2GO.

    Args:
        to_address: Recipient email address.
        subject: Email subject line.
        body: Email body content.

    Returns:
        True if email was sent successfully, False otherwise.
    """
    settings = get_settings()

    logger.info("Sending email to %s: %s", to_address, subject)

    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = settings.email_from_address
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Connect to SMTP server and send
        with smtplib.SMTP(settings.smtp2go_host, settings.smtp2go_port) as server:
            server.starttls()
            server.login(settings.smtp2go_username, settings.smtp2go_password)
            server.sendmail(
                settings.email_from_address,
                to_address,
                msg.as_string(),
            )

        logger.info("Email sent successfully to %s", to_address)
        return True

    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_address, e)
        return False


def format_pr_summary_email(
    repositories: dict[str, int],
    application_url: str,
) -> tuple[str, str]:
    """Format a PR summary notification email.

    Args:
        repositories: Dictionary mapping repo names to PR counts.
        application_url: Base URL of the application.

    Returns:
        Tuple of (subject, body) for the email.
    """
    subject = "[PR-Review] Open Pull Requests Summary"

    body_lines = [
        "You have open pull requests that need attention.",
        "",
        "Repository Summary:",
    ]

    for repo_name, pr_count in repositories.items():
        body_lines.append(f"- {repo_name}: {pr_count} open PR{'s' if pr_count != 1 else ''}")

    body_lines.extend(
        [
            "",
            f"View details: {application_url}/",
            "",
            "---",
            "This is an automated message from PR-Review.",
            f"To manage your notification settings, visit {application_url}/settings",
        ]
    )

    return subject, "\n".join(body_lines)
```

**Step 4: Run test to verify it passes**

Run: `cd apps/scheduler && pytest tests/test_services/test_email.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apps/scheduler/src/pr_review_scheduler/services/email.py \
        apps/scheduler/tests/test_services/test_email.py
git commit -m "feat(scheduler): implement SMTP2GO email sending (Task 6.4)"
```

---

## Task 6.5: Implement Schedule Change Polling

**Goal:** Add polling loop to detect schedule changes and update APScheduler jobs.

**Files:**
- Modify: `apps/scheduler/src/pr_review_scheduler/main.py`
- Create: `apps/scheduler/src/pr_review_scheduler/sync.py`
- Test: `apps/scheduler/tests/test_sync.py`

**Step 1: Write the failing test for sync module**

```python
# apps/scheduler/tests/test_sync.py
"""Tests for schedule synchronization."""

import pytest
from unittest.mock import MagicMock, patch

from pr_review_scheduler.sync import sync_schedules


@pytest.fixture
def mock_scheduler():
    """Create a mock scheduler."""
    scheduler = MagicMock()
    scheduler.get_jobs.return_value = []
    return scheduler


def test_sync_schedules_adds_new_jobs(mock_scheduler):
    """Test that new schedules are added as jobs."""
    schedules = [
        {
            "id": "schedule-1",
            "name": "Daily Check",
            "cron_expression": "0 9 * * 1-5",
            "is_active": True,
        },
    ]

    with patch("pr_review_scheduler.sync.get_active_schedules", return_value=schedules), \
         patch("pr_review_scheduler.sync.get_all_schedule_ids", return_value={"schedule-1"}), \
         patch("pr_review_scheduler.sync.add_notification_job") as mock_add:

        sync_schedules(mock_scheduler)

        mock_add.assert_called_once_with(mock_scheduler, "schedule-1", "0 9 * * 1-5")


def test_sync_schedules_removes_deleted_jobs(mock_scheduler):
    """Test that deleted schedules have their jobs removed."""
    mock_job = MagicMock()
    mock_job.id = "deleted-schedule"
    mock_scheduler.get_jobs.return_value = [mock_job]

    with patch("pr_review_scheduler.sync.get_active_schedules", return_value=[]), \
         patch("pr_review_scheduler.sync.get_all_schedule_ids", return_value=set()), \
         patch("pr_review_scheduler.sync.remove_job") as mock_remove:

        sync_schedules(mock_scheduler)

        mock_remove.assert_called_once_with(mock_scheduler, "deleted-schedule")


def test_sync_schedules_removes_inactive_jobs(mock_scheduler):
    """Test that inactive schedules have their jobs removed."""
    mock_job = MagicMock()
    mock_job.id = "inactive-schedule"
    mock_scheduler.get_jobs.return_value = [mock_job]

    # Schedule exists but is inactive
    with patch("pr_review_scheduler.sync.get_active_schedules", return_value=[]), \
         patch("pr_review_scheduler.sync.get_all_schedule_ids", return_value={"inactive-schedule"}), \
         patch("pr_review_scheduler.sync.remove_job") as mock_remove:

        sync_schedules(mock_scheduler)

        mock_remove.assert_called_once_with(mock_scheduler, "inactive-schedule")


def test_sync_schedules_updates_existing_jobs(mock_scheduler):
    """Test that existing jobs are updated if cron changed."""
    mock_job = MagicMock()
    mock_job.id = "schedule-1"
    mock_scheduler.get_jobs.return_value = [mock_job]

    schedules = [
        {
            "id": "schedule-1",
            "name": "Daily Check",
            "cron_expression": "0 10 * * 1-5",  # Changed from 9 to 10
            "is_active": True,
        },
    ]

    with patch("pr_review_scheduler.sync.get_active_schedules", return_value=schedules), \
         patch("pr_review_scheduler.sync.get_all_schedule_ids", return_value={"schedule-1"}), \
         patch("pr_review_scheduler.sync.add_notification_job") as mock_add:

        sync_schedules(mock_scheduler)

        # Should update (re-add) the job
        mock_add.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `cd apps/scheduler && pytest tests/test_sync.py -v`
Expected: FAIL

**Step 3: Write the sync module**

```python
# apps/scheduler/src/pr_review_scheduler/sync.py
"""Schedule synchronization module.

This module provides functionality to sync database schedules with APScheduler jobs.
"""

import logging
from typing import TYPE_CHECKING

from pr_review_scheduler.scheduler import add_notification_job, remove_job
from pr_review_scheduler.services.database import get_active_schedules, get_all_schedule_ids

if TYPE_CHECKING:
    from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


def sync_schedules(scheduler: "BackgroundScheduler") -> None:
    """Synchronize database schedules with APScheduler jobs.

    This function:
    1. Adds jobs for new active schedules
    2. Removes jobs for deleted schedules
    3. Removes jobs for deactivated schedules
    4. Updates jobs if cron expression changed

    Args:
        scheduler: The APScheduler instance.
    """
    logger.debug("Syncing schedules from database")

    # Get current state
    active_schedules = get_active_schedules()
    all_schedule_ids = get_all_schedule_ids()
    current_jobs = {job.id: job for job in scheduler.get_jobs()}

    # Track active schedule IDs for comparison
    active_schedule_ids = {s["id"] for s in active_schedules}

    # Add or update jobs for active schedules
    for schedule in active_schedules:
        schedule_id = schedule["id"]
        cron_expression = schedule["cron_expression"]

        if schedule_id not in current_jobs:
            # New schedule - add job
            logger.info("Adding new job for schedule: %s", schedule_id)
            add_notification_job(scheduler, schedule_id, cron_expression)
        else:
            # Existing job - update it (add_notification_job handles replacement)
            # This ensures cron changes are picked up
            add_notification_job(scheduler, schedule_id, cron_expression)

    # Remove jobs for deleted or deactivated schedules
    for job_id in current_jobs:
        if job_id not in all_schedule_ids:
            # Schedule was deleted
            logger.info("Removing job for deleted schedule: %s", job_id)
            remove_job(scheduler, job_id)
        elif job_id not in active_schedule_ids:
            # Schedule was deactivated
            logger.info("Removing job for inactive schedule: %s", job_id)
            remove_job(scheduler, job_id)

    logger.debug("Schedule sync complete. %d active jobs", len(scheduler.get_jobs()))
```

**Step 4: Run test to verify sync module passes**

Run: `cd apps/scheduler && pytest tests/test_sync.py -v`
Expected: PASS

**Step 5: Update main.py to include polling**

```python
# apps/scheduler/src/pr_review_scheduler/main.py
"""Main entry point for the PR-Review Scheduler.

This module starts the scheduler service and handles graceful shutdown.

Usage:
    python -m pr_review_scheduler.main
"""

import logging
import signal
import sys
import time
from threading import Event, Thread
from types import FrameType

from pr_review_scheduler import __version__
from pr_review_scheduler.config import get_settings
from pr_review_scheduler.scheduler import (
    create_scheduler,
    shutdown_scheduler,
    start_scheduler,
)
from pr_review_scheduler.sync import sync_schedules

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global scheduler instance for signal handlers
_scheduler = None
_stop_event = Event()


def signal_handler(signum: int, frame: FrameType | None) -> None:
    """Handle termination signals for graceful shutdown.

    Args:
        signum: Signal number received.
        frame: Current stack frame.
    """
    sig_name = signal.Signals(signum).name
    logger.info("Received signal %s, shutting down...", sig_name)
    _stop_event.set()
    if _scheduler:
        shutdown_scheduler(_scheduler, wait=True)
    sys.exit(0)


def polling_loop(scheduler, poll_interval: int) -> None:
    """Background thread that polls for schedule changes.

    Args:
        scheduler: The APScheduler instance.
        poll_interval: Seconds between polls.
    """
    logger.info("Starting schedule polling loop (interval: %ds)", poll_interval)
    while not _stop_event.is_set():
        try:
            sync_schedules(scheduler)
        except Exception as e:
            logger.error("Error syncing schedules: %s", e)

        # Wait for poll interval or until stop event
        _stop_event.wait(timeout=poll_interval)

    logger.info("Polling loop stopped")


def main() -> None:
    """Main entry point for the scheduler service."""
    global _scheduler

    settings = get_settings()

    logger.info("Starting PR-Review Scheduler v%s", __version__)
    logger.info("Database URL: %s", settings.database_url)
    logger.info("Poll interval: %d seconds", settings.schedule_poll_interval)

    # Create and start scheduler
    _scheduler = create_scheduler()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        start_scheduler(_scheduler)

        # Initial sync
        logger.info("Performing initial schedule sync...")
        sync_schedules(_scheduler)

        # Start polling thread
        poll_thread = Thread(
            target=polling_loop,
            args=(_scheduler, settings.schedule_poll_interval),
            daemon=True,
        )
        poll_thread.start()

        logger.info("Scheduler is running. Press Ctrl+C to exit.")

        # Keep the main thread alive
        while not _stop_event.is_set():
            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        _stop_event.set()
        shutdown_scheduler(_scheduler, wait=True)


if __name__ == "__main__":
    main()
```

**Step 6: Run all tests to verify everything works**

Run: `cd apps/scheduler && pytest -v`
Expected: PASS

**Step 7: Commit**

```bash
git add apps/scheduler/src/pr_review_scheduler/sync.py \
        apps/scheduler/src/pr_review_scheduler/main.py \
        apps/scheduler/tests/test_sync.py
git commit -m "feat(scheduler): implement schedule change polling (Task 6.5)"
```

---

## Task 6.6: Add PR Caching to Database

**Goal:** Implement storing fetched PRs in the cached_pull_requests table.

**Files:**
- Modify: `apps/scheduler/src/pr_review_scheduler/services/database.py`
- Test: `apps/scheduler/tests/test_services/test_database.py` (add cache tests)

**Step 1: Add failing tests for cache functionality**

Add to `apps/scheduler/tests/test_services/test_database.py`:

```python
def test_cache_pull_requests(db_session, monkeypatch):
    """Test caching PR data."""
    session, engine, encryption_key = db_session

    from pr_review_scheduler.services import database as db_module
    monkeypatch.setattr(db_module, "_get_engine", lambda: engine)

    from pr_review_scheduler.services.database import cache_pull_requests

    prs = [
        {
            "number": 1,
            "title": "Add feature",
            "author": "user1",
            "author_avatar_url": "https://avatar.png",
            "labels": '[{"name": "bug", "color": "red"}]',
            "checks_status": "pass",
            "html_url": "https://github.com/org/repo/pull/1",
            "created_at": datetime.now(UTC),
            "organization": "my-org",
            "repository": "repo-1",
        },
    ]

    cache_pull_requests("schedule-active-1", prs)

    # Verify data was cached
    cached = session.query(CachedPullRequest).filter_by(schedule_id="schedule-active-1").all()
    assert len(cached) == 1
    assert cached[0].pr_number == 1
    assert cached[0].title == "Add feature"


def test_cache_pull_requests_replaces_existing(db_session, monkeypatch):
    """Test that caching replaces existing cached PRs."""
    session, engine, encryption_key = db_session

    from pr_review_scheduler.services import database as db_module
    monkeypatch.setattr(db_module, "_get_engine", lambda: engine)

    from pr_review_scheduler.services.database import cache_pull_requests

    # Add initial PR
    initial_prs = [
        {
            "number": 1,
            "title": "Old PR",
            "author": "user1",
            "author_avatar_url": None,
            "labels": None,
            "checks_status": "pending",
            "html_url": "https://github.com/org/repo/pull/1",
            "created_at": datetime.now(UTC),
            "organization": "my-org",
            "repository": "repo-1",
        },
    ]
    cache_pull_requests("schedule-active-1", initial_prs)

    # Replace with new PR
    new_prs = [
        {
            "number": 2,
            "title": "New PR",
            "author": "user2",
            "author_avatar_url": None,
            "labels": None,
            "checks_status": "pass",
            "html_url": "https://github.com/org/repo/pull/2",
            "created_at": datetime.now(UTC),
            "organization": "my-org",
            "repository": "repo-1",
        },
    ]
    cache_pull_requests("schedule-active-1", new_prs)

    # Verify only new PR exists
    cached = session.query(CachedPullRequest).filter_by(schedule_id="schedule-active-1").all()
    assert len(cached) == 1
    assert cached[0].pr_number == 2
    assert cached[0].title == "New PR"
```

**Step 2: Run test to verify it fails**

Run: `cd apps/scheduler && pytest tests/test_services/test_database.py::test_cache_pull_requests -v`
Expected: FAIL

**Step 3: Implement cache_pull_requests**

Update the `cache_pull_requests` function in `apps/scheduler/src/pr_review_scheduler/services/database.py`:

```python
def cache_pull_requests(
    schedule_id: str,
    pull_requests: list[dict[str, Any]],
) -> None:
    """Cache fetched pull requests in the database.

    Replaces any existing cached PRs for the schedule.

    Args:
        schedule_id: The schedule ID.
        pull_requests: List of PR data to cache.
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
```

Also add the uuid import at the top of the file:

```python
from uuid import uuid4
```

**Step 4: Run test to verify it passes**

Run: `cd apps/scheduler && pytest tests/test_services/test_database.py -v`
Expected: PASS

**Step 5: Run all scheduler tests**

Run: `cd apps/scheduler && pytest -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add apps/scheduler/src/pr_review_scheduler/services/database.py \
        apps/scheduler/tests/test_services/test_database.py
git commit -m "feat(scheduler): implement PR caching to database (Task 6.6)"
```

---

## Final Integration Test

**Step 1: Run all scheduler tests with coverage**

```bash
cd apps/scheduler && pytest --cov=pr_review_scheduler --cov-report=term-missing -v
```

Expected: >90% coverage, all tests pass

**Step 2: Run linter**

```bash
cd apps/scheduler && ruff check .
```

Expected: No errors

**Step 3: Final commit for Phase 6**

```bash
git add -A
git commit -m "feat(scheduler): complete Phase 6 - Scheduler Service implementation"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 6.1 | APScheduler job management | `scheduler.py`, `test_scheduler.py` |
| 6.2 | Database service for schedules | `services/database.py`, `test_database.py` |
| 6.3 | PR fetching job + GitHub service | `services/github.py`, `jobs/pr_notification.py` |
| 6.4 | SMTP2GO email sending | `services/email.py`, `test_email.py` |
| 6.5 | Schedule change polling | `sync.py`, `main.py`, `test_sync.py` |
| 6.6 | PR caching to database | `services/database.py` (cache_pull_requests) |

**Test Commands:**
- Run all: `cd apps/scheduler && pytest -v`
- With coverage: `cd apps/scheduler && pytest --cov=pr_review_scheduler -v`
- Specific file: `cd apps/scheduler && pytest tests/test_scheduler.py -v`
