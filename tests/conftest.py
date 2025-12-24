import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import get_db
from app.models import ORM_BASE_MODEL
from app.redis_client import get_redis_client
from app.auth import dependencies as auth_deps
from unittest.mock import MagicMock, patch

# Use in-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with special settings for SQLite
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Use StaticPool for in-memory database
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database for each test.
    """
    # Create all tables
    ORM_BASE_MODEL.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        ORM_BASE_MODEL.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a TestClient with overridden dependencies.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Mock Redis client to avoid Redis dependency in tests
    def mock_redis():
        mock = MagicMock()
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        mock.hgetall.return_value = {}
        mock.hincrby.return_value = True
        mock.expire.return_value = True
        return mock
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = mock_redis
    
    # Mock IP geolocation and Redis at module level
    with patch('app.auth.routers.get_country_by_ip', return_value='United States'), \
         patch('app.url.url_utils.get_redis_client', return_value=mock_redis()):
        with TestClient(app) as test_client:
            yield test_client
    
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(client):
    """
    Create a test user and return registration response with tokens.
    """
    response = client.post("/api/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "TestPass123!"
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_headers(test_user):
    """
    Return authorization headers with access token.
    """
    return {"Authorization": f"Bearer {test_user['access_token']}"}


@pytest.fixture
def second_user(client):
    """
    Create a second test user for testing user isolation.
    """
    response = client.post("/api/auth/register", json={
        "name": "Second User",
        "email": "second@example.com",
        "password": "TestPass123!"
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def second_auth_headers(second_user):
    """
    Return authorization headers for second user.
    """
    return {"Authorization": f"Bearer {second_user['access_token']}"}
