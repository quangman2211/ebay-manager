#!/usr/bin/env python3
"""
Test CSV upload functionality with real data
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
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_csv.db"
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
    """Setup test database with user and account"""
    # Clean up test database if exists
    if os.path.exists("test_csv.db"):
        os.remove("test_csv.db")
    
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
    print("Testing CSV upload functionality...")
    
    user_id, account_id = setup_test_data()
    client = TestClient(app)
    
    # Login
    response = client.post(
        "/api/v1/login",
        data={"username": "testuser", "password": "test123"}
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        exit(1)
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login successful")
    
    # Test order CSV upload
    print("Testing order CSV upload...")
    
    # Read the sample order CSV
    order_csv_path = "../Docs/DATA/ebay-order.csv"
    if os.path.exists(order_csv_path):
        with open(order_csv_path, 'r', encoding='utf-8') as f:
            order_csv_content = f.read()
        
        # Upload order CSV
        files = {"file": ("ebay-order.csv", order_csv_content, "text/csv")}
        data = {"account_id": account_id, "data_type": "order"}
        
        response = client.post(
            "/api/v1/csv/upload",
            headers=headers,
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Order CSV upload successful: {result}")
        else:
            print(f"❌ Order CSV upload failed: {response.status_code}")
            print(response.json())
    else:
        print(f"❌ Order CSV file not found at {order_csv_path}")
    
    # Test listing CSV upload
    print("Testing listing CSV upload...")
    
    # Read the sample listing CSV
    listing_csv_path = "../Docs/DATA/ebay-listing.csv"
    if os.path.exists(listing_csv_path):
        with open(listing_csv_path, 'r', encoding='utf-8') as f:
            listing_csv_content = f.read()
        
        # Upload listing CSV
        files = {"file": ("ebay-listing.csv", listing_csv_content, "text/csv")}
        data = {"account_id": account_id, "data_type": "listing"}
        
        response = client.post(
            "/api/v1/csv/upload",
            headers=headers,
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Listing CSV upload successful: {result}")
        else:
            print(f"❌ Listing CSV upload failed: {response.status_code}")
            print(response.json())
    else:
        print(f"❌ Listing CSV file not found at {listing_csv_path}")
    
    # Test retrieving orders
    print("Testing order retrieval...")
    response = client.get(f"/api/v1/orders?account_id={account_id}", headers=headers)
    if response.status_code == 200:
        orders = response.json()
        print(f"✅ Retrieved {len(orders)} orders")
        if orders:
            print(f"First order: {orders[0]['item_id']}")
    else:
        print(f"❌ Order retrieval failed: {response.status_code}")
    
    # Test retrieving listings
    print("Testing listing retrieval...")
    response = client.get(f"/api/v1/listings?account_id={account_id}", headers=headers)
    if response.status_code == 200:
        listings = response.json()
        print(f"✅ Retrieved {len(listings)} listings")
        if listings:
            print(f"First listing: {listings[0]['item_id']}")
    else:
        print(f"❌ Listing retrieval failed: {response.status_code}")
    
    # Clean up
    os.remove("test_csv.db")
    print("CSV upload tests completed!")