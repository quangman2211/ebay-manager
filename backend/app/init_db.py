from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models import User, Account
from app.auth import get_password_hash
from app.constants import GUEST_ACCOUNT_CONFIG


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def create_admin_user():
    """Create default admin user if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@ebaymanager.com",
                password_hash=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("Default admin user created: admin / admin123")
        else:
            print("Admin user already exists")
    finally:
        db.close()
        
        
def create_guest_account():
    """Create GUEST account for data preservation during account deletions"""
    db = SessionLocal()
    try:
        # Check if GUEST account already exists
        existing_guest = db.query(Account).filter(
            Account.platform_username == GUEST_ACCOUNT_CONFIG["PLATFORM_USERNAME"]
        ).first()
        
        if existing_guest:
            print(f"GUEST account already exists (ID: {existing_guest.id})")
            return
        
        # Verify admin user exists (required for GUEST account)
        admin_user = db.query(User).filter(User.id == 1).first()
        if not admin_user:
            print("ERROR: Admin user (ID: 1) not found. Please create admin user first.")
            return
        
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
        
        print(f"GUEST account created successfully (ID: {guest_account.id})")
        print(f"GUEST account details: {guest_account.name} - {guest_account.platform_username}")
        
    except Exception as e:
        print(f"ERROR: Failed to create GUEST account: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully!")
    
    print("Creating admin user...")
    create_admin_user()
    
    print("Creating GUEST account...")
    create_guest_account()
    
    print("Database initialization complete!")