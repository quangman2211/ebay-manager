#!/usr/bin/env python3
"""
Basic tests for eBay Manager backend
"""
import pytest


def test_database_connection(test_client):
    """Test that we can connect to the database"""
    response = test_client.get("/api/v1/accounts")
    # Should return 401 (unauthorized) since we're not logged in
    assert response.status_code == 401


def test_admin_user_creation(test_client):
    """Test that admin user can be created and login works"""
    # Test login with admin credentials (created in conftest.py)
    response = test_client.post(
        "/api/v1/login",
        data={"username": "admin", "password": "admin123"}
    )
    
    # Should successfully authenticate
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Test that we can use the token to get user info
    token = data["access_token"]
    me_response = test_client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["username"] == "admin"
    assert user_data["role"] == "admin"


def test_protected_endpoint(test_client):
    """Test that protected endpoints work with authentication"""
    # First login to get token
    login_response = test_client.post(
        "/api/v1/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Test protected endpoint with token
    response = test_client.get(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should now return 200 (or appropriate response)
    assert response.status_code in [200, 404]  # 404 if no accounts exist yet