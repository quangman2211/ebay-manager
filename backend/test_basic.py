#!/usr/bin/env python3
"""
Basic tests for eBay Manager backend
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.init_db import create_admin_user

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def setup_test_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up
    Base.metadata.drop_all(bind=engine)

def test_database_connection(setup_test_db):
    """Test that we can connect to the database"""
    client = TestClient(app)
    response = client.get("/api/v1/accounts")
    # Should return 401 (unauthorized) since we're not logged in
    assert response.status_code == 401

def test_admin_user_creation(setup_test_db):
    """Test that admin user can be created"""
    create_admin_user()
    
    # Test login with admin credentials
    client = TestClient(app)
    response = client.post(
        "/api/v1/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

if __name__ == "__main__":
    # Run basic tests
    print("Running basic tests...")
    
    # Clean up test database if exists
    if os.path.exists("test.db"):
        os.remove("test.db")
    
    # Setup test database
    Base.metadata.create_all(bind=engine)
    
    # Create admin user in test database
    db = TestingSessionLocal()
    try:
        from app.models import User
        from app.auth import get_password_hash
        
        admin_user = User(
            username="admin",
            email="admin@test.com",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("Test admin user created")
    finally:
        db.close()
    
    # Test API endpoints
    client = TestClient(app)
    
    # Test login
    print("Testing login...")
    response = client.post(
        "/api/v1/login",
        data={"username": "admin", "password": "admin123"}
    )
    
    if response.status_code == 200:
        print("✅ Login test passed")
        token = response.json()["access_token"]
        
        # Test protected endpoint
        print("Testing protected endpoint...")
        response = client.get(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            print("✅ Protected endpoint test passed")
        else:
            print(f"❌ Protected endpoint test failed: {response.status_code}")
    else:
        print(f"❌ Login test failed: {response.status_code}")
        print(response.json())
    
    # Clean up
    os.remove("test.db")
    print("Basic tests completed!")