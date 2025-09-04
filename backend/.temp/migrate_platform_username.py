#!/usr/bin/env python3
"""
Database Migration Script: Consolidate username fields
Migrates data from ebay_username to platform_username and removes duplicate field

Following SOLID principles:
- Single Responsibility: This script handles only username field migration
- Open/Closed: Extensible for future platform migrations
- Dependency Inversion: Uses database abstractions
"""

import sqlite3
import shutil
import os
from datetime import datetime


class UsernameMigration:
    """Handles migration of username fields from ebay_username to platform_username"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def backup_database(self) -> str:
        """Create a backup of the database before migration"""
        print(f"Creating backup: {self.backup_path}")
        shutil.copy2(self.db_path, self.backup_path)
        return self.backup_path
    
    def verify_data_integrity(self) -> bool:
        """Verify data integrity before migration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check for accounts with ebay_username but no platform_username
            cursor.execute("""
                SELECT COUNT(*) FROM accounts 
                WHERE ebay_username IS NOT NULL 
                AND (platform_username IS NULL OR platform_username = '')
            """)
            missing_platform_username = cursor.fetchone()[0]
            
            # Check for data inconsistencies
            cursor.execute("""
                SELECT COUNT(*) FROM accounts 
                WHERE ebay_username IS NOT NULL 
                AND platform_username IS NOT NULL 
                AND ebay_username != platform_username
            """)
            inconsistent_data = cursor.fetchone()[0]
            
            print(f"Accounts needing migration: {missing_platform_username}")
            print(f"Accounts with inconsistent data: {inconsistent_data}")
            
            return inconsistent_data == 0
            
        finally:
            conn.close()
    
    def migrate_username_data(self) -> int:
        """Migrate ebay_username data to platform_username where needed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update accounts where platform_username is missing but ebay_username exists
            cursor.execute("""
                UPDATE accounts 
                SET platform_username = ebay_username 
                WHERE ebay_username IS NOT NULL 
                AND (platform_username IS NULL OR platform_username = '')
            """)
            
            updated_rows = cursor.rowcount
            conn.commit()
            
            print(f"Updated {updated_rows} accounts with platform_username")
            return updated_rows
            
        finally:
            conn.close()
    
    def verify_migration_success(self) -> bool:
        """Verify that all accounts have platform_username populated"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check that all active accounts have platform_username
            cursor.execute("""
                SELECT COUNT(*) FROM accounts 
                WHERE is_active = 1 
                AND (platform_username IS NULL OR platform_username = '')
            """)
            missing_platform_username = cursor.fetchone()[0]
            
            # Show current state
            cursor.execute("""
                SELECT id, ebay_username, platform_username, name 
                FROM accounts 
                ORDER BY id
            """)
            accounts = cursor.fetchall()
            
            print("\n=== POST-MIGRATION ACCOUNT DATA ===")
            print("ID | ebay_username | platform_username | name")
            print("-" * 60)
            for account in accounts:
                ebay_user = account[1] or "NULL"
                platform_user = account[2] or "NULL"
                print(f"{account[0]:2} | {ebay_user:13} | {platform_user:17} | {account[3]}")
            
            return missing_platform_username == 0
            
        finally:
            conn.close()
    
    def run_migration(self) -> bool:
        """Execute the complete migration process"""
        print("=== USERNAME FIELD MIGRATION ===")
        print(f"Database: {self.db_path}")
        
        # Step 1: Backup database
        self.backup_database()
        
        # Step 2: Verify data integrity
        if not self.verify_data_integrity():
            print("❌ Data integrity check failed! Aborting migration.")
            return False
        
        # Step 3: Migrate data
        updated_count = self.migrate_username_data()
        
        # Step 4: Verify migration success
        if self.verify_migration_success():
            print(f"✅ Migration successful! Updated {updated_count} records.")
            print(f"Backup saved as: {self.backup_path}")
            return True
        else:
            print("❌ Migration verification failed!")
            return False


def main():
    """Main migration execution"""
    db_path = "ebay_manager.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    migration = UsernameMigration(db_path)
    success = migration.run_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("Next steps:")
        print("1. Update Account model to remove ebay_username field")
        print("2. Update backend CRUD operations")
        print("3. Update frontend components")
        print("4. Run tests to ensure everything works")
    else:
        print("\n💥 Migration failed! Check backup and try again.")
    
    return success


if __name__ == "__main__":
    main()