"""Tests for schedules CRUD endpoints."""

from pr_review_shared import decrypt_token, encrypt_token

from pr_review_api.config import get_settings
from pr_review_api.main import app
from pr_review_api.models.schedule import NotificationSchedule, ScheduleRepository


class TestListSchedules:
    """Tests for GET /api/schedules."""

    def test_requires_authentication(self, client):
        """Should return 401/403 without Authorization header."""
        response = client.get("/api/schedules")
        # FastAPI HTTPBearer returns 403 for missing credentials
        assert response.status_code in [401, 403]

    def test_returns_empty_list_for_new_user(
        self, client, test_user, auth_headers, test_settings
    ):
        """Should return empty list when user has no schedules."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        response = client.get("/api/schedules", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "schedules" in data["data"]
        assert data["data"]["schedules"] == []

    def test_returns_user_schedules(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return list of schedules belonging to the user."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Create schedules for the user
        encrypted_pat = encrypt_token("ghp_test_token", test_settings.encryption_key)
        schedule1 = NotificationSchedule(
            user_id=test_user.id,
            name="Daily Check",
            cron_expression="0 9 * * 1-5",
            github_pat=encrypted_pat,
            is_active=True,
        )
        schedule2 = NotificationSchedule(
            user_id=test_user.id,
            name="Weekly Check",
            cron_expression="0 9 * * 1",
            github_pat=encrypted_pat,
            is_active=False,
        )
        db_session.add(schedule1)
        db_session.add(schedule2)
        db_session.commit()

        # Add repositories to schedule1
        repo1 = ScheduleRepository(
            schedule_id=schedule1.id,
            organization="my-org",
            repository="my-repo",
        )
        db_session.add(repo1)
        db_session.commit()

        response = client.get("/api/schedules", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        schedules = data["data"]["schedules"]
        assert len(schedules) == 2

        # Verify schedule data (order may vary)
        schedule_names = {s["name"] for s in schedules}
        assert schedule_names == {"Daily Check", "Weekly Check"}

    def test_user_isolation(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should not return schedules belonging to other users."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Create a schedule for another user
        from pr_review_api.models.user import User

        other_user = User(
            id="99999",
            github_username="otheruser",
            github_access_token="encrypted_token",
            email="other@example.com",
        )
        db_session.add(other_user)
        db_session.commit()

        encrypted_pat = encrypt_token("ghp_test_token", test_settings.encryption_key)
        other_schedule = NotificationSchedule(
            user_id=other_user.id,
            name="Other User Schedule",
            cron_expression="0 9 * * *",
            github_pat=encrypted_pat,
        )
        db_session.add(other_schedule)
        db_session.commit()

        response = client.get("/api/schedules", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        schedules = data["data"]["schedules"]
        assert len(schedules) == 0


class TestCreateSchedule:
    """Tests for POST /api/schedules."""

    def test_requires_authentication(self, client):
        """Should return 401/403 without Authorization header."""
        response = client.post(
            "/api/schedules",
            json={
                "name": "Test Schedule",
                "cron_expression": "0 9 * * 1-5",
                "github_pat": "ghp_test",
                "repositories": [{"organization": "org", "repository": "repo"}],
            },
        )
        assert response.status_code in [401, 403]

    def test_creates_schedule_successfully(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should create a new schedule with encrypted PAT."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        response = client.post(
            "/api/schedules",
            headers=auth_headers,
            json={
                "name": "Daily PR Check",
                "cron_expression": "0 9 * * 1-5",
                "github_pat": "ghp_testtoken123",
                "repositories": [
                    {"organization": "my-org", "repository": "repo-1"},
                    {"organization": "my-org", "repository": "repo-2"},
                ],
                "is_active": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        schedule = data["data"]["schedule"]
        assert schedule["name"] == "Daily PR Check"
        assert schedule["cron_expression"] == "0 9 * * 1-5"
        assert schedule["is_active"] is True
        assert len(schedule["repositories"]) == 2
        assert "id" in schedule
        assert "created_at" in schedule
        assert "updated_at" in schedule

        # Verify PAT is not in response
        assert "github_pat" not in schedule

        # Verify PAT is encrypted in database
        db_schedule = (
            db_session.query(NotificationSchedule)
            .filter(NotificationSchedule.id == schedule["id"])
            .first()
        )
        assert db_schedule is not None
        decrypted_pat = decrypt_token(db_schedule.github_pat, test_settings.encryption_key)
        assert decrypted_pat == "ghp_testtoken123"

    def test_creates_schedule_with_default_is_active(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should default is_active to True if not provided."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        response = client.post(
            "/api/schedules",
            headers=auth_headers,
            json={
                "name": "Test Schedule",
                "cron_expression": "0 9 * * *",
                "github_pat": "ghp_test",
                "repositories": [{"organization": "org", "repository": "repo"}],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["schedule"]["is_active"] is True

    def test_validates_missing_required_fields(
        self, client, test_user, auth_headers, test_settings
    ):
        """Should return 422 for missing required fields."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Missing name
        response = client.post(
            "/api/schedules",
            headers=auth_headers,
            json={
                "cron_expression": "0 9 * * *",
                "github_pat": "ghp_test",
                "repositories": [{"organization": "org", "repository": "repo"}],
            },
        )
        assert response.status_code == 422

        # Missing cron_expression
        response = client.post(
            "/api/schedules",
            headers=auth_headers,
            json={
                "name": "Test",
                "github_pat": "ghp_test",
                "repositories": [{"organization": "org", "repository": "repo"}],
            },
        )
        assert response.status_code == 422

        # Missing github_pat
        response = client.post(
            "/api/schedules",
            headers=auth_headers,
            json={
                "name": "Test",
                "cron_expression": "0 9 * * *",
                "repositories": [{"organization": "org", "repository": "repo"}],
            },
        )
        assert response.status_code == 422

        # Missing repositories
        response = client.post(
            "/api/schedules",
            headers=auth_headers,
            json={
                "name": "Test",
                "cron_expression": "0 9 * * *",
                "github_pat": "ghp_test",
            },
        )
        assert response.status_code == 422

    def test_validates_empty_repositories(
        self, client, test_user, auth_headers, test_settings
    ):
        """Should return 422 for empty repositories list."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        response = client.post(
            "/api/schedules",
            headers=auth_headers,
            json={
                "name": "Test",
                "cron_expression": "0 9 * * *",
                "github_pat": "ghp_test",
                "repositories": [],
            },
        )
        assert response.status_code == 422


class TestGetSchedule:
    """Tests for GET /api/schedules/{id}."""

    def test_requires_authentication(self, client):
        """Should return 401/403 without Authorization header."""
        response = client.get("/api/schedules/some-id")
        assert response.status_code in [401, 403]

    def test_returns_schedule_by_id(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return a specific schedule by ID."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Create a schedule
        encrypted_pat = encrypt_token("ghp_test", test_settings.encryption_key)
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="My Schedule",
            cron_expression="0 9 * * 1-5",
            github_pat=encrypted_pat,
            is_active=True,
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

        response = client.get(f"/api/schedules/{schedule.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        result = data["data"]["schedule"]
        assert result["id"] == schedule.id
        assert result["name"] == "My Schedule"
        assert result["cron_expression"] == "0 9 * * 1-5"
        assert result["is_active"] is True
        assert len(result["repositories"]) == 1
        assert result["repositories"][0]["organization"] == "my-org"
        assert result["repositories"][0]["repository"] == "my-repo"

    def test_returns_404_for_nonexistent_schedule(
        self, client, test_user, auth_headers, test_settings
    ):
        """Should return 404 for schedule that doesn't exist."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        response = client.get("/api/schedules/nonexistent-id", headers=auth_headers)

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Schedule not found"

    def test_returns_404_for_other_users_schedule(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return 404 for schedule belonging to another user."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Create another user and their schedule
        from pr_review_api.models.user import User

        other_user = User(
            id="99999",
            github_username="otheruser",
            github_access_token="encrypted_token",
        )
        db_session.add(other_user)
        db_session.commit()

        encrypted_pat = encrypt_token("ghp_test", test_settings.encryption_key)
        other_schedule = NotificationSchedule(
            user_id=other_user.id,
            name="Other Schedule",
            cron_expression="0 9 * * *",
            github_pat=encrypted_pat,
        )
        db_session.add(other_schedule)
        db_session.commit()

        response = client.get(f"/api/schedules/{other_schedule.id}", headers=auth_headers)

        assert response.status_code == 404


class TestUpdateSchedule:
    """Tests for PUT /api/schedules/{id}."""

    def test_requires_authentication(self, client):
        """Should return 401/403 without Authorization header."""
        response = client.put(
            "/api/schedules/some-id",
            json={"name": "Updated Name"},
        )
        assert response.status_code in [401, 403]

    def test_updates_single_field(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should update only the provided field."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Create a schedule
        encrypted_pat = encrypt_token("ghp_original", test_settings.encryption_key)
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Original Name",
            cron_expression="0 9 * * 1-5",
            github_pat=encrypted_pat,
            is_active=True,
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

        response = client.put(
            f"/api/schedules/{schedule.id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()
        result = data["data"]["schedule"]
        assert result["name"] == "Updated Name"
        assert result["cron_expression"] == "0 9 * * 1-5"  # Unchanged
        assert result["is_active"] is True  # Unchanged
        assert len(result["repositories"]) == 1  # Unchanged

    def test_updates_all_fields(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should update all provided fields."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Create a schedule
        encrypted_pat = encrypt_token("ghp_original", test_settings.encryption_key)
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Original Name",
            cron_expression="0 9 * * 1-5",
            github_pat=encrypted_pat,
            is_active=True,
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

        response = client.put(
            f"/api/schedules/{schedule.id}",
            headers=auth_headers,
            json={
                "name": "Updated Name",
                "cron_expression": "0 10 * * *",
                "github_pat": "ghp_newtoken",
                "repositories": [
                    {"organization": "new-org", "repository": "new-repo"},
                ],
                "is_active": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        result = data["data"]["schedule"]
        assert result["name"] == "Updated Name"
        assert result["cron_expression"] == "0 10 * * *"
        assert result["is_active"] is False
        assert len(result["repositories"]) == 1
        assert result["repositories"][0]["organization"] == "new-org"
        assert result["repositories"][0]["repository"] == "new-repo"

        # Verify PAT is encrypted with new value
        db_session.refresh(schedule)
        decrypted_pat = decrypt_token(schedule.github_pat, test_settings.encryption_key)
        assert decrypted_pat == "ghp_newtoken"

    def test_updates_repositories_replaces_all(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should replace all repositories when repositories is provided."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Create a schedule with multiple repositories
        encrypted_pat = encrypt_token("ghp_test", test_settings.encryption_key)
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="Test",
            cron_expression="0 9 * * *",
            github_pat=encrypted_pat,
        )
        db_session.add(schedule)
        db_session.commit()

        for i in range(3):
            repo = ScheduleRepository(
                schedule_id=schedule.id,
                organization=f"org-{i}",
                repository=f"repo-{i}",
            )
            db_session.add(repo)
        db_session.commit()

        # Verify we have 3 repositories
        repos_count = (
            db_session.query(ScheduleRepository)
            .filter(ScheduleRepository.schedule_id == schedule.id)
            .count()
        )
        assert repos_count == 3

        # Update with new repositories
        response = client.put(
            f"/api/schedules/{schedule.id}",
            headers=auth_headers,
            json={
                "repositories": [
                    {"organization": "new-org", "repository": "new-repo"},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        result = data["data"]["schedule"]
        assert len(result["repositories"]) == 1
        assert result["repositories"][0]["organization"] == "new-org"

        # Verify old repositories are deleted
        repos_count = (
            db_session.query(ScheduleRepository)
            .filter(ScheduleRepository.schedule_id == schedule.id)
            .count()
        )
        assert repos_count == 1

    def test_returns_404_for_nonexistent_schedule(
        self, client, test_user, auth_headers, test_settings
    ):
        """Should return 404 for schedule that doesn't exist."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        response = client.put(
            "/api/schedules/nonexistent-id",
            headers=auth_headers,
            json={"name": "Test"},
        )

        assert response.status_code == 404

    def test_returns_404_for_other_users_schedule(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return 404 for schedule belonging to another user."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Create another user and their schedule
        from pr_review_api.models.user import User

        other_user = User(
            id="99999",
            github_username="otheruser",
            github_access_token="encrypted_token",
        )
        db_session.add(other_user)
        db_session.commit()

        encrypted_pat = encrypt_token("ghp_test", test_settings.encryption_key)
        other_schedule = NotificationSchedule(
            user_id=other_user.id,
            name="Other Schedule",
            cron_expression="0 9 * * *",
            github_pat=encrypted_pat,
        )
        db_session.add(other_schedule)
        db_session.commit()

        response = client.put(
            f"/api/schedules/{other_schedule.id}",
            headers=auth_headers,
            json={"name": "Hacked!"},
        )

        assert response.status_code == 404

        # Verify schedule was not modified
        db_session.refresh(other_schedule)
        assert other_schedule.name == "Other Schedule"


class TestDeleteSchedule:
    """Tests for DELETE /api/schedules/{id}."""

    def test_requires_authentication(self, client):
        """Should return 401/403 without Authorization header."""
        response = client.delete("/api/schedules/some-id")
        assert response.status_code in [401, 403]

    def test_deletes_schedule_successfully(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should delete schedule and return 204."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Create a schedule
        encrypted_pat = encrypt_token("ghp_test", test_settings.encryption_key)
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="To Delete",
            cron_expression="0 9 * * *",
            github_pat=encrypted_pat,
        )
        db_session.add(schedule)
        db_session.commit()
        schedule_id = schedule.id

        repo = ScheduleRepository(
            schedule_id=schedule_id,
            organization="my-org",
            repository="my-repo",
        )
        db_session.add(repo)
        db_session.commit()

        response = client.delete(f"/api/schedules/{schedule_id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify schedule is deleted
        deleted = (
            db_session.query(NotificationSchedule)
            .filter(NotificationSchedule.id == schedule_id)
            .first()
        )
        assert deleted is None

    def test_cascade_deletes_repositories(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should cascade delete associated repositories."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Create a schedule with repositories
        encrypted_pat = encrypt_token("ghp_test", test_settings.encryption_key)
        schedule = NotificationSchedule(
            user_id=test_user.id,
            name="To Delete",
            cron_expression="0 9 * * *",
            github_pat=encrypted_pat,
        )
        db_session.add(schedule)
        db_session.commit()
        schedule_id = schedule.id

        for i in range(3):
            repo = ScheduleRepository(
                schedule_id=schedule_id,
                organization=f"org-{i}",
                repository=f"repo-{i}",
            )
            db_session.add(repo)
        db_session.commit()

        # Verify repositories exist
        repos_count = (
            db_session.query(ScheduleRepository)
            .filter(ScheduleRepository.schedule_id == schedule_id)
            .count()
        )
        assert repos_count == 3

        response = client.delete(f"/api/schedules/{schedule_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify repositories are deleted
        repos_count = (
            db_session.query(ScheduleRepository)
            .filter(ScheduleRepository.schedule_id == schedule_id)
            .count()
        )
        assert repos_count == 0

    def test_returns_404_for_nonexistent_schedule(
        self, client, test_user, auth_headers, test_settings
    ):
        """Should return 404 for schedule that doesn't exist."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        response = client.delete("/api/schedules/nonexistent-id", headers=auth_headers)

        assert response.status_code == 404

    def test_returns_404_for_other_users_schedule(
        self, client, test_user, auth_headers, db_session, test_settings
    ):
        """Should return 404 for schedule belonging to another user."""
        app.dependency_overrides[get_settings] = lambda: test_settings

        # Create another user and their schedule
        from pr_review_api.models.user import User

        other_user = User(
            id="99999",
            github_username="otheruser",
            github_access_token="encrypted_token",
        )
        db_session.add(other_user)
        db_session.commit()

        encrypted_pat = encrypt_token("ghp_test", test_settings.encryption_key)
        other_schedule = NotificationSchedule(
            user_id=other_user.id,
            name="Other Schedule",
            cron_expression="0 9 * * *",
            github_pat=encrypted_pat,
        )
        db_session.add(other_schedule)
        db_session.commit()

        response = client.delete(f"/api/schedules/{other_schedule.id}", headers=auth_headers)

        assert response.status_code == 404

        # Verify schedule was not deleted
        exists = (
            db_session.query(NotificationSchedule)
            .filter(NotificationSchedule.id == other_schedule.id)
            .first()
        )
        assert exists is not None
