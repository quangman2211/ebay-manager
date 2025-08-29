"""
Integration Tests for Authentication Endpoints
Following SOLID principles - Single Responsibility for each test
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from ..conftest import UserFactory, assert_response_success, assert_response_error

class TestUserRegistration:
    """Test user registration endpoint"""
    
    def test_register_user_success(self, client: TestClient):
        """Test successful user registration"""
        user_data = UserFactory.create_user_data(
            username="newuser",
            email="newuser@example.com"
        )
        
        response = client.post("/api/v1/auth/register", json=user_data)
        data = assert_response_success(response, 201)
        
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
    
    def test_register_user_duplicate_username(self, client: TestClient, test_user: User):
        """Test registration with duplicate username"""
        user_data = UserFactory.create_user_data(
            username=test_user.username,  # Use existing username
            email="different@example.com"
        )
        
        response = client.post("/api/v1/auth/register", json=user_data)
        data = assert_response_error(response, 400)
        
        assert "Username already exists" in data["error"]["message"]
    
    def test_register_user_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with duplicate email"""
        user_data = UserFactory.create_user_data(
            username="differentuser",
            email=test_user.email  # Use existing email
        )
        
        response = client.post("/api/v1/auth/register", json=user_data)
        data = assert_response_error(response, 400)
        
        assert "Email already exists" in data["error"]["message"]
    
    def test_register_user_invalid_email(self, client: TestClient):
        """Test registration with invalid email format"""
        user_data = UserFactory.create_user_data(email="invalid-email")
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert_response_error(response, 422)  # Validation error
    
    def test_register_user_weak_password(self, client: TestClient):
        """Test registration with weak password"""
        user_data = UserFactory.create_user_data(password="weak")
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert_response_error(response, 422)  # Validation error
    
    def test_register_user_short_username(self, client: TestClient):
        """Test registration with too short username"""
        user_data = UserFactory.create_user_data(username="ab")  # Too short
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert_response_error(response, 422)  # Validation error

class TestUserLogin:
    """Test user login endpoint"""
    
    def test_login_with_username_success(self, client: TestClient, test_user: User):
        """Test successful login with username"""
        login_data = {
            "username_or_email": test_user.username,
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        data = assert_response_success(response)
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["user"]["username"] == test_user.username
        assert data["user"]["id"] == test_user.id
    
    def test_login_with_email_success(self, client: TestClient, test_user: User):
        """Test successful login with email"""
        login_data = {
            "username_or_email": test_user.email,
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        data = assert_response_success(response)
        
        assert "access_token" in data
        assert data["user"]["email"] == test_user.email
    
    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with wrong password"""
        login_data = {
            "username_or_email": test_user.username,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        data = assert_response_error(response, 401)
        
        assert "Invalid credentials" in data["error"]["message"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user"""
        login_data = {
            "username_or_email": "nonexistent",
            "password": "somepassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        data = assert_response_error(response, 401)
        
        assert "Invalid credentials" in data["error"]["message"]
    
    def test_login_inactive_user(self, client: TestClient, test_user: User, db_session: Session):
        """Test login with inactive user"""
        # Make user inactive
        test_user.is_active = False
        db_session.commit()
        
        login_data = {
            "username_or_email": test_user.username,
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        data = assert_response_error(response, 401)
        
        assert "Invalid credentials" in data["error"]["message"]

class TestTokenRefresh:
    """Test token refresh endpoint"""
    
    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """Test successful token refresh"""
        # First login to get tokens
        login_data = {
            "username_or_email": test_user.username,
            "password": "testpass123"
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        login_data_response = assert_response_success(login_response)
        refresh_token = login_data_response["refresh_token"]
        
        # Use refresh token to get new access token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        data = assert_response_success(response)
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token"""
        refresh_data = {"refresh_token": "invalid.token.here"}
        
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        data = assert_response_error(response, 401)
        
        assert "Invalid refresh token" in data["error"]["message"]

class TestProtectedEndpoints:
    """Test protected endpoints"""
    
    def test_get_current_user_success(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test getting current user info with valid token"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        data = assert_response_success(response)
        
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["role"] == test_user.role
    
    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user info without token"""
        response = client.get("/api/v1/auth/me")
        assert_response_error(response, 403)  # Forbidden due to no token
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user info with invalid token"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert_response_error(response, 401)
    
    def test_update_user_profile_success(self, client: TestClient, auth_headers: dict):
        """Test updating user profile"""
        profile_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        response = client.put("/api/v1/auth/me", json=profile_data, headers=auth_headers)
        data = assert_response_success(response)
        
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
    
    def test_change_password_success(self, client: TestClient, auth_headers: dict):
        """Test successful password change"""
        password_data = {
            "current_password": "testpass123",
            "new_password": "NewPassword123!"
        }
        
        response = client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        data = assert_response_success(response)
        
        assert data["success"] is True
        assert "successfully" in data["message"]
    
    def test_change_password_wrong_current(self, client: TestClient, auth_headers: dict):
        """Test password change with wrong current password"""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "NewPassword123!"
        }
        
        response = client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        data = assert_response_error(response, 400)
        
        assert "incorrect" in data["error"]["message"].lower()
    
    def test_change_password_weak_new(self, client: TestClient, auth_headers: dict):
        """Test password change with weak new password"""
        password_data = {
            "current_password": "testpass123",
            "new_password": "weak"
        }
        
        response = client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        assert_response_error(response, 422)  # Validation error
    
    def test_verify_token_success(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test token verification endpoint"""
        response = client.get("/api/v1/auth/verify-token", headers=auth_headers)
        data = assert_response_success(response)
        
        assert data["success"] is True
        assert "valid" in data["message"]
        assert data["data"]["user_id"] == test_user.id
        assert data["data"]["username"] == test_user.username
        assert data["data"]["role"] == test_user.role
    
    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """Test successful logout"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        data = assert_response_success(response)
        
        assert data["success"] is True
        assert "successfully" in data["message"]

class TestRoleBasedAccess:
    """Test role-based access control"""
    
    def test_admin_user_login(self, client: TestClient, test_admin: User):
        """Test admin user can login and has admin role"""
        login_data = {
            "username_or_email": test_admin.username,
            "password": "adminpass123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        data = assert_response_success(response)
        
        assert data["user"]["role"] == "admin"
        assert data["user"]["username"] == test_admin.username
    
    def test_user_properties(self, test_user: User, test_admin: User):
        """Test user model properties"""
        # Test regular user
        assert test_user.is_admin is False
        assert test_user.full_name == "Test User"
        
        # Test admin user
        assert test_admin.is_admin is True
        assert test_admin.full_name == "Test Admin"
    
    def test_user_full_name_fallback(self, db_session: Session):
        """Test full name fallback to username"""
        user_data = {
            "username": "usernameonly",
            "email": "username@example.com",
            "password_hash": "hashedpass",
            "role": "user"
            # No first_name or last_name
        }
        
        user = User(**user_data)
        assert user.full_name == "usernameonly"  # Should fallback to username