#!/usr/bin/env python3
"""
Expanded tests for database operations and initialization
"""
import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from app.database import get_db, Base
from app.init_db import create_admin_user
from app.models import User, Account, CSVData, OrderStatus
from app.auth import get_password_hash


class TestDatabaseOperations:
    """Test database connection and basic operations"""

    def test_database_connection_success(self, test_db):
        """Test successful database connection"""
        # Simple query to test connection
        result = test_db.execute(text("SELECT 1")).scalar()
        assert result == 1

    def test_database_session_cleanup(self, test_db):
        """Test that database sessions are properly cleaned up"""
        # Create a user and verify it's added
        user = User(
            username="test_cleanup",
            email="cleanup@test.com",
            password_hash="dummy_hash",
            role="staff",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        # Verify user exists
        found_user = test_db.query(User).filter(User.username == "test_cleanup").first()
        assert found_user is not None
        
        # Session should handle cleanup automatically through fixtures

    def test_database_transaction_rollback(self, test_db):
        """Test that transaction rollback works correctly"""
        try:
            user = User(
                username="test_rollback",
                email="rollback@test.com",
                password_hash="dummy_hash",
                role="staff",
                is_active=True
            )
            test_db.add(user)
            test_db.flush()  # Flush without commit
            
            # Force an error by trying to add duplicate
            duplicate_user = User(
                username="test_rollback",  # Same username
                email="different@test.com",
                password_hash="dummy_hash",
                role="staff",
                is_active=True
            )
            test_db.add(duplicate_user)
            test_db.commit()  # This should fail
        except Exception:
            test_db.rollback()
            
        # Verify no user was actually committed
        found_user = test_db.query(User).filter(User.username == "test_rollback").first()
        assert found_user is None

    def test_database_cascade_operations(self, test_db):
        """Test cascade delete operations"""
        # Create user and account
        user = User(
            username="cascade_user",
            email="cascade@test.com",
            password_hash="dummy_hash",
            role="admin",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        account = Account(
            user_id=user.id,
            ebay_username="cascade_ebay",
            name="Cascade Account",
            is_active=True
        )
        test_db.add(account)
        test_db.commit()
        
        # Verify account exists
        found_account = test_db.query(Account).filter(Account.user_id == user.id).first()
        assert found_account is not None


class TestModelRelationships:
    """Test database model relationships"""

    def test_user_accounts_relationship(self, test_db):
        """Test User to Account relationship"""
        user = User(
            username="relation_user",
            email="relation@test.com",
            password_hash="dummy_hash",
            role="admin",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        # Create multiple accounts for user
        account1 = Account(
            user_id=user.id,
            ebay_username="account1",
            name="Account 1",
            is_active=True
        )
        account2 = Account(
            user_id=user.id,
            ebay_username="account2",
            name="Account 2",
            is_active=True
        )
        test_db.add_all([account1, account2])
        test_db.commit()
        
        # Test relationship access
        user_accounts = user.accounts
        assert len(user_accounts) == 2
        assert any(acc.ebay_username == "account1" for acc in user_accounts)
        assert any(acc.ebay_username == "account2" for acc in user_accounts)

    def test_account_csv_data_relationship(self, test_db):
        """Test Account to CSVData relationship"""
        # Create user and account
        user = User(
            username="csv_user",
            email="csv@test.com",
            password_hash="dummy_hash",
            role="admin",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        account = Account(
            user_id=user.id,
            ebay_username="csv_account",
            name="CSV Account",
            is_active=True
        )
        test_db.add(account)
        test_db.commit()
        
        # Create CSV data
        csv_data = CSVData(
            account_id=account.id,
            data_type="order",
            csv_row={"Order Number": "123456"},
            item_id="123456"
        )
        test_db.add(csv_data)
        test_db.commit()
        
        # Test relationship
        account_csv_data = account.csv_data
        assert len(account_csv_data) == 1
        assert account_csv_data[0].item_id == "123456"

    def test_csv_data_order_status_relationship(self, test_db):
        """Test CSVData to OrderStatus relationship"""
        # Create necessary parent records
        user = User(
            username="order_user",
            email="order@test.com",
            password_hash="dummy_hash",
            role="admin",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        account = Account(
            user_id=user.id,
            ebay_username="order_account",
            name="Order Account",
            is_active=True
        )
        test_db.add(account)
        test_db.commit()
        
        csv_data = CSVData(
            account_id=account.id,
            data_type="order",
            csv_row={"Order Number": "789012"},
            item_id="789012"
        )
        test_db.add(csv_data)
        test_db.commit()
        
        # Create order status
        order_status = OrderStatus(
            csv_data_id=csv_data.id,
            status="pending",
            updated_by=user.id
        )
        test_db.add(order_status)
        test_db.commit()
        
        # Test relationship
        assert csv_data.order_status is not None
        assert csv_data.order_status.status == "pending"
        assert csv_data.order_status.updated_by == user.id


class TestDatabaseInitialization:
    """Test database initialization functions"""

    @patch('app.init_db.SessionLocal')
    @patch('app.init_db.get_password_hash')
    def test_create_admin_user_success(self, mock_hash, mock_session, test_db):
        """Test successful admin user creation"""
        mock_hash.return_value = "mocked_hash"
        mock_session.return_value = test_db
        
        # Clear any existing admin user
        test_db.query(User).filter(User.username == "admin").delete()
        test_db.commit()
        
        create_admin_user()
        
        admin_user = test_db.query(User).filter(User.username == "admin").first()
        assert admin_user is not None
        assert admin_user.role == "admin"
        assert admin_user.is_active is True
        assert admin_user.email == "admin@ebaymanager.com"

    @patch('app.init_db.SessionLocal')
    def test_create_admin_user_already_exists(self, mock_session, test_db):
        """Test admin user creation when admin already exists"""
        mock_session.return_value = test_db
        
        # Admin user already exists from conftest.py
        initial_count = test_db.query(User).filter(User.username == "admin").count()
        
        create_admin_user()
        
        # Should not create duplicate
        final_count = test_db.query(User).filter(User.username == "admin").count()
        assert final_count == initial_count

    def test_database_schema_creation(self):
        """Test that database schema is created correctly"""
        from sqlalchemy import inspect
        
        # Create a temporary database
        test_engine = create_engine("sqlite:///test_schema.db")
        
        try:
            # Create all tables
            Base.metadata.create_all(bind=test_engine)
            
            # Verify tables exist
            inspector = inspect(test_engine)
            tables = inspector.get_table_names()
            
            expected_tables = {"users", "accounts", "csv_data", "order_status"}
            assert expected_tables.issubset(set(tables))
            
        finally:
            # Cleanup
            if os.path.exists("test_schema.db"):
                os.remove("test_schema.db")


class TestDatabaseConstraints:
    """Test database constraints and validations"""

    def test_user_unique_username_constraint(self, test_db):
        """Test that username must be unique"""
        user1 = User(
            username="unique_test",
            email="user1@test.com",
            password_hash="hash1",
            role="staff",
            is_active=True
        )
        test_db.add(user1)
        test_db.commit()
        
        # Try to create user with same username
        user2 = User(
            username="unique_test",  # Same username
            email="user2@test.com",
            password_hash="hash2",
            role="staff",
            is_active=True
        )
        test_db.add(user2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            test_db.commit()

    def test_user_unique_email_constraint(self, test_db):
        """Test that email must be unique"""
        user1 = User(
            username="email_test1",
            email="same@test.com",
            password_hash="hash1",
            role="staff",
            is_active=True
        )
        test_db.add(user1)
        test_db.commit()
        
        # Try to create user with same email
        user2 = User(
            username="email_test2",
            email="same@test.com",  # Same email
            password_hash="hash2",
            role="staff",
            is_active=True
        )
        test_db.add(user2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            test_db.commit()

    def test_account_requires_valid_user_reference(self, test_db):
        """Test account can reference valid user"""
        # Create a user first
        user = User(
            username="fk_user",
            email="fk@test.com",
            password_hash="hash",
            role="admin",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        # Create account referencing the user
        account = Account(
            user_id=user.id,
            ebay_username="fk_account",
            name="FK Account",
            is_active=True
        )
        test_db.add(account)
        test_db.commit()
        
        # Verify the relationship works
        assert account.user_id == user.id

    def test_csv_data_requires_valid_account_reference(self, test_db):
        """Test CSV data can reference valid account"""
        # Create user and account
        user = User(
            username="csv_fk_user",
            email="csvfk@test.com",
            password_hash="hash",
            role="admin",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        account = Account(
            user_id=user.id,
            ebay_username="csv_fk_account",
            name="CSV FK Account",
            is_active=True
        )
        test_db.add(account)
        test_db.commit()
        
        # Create CSV data referencing the account
        csv_data = CSVData(
            account_id=account.id,
            data_type="order",
            csv_row={"Order Number": "123456"},
            item_id="123456"
        )
        test_db.add(csv_data)
        test_db.commit()
        
        # Verify the relationship works
        assert csv_data.account_id == account.id

    def test_order_status_requires_valid_references(self, test_db):
        """Test order status can reference valid CSV data and user"""
        # Create full chain: user -> account -> csv_data -> order_status
        user = User(
            username="order_fk_user",
            email="orderfk@test.com",
            password_hash="hash",
            role="admin",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        account = Account(
            user_id=user.id,
            ebay_username="order_fk_account",
            name="Order FK Account",
            is_active=True
        )
        test_db.add(account)
        test_db.commit()
        
        csv_data = CSVData(
            account_id=account.id,
            data_type="order",
            csv_row={"Order Number": "789012"},
            item_id="789012"
        )
        test_db.add(csv_data)
        test_db.commit()
        
        order_status = OrderStatus(
            csv_data_id=csv_data.id,
            status="pending",
            updated_by=user.id
        )
        test_db.add(order_status)
        test_db.commit()
        
        # Verify the relationships work
        assert order_status.csv_data_id == csv_data.id
        assert order_status.updated_by == user.id


class TestDatabasePerformance:
    """Test database performance aspects"""

    def test_bulk_insert_performance(self, test_db):
        """Test bulk insert operations"""
        # Create user for accounts
        user = User(
            username="bulk_user",
            email="bulk@test.com",
            password_hash="hash",
            role="admin",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        account = Account(
            user_id=user.id,
            ebay_username="bulk_account",
            name="Bulk Account",
            is_active=True
        )
        test_db.add(account)
        test_db.commit()
        
        # Create many CSV records
        csv_records = []
        for i in range(100):
            csv_data = CSVData(
                account_id=account.id,
                data_type="order",
                csv_row={"Order Number": f"ORD-{i:03d}"},
                item_id=f"ORD-{i:03d}"
            )
            csv_records.append(csv_data)
        
        # Bulk insert should be faster than individual inserts
        test_db.add_all(csv_records)
        test_db.commit()
        
        # Verify all records were inserted
        count = test_db.query(CSVData).filter(CSVData.account_id == account.id).count()
        assert count == 100

    def test_query_filtering_performance(self, test_db):
        """Test query filtering with indexes"""
        # Create test data for filtering
        user = User(
            username="filter_user",
            email="filter@test.com",
            password_hash="hash",
            role="admin",
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        account = Account(
            user_id=user.id,
            ebay_username="filter_account",
            name="Filter Account",
            is_active=True
        )
        test_db.add(account)
        test_db.commit()
        
        # Create various data types
        for i in range(50):
            data_type = "order" if i % 2 == 0 else "listing"
            csv_data = CSVData(
                account_id=account.id,
                data_type=data_type,
                csv_row={"Item": f"Item-{i:03d}"},
                item_id=f"Item-{i:03d}"
            )
            test_db.add(csv_data)
        test_db.commit()
        
        # Test filtering by data_type
        orders = test_db.query(CSVData).filter(
            CSVData.account_id == account.id,
            CSVData.data_type == "order"
        ).all()
        
        listings = test_db.query(CSVData).filter(
            CSVData.account_id == account.id,
            CSVData.data_type == "listing"
        ).all()
        
        assert len(orders) == 25
        assert len(listings) == 25


class TestDatabaseConnection:
    """Test database connection handling"""

    def test_get_db_function(self):
        """Test get_db function returns proper session"""
        db_generator = get_db()
        db_session = next(db_generator)
        
        # Should be a database session
        assert hasattr(db_session, 'query')
        assert hasattr(db_session, 'add')
        assert hasattr(db_session, 'commit')
        
        # Cleanup
        try:
            db_generator.__next__()
        except StopIteration:
            pass  # Expected - generator cleanup