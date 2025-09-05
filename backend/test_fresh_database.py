#!/usr/bin/env python3
"""
Test script to simulate fresh database deployment
Tests automatic GUEST account creation
"""

import os
import sys
import tempfile
import sqlite3
import logging
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_fresh_database():
    """Test GUEST account initialization with fresh database"""
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db_path = temp_db.name
    temp_db.close()
    
    logger.info(f"🗄️  Created temporary database: {temp_db_path}")
    
    try:
        # Override database URL to use temp database
        os.environ['DATABASE_URL'] = f'sqlite:///{temp_db_path}'
        
        # Import after setting DATABASE_URL
        from app.database import engine, SessionLocal, Base
        from app.models import User, Account
        from app.auth import get_password_hash
        from app.constants import GUEST_ACCOUNT_CONFIG
        from app.services.guest_account_service import GuestAccountService
        
        logger.info("📋 Step 1: Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created")
        
        logger.info("👤 Step 2: Creating admin user...")
        db = SessionLocal()
        try:
            admin_user = User(
                username="admin",
                email="admin@test.com", 
                password_hash=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            logger.info(f"✅ Admin user created (ID: {admin_user.id})")
        finally:
            db.close()
        
        logger.info("🔍 Step 3: Testing GUEST account auto-creation...")
        db = SessionLocal()
        try:
            # Check if GUEST account exists (should not exist yet)
            existing_guest = db.query(Account).filter(
                Account.platform_username == GUEST_ACCOUNT_CONFIG["PLATFORM_USERNAME"]
            ).first()
            
            if existing_guest:
                logger.warning("⚠️  GUEST account already exists - this shouldn't happen with fresh DB")
                return False
            
            logger.info("📝 No GUEST account found (expected for fresh DB)")
            
            # Test lazy initialization through GuestAccountService
            logger.info("🔄 Testing lazy initialization...")
            guest_service = GuestAccountService(db)
            guest_account = guest_service.get_guest_account()
            
            if guest_account:
                logger.info(f"✅ GUEST account created via lazy initialization (ID: {guest_account.id})")
                logger.info(f"📋 Details: {guest_account.name} - {guest_account.platform_username}")
                
                # Verify account properties
                assert guest_account.account_type == GUEST_ACCOUNT_CONFIG["ACCOUNT_TYPE"]
                assert guest_account.connection_status == GUEST_ACCOUNT_CONFIG["CONNECTION_STATUS"]
                assert guest_account.is_active == True
                assert guest_account.data_processing_enabled == False
                
                logger.info("✅ GUEST account properties validated")
                return True
            else:
                logger.error("❌ Failed to create GUEST account via lazy initialization")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            os.unlink(temp_db_path)
            logger.info(f"🧹 Cleaned up temporary database: {temp_db_path}")
        except:
            pass

def test_startup_initialization():
    """Test the FastAPI startup event initialization"""
    logger.info("🚀 Testing FastAPI startup initialization...")
    
    try:
        # This simulates what happens in main.py startup event
        from app.database import SessionLocal
        from app.models import User, Account
        from app.constants import GUEST_ACCOUNT_CONFIG
        from app.services.guest_account_service import GuestAccountService
        
        db = SessionLocal()
        try:
            # Check admin user exists
            admin_user = db.query(User).filter(User.id == 1).first()
            if not admin_user:
                logger.warning("⚠️  Admin user not found - startup initialization would be skipped")
                return False
                
            # Test GUEST account service
            guest_service = GuestAccountService(db)
            guest_account = guest_service.get_guest_account()
            
            if guest_account:
                logger.info(f"✅ GUEST account available (ID: {guest_account.id})")
                logger.info("🎯 Startup initialization would succeed")
                return True
            else:
                logger.error("❌ GUEST account not available - startup would create it")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Startup test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Automatic GUEST Account Initialization")
    print("=" * 50)
    
    # Test 1: Fresh database scenario
    print("\n🔬 TEST 1: Fresh Database Scenario")
    test1_result = test_fresh_database()
    
    # Test 2: Existing database scenario  
    print("\n🔬 TEST 2: Startup Initialization")
    test2_result = test_startup_initialization()
    
    print("\n📊 RESULTS:")
    print(f"  Fresh Database Test: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"  Startup Test:       {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ GUEST account automatic initialization is working correctly")
        print("✅ Fresh database deployments will work without manual intervention")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED!")
        print("❌ Manual intervention may be required for fresh database deployments")
        sys.exit(1)