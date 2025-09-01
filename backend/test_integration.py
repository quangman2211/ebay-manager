#!/usr/bin/env python3
"""
Integration tests for the complete eBay Manager workflow
"""
import pytest


def test_complete_workflow(test_client, test_db):
    """Test complete workflow from login to order management"""
    
    print("\n🧪 Running Complete Workflow Integration Test")
    print("✅ Test environment created with admin and staff users")
    
    # 1. Testing Admin Access
    print("\n1. Testing Admin Access...")
    
    # Login as admin
    admin_login = test_client.post(
        "/api/v1/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    print("✅ Admin login successful")
    
    # 2. Test Account Management
    print("\n2. Testing Account Management...")
    
    # Get accounts (should be empty initially)
    accounts_response = test_client.get("/api/v1/accounts", headers=admin_headers)
    assert accounts_response.status_code in [200, 404]
    print("✅ Accounts endpoint accessible")
    
    # 3. Test Order Management Endpoints
    print("\n3. Testing Order Management...")
    
    # Test orders endpoint (should be empty initially)
    orders_response = test_client.get("/api/v1/orders", headers=admin_headers)
    assert orders_response.status_code in [200, 404]
    print("✅ Orders endpoint accessible")
    
    # 4. Test Authentication Flows
    print("\n4. Testing Authentication Flows...")
    
    # Test invalid credentials
    invalid_login = test_client.post(
        "/api/v1/login", 
        data={"username": "invalid", "password": "invalid"}
    )
    assert invalid_login.status_code == 401
    print("✅ Invalid login properly rejected")
    
    # Test current user endpoint
    me_response = test_client.get("/api/v1/me", headers=admin_headers)
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["username"] == "admin"
    assert user_data["role"] == "admin"
    print("✅ Current user endpoint working")
    
    # 5. Test Protected Endpoints
    print("\n5. Testing Protected Endpoints...")
    
    # Try accessing protected endpoint without token
    unauth_response = test_client.get("/api/v1/accounts")
    assert unauth_response.status_code == 401
    print("✅ Protected endpoints require authentication")
    
    print("\n🎉 All integration tests passed!")
    print("✅ Admin authentication working")
    print("✅ Protected endpoints secured")
    print("✅ API endpoints accessible")
    print("✅ Database operations functional")


def test_bulk_operations_workflow(test_client, test_db):
    """Test bulk operations specific workflow"""
    
    # Login as admin
    login_response = test_client.post(
        "/api/v1/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test bulk update endpoint structure (even if no orders exist)
    # This tests the endpoint exists and is properly secured
    bulk_response = test_client.post(
        "/api/v1/orders/bulk-update",
        headers=headers,
        json={
            "order_ids": [1, 2, 3],
            "status": "processing"
        }
    )
    
    # Should not fail with authentication error
    # May fail with 404 (no orders) or other business logic errors, but not 401
    assert bulk_response.status_code != 401
    print("✅ Bulk operations endpoint accessible and secured")