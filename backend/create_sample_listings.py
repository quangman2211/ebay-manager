#!/usr/bin/env python3
"""
Create sample listings for E2E testing
"""
import sys
sys.path.append('.')

from app.database import SessionLocal, engine, Base
from app.models import User, Account, CSVData
import json

def create_sample_listings():
    """Create sample listings for testing"""
    print("Creating sample listings for E2E testing...")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get admin user and create a test account if needed
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("Admin user not found!")
            return
        
        # Create or get test account
        test_account = db.query(Account).filter(Account.user_id == admin_user.id).first()
        if not test_account:
            test_account = Account(
                user_id=admin_user.id,
                ebay_username="test_seller",
                name="Test eBay Account",
                is_active=True
            )
            db.add(test_account)
            db.commit()
            db.refresh(test_account)
        
        # Sample listings data
        sample_listings = [
            {
                "item_id": "123456789",
                "csv_row": {
                    "Title": "Test Product 1 - Wireless Headphones",
                    "Item #": "123456789",
                    "Current price": "29.99",
                    "Start price": "29.99", 
                    "Available quantity": "15",
                    "Sold quantity": "5",
                    "Watchers": "12",
                    "Status": "active",
                    "Format": "FIXED_PRICE",
                    "Custom label (SKU)": "WH-001",
                    "Start date": "2024-01-15",
                    "End date": "2024-12-31",
                    "Description": "High-quality wireless headphones with noise cancellation"
                }
            },
            {
                "item_id": "234567890",
                "csv_row": {
                    "Title": "Test Product 2 - Smartphone Case",
                    "Item #": "234567890",
                    "Current price": "15.99",
                    "Start price": "15.99",
                    "Available quantity": "3",
                    "Sold quantity": "22",
                    "Watchers": "8",
                    "Status": "active",
                    "Format": "FIXED_PRICE", 
                    "Custom label (SKU)": "SC-002",
                    "Start date": "2024-02-01",
                    "End date": "2024-11-30",
                    "Description": "Protective smartphone case with premium materials"
                }
            },
            {
                "item_id": "345678901",
                "csv_row": {
                    "Title": "Test Product 3 - USB Cable",
                    "Item #": "345678901",
                    "Current price": "9.99",
                    "Start price": "9.99",
                    "Available quantity": "0",
                    "Sold quantity": "45",
                    "Watchers": "2",
                    "Status": "active",
                    "Format": "FIXED_PRICE",
                    "Custom label (SKU)": "USB-003", 
                    "Start date": "2024-01-01",
                    "End date": "2024-12-31",
                    "Description": "High-speed USB cable for data transfer and charging"
                }
            },
            {
                "item_id": "456789012",
                "csv_row": {
                    "Title": "Test Product 4 - Bluetooth Speaker",
                    "Item #": "456789012",
                    "Current price": "49.99",
                    "Start price": "49.99",
                    "Available quantity": "25",
                    "Sold quantity": "10",
                    "Watchers": "18",
                    "Status": "active",
                    "Format": "FIXED_PRICE",
                    "Custom label (SKU)": "BT-004",
                    "Start date": "2024-03-01",
                    "End date": "2024-12-31",
                    "Description": "Portable bluetooth speaker with excellent sound quality"
                }
            },
            {
                "item_id": "567890123", 
                "csv_row": {
                    "Title": "Test Product 5 - Gaming Mouse",
                    "Item #": "567890123",
                    "Current price": "35.99",
                    "Start price": "39.99",
                    "Available quantity": "8",
                    "Sold quantity": "15",
                    "Watchers": "25",
                    "Status": "inactive",
                    "Format": "FIXED_PRICE",
                    "Custom label (SKU)": "GM-005",
                    "Start date": "2024-02-15",
                    "End date": "2024-10-31",
                    "Description": "High-precision gaming mouse with RGB lighting"
                }
            }
        ]
        
        # Delete existing test listings
        db.query(CSVData).filter(
            CSVData.account_id == test_account.id,
            CSVData.data_type == "listing"
        ).delete()
        
        # Create sample listings
        for listing_data in sample_listings:
            listing = CSVData(
                account_id=test_account.id,
                data_type="listing",
                item_id=listing_data["item_id"],
                csv_row=listing_data["csv_row"]
            )
            db.add(listing)
        
        db.commit()
        print(f"✅ Created {len(sample_listings)} sample listings successfully!")
        print("Sample listings:")
        for listing in sample_listings:
            print(f"  - {listing['csv_row']['Title']} (${listing['csv_row']['Current price']})")
        
    except Exception as e:
        print(f"❌ Error creating sample listings: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_listings()