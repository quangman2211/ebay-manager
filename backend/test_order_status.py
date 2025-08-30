#!/usr/bin/env python3
"""
Test order status management workflow
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_status.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def setup_test_data():
    """Setup test database with user, account and orders"""
    # Clean up test database if exists
    if os.path.exists("test_status.db"):
        os.remove("test_status.db")
    
    # Setup test database
    Base.metadata.create_all(bind=engine)
    
    # Create test user and account
    db = TestingSessionLocal()
    try:
        from app.models import User, Account
        from app.auth import get_password_hash
        
        # Create user
        user = User(
            username="testuser",
            email="test@test.com",
            password_hash=get_password_hash("test123"),
            role="staff",
            is_active=True
        )
        db.add(user)
        db.flush()
        
        # Create account
        account = Account(
            user_id=user.id,
            ebay_username="testebayuser",
            name="Test eBay Account",
            is_active=True
        )
        db.add(account)
        db.commit()
        print("Test user and account created")
        return user.id, account.id
    finally:
        db.close()

if __name__ == "__main__":
    print("Testing order status management workflow...")
    
    user_id, account_id = setup_test_data()
    client = TestClient(app)
    
    # Login
    response = client.post(
        "/api/v1/login",
        data={"username": "testuser", "password": "test123"}
    )
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Upload order CSV first
    order_csv_path = "../Docs/DATA/ebay-order.csv"
    with open(order_csv_path, 'r', encoding='utf-8') as f:
        order_csv_content = f.read()
    
    files = {"file": ("ebay-order.csv", order_csv_content, "text/csv")}
    data = {"account_id": account_id, "data_type": "order"}
    
    response = client.post("/api/v1/csv/upload", headers=headers, files=files, data=data)
    print(f"✅ Order CSV uploaded: {response.json()}")
    
    # Get orders to get their IDs
    response = client.get(f"/api/v1/orders?account_id={account_id}", headers=headers)
    orders = response.json()
    print(f"✅ Retrieved {len(orders)} orders")
    
    if orders:
        # Test updating order statuses
        order_id = orders[0]['id']
        print(f"Testing status updates for order {order_id}")
        
        # Test all status transitions
        statuses = ["processing", "shipped", "completed"]
        
        for status in statuses:
            response = client.put(
                f"/api/v1/orders/{order_id}/status",
                headers=headers,
                json={"status": status}
            )
            
            if response.status_code == 200:
                print(f"✅ Updated order to {status}")
            else:
                print(f"❌ Failed to update order to {status}: {response.status_code}")
                print(response.json())
        
        # Verify final status
        response = client.get(f"/api/v1/orders?account_id={account_id}", headers=headers)
        updated_orders = response.json()
        final_order = updated_orders[0]
        
        if 'order_status' in final_order and final_order['order_status']:
            print(f"✅ Final order status: {final_order['order_status']['status']}")
        else:
            print("❌ Order status not found in response")
            print(f"Order data keys: {list(final_order.keys())}")
            if 'order_status' in final_order:
                print(f"Order status value: {final_order['order_status']}")
        
        # Test filtering by status
        print("Testing status filtering...")
        response = client.get(f"/api/v1/orders?account_id={account_id}&status=completed", headers=headers)
        completed_orders = response.json()
        print(f"✅ Found {len(completed_orders)} completed orders")
        
        response = client.get(f"/api/v1/orders?account_id={account_id}&status=pending", headers=headers)
        pending_orders = response.json()
        print(f"✅ Found {len(pending_orders)} pending orders")
        
    # Clean up
    os.remove("test_status.db")
    print("Order status tests completed!")