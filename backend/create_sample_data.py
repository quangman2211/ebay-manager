#!/usr/bin/env python3
"""
Sample Data Creation Script - eBay Manager
Creates comprehensive test data for multiple accounts, orders, and listings
"""

import os
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import random

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, Account, CSVData, OrderStatus, User, AccountMetrics

def create_sample_accounts(db: Session):
    """Create multiple test eBay accounts"""
    # Get the admin user
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        print("❌ Admin user not found. Please run init_db.py first.")
        return []
    
    accounts_data = [
        {
            "name": "Electronics Store Pro",
            "ebay_username": "electronics_pro_2024",
            "account_type": "ebay",
            "auth_status": "active",
            "sync_enabled": True
        },
        {
            "name": "Fashion Boutique",
            "ebay_username": "fashion_boutique_main",
            "account_type": "ebay",
            "auth_status": "active",
            "sync_enabled": True
        },
        {
            "name": "Home & Garden Store",
            "ebay_username": "home_garden_shop",
            "account_type": "ebay",
            "auth_status": "pending",
            "sync_enabled": False
        },
        {
            "name": "Sports Equipment Co",
            "ebay_username": "sports_equipment_co",
            "account_type": "ebay",
            "auth_status": "expired",
            "sync_enabled": True
        },
        {
            "name": "Books & Media Hub",
            "ebay_username": "books_media_hub",
            "account_type": "ebay",
            "auth_status": "active",
            "sync_enabled": True
        }
    ]
    
    created_accounts = []
    
    for account_data in accounts_data:
        # Check if account already exists
        existing = db.query(Account).filter(Account.ebay_username == account_data["ebay_username"]).first()
        if existing:
            print(f"📋 Account {account_data['name']} already exists, skipping...")
            created_accounts.append(existing)
            continue
            
        account = Account(
            user_id=admin.id,
            name=account_data["name"],
            ebay_username=account_data["ebay_username"],
            account_type=account_data["account_type"],
            auth_status=account_data["auth_status"],
            sync_enabled=account_data["sync_enabled"],
            is_active=True,
            last_sync_at=datetime.now() - timedelta(hours=random.randint(1, 24))
        )
        
        db.add(account)
        created_accounts.append(account)
        print(f"✅ Created account: {account_data['name']}")
    
    db.commit()
    return created_accounts

def create_sample_orders(db: Session, accounts):
    """Create sample orders for each account"""
    order_statuses = ["pending", "processing", "shipped", "completed"]
    
    sample_orders = [
        {
            "order_number": "ORD001",
            "item_number": "123456789012",
            "buyer_username": "buyer123",
            "item_title": "iPhone 15 Pro Max 256GB",
            "quantity": 1,
            "sale_price": "1299.99",
            "shipping_cost": "15.99",
            "customer_name": "John Smith",
            "customer_email": "john.smith@email.com"
        },
        {
            "order_number": "ORD002",
            "item_number": "123456789013",
            "buyer_username": "fashionlover",
            "item_title": "Designer Handbag - Leather",
            "quantity": 1,
            "sale_price": "299.99",
            "shipping_cost": "12.99",
            "customer_name": "Sarah Johnson",
            "customer_email": "sarah.j@email.com"
        },
        {
            "order_number": "ORD003",
            "item_number": "123456789014",
            "buyer_username": "homeimprover",
            "item_title": "Garden Tool Set - Professional",
            "quantity": 2,
            "sale_price": "149.99",
            "shipping_cost": "19.99",
            "customer_name": "Mike Wilson",
            "customer_email": "mike.w@email.com"
        },
        {
            "order_number": "ORD004",
            "item_number": "123456789015",
            "buyer_username": "sportsstar",
            "item_title": "Professional Tennis Racket",
            "quantity": 1,
            "sale_price": "199.99",
            "shipping_cost": "9.99",
            "customer_name": "Lisa Brown",
            "customer_email": "lisa.brown@email.com"
        },
        {
            "order_number": "ORD005",
            "item_number": "123456789016",
            "buyer_username": "booklover",
            "item_title": "Rare Book Collection - History",
            "quantity": 3,
            "sale_price": "89.99",
            "shipping_cost": "14.99",
            "customer_name": "David Lee",
            "customer_email": "david.lee@email.com"
        }
    ]
    
    for i, account in enumerate(accounts):
        # Create 3-5 orders per account
        orders_count = random.randint(3, 5)
        
        for j in range(orders_count):
            order_data = sample_orders[j % len(sample_orders)].copy()
            order_data["order_number"] = f"{account.ebay_username.upper()}_{order_data['order_number']}_{j+1}"
            order_data["account_id"] = account.id
            
            # Create CSV data entry
            csv_data = CSVData(
                account_id=account.id,
                data_type="order",
                item_id=order_data["order_number"],
                csv_row=order_data,
                processing_status="completed",
                processed_at=datetime.now() - timedelta(days=random.randint(1, 30))
            )
            
            db.add(csv_data)
            db.flush()  # Get the ID
            
            # Create order status
            status = random.choice(order_statuses)
            order_status = OrderStatus(
                csv_data_id=csv_data.id,
                status=status,
                updated_by=account.user_id,
                updated_at=datetime.now() - timedelta(hours=random.randint(1, 72))
            )
            
            db.add(order_status)
            
        print(f"✅ Created {orders_count} orders for account: {account.name}")
    
    db.commit()

