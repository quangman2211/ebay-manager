"""
Test Configuration and Fixtures
Following SOLID principles for test setup
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from main import app
from app.models.base import Base, get_db
from app.models import User, Account
from app.utils.auth import PasswordManager
from app.core.config import settings

# Test database URL (in-memory SQLite for fast tests)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a test database session
    Following SOLID: Single Responsibility for test database setup
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with dependency overrides
    Following SOLID: Single Responsibility for test client setup
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session: Session) -> User:
    """
    Create a test user
    Following SOLID: Single Responsibility for test user creation
    """
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password_hash": PasswordManager.hash_password("testpass123"),
        "first_name": "Test",
        "last_name": "User",
        "role": "user",
        "is_active": True,
        "email_verified": True
    }
    
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user

@pytest.fixture
def test_admin(db_session: Session) -> User:
    """
    Create a test admin user
    Following SOLID: Single Responsibility for test admin creation
    """
    admin_data = {
        "username": "testadmin",
        "email": "testadmin@example.com",
        "password_hash": PasswordManager.hash_password("adminpass123"),
        "first_name": "Test",
        "last_name": "Admin",
        "role": "admin",
        "is_active": True,
        "email_verified": True
    }
    
    admin = User(**admin_data)
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    
    return admin

@pytest.fixture
def test_account(db_session: Session, test_user: User) -> Account:
    """
    Create a test eBay account
    Following SOLID: Single Responsibility for test account creation
    """
    account_data = {
        "user_id": test_user.id,
        "ebay_account_name": "testebayaccount",
        "ebay_store_name": "Test eBay Store",
        "status": "active",
        "currency": "USD",
        "timezone": "UTC",
        "business_name": "Test Business",
        "contact_email": "contact@test.com"
    }
    
    account = Account(**account_data)
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    
    return account

@pytest.fixture
def auth_headers(client: TestClient, test_user: User) -> dict:
    """
    Get authentication headers for test user
    Following SOLID: Single Responsibility for auth header creation
    """
    # Login to get token
    login_data = {
        "username_or_email": test_user.username,
        "password": "testpass123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client: TestClient, test_admin: User) -> dict:
    """
    Get authentication headers for test admin
    Following SOLID: Single Responsibility for admin auth header creation
    """
    # Login to get token
    login_data = {
        "username_or_email": test_admin.username,
        "password": "adminpass123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Test data factories
class UserFactory:
    """
    Factory for creating test users
    Following SOLID: Single Responsibility for user test data
    """
    
    @staticmethod
    def create_user_data(
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "testpass123",
        role: str = "user"
    ) -> dict:
        return {
            "username": username,
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User",
            "role": role
        }

class AccountFactory:
    """
    Factory for creating test accounts
    Following SOLID: Single Responsibility for account test data
    """
    
    @staticmethod
    def create_account_data(
        ebay_account_name: str = "testebayaccount",
        ebay_store_name: str = "Test Store",
        status: str = "active"
    ) -> dict:
        return {
            "ebay_account_name": ebay_account_name,
            "ebay_store_name": ebay_store_name,
            "status": status,
            "currency": "USD",
            "timezone": "UTC",
            "business_name": "Test Business",
            "contact_email": "contact@test.com"
        }

# Test utilities
def assert_response_success(response, expected_status: int = 200):
    """Assert that API response is successful"""
    assert response.status_code == expected_status
    return response.json()

def assert_response_error(response, expected_status: int = 400):
    """Assert that API response is an error"""
    assert response.status_code == expected_status
    data = response.json()
    assert "error" in data
    return data

def create_test_jwt_token(user_id: int, username: str, role: str = "user") -> str:
    """Create a test JWT token for authentication tests"""
    from app.utils.auth import JWTManager
    
    token_data = {
        "sub": str(user_id),
        "username": username,
        "role": role
    }
    
    return JWTManager.create_access_token(token_data)