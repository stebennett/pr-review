"""Shared test fixtures for PR-Review API tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from pr_review_api.config import Settings, get_settings
from pr_review_api.database import Base, get_db
from pr_review_api.main import app
from pr_review_api.models.user import User
from pr_review_api.services.jwt import create_access_token

# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


def get_test_settings() -> Settings:
    """Create test settings with mock values."""
    return Settings(
        database_url=SQLALCHEMY_DATABASE_URL,
        github_client_id="test_client_id",
        github_client_secret="test_client_secret",
        github_redirect_uri="http://localhost:8000/api/auth/callback",
        jwt_secret_key="test_jwt_secret_key_for_testing_only_do_not_use_in_production",
        jwt_algorithm="HS256",
        jwt_expiration_hours=24,
        encryption_key="Bk-QQPOIum-aABcMc2Y4505DQ4nn3iIc2zhk0JTuf8M=",
        cors_origins="http://localhost:5173",
        frontend_url="http://localhost:5173",
    )


@pytest.fixture
def test_settings():
    """Provide test settings."""
    return get_test_settings()


@pytest.fixture
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Create a test database session."""
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_engine, test_settings):
    """Create a test client with overridden dependencies."""
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    def override_get_settings():
        return test_settings

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session) -> User:
    """Create a test user in the database."""
    user = User(
        id="12345",
        github_username="testuser",
        github_access_token="encrypted_token_placeholder",
        email="test@example.com",
        avatar_url="https://avatars.githubusercontent.com/u/12345",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user, test_settings) -> dict[str, str]:
    """Create authorization headers with a valid JWT for the test user."""
    # Override settings for token creation
    original_settings = get_settings()
    app.dependency_overrides[get_settings] = lambda: test_settings

    token = create_access_token(user_id=test_user.id)

    app.dependency_overrides[get_settings] = lambda: original_settings

    return {"Authorization": f"Bearer {token}"}
