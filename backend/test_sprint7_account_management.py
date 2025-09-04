"""
Sprint 7: Account Management API Tests
Comprehensive test coverage for account management functionality
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.models import User, Account, UserAccountPermission, AccountSettings, AccountMetrics
from app.auth import get_password_hash


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sprint7.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)




@pytest.fixture(scope="function")
def test_db():
    """Create test database session for each test"""
    # Clean start for each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture 
def test_users(test_db):
    """Create test users with proper session management"""
    
    # Create admin user
    admin_user = User(
        username="admin_user",
        email="admin@test.com",
        password_hash=get_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    
    # Create staff user
    staff_user = User(
        username="staff_user", 
        email="staff@test.com",
        password_hash=get_password_hash("staff123"),
        role="staff",
        is_active=True
    )
    
    test_db.add_all([admin_user, staff_user])
    test_db.commit()
    test_db.refresh(admin_user)
    test_db.refresh(staff_user)
    
    # Create test accounts
    account1 = Account(
        user_id=admin_user.id,
        ebay_username="test_seller1",
        name="Test Account 1",
        is_active=True,
        account_type="ebay",
        auth_status="active",
        sync_enabled=True,
        settings='{"auto_sync": true}',
        performance_metrics='{}'
    )
    
    account2 = Account(
        user_id=staff_user.id,
        ebay_username="test_seller2", 
        name="Test Account 2",
        is_active=True,
        account_type="ebay",
        auth_status="pending",
        sync_enabled=False,
        settings='{"auto_sync": false}',
        performance_metrics='{}'
    )
    
    test_db.add_all([account1, account2])
    test_db.commit()
    test_db.refresh(account1)
    test_db.refresh(account2)
    
    # Create permissions
    permission1 = UserAccountPermission(
        user_id=admin_user.id,
        account_id=account1.id,
        permission_level="admin",
        granted_by=admin_user.id,
        is_active=True
    )
    
    permission2 = UserAccountPermission(
        user_id=staff_user.id,
        account_id=account2.id,
        permission_level="edit",
        granted_by=admin_user.id,
        is_active=True
    )
    
    test_db.add_all([permission1, permission2])
    test_db.commit()
    
    # Return data that won't become detached
    return {
        "admin": {"id": admin_user.id, "username": "admin_user", "role": "admin"},
        "staff": {"id": staff_user.id, "username": "staff_user", "role": "staff"},
        "accounts": [
            {"id": account1.id, "name": "Test Account 1", "user_id": admin_user.id},
            {"id": account2.id, "name": "Test Account 2", "user_id": staff_user.id}
        ]
    }


def get_auth_token(username: str, password: str):
    """Get authentication token for user"""
    response = client.post(
        "/api/v1/login",
        data={"username": username, "password": password}
    )
    return response.json()["access_token"]


class TestAccountManagement:
    """Test account management endpoints"""
    
    def test_update_account_details_success(self, test_users):
        """Test successful account update"""
        token = get_auth_token("admin_user", "admin123")
        account_id = test_users["accounts"][0]["id"]
        
        response = client.put(
            f"/api/v1/accounts/{account_id}",
            json={
                "name": "Updated Account Name",
                "auth_status": "active",
                "sync_enabled": False
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Account Name"
        assert data["is_active"] == True
    
    def test_update_account_permission_denied(self, test_users):
        """Test account update with insufficient permissions"""
        token = get_auth_token("staff_user", "staff123")
        account_id = test_users["accounts"][0]["id"]  # Admin's account
        
        response = client.put(
            f"/api/v1/accounts/{account_id}",
            json={"name": "Should Fail"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
    
    def test_get_account_details_success(self, test_users):
        """Test getting detailed account information"""
        token = get_auth_token("admin_user", "admin123")
        account_id = test_users["accounts"][0]["id"]
        
        response = client.get(
            f"/api/v1/accounts/{account_id}/details",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == account_id
        assert data["name"] == "Test Account 1"
        assert "settings" in data
        assert "performance_metrics" in data
        assert "user_permissions" in data
    
    def test_get_account_details_not_found(self, test_users):
        """Test getting details for non-existent account"""
        token = get_auth_token("admin_user", "admin123")
        
        response = client.get(
            "/api/v1/accounts/9999/details",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
    
    def test_deactivate_account_success(self, test_users):
        """Test account deactivation by admin"""
        token = get_auth_token("admin_user", "admin123")
        account_id = test_users["accounts"][0]["id"]
        
        response = client.delete(
            f"/api/v1/accounts/{account_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "deactivated" in response.json()["message"].lower()
    
    def test_deactivate_account_insufficient_permission(self, test_users):
        """Test account deactivation with insufficient permissions"""
        token = get_auth_token("staff_user", "staff123")
        account_id = test_users["accounts"][0]["id"]
        
        response = client.delete(
            f"/api/v1/accounts/{account_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403


class TestPermissionManagement:
    """Test permission management endpoints"""
    
    def test_create_user_permission_success(self, test_users):
        """Test creating user permission"""
        token = get_auth_token("admin_user", "admin123")
        account_id = test_users["accounts"][0]["id"]
        user_id = test_users["staff"]["id"]
        
        response = client.post(
            f"/api/v1/accounts/{account_id}/permissions",
            json={
                "user_id": user_id,
                "account_id": account_id,
                "permission_level": "view",
                "is_active": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert data["account_id"] == account_id
        assert data["permission_level"] == "view"
        assert data["is_active"] == True
    
    def test_create_permission_invalid_user(self, test_users):
        """Test creating permission for non-existent user"""
        token = get_auth_token("admin_user", "admin123")
        account_id = test_users["accounts"][0]["id"]
        
        response = client.post(
            f"/api/v1/accounts/{account_id}/permissions",
            json={
                "user_id": 9999,
                "account_id": account_id,
                "permission_level": "view"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]
    
    def test_get_account_permissions_success(self, test_users):
        """Test getting all permissions for an account"""
        token = get_auth_token("admin_user", "admin123")
        account_id = test_users["accounts"][0]["id"]
        
        response = client.get(
            f"/api/v1/accounts/{account_id}/permissions",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # At least the admin's permission
        assert data[0]["account_id"] == account_id
    
    def test_get_user_permissions_success(self, test_users):
        """Test getting all permissions for a user"""
        token = get_auth_token("admin_user", "admin123")
        user_id = test_users["admin"]["id"]
        
        response = client.get(
            f"/api/v1/users/{user_id}/permissions",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["user_id"] == user_id
    
    def test_get_user_permissions_unauthorized(self, test_users):
        """Test getting permissions for other user as staff"""
        token = get_auth_token("staff_user", "staff123")
        user_id = test_users["admin"]["id"]
        
        response = client.get(
            f"/api/v1/users/{user_id}/permissions",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()
    
    def test_bulk_update_permissions_success(self, test_users):
        """Test bulk permission updates"""
        token = get_auth_token("admin_user", "admin123")
        account_id = test_users["accounts"][0]["id"]
        staff_id = test_users["staff"]["id"]
        
        response = client.post(
            f"/api/v1/accounts/{account_id}/permissions/bulk",
            json={
                "account_id": account_id,
                "permissions": [
                    {
                        "user_id": staff_id,
                        "account_id": account_id,
                        "permission_level": "edit",
                        "is_active": True
                    }
                ]
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == account_id
        assert data["updated_count"] == 1
        assert len(data["errors"]) == 0


class TestAccountSettings:
    """Test account settings management"""
    
    def test_get_account_settings_success(self, test_users):
        """Test getting account settings"""
        token = get_auth_token("admin_user", "admin123")
        account_id = test_users["accounts"][0]["id"]
        
        response = client.get(
            f"/api/v1/accounts/{account_id}/settings",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_account_settings_success(self, test_users):
        """Test updating account settings"""
        token = get_auth_token("admin_user", "admin123")
        account_id = test_users["accounts"][0]["id"]
        
        response = client.put(
            f"/api/v1/accounts/{account_id}/settings",
            json=[
                {
                    "setting_key": "test_setting",
                    "setting_value": "test_value",
                    "setting_type": "string"
                }
            ],
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"]
        assert data["updated_count"] == 1
    
    def test_update_settings_permission_denied(self, test_users):
        """Test updating settings with insufficient permissions"""
        token = get_auth_token("staff_user", "staff123")
        account_id = test_users["accounts"][0]["id"]  # Admin's account
        
        response = client.put(
            f"/api/v1/accounts/{account_id}/settings",
            json=[{"setting_key": "test", "setting_value": "test"}],
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403


class TestAccountSwitching:
    """Test account switching functionality"""
    
    def test_switch_account_success(self, test_users):
        """Test successful account switching"""
        token = get_auth_token("admin_user", "admin123")
        account_id = test_users["accounts"][0]["id"]
        
        response = client.post(
            "/api/v1/accounts/switch",
            json={"account_id": account_id},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "switched successfully" in data["message"].lower()
        assert data["active_account"]["id"] == account_id
        assert data["active_account"]["name"] == "Test Account 1"
    
    def test_switch_account_no_permission(self, test_users):
        """Test switching to account without permission"""
        token = get_auth_token("staff_user", "staff123")
        account_id = test_users["accounts"][0]["id"]  # Admin's account
        
        response = client.post(
            "/api/v1/accounts/switch",
            json={"account_id": account_id},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "no permission" in response.json()["detail"].lower()
    
    def test_switch_nonexistent_account(self, test_users):
        """Test switching to non-existent account"""
        token = get_auth_token("admin_user", "admin123")
        
        response = client.post(
            "/api/v1/accounts/switch",
            json={"account_id": 9999},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404


class TestAuthorizationMatrix:
    """Test comprehensive authorization matrix"""
    
    def test_admin_full_access(self, test_users):
        """Test admin has full access to all operations"""
        token = get_auth_token("admin_user", "admin123")
        
        # Test access to both accounts
        for account in test_users["accounts"]:
            account_id = account["id"]
            
            # Should be able to view details
            response = client.get(
                f"/api/v1/accounts/{account_id}/details",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            
            # Should be able to update
            response = client.put(
                f"/api/v1/accounts/{account_id}",
                json={"sync_enabled": True},
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            
            # Should be able to view settings
            response = client.get(
                f"/api/v1/accounts/{account_id}/settings",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
    
    def test_staff_limited_access(self, test_users):
        """Test staff has limited access based on permissions"""
        token = get_auth_token("staff_user", "staff123")
        
        # Should have access to own account
        own_account_id = test_users["accounts"][1]["id"]
        response = client.get(
            f"/api/v1/accounts/{own_account_id}/details",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Should NOT have access to admin's account
        admin_account_id = test_users["accounts"][0]["id"]
        response = client.get(
            f"/api/v1/accounts/{admin_account_id}/details",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


class TestErrorHandling:
    """Test comprehensive error handling"""
    
    def test_invalid_json_request(self, test_users):
        """Test handling of invalid JSON requests"""
        token = get_auth_token("admin_user", "admin123")
        account_id = test_users["accounts"][0]["id"]
        
        response = client.put(
            f"/api/v1/accounts/{account_id}",
            data="invalid json",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_authentication(self, test_users):
        """Test requests without authentication"""
        account_id = test_users["accounts"][0]["id"]
        
        response = client.get(f"/api/v1/accounts/{account_id}/details")
        assert response.status_code == 401
    
    def test_invalid_permission_level(self, test_users):
        """Test invalid permission level in requests"""
        token = get_auth_token("admin_user", "admin123")
        account_id = test_users["accounts"][0]["id"]
        user_id = test_users["staff"]["id"]
        
        response = client.post(
            f"/api/v1/accounts/{account_id}/permissions",
            json={
                "user_id": user_id,
                "account_id": account_id,
                "permission_level": "invalid_level"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422


# Run tests with coverage
if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--cov=app.services",
        "--cov=app.main",
        "--cov-report=term-missing",
        "--cov-report=html:coverage_sprint7",
        "--tb=short"
    ])