#!/usr/bin/env python3
"""
Database migration script to add profile fields to User model and create UserActivity table.
Run this script to update the database schema for the Profile Page feature.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Add the app directory to the path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from database import engine, SessionLocal
from models import Base


def check_column_exists(engine: Engine, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    with engine.connect() as conn:
        # For SQLite, we can check the table schema
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result.fetchall()]  # Column names are in index 1
        return column_name in columns


def check_table_exists(engine: Engine, table_name: str) -> bool:
    """Check if a table exists in the database."""
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        ), (table_name,))
        return result.fetchone() is not None


def add_profile_fields_to_users():
    """Add profile fields to the users table."""
    print("Adding profile fields to users table...")
    
    # Check which columns need to be added
    columns_to_add = [
        ('bio', 'TEXT'),
        ('phone', 'VARCHAR'),
        ('avatar_url', 'VARCHAR'),
        ('last_login', 'DATETIME')
    ]
    
    with engine.connect() as conn:
        for column_name, column_type in columns_to_add:
            if not check_column_exists(engine, 'users', column_name):
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                    conn.commit()
                    print(f"  ✓ Added column '{column_name}' to users table")
                except Exception as e:
                    print(f"  ✗ Error adding column '{column_name}': {e}")
                    conn.rollback()
            else:
                print(f"  - Column '{column_name}' already exists in users table")


def create_user_activities_table():
    """Create the user_activities table if it doesn't exist."""
    print("Creating user_activities table...")
    
    if not check_table_exists(engine, 'user_activities'):
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE user_activities (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        activity_type VARCHAR NOT NULL,
                        description TEXT,
                        activity_metadata JSON,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """))
                
                # Create index on user_id and activity_type for faster queries
                conn.execute(text("""
                    CREATE INDEX ix_user_activities_user_id ON user_activities (user_id)
                """))
                conn.execute(text("""
                    CREATE INDEX ix_user_activities_activity_type ON user_activities (activity_type)
                """))
                conn.execute(text("""
                    CREATE INDEX ix_user_activities_created_at ON user_activities (created_at)
                """))
                
                conn.commit()
                print("  ✓ Created user_activities table with indexes")
        except Exception as e:
            print(f"  ✗ Error creating user_activities table: {e}")
            return False
    else:
        print("  - user_activities table already exists")
    
    return True


def add_sample_activity_data():
    """Add some sample activity data for testing."""
    print("Adding sample activity data...")
    
    try:
        db = SessionLocal()
        
        # Check if we have any users
        result = db.execute(text("SELECT COUNT(*) FROM users")).fetchone()
        user_count = result[0] if result else 0
        
        if user_count == 0:
            print("  - No users found, skipping sample data creation")
            return
        
        # Check if activity data already exists
        result = db.execute(text("SELECT COUNT(*) FROM user_activities")).fetchone()
        activity_count = result[0] if result else 0
        
        if activity_count > 0:
            print("  - Activity data already exists, skipping sample data creation")
            return
        
        # Get the first user ID
        result = db.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
        user_id = result[0] if result else None
        
        if not user_id:
            print("  - No valid user ID found")
            return
        
        # Add some sample activities
        sample_activities = [
            {
                'user_id': user_id,
                'activity_type': 'login',
                'description': 'User logged in',
                'activity_metadata': '{"ip_address": "127.0.0.1", "user_agent": "Browser"}'
            },
            {
                'user_id': user_id,
                'activity_type': 'profile_update',
                'description': 'Updated profile information',
                'activity_metadata': '{"fields_updated": ["bio", "phone"]}'
            },
            {
                'user_id': user_id,
                'activity_type': 'csv_upload',
                'description': 'Uploaded CSV file',
                'activity_metadata': '{"filename": "orders.csv", "record_count": 25, "data_type": "order"}'
            }
        ]
        
        for activity in sample_activities:
            db.execute(text("""
                INSERT INTO user_activities (user_id, activity_type, description, activity_metadata, created_at)
                VALUES (:user_id, :activity_type, :description, :activity_metadata, datetime('now', '-' || abs(random()) % 168 || ' hours'))
            """), activity)
        
        db.commit()
        print(f"  ✓ Added {len(sample_activities)} sample activities for user {user_id}")
        
    except Exception as e:
        print(f"  ✗ Error adding sample activity data: {e}")
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()


def verify_migration():
    """Verify that the migration was successful."""
    print("\nVerifying migration...")
    
    # Check users table columns
    user_columns = ['bio', 'phone', 'avatar_url', 'last_login']
    missing_columns = []
    
    for column in user_columns:
        if not check_column_exists(engine, 'users', column):
            missing_columns.append(column)
    
    if missing_columns:
        print(f"  ✗ Missing columns in users table: {', '.join(missing_columns)}")
        return False
    else:
        print("  ✓ All profile columns exist in users table")
    
    # Check user_activities table
    if not check_table_exists(engine, 'user_activities'):
        print("  ✗ user_activities table does not exist")
        return False
    else:
        print("  ✓ user_activities table exists")
        
        # Check for some basic columns
        required_columns = ['id', 'user_id', 'activity_type', 'created_at']
        for column in required_columns:
            if not check_column_exists(engine, 'user_activities', column):
                print(f"  ✗ Missing column '{column}' in user_activities table")
                return False
        
        print("  ✓ user_activities table has all required columns")
    
    print("  ✓ Migration verification successful")
    return True


def main():
    """Run the complete migration process."""
    print("Starting Profile Page database migration...")
    print(f"Database URL: {engine.url}")
    print("=" * 60)
    
    try:
        # Step 1: Add profile fields to users table
        add_profile_fields_to_users()
        print()
        
        # Step 2: Create user_activities table
        if create_user_activities_table():
            print()
            
            # Step 3: Add sample data
            add_sample_activity_data()
            print()
        
        # Step 4: Verify migration
        if verify_migration():
            print("\n" + "=" * 60)
            print("✓ Profile Page database migration completed successfully!")
            print("\nYou can now:")
            print("1. Start the backend server: python -m app.main")
            print("2. Access the Profile page in the frontend")
            print("3. Test profile updates and avatar uploads")
        else:
            print("\n" + "=" * 60)
            print("✗ Migration verification failed. Please check the errors above.")
            return 1
            
    except Exception as e:
        print(f"\n✗ Migration failed with error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())