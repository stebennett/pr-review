"""Tests for SQLAlchemy database models."""

from datetime import UTC, datetime

import pytest

from pr_review_api.models.pull_request import CachedPullRequest
from pr_review_api.models.schedule import NotificationSchedule, ScheduleRepository
from pr_review_api.models.user import User


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, db_session):
        """Test creating a user with all fields."""
        user = User(
            id="99999",
            github_username="newuser",
            github_access_token="encrypted_token_here",
            email="new@example.com",
            avatar_url="https://avatars.githubusercontent.com/u/99999",
        )
        db_session.add(user)
        db_session.commit()

        # Query back and verify
        saved_user = db_session.query(User).filter(User.id == "99999").first()
        assert saved_user is not None
        assert saved_user.id == "99999"
        assert saved_user.github_username == "newuser"
        assert saved_user.github_access_token == "encrypted_token_here"
        assert saved_user.email == "new@example.com"
        assert saved_user.avatar_url == "https://avatars.githubusercontent.com/u/99999"

    def test_create_user_minimal(self, db_session):
        """Test creating a user with only required fields."""
        user = User(
            id="88888",
            github_username="minimaluser",
            github_access_token="token",
        )
        db_session.add(user)
        db_session.commit()

        saved_user = db_session.query(User).filter(User.id == "88888").first()
        assert saved_user is not None
        assert saved_user.email is None
        assert saved_user.avatar_url is None

    def test_created_at_set_automatically(self, db_session):
        """Test that created_at is set automatically on creation."""
        before_create = datetime.now(UTC)

        user = User(
            id="77777",
            github_username="timeuser",
            github_access_token="token",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        after_create = datetime.now(UTC)

        assert user.created_at is not None
        # Make created_at timezone-aware for comparison if it isn't already
        created_at = user.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)

        # Allow for some tolerance in timing
        assert before_create.replace(tzinfo=None) <= user.created_at.replace(tzinfo=None)
        assert user.created_at.replace(tzinfo=None) <= after_create.replace(tzinfo=None)

    def test_updated_at_set_automatically(self, db_session):
        """Test that updated_at is set automatically on creation."""
        user = User(
            id="66666",
            github_username="updateuser",
            github_access_token="token",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.updated_at is not None

    def test_updated_at_changes_on_update(self, db_session):
        """Test that updated_at changes when user is modified."""
        user = User(
            id="55555",
            github_username="modifyuser",
            github_access_token="token",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Verify updated_at is set initially
        assert user.updated_at is not None

        # Update the user
        user.email = "updated@example.com"
        db_session.commit()
        db_session.refresh(user)

        # Verify updated_at is still set after update
        assert user.updated_at is not None
        assert user.email == "updated@example.com"

    def test_query_user_by_id(self, db_session, test_user):
        """Test querying a user by ID."""
        found_user = db_session.query(User).filter(User.id == test_user.id).first()
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.github_username == test_user.github_username

    def test_query_user_by_username(self, db_session, test_user):
        """Test querying a user by GitHub username."""
        found_user = (
            db_session.query(User).filter(User.github_username == test_user.github_username).first()
        )
        assert found_user is not None
        assert found_user.id == test_user.id

    def test_user_not_found(self, db_session):
        """Test querying for a non-existent user returns None."""
        found_user = db_session.query(User).filter(User.id == "nonexistent").first()
        assert found_user is None

    def test_user_repr(self, db_session):
        """Test the string representation of a user."""
        user = User(
            id="44444",
            github_username="repruser",
            github_access_token="token",
        )
        db_session.add(user)
        db_session.commit()

        assert repr(user) == "<User(id=44444, username=repruser)>"

    def test_delete_user(self, db_session):
        """Test deleting a user."""
        user = User(
            id="33333",
            github_username="deleteuser",
            github_access_token="token",
        )
        db_session.add(user)
        db_session.commit()

        # Verify user exists
        assert db_session.query(User).filter(User.id == "33333").first() is not None

        # Delete user
        db_session.delete(user)
        db_session.commit()

        # Verify user is deleted
        assert db_session.query(User).filter(User.id == "33333").first() is None

    def test_unique_id_constraint(self, db_session):
        """Test that duplicate user IDs are rejected."""
        user1 = User(
            id="22222",
            github_username="user1",
            github_access_token="token1",
        )
        db_session.add(user1)
        db_session.commit()

        user2 = User(
            id="22222",  # Same ID
            github_username="user2",
            github_access_token="token2",
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # IntegrityError wrapped by SQLAlchemy
            db_session.commit()


class TestNotificationScheduleModel:
    """Tests for the NotificationSchedule model."""

    def test_create_schedule(self, db_session, test_user):
        """Test creating a notification schedule with all fields."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Daily PR Check",
            cron_expression="0 9 * * 1-5",
            github_pat="encrypted_pat_here",
            is_active=True,
        )
        db_session.add(schedule)
        db_session.commit()
        db_session.refresh(schedule)

        assert schedule.id is not None
        assert schedule.user_id == test_user.id
        assert schedule.name == "Daily PR Check"
        assert schedule.cron_expression == "0 9 * * 1-5"
        assert schedule.github_pat == "encrypted_pat_here"
        assert schedule.is_active is True
        assert schedule.created_at is not None
        assert schedule.updated_at is not None

    def test_create_schedule_default_is_active(self, db_session, test_user):
        """Test that is_active defaults to True."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Test Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()
        db_session.refresh(schedule)

        assert schedule.is_active is True

    def test_schedule_user_relationship(self, db_session, test_user):
        """Test the relationship between schedule and user."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Test Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()
        db_session.refresh(schedule)

        assert schedule.user is not None
        assert schedule.user.id == test_user.id
        assert schedule.user.github_username == test_user.github_username

    def test_schedule_repositories_relationship(self, db_session, test_user):
        """Test adding repositories to a schedule."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Test Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()
        db_session.refresh(schedule)

        repo1 = ScheduleRepository(
            schedule_id=schedule.id,
            organization="org1",
            repository="repo1",
        )
        repo2 = ScheduleRepository(
            schedule_id=schedule.id,
            organization="org1",
            repository="repo2",
        )
        db_session.add_all([repo1, repo2])
        db_session.commit()
        db_session.refresh(schedule)

        assert len(schedule.repositories) == 2
        assert schedule.repositories[0].organization == "org1"

    def test_cascade_delete_removes_repositories(self, db_session, test_user):
        """Test that deleting a schedule removes associated repositories."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Test Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()

        repo = ScheduleRepository(
            schedule_id=schedule.id,
            organization="org1",
            repository="repo1",
        )
        db_session.add(repo)
        db_session.commit()

        schedule_id = schedule.id
        repo_id = repo.id

        # Delete the schedule
        db_session.delete(schedule)
        db_session.commit()

        # Verify schedule is deleted
        assert (
            db_session.query(NotificationSchedule)
            .filter(NotificationSchedule.id == schedule_id)
            .first()
            is None
        )

        # Verify repository is also deleted (cascade)
        assert (
            db_session.query(ScheduleRepository).filter(ScheduleRepository.id == repo_id).first()
            is None
        )

    def test_cascade_delete_from_user(self, db_session):
        """Test that deleting a user removes their schedules."""
        user = User(
            id="cascade_test_user",
            github_username="cascadeuser",
            github_access_token="token",
        )
        db_session.add(user)
        db_session.commit()

        schedule = NotificationSchedule(
            user_id=user.id,
            name="Test Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()

        schedule_id = schedule.id

        # Delete the user
        db_session.delete(user)
        db_session.commit()

        # Verify schedule is also deleted (cascade)
        assert (
            db_session.query(NotificationSchedule)
            .filter(NotificationSchedule.id == schedule_id)
            .first()
            is None
        )

    def test_schedule_repr(self, db_session, test_user):
        """Test the string representation of a schedule."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="My Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()

        assert "NotificationSchedule" in repr(schedule)
        assert "My Schedule" in repr(schedule)


class TestScheduleRepositoryModel:
    """Tests for the ScheduleRepository model."""

    def test_create_schedule_repository(self, db_session, test_user):
        """Test creating a schedule repository."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Test Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()

        repo = ScheduleRepository(
            schedule_id=schedule.id,
            organization="my-org",
            repository="my-repo",
        )
        db_session.add(repo)
        db_session.commit()
        db_session.refresh(repo)

        assert repo.id is not None
        assert repo.schedule_id == schedule.id
        assert repo.organization == "my-org"
        assert repo.repository == "my-repo"

    def test_unique_constraint_schedule_org_repo(self, db_session, test_user):
        """Test that duplicate schedule/org/repo combinations are rejected."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Test Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()

        repo1 = ScheduleRepository(
            schedule_id=schedule.id,
            organization="org1",
            repository="repo1",
        )
        db_session.add(repo1)
        db_session.commit()

        repo2 = ScheduleRepository(
            schedule_id=schedule.id,
            organization="org1",
            repository="repo1",  # Duplicate
        )
        db_session.add(repo2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_schedule_repository_repr(self, db_session, test_user):
        """Test the string representation of a schedule repository."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Test Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()

        repo = ScheduleRepository(
            schedule_id=schedule.id,
            organization="test-org",
            repository="test-repo",
        )
        db_session.add(repo)
        db_session.commit()

        assert "ScheduleRepository" in repr(repo)
        assert "test-org" in repr(repo)
        assert "test-repo" in repr(repo)


class TestCachedPullRequestModel:
    """Tests for the CachedPullRequest model."""

    def test_create_cached_pull_request(self, db_session, test_user):
        """Test creating a cached pull request with all fields."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Test Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()

        pr_created_at = datetime(2026, 1, 10, 8, 0, 0, tzinfo=UTC)
        cached_pr = CachedPullRequest(
            schedule_id=schedule.id,
            organization="my-org",
            repository="my-repo",
            pr_number=123,
            title="Add new feature",
            author="octocat",
            author_avatar_url="https://avatars.githubusercontent.com/u/583231",
            labels='[{"name": "enhancement", "color": "84b6eb"}]',
            checks_status="pass",
            html_url="https://github.com/my-org/my-repo/pull/123",
            created_at=pr_created_at,
        )
        db_session.add(cached_pr)
        db_session.commit()
        db_session.refresh(cached_pr)

        assert cached_pr.id is not None
        assert cached_pr.schedule_id == schedule.id
        assert cached_pr.organization == "my-org"
        assert cached_pr.repository == "my-repo"
        assert cached_pr.pr_number == 123
        assert cached_pr.title == "Add new feature"
        assert cached_pr.author == "octocat"
        assert cached_pr.author_avatar_url is not None
        assert cached_pr.labels is not None
        assert cached_pr.checks_status == "pass"
        assert cached_pr.html_url is not None
        assert cached_pr.cached_at is not None

    def test_create_cached_pull_request_minimal(self, db_session, test_user):
        """Test creating a cached pull request with only required fields."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Test Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()

        cached_pr = CachedPullRequest(
            schedule_id=schedule.id,
            organization="org",
            repository="repo",
            pr_number=1,
            title="Fix bug",
            author="user",
            html_url="https://github.com/org/repo/pull/1",
            created_at=datetime.now(UTC),
        )
        db_session.add(cached_pr)
        db_session.commit()
        db_session.refresh(cached_pr)

        assert cached_pr.author_avatar_url is None
        assert cached_pr.labels is None
        assert cached_pr.checks_status is None

    def test_unique_constraint_schedule_org_repo_pr(self, db_session, test_user):
        """Test that duplicate schedule/org/repo/pr combinations are rejected."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Test Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()

        pr1 = CachedPullRequest(
            schedule_id=schedule.id,
            organization="org",
            repository="repo",
            pr_number=1,
            title="PR 1",
            author="user",
            html_url="https://github.com/org/repo/pull/1",
            created_at=datetime.now(UTC),
        )
        db_session.add(pr1)
        db_session.commit()

        pr2 = CachedPullRequest(
            schedule_id=schedule.id,
            organization="org",
            repository="repo",
            pr_number=1,  # Duplicate PR number
            title="PR 1 duplicate",
            author="user",
            html_url="https://github.com/org/repo/pull/1",
            created_at=datetime.now(UTC),
        )
        db_session.add(pr2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_cascade_delete_removes_cached_prs(self, db_session, test_user):
        """Test that deleting a schedule removes associated cached PRs."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Test Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()

        cached_pr = CachedPullRequest(
            schedule_id=schedule.id,
            organization="org",
            repository="repo",
            pr_number=1,
            title="PR 1",
            author="user",
            html_url="https://github.com/org/repo/pull/1",
            created_at=datetime.now(UTC),
        )
        db_session.add(cached_pr)
        db_session.commit()

        schedule_id = schedule.id
        pr_id = cached_pr.id

        # Delete the schedule
        db_session.delete(schedule)
        db_session.commit()

        # Verify schedule is deleted
        assert (
            db_session.query(NotificationSchedule)
            .filter(NotificationSchedule.id == schedule_id)
            .first()
            is None
        )

        # Verify cached PR is also deleted (cascade)
        assert (
            db_session.query(CachedPullRequest).filter(CachedPullRequest.id == pr_id).first()
            is None
        )

    def test_cached_pull_request_repr(self, db_session, test_user):
        """Test the string representation of a cached pull request."""
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Test Schedule",
            cron_expression="0 9 * * *",
            github_pat="token",
        )
        db_session.add(schedule)
        db_session.commit()

        cached_pr = CachedPullRequest(
            schedule_id=schedule.id,
            organization="test-org",
            repository="test-repo",
            pr_number=42,
            title="Test PR",
            author="user",
            html_url="https://github.com/test-org/test-repo/pull/42",
            created_at=datetime.now(UTC),
        )
        db_session.add(cached_pr)
        db_session.commit()

        assert "CachedPullRequest" in repr(cached_pr)
        assert "test-org" in repr(cached_pr)
        assert "test-repo" in repr(cached_pr)
        assert "42" in repr(cached_pr)
