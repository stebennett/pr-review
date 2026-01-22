"""Tests for the database service."""

import pytest
from pr_review_shared.encryption import encrypt_token, generate_encryption_key
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from pr_review_scheduler.services import database


@pytest.fixture
def encryption_key() -> str:
    """Generate an encryption key for tests."""
    return generate_encryption_key()


@pytest.fixture
def test_engine():
    """Create an in-memory SQLite database engine with test schema."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # Create tables using the models defined in database.py
    database.Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create a session for the test database."""
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def setup_test_data(test_session: Session, encryption_key: str, monkeypatch):
    """Set up test data in the database."""
    # Monkeypatch the _get_engine function to return our test engine
    monkeypatch.setattr(
        "pr_review_scheduler.services.database._get_engine",
        lambda: test_session.get_bind(),
    )
    # Monkeypatch get_settings to return test encryption key
    from pr_review_scheduler.config import Settings

    test_settings = Settings(
        database_url="sqlite:///:memory:",
        encryption_key=encryption_key,
    )
    monkeypatch.setattr(
        "pr_review_scheduler.services.database.get_settings",
        lambda: test_settings,
    )

    # Create test user
    test_user = database.User(
        id="user-123",
        github_username="testuser",
        github_access_token="encrypted-token",
        email="testuser@example.com",
        avatar_url="https://github.com/testuser.png",
    )
    test_session.add(test_user)

    # Create active schedule with encrypted PAT
    encrypted_pat = encrypt_token("ghp_test_pat_12345", encryption_key)
    active_schedule = database.NotificationSchedule(
        id="schedule-active-1",
        user_id="user-123",
        name="Daily PR Review",
        cron_expression="0 9 * * 1-5",
        github_pat=encrypted_pat,
        is_active=True,
    )
    test_session.add(active_schedule)

    # Add repositories to active schedule
    repo1 = database.ScheduleRepository(
        id="repo-1",
        schedule_id="schedule-active-1",
        organization="myorg",
        repository="frontend",
    )
    repo2 = database.ScheduleRepository(
        id="repo-2",
        schedule_id="schedule-active-1",
        organization="myorg",
        repository="backend",
    )
    test_session.add_all([repo1, repo2])

    # Create inactive schedule
    encrypted_pat_inactive = encrypt_token("ghp_inactive_pat", encryption_key)
    inactive_schedule = database.NotificationSchedule(
        id="schedule-inactive-1",
        user_id="user-123",
        name="Weekly Review",
        cron_expression="0 10 * * 1",
        github_pat=encrypted_pat_inactive,
        is_active=False,
    )
    test_session.add(inactive_schedule)

    # Add repository to inactive schedule
    repo3 = database.ScheduleRepository(
        id="repo-3",
        schedule_id="schedule-inactive-1",
        organization="otherorg",
        repository="project",
    )
    test_session.add(repo3)

    test_session.commit()

    return {
        "user": test_user,
        "active_schedule": active_schedule,
        "inactive_schedule": inactive_schedule,
        "encryption_key": encryption_key,
    }


class TestGetActiveSchedules:
    """Tests for get_active_schedules function."""

    def test_get_active_schedules_returns_only_active(self, setup_test_data):
        """Verify that only active schedules are returned."""
        schedules = database.get_active_schedules()

        assert len(schedules) == 1
        assert schedules[0]["id"] == "schedule-active-1"
        assert schedules[0]["is_active"] is True

    def test_get_active_schedules_includes_decrypted_pat(self, setup_test_data):
        """Verify that the PAT is decrypted in the returned schedule."""
        schedules = database.get_active_schedules()

        assert len(schedules) == 1
        assert schedules[0]["github_pat"] == "ghp_test_pat_12345"

    def test_get_active_schedules_includes_repositories(self, setup_test_data):
        """Verify that repositories are included in the returned schedule."""
        schedules = database.get_active_schedules()

        assert len(schedules) == 1
        repositories = schedules[0]["repositories"]
        assert len(repositories) == 2

        # Check repository data structure
        repo_names = {(r["organization"], r["repository"]) for r in repositories}
        assert ("myorg", "frontend") in repo_names
        assert ("myorg", "backend") in repo_names

    def test_get_active_schedules_includes_user_email(self, setup_test_data):
        """Verify that user email is included in the returned schedule."""
        schedules = database.get_active_schedules()

        assert len(schedules) == 1
        assert schedules[0]["user_email"] == "testuser@example.com"

    def test_get_active_schedules_correct_structure(self, setup_test_data):
        """Verify the complete structure of returned schedule dictionaries."""
        schedules = database.get_active_schedules()

        assert len(schedules) == 1
        schedule = schedules[0]

        # Check all required keys are present
        required_keys = {
            "id",
            "user_id",
            "user_email",
            "name",
            "cron_expression",
            "github_pat",
            "is_active",
            "repositories",
        }
        assert set(schedule.keys()) >= required_keys

        # Check values
        assert schedule["id"] == "schedule-active-1"
        assert schedule["user_id"] == "user-123"
        assert schedule["user_email"] == "testuser@example.com"
        assert schedule["name"] == "Daily PR Review"
        assert schedule["cron_expression"] == "0 9 * * 1-5"
        assert schedule["is_active"] is True