def create_sample_listings(db: Session, accounts):
    """Create sample listings for each account"""
    
    sample_listings = [
        {
            "item_number": "LIS001",
            "title": "Smartphone Case - Premium Quality",
            "sku": "CASE001",
            "price": "24.99",
            "quantity_available": 150,
            "quantity_sold": 45,
            "watchers": 23,
            "format": "Fixed Price",
            "category": "Electronics"
        },
        {
            "item_number": "LIS002",
            "title": "Women's Fashion Scarf - Silk",
            "sku": "SCARF001",
            "price": "39.99",
            "quantity_available": 75,
            "quantity_sold": 22,
            "watchers": 18,
            "format": "Fixed Price",
            "category": "Fashion"
        },
        {
            "item_number": "LIS003",
            "title": "Garden Hose - Heavy Duty 50ft",
            "sku": "HOSE001",
            "price": "69.99",
            "quantity_available": 30,
            "quantity_sold": 12,
            "watchers": 8,
            "format": "Best Offer",
            "category": "Garden"
        },
        {
            "item_number": "LIS004",
            "title": "Basketball - Official Size",
            "sku": "BALL001",
            "price": "29.99",
            "quantity_available": 100,
            "quantity_sold": 67,
            "watchers": 15,
            "format": "Fixed Price",
            "category": "Sports"
        },
        {
            "item_number": "LIS005",
            "title": "Classic Novel Set - 10 Books",
            "sku": "BOOK001",
            "price": "79.99",
            "quantity_available": 25,
            "quantity_sold": 8,
            "watchers": 12,
            "format": "Auction",
            "category": "Books"
        }
    ]
    
    for i, account in enumerate(accounts):
        # Create 5-8 listings per account
        listings_count = random.randint(5, 8)
        
        for j in range(listings_count):
            listing_data = sample_listings[j % len(sample_listings)].copy()
            listing_data["item_number"] = f"{account.ebay_username.upper()}_{listing_data['item_number']}_{j+1}"
            listing_data["account_id"] = account.id
            
            # Vary the data slightly
            listing_data["price"] = str(float(listing_data["price"]) + random.uniform(-10, 10))
            listing_data["quantity_available"] = random.randint(10, 200)
            listing_data["quantity_sold"] = random.randint(0, 100)
            listing_data["watchers"] = random.randint(0, 50)
            
            # Create CSV data entry
            csv_data = CSVData(
                account_id=account.id,
                data_type="listing",
                item_id=listing_data["item_number"],
                csv_row=listing_data,
                processing_status="completed",
                processed_at=datetime.now() - timedelta(days=random.randint(1, 15))
            )
            
            db.add(csv_data)
            
        print(f"✅ Created {listings_count} listings for account: {account.name}")
    
    db.commit()

def create_sample_metrics(db: Session, accounts):
    """Create sample account metrics"""
    
    for account in accounts:
        # Create metrics for last 30 days
        for days_ago in range(30):
            metric_date = date.today() - timedelta(days=days_ago)
            
            # Calculate metrics based on account data
            orders_count = db.query(CSVData).filter(
                CSVData.account_id == account.id,
                CSVData.data_type == "order"
            ).count()
            
            listings_count = db.query(CSVData).filter(
                CSVData.account_id == account.id,
                CSVData.data_type == "listing"
            ).count()
            
            # Generate realistic daily metrics
            daily_orders = random.randint(0, max(1, orders_count // 10))
            daily_revenue = Decimal(str(random.uniform(0, 1000)))
            daily_views = random.randint(50, 500)
            daily_watchers = random.randint(0, 25)
            conversion_rate = Decimal(str(random.uniform(0.01, 0.15)))
            
            metrics = AccountMetrics(
                account_id=account.id,
                metric_date=metric_date,
                total_orders=daily_orders,
                total_revenue=daily_revenue,
                active_listings=listings_count,
                total_views=daily_views,
                watchers=daily_watchers,
                conversion_rate=conversion_rate
            )
            
            db.add(metrics)
        
        print(f"✅ Created 30 days of metrics for account: {account.name}")
    
    db.commit()

def main():
    """Main function to create all sample data"""
    print("🚀 Creating sample data for eBay Manager...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create sample accounts
        print("\n📋 Creating sample accounts...")
        accounts = create_sample_accounts(db)
        
        # Create sample orders
        print("\n📦 Creating sample orders...")
        create_sample_orders(db, accounts)
        
        # Create sample listings
        print("\n📝 Creating sample listings...")
        create_sample_listings(db, accounts)
        
        # Create sample metrics
        print("\n📊 Creating sample metrics...")
        create_sample_metrics(db, accounts)
        
        print("\n🎉 Sample data creation completed successfully!")
        print(f"   Created {len(accounts)} accounts")
        
        # Display summary
        total_orders = db.query(CSVData).filter(CSVData.data_type == "order").count()
        total_listings = db.query(CSVData).filter(CSVData.data_type == "listing").count()
        total_metrics = db.query(AccountMetrics).count()
        
        print(f"   Created {total_orders} orders")
        print(f"   Created {total_listings} listings")
        print(f"   Created {total_metrics} metric records")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
        raise
        
    finally:
        db.close()

if __name__ == "__main__":
    main()