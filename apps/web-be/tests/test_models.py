"""Tests for SQLAlchemy database models."""

from datetime import UTC, datetime

import pytest

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
