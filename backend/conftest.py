#!/usr/bin/env python3
"""
Pytest configuration for eBay Manager backend tests
"""
import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database import get_db, Base
from app.init_db import create_admin_user

# Test database URL - use a separate test database file
TEST_DATABASE_URL = "sqlite:///./test_ebay_manager.db"

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine for the entire test session"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    return engine

@pytest.fixture(scope="session")
def test_session_maker(test_engine):
    """Create a session maker for tests"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    return TestingSessionLocal

@pytest.fixture(scope="session")
def setup_test_database(test_engine, test_session_maker):
    """Set up the test database with tables and initial data"""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create admin user for tests
    db = test_session_maker()
    try:
        create_admin_user_for_tests(db)
    finally:
        db.close()
    
    yield
    
    # Cleanup: Drop all tables after tests
    Base.metadata.drop_all(bind=test_engine)
    
    # Remove test database file
    if os.path.exists("./test_ebay_manager.db"):
        os.remove("./test_ebay_manager.db")

@pytest.fixture(scope="function")
def test_db(test_session_maker, setup_test_database):
    """Provide a database session for individual tests"""
    db = test_session_maker()
    try:
        yield db
    finally:
        # Rollback any changes made during the test
        db.rollback()
        db.close()

@pytest.fixture(scope="function")
def test_client(test_db, test_session_maker):
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            db = test_session_maker()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def create_admin_user_for_tests(db):
    """Create admin user specifically for tests"""
    from app.models import User
    from app.auth import get_password_hash
    
    # Check if admin user already exists
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@testdomain.com",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("Test admin user created: admin / admin123")
    else:
        print("Test admin user already exists")