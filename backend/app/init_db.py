from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models import User
from app.auth import get_password_hash


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


if __name__ == "__main__":
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully!")
    
    print("Creating admin user...")
    create_admin_user()
    print("Database initialization complete!")