class TestGetScheduleById:
    """Tests for get_schedule_by_id function."""

    def test_get_schedule_by_id_active(self, setup_test_data):
        """Verify that an active schedule can be retrieved by ID."""
        schedule = database.get_schedule_by_id("schedule-active-1")

        assert schedule is not None
        assert schedule["id"] == "schedule-active-1"
        assert schedule["name"] == "Daily PR Review"
        assert schedule["github_pat"] == "ghp_test_pat_12345"

    def test_get_schedule_by_id_inactive(self, setup_test_data):
        """Verify that an inactive schedule can be retrieved by ID."""
        schedule = database.get_schedule_by_id("schedule-inactive-1")

        assert schedule is not None
        assert schedule["id"] == "schedule-inactive-1"
        assert schedule["name"] == "Weekly Review"
        assert schedule["is_active"] is False

    def test_get_schedule_by_id_not_found(self, setup_test_data):
        """Verify that None is returned for non-existent schedule."""
        schedule = database.get_schedule_by_id("non-existent-id")

        assert schedule is None

    def test_get_schedule_by_id_includes_repositories(self, setup_test_data):
        """Verify that repositories are included when getting by ID."""
        schedule = database.get_schedule_by_id("schedule-active-1")

        assert schedule is not None
        assert len(schedule["repositories"]) == 2


class TestGetUserEmail:
    """Tests for get_user_email function."""

    def test_get_user_email_found(self, setup_test_data):
        """Verify that user email can be retrieved."""
        email = database.get_user_email("user-123")

        assert email == "testuser@example.com"

    def test_get_user_email_not_found(self, setup_test_data):
        """Verify that None is returned for non-existent user."""
        email = database.get_user_email("non-existent-user")

        assert email is None


class TestGetAllScheduleIds:
    """Tests for get_all_schedule_ids function."""

    def test_get_all_schedule_ids_returns_all(self, setup_test_data):
        """Verify that all schedule IDs are returned (active and inactive)."""
        schedule_ids = database.get_all_schedule_ids()

        assert len(schedule_ids) == 2
        assert "schedule-active-1" in schedule_ids
        assert "schedule-inactive-1" in schedule_ids


class TestDecryptionErrorHandling:
    """Tests for decryption error handling."""

    def test_get_active_schedules_skips_invalid_pat(
        self, test_session: Session, monkeypatch
    ):
        """Verify that schedules with invalid PATs are skipped gracefully."""
        # Monkeypatch engine
        monkeypatch.setattr(
            "pr_review_scheduler.services.database._get_engine",
            lambda: test_session.get_bind(),
        )

        # Generate a different encryption key for settings (wrong key)
        wrong_key = generate_encryption_key()
        from pr_review_scheduler.config import Settings

        test_settings = Settings(
            database_url="sqlite:///:memory:",
            encryption_key=wrong_key,
        )
        monkeypatch.setattr(
            "pr_review_scheduler.services.database.get_settings",
            lambda: test_settings,
        )

        # Create user
        test_user = database.User(
            id="user-456",
            github_username="baduser",
            github_access_token="token",
            email="bad@example.com",
        )
        test_session.add(test_user)

        # Create schedule with PAT encrypted with a different key
        correct_key = generate_encryption_key()
        encrypted_pat = encrypt_token("ghp_secret", correct_key)

        bad_schedule = database.NotificationSchedule(
            id="schedule-bad-pat",
            user_id="user-456",
            name="Bad PAT Schedule",
            cron_expression="0 8 * * *",
            github_pat=encrypted_pat,  # Encrypted with different key
            is_active=True,
        )
        test_session.add(bad_schedule)
        test_session.commit()

        # Should return empty list (skipped due to decryption error)
        schedules = database.get_active_schedules()
        assert all(s["id"] != "schedule-bad-pat" for s in schedules)
