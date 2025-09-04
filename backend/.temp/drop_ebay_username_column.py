#!/usr/bin/env python3
"""
Database Migration Script: Drop ebay_username column
Safely removes the obsolete ebay_username column after data migration

Following SOLID principles:
- Single Responsibility: This script handles only column removal
- Open/Closed: Extensible for future column cleanup
"""

import sqlite3
import shutil
from datetime import datetime


class DropEbayUsernameColumn:
    """Handles dropping the obsolete ebay_username column"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.backup_path = f"{db_path}.pre_drop.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def backup_database(self) -> str:
        """Create a backup before dropping column"""
        print(f"Creating backup: {self.backup_path}")
        shutil.copy2(self.db_path, self.backup_path)
        return self.backup_path
    
    def verify_platform_username_populated(self) -> bool:
        """Verify all accounts have platform_username before dropping ebay_username"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM accounts 
                WHERE platform_username IS NULL OR platform_username = ''
            """)
            missing_platform_username = cursor.fetchone()[0]
            
            if missing_platform_username > 0:
                print(f"❌ Found {missing_platform_username} accounts without platform_username!")
                return False
            
            print("✅ All accounts have platform_username populated")
            return True
            
        finally:
            conn.close()
    
    def drop_ebay_username_column(self) -> bool:
        """Drop the ebay_username column using SQLite table recreation method"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # SQLite doesn't support DROP COLUMN directly, so we recreate the table
            print("Creating new accounts table without ebay_username...")
            
            # Create new accounts table without ebay_username
            cursor.execute("""
                CREATE TABLE accounts_new (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    platform_username VARCHAR NOT NULL,
                    name VARCHAR NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    account_type VARCHAR DEFAULT 'ebay',
                    connection_status VARCHAR DEFAULT 'authenticated',
                    last_sync_at DATETIME,
                    data_processing_enabled BOOLEAN DEFAULT 1,
                    settings TEXT DEFAULT '{}',
                    performance_metrics TEXT DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Copy data from old table to new table (excluding ebay_username)
            print("Copying data to new table...")
            cursor.execute("""
                INSERT INTO accounts_new (
                    id, user_id, platform_username, name, is_active, created_at,
                    account_type, connection_status, last_sync_at, data_processing_enabled,
                    settings, performance_metrics
                )
                SELECT 
                    id, user_id, platform_username, name, is_active, created_at,
                    account_type, connection_status, last_sync_at, data_processing_enabled,
                    settings, performance_metrics
                FROM accounts
            """)
            
            copied_rows = cursor.rowcount
            print(f"Copied {copied_rows} accounts to new table")
            
            # Drop old table and rename new one
            print("Replacing old table...")
            cursor.execute("DROP TABLE accounts")
            cursor.execute("ALTER TABLE accounts_new RENAME TO accounts")
            
            # Recreate indexes
            print("Recreating indexes...")
            cursor.execute("CREATE INDEX idx_accounts_platform_username ON accounts(platform_username)")
            cursor.execute("CREATE INDEX idx_accounts_user_id ON accounts(user_id)")
            
            conn.commit()
            print("✅ Successfully dropped ebay_username column")
            return True
            
        except Exception as e:
            print(f"❌ Error dropping column: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def verify_schema_updated(self) -> bool:
        """Verify the ebay_username column is gone"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("PRAGMA table_info(accounts)")
            columns = cursor.fetchall()
            
            print("\n=== UPDATED ACCOUNTS TABLE SCHEMA ===")
            for col in columns:
                print(f"{col[1]:25} {col[2]:15} NULL: {not col[3]:5}")
            
            # Check if ebay_username still exists
            column_names = [col[1] for col in columns]
            has_ebay_username = 'ebay_username' in column_names
            has_platform_username = 'platform_username' in column_names
            
            if has_ebay_username:
                print("❌ ebay_username column still exists!")
                return False
            
            if not has_platform_username:
                print("❌ platform_username column is missing!")
                return False
            
            print("✅ Schema updated correctly - ebay_username removed, platform_username retained")
            return True
            
        finally:
            conn.close()
    
    def run_column_drop(self) -> bool:
        """Execute the complete column drop process"""
        print("=== DROP EBAY_USERNAME COLUMN ===")
        print(f"Database: {self.db_path}")
        
        # Step 1: Backup database
        self.backup_database()
        
        # Step 2: Verify platform_username is populated
        if not self.verify_platform_username_populated():
            print("❌ Cannot drop ebay_username - platform_username not ready!")
            return False
        
        # Step 3: Drop the column
        if not self.drop_ebay_username_column():
            print("❌ Failed to drop ebay_username column!")
            return False
        
        # Step 4: Verify schema is updated
        if self.verify_schema_updated():
            print(f"✅ Column drop successful!")
            print(f"Backup saved as: {self.backup_path}")
            return True
        else:
            print("❌ Schema verification failed!")
            return False


def main():
    """Main execution"""
    db_path = "ebay_manager.db"
    
    dropper = DropEbayUsernameColumn(db_path)
    success = dropper.run_column_drop()
    
    if success:
        print("\n🎉 Database schema updated successfully!")
        print("ebay_username column has been removed")
        print("platform_username is now the primary username field")
    else:
        print("\n💥 Column drop failed! Check backup and try again.")
    
    return success


if __name__ == "__main__":
    main()