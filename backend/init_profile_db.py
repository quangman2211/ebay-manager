#!/usr/bin/env python3
"""
Initialize database with all tables including new profile features.
This script creates all tables from scratch, including the new profile fields.
"""

import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from database import engine
from models import Base


def init_database():
    """Initialize the database with all tables."""
    print("Initializing database with all tables...")
    print(f"Database URL: {engine.url}")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully!")
        
        # List the tables created
        print("\nTables created:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
        
        print("\nDatabase initialization completed!")
        return True
        
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = init_database()
    exit(0 if success else 1)