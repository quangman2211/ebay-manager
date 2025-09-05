"""
Initialize GUEST-ACCOUNT system for data preservation
This script creates the special GUEST account used when deleting regular accounts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import Account, User
from app.constants import GUEST_ACCOUNT_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_guest_account():
    """
    Create or update the GUEST-ACCOUNT system account
    This account is used to preserve data when regular accounts are deleted
    """
    db = SessionLocal()
    try:
        # Check if GUEST account already exists
        existing_guest = db.query(Account).filter(
            Account.platform_username == GUEST_ACCOUNT_CONFIG["PLATFORM_USERNAME"]
        ).first()
        
        if existing_guest:
            logger.info(f"GUEST account already exists (ID: {existing_guest.id})")
            return existing_guest
        
        # Ensure system admin user exists (ID: 1)
        admin_user = db.query(User).filter(User.id == 1).first()
        if not admin_user:
            logger.error("System admin user (ID: 1) not found. Please create admin user first.")
            return None
        
        # Create GUEST account
        guest_account = Account(
            user_id=GUEST_ACCOUNT_CONFIG["USER_ID"],
            platform_username=GUEST_ACCOUNT_CONFIG["PLATFORM_USERNAME"],
            name=GUEST_ACCOUNT_CONFIG["NAME"],
            is_active=True,  # Always active for system account
            account_type=GUEST_ACCOUNT_CONFIG["ACCOUNT_TYPE"],
            connection_status=GUEST_ACCOUNT_CONFIG["CONNECTION_STATUS"],
            data_processing_enabled=False,  # GUEST account doesn't process new data
            settings='{"is_guest_account": true, "is_deletable": false, "is_editable": false}',
            performance_metrics='{"description": "System account for preserving data from deleted accounts"}'
        )
        
        db.add(guest_account)
        db.commit()
        db.refresh(guest_account)
        
        logger.info(f"GUEST account created successfully (ID: {guest_account.id})")
        logger.info(f"GUEST account details: {guest_account.name} - {guest_account.platform_username}")
        
        return guest_account
        
    except Exception as e:
        logger.error(f"Error creating GUEST account: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def verify_guest_account():
    """Verify GUEST account exists and is properly configured"""
    db = SessionLocal()
    try:
        guest_account = db.query(Account).filter(
            Account.platform_username == GUEST_ACCOUNT_CONFIG["PLATFORM_USERNAME"]
        ).first()
        
        if not guest_account:
            logger.warning("GUEST account not found")
            return False
        
        logger.info("GUEST account verification:")
        logger.info(f"  ID: {guest_account.id}")
        logger.info(f"  Name: {guest_account.name}")
        logger.info(f"  Platform Username: {guest_account.platform_username}")
        logger.info(f"  Account Type: {guest_account.account_type}")
        logger.info(f"  Is Active: {guest_account.is_active}")
        logger.info(f"  Settings: {guest_account.settings}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying GUEST account: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Initializing GUEST-ACCOUNT system...")
    
    # Create GUEST account
    guest_account = create_guest_account()
    
    if guest_account:
        # Verify creation
        if verify_guest_account():
            logger.info("GUEST-ACCOUNT system initialized successfully!")
        else:
            logger.error("GUEST account verification failed")
    else:
        logger.error("Failed to create GUEST account")