"""
Guest Account Service - Handles data preservation during account deletions
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import json
import logging
from datetime import datetime

from app.models import Account, CSVData, OrderStatus, UserAccountPermission, AccountSettings
from app.constants import GUEST_ACCOUNT_CONFIG, DeletionAction
from app.schemas import PermissionLevel

logger = logging.getLogger(__name__)


class GuestAccountService:
    """
    Service for managing GUEST account operations
    
    Single Responsibility: Handles all GUEST account related operations
    Open/Closed: Extensible for new data types without modification
    Dependency Inversion: Depends on database session abstraction
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_guest_account(self) -> Optional[Account]:
        """
        Get the system GUEST account
        Creates it automatically if it doesn't exist (lazy initialization)
        
        Returns:
            GUEST account instance or None if creation failed
        """
        guest_account = self.db.query(Account).filter(
            Account.platform_username == GUEST_ACCOUNT_CONFIG["PLATFORM_USERNAME"]
        ).first()
        
        if guest_account:
            return guest_account
            
        # GUEST account not found, attempt to create it (lazy initialization)
        logger.warning("GUEST account not found, attempting to create it automatically...")
        return self._create_guest_account_lazy()
    
    def _create_guest_account_lazy(self) -> Optional[Account]:
        """
        Lazy creation of GUEST account when it doesn't exist
        This is a fallback mechanism for runtime safety
        
        Returns:
            Created GUEST account or None if creation failed
        """
        try:
            # Verify admin user exists (required for GUEST account)
            from app.models import User
            admin_user = self.db.query(User).filter(User.id == GUEST_ACCOUNT_CONFIG["USER_ID"]).first()
            
            if not admin_user:
                logger.error(f"Admin user (ID: {GUEST_ACCOUNT_CONFIG['USER_ID']}) not found. Cannot create GUEST account.")
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
            
            self.db.add(guest_account)
            self.db.commit()
            self.db.refresh(guest_account)
            
            logger.info(f"✅ GUEST account created successfully via lazy initialization (ID: {guest_account.id})")
            logger.info(f"📋 GUEST account: {guest_account.name} - {guest_account.platform_username}")
            
            return guest_account
            
        except Exception as e:
            logger.error(f"❌ Failed to create GUEST account lazily: {e}")
            try:
                self.db.rollback()
            except:
                pass
            return None

    def is_guest_account(self, account: Account) -> bool:
        """
        Check if given account is the GUEST account
        
        Args:
            account: Account to check
            
        Returns:
            True if account is GUEST account
        """
        return (account.platform_username == GUEST_ACCOUNT_CONFIG["PLATFORM_USERNAME"] or
                account.account_type == "system")
    
    def transfer_account_data(
        self, 
        source_account: Account, 
        target_user_id: int
    ) -> Dict[str, Any]:
        """
        Transfer all data from source account to GUEST account
        
        Args:
            source_account: Account being deleted
            target_user_id: User performing the operation
            
        Returns:
            Transfer summary with counts
            
        Raises:
            ValueError: If GUEST account not found or transfer fails
        """
        guest_account = self.get_guest_account()
        if not guest_account:
            raise ValueError("GUEST account not available for data transfer")
        
        if not guest_account.id:
            raise ValueError("GUEST account has invalid ID")
            
        # Additional validation
        if not isinstance(guest_account.id, int) or guest_account.id <= 0:
            raise ValueError(f"GUEST account ID is invalid: {guest_account.id}")
        
        # Store GUEST account ID as variable to prevent SQLAlchemy session issues
        guest_account_id = guest_account.id
        logger.info(f"Using GUEST account ID: {guest_account_id} (type: {type(guest_account_id)})")
        
        logger.info(f"Starting data transfer from account {source_account.name} (ID: {source_account.id}) to GUEST (ID: {guest_account_id})")
        
        transfer_summary = {
            "source_account_id": source_account.id,
            "source_account_name": source_account.name,
            "guest_account_id": guest_account_id,
            "transferred_orders": 0,
            "transferred_listings": 0,
            "transferred_order_statuses": 0,
            "skipped_permissions": 0,
            "skipped_settings": 0,
            "transfer_timestamp": None,
            "errors": []
        }
        
        try:
            # 1. Transfer CSV data (orders and listings) to GUEST account
            csv_data_records = self.db.query(CSVData).filter(
                CSVData.account_id == source_account.id
            ).all()
            
            logger.info(f"Found {len(csv_data_records)} CSV records to transfer")
            
            # Early return if no data to transfer
            if not csv_data_records:
                logger.warning(f"No CSV records found for source account {source_account.id}")
                transfer_summary["transfer_timestamp"] = datetime.now().isoformat()
                return transfer_summary
            
            for i, csv_record in enumerate(csv_data_records, 1):
                logger.info(f"Processing CSV record {i}/{len(csv_data_records)}: ID={csv_record.id}, current account_id={csv_record.account_id}")
                
                # Validate record before transfer
                if csv_record.account_id != source_account.id:
                    logger.warning(f"CSV record {csv_record.id} has unexpected account_id {csv_record.account_id}, expected {source_account.id}")
                    continue
                    
                # Add metadata about original account
                original_metadata = {
                    "original_account_id": source_account.id,
                    "original_account_name": source_account.name,
                    "original_platform_username": source_account.platform_username,
                    "transferred_at": datetime.now().isoformat(),
                    "transferred_by": target_user_id
                }
                
                # Update account context with original account info
                try:
                    existing_context = json.loads(csv_record.account_context) if csv_record.account_context else {}
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Invalid JSON in account_context for record {csv_record.id}: {e}")
                    existing_context = {}
                
                existing_context.update(original_metadata)
                new_context = json.dumps(existing_context)
                
                # Log the transformation
                logger.debug(f"Updating context for record {csv_record.id}: {new_context}")
                csv_record.account_context = new_context
                
                # Transfer to GUEST account - use stored ID to prevent SQLAlchemy session issues
                old_account_id = csv_record.account_id
                csv_record.account_id = guest_account_id
                
                logger.info(f"✅ Transferred CSV record {csv_record.id}: {old_account_id} → {guest_account_id}, data_type={csv_record.data_type}")
                
                if csv_record.data_type == "order":
                    transfer_summary["transferred_orders"] += 1
                elif csv_record.data_type == "listing":
                    transfer_summary["transferred_listings"] += 1
            
            # 2. Update order statuses (they should automatically follow CSV data)
            order_statuses = self.db.query(OrderStatus).join(CSVData).filter(
                CSVData.account_id == guest_account_id  # Now pointing to guest account
            ).all()
            transfer_summary["transferred_order_statuses"] = len(order_statuses)
            
            # 3. Skip permissions and settings (don't transfer to GUEST account)
            permissions = self.db.query(UserAccountPermission).filter(
                UserAccountPermission.account_id == source_account.id
            ).all()
            transfer_summary["skipped_permissions"] = len(permissions)
            
            settings = self.db.query(AccountSettings).filter(
                AccountSettings.account_id == source_account.id
            ).all()
            transfer_summary["skipped_settings"] = len(settings)
            
            # 4. Delete permissions and settings (not needed for GUEST account)
            for permission in permissions:
                self.db.delete(permission)
            for setting in settings:
                self.db.delete(setting)
            
            # 5. Flush changes to database before validation (but don't commit yet)
            self.db.flush()
            logger.info("Database changes flushed before validation")
            
            # 6. Validate all CSV records have been properly transferred before committing
            validation_records = self.db.query(CSVData).filter(
                CSVData.account_id == guest_account_id
            ).all()
            
            # Count records that were transferred from this specific source account
            transferred_count = 0
            for record in validation_records:
                try:
                    context = json.loads(record.account_context or '{}')
                    if context.get('original_account_id') == source_account.id:
                        transferred_count += 1
                        logger.debug(f"Validated transferred record {record.id} from account {source_account.id}")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Invalid JSON in account_context for record {record.id}: {e}")
                    continue
            
            logger.info(f"Validation: {transferred_count} records transferred to GUEST account (expected: {len(csv_data_records)})")
            
            if transferred_count != len(csv_data_records):
                # Enhanced error reporting
                logger.error(f"Transfer validation failed:")
                logger.error(f"  Expected: {len(csv_data_records)} records")
                logger.error(f"  Found: {transferred_count} records")
                logger.error(f"  Source account ID: {source_account.id}")
                logger.error(f"  GUEST account ID: {guest_account_id}")
                
                # Log all validation records for debugging
                for i, record in enumerate(validation_records):
                    context = json.loads(record.account_context or '{}') if record.account_context else {}
                    logger.error(f"  Validation record {i+1}: ID={record.id}, original_account_id={context.get('original_account_id', 'None')}")
                
                raise ValueError(f"Transfer validation failed: expected {len(csv_data_records)} records, found {transferred_count}")
            
            # 7. Finally delete the source account and commit all changes
            self.db.delete(source_account)
            
            # Commit the entire transaction
            self.db.commit()
            logger.info(f"Transaction committed successfully - account {source_account.id} deleted and data transferred")
            
            transfer_summary["transfer_timestamp"] = datetime.now().isoformat()
            
            logger.info(f"Data transfer completed successfully:")
            logger.info(f"  Orders transferred: {transfer_summary['transferred_orders']}")
            logger.info(f"  Listings transferred: {transfer_summary['transferred_listings']}")
            logger.info(f"  Order statuses updated: {transfer_summary['transferred_order_statuses']}")
            
            return transfer_summary
            
        except Exception as e:
            logger.error(f"Error during data transfer: {e}")
            logger.error(f"Rolling back transaction for account {source_account.id}")
            transfer_summary["errors"].append(str(e))
            
            # Rollback transaction
            try:
                self.db.rollback()
                logger.info("Transaction rolled back successfully")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback transaction: {rollback_error}")
            
            raise ValueError(f"Data transfer failed: {str(e)}")
    
    def get_guest_account_summary(self) -> Dict[str, Any]:
        """
        Get summary of data stored in GUEST account
        
        Returns:
            Summary with counts and statistics
        """
        guest_account = self.get_guest_account()
        if not guest_account:
            return {"error": "GUEST account not found"}
        
        # Count data in GUEST account
        orders_count = self.db.query(CSVData).filter(
            and_(
                CSVData.account_id == guest_account.id,
                CSVData.data_type == "order"
            )
        ).count()
        
        listings_count = self.db.query(CSVData).filter(
            and_(
                CSVData.account_id == guest_account.id,
                CSVData.data_type == "listing"
            )
        ).count()
        
        # Get original account information from transferred data
        transferred_data = self.db.query(CSVData).filter(
            CSVData.account_id == guest_account.id
        ).all()
        
        original_accounts = set()
        for record in transferred_data:
            try:
                context = json.loads(record.account_context) if record.account_context else {}
                if "original_account_name" in context:
                    original_accounts.add(context["original_account_name"])
            except (json.JSONDecodeError, TypeError):
                continue
        
        return {
            "guest_account_id": guest_account.id,
            "guest_account_name": guest_account.name,
            "total_orders": orders_count,
            "total_listings": listings_count,
            "total_records": orders_count + listings_count,
            "original_accounts_count": len(original_accounts),
            "original_accounts": list(original_accounts)
        }
    
    def validate_account_deletion(self, account: Account) -> Dict[str, Any]:
        """
        Validate account for deletion and provide impact summary
        
        Args:
            account: Account to be deleted
            
        Returns:
            Validation result with data impact summary
        """
        if self.is_guest_account(account):
            return {
                "can_delete": False,
                "reason": "GUEST account cannot be deleted",
                "data_impact": None
            }
        
        # Count data that would be affected
        orders_count = self.db.query(CSVData).filter(
            and_(
                CSVData.account_id == account.id,
                CSVData.data_type == "order"
            )
        ).count()
        
        listings_count = self.db.query(CSVData).filter(
            and_(
                CSVData.account_id == account.id,
                CSVData.data_type == "listing"
            )
        ).count()
        
        permissions_count = self.db.query(UserAccountPermission).filter(
            UserAccountPermission.account_id == account.id
        ).count()
        
        settings_count = self.db.query(AccountSettings).filter(
            AccountSettings.account_id == account.id
        ).count()
        
        return {
            "can_delete": True,
            "data_impact": {
                "orders": orders_count,
                "listings": listings_count,
                "permissions": permissions_count,
                "settings": settings_count,
                "total_records": orders_count + listings_count
            }
        }