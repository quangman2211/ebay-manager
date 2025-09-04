"""
Account Service - Sprint 7
Handles business logic for eBay account management following SOLID principles
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, date
import json
import logging

from app.models import Account, User, UserAccountPermission, AccountSettings, AccountMetrics
from app.schemas import (
    AccountCreate, AccountUpdateRequest, EnhancedAccountResponse,
    UserAccountPermissionCreate, UserAccountPermissionUpdate,
    AccountSettingsCreate, AccountSettingsUpdate,
    PermissionLevel, ConnectionStatus, AccountType
)

logger = logging.getLogger(__name__)


class PermissionError(Exception):
    """Custom exception for permission-related errors"""
    pass


class AccountService:
    """
    Account management service following SOLID principles
    
    Single Responsibility: Manages account-related business logic
    Open/Closed: Extensible for new account types without modification
    Dependency Inversion: Depends on database session abstraction
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_account(
        self, 
        account_data: AccountCreate, 
        creator_user: User
    ) -> Account:
        """
        Create a new eBay account with proper permission checks
        
        Args:
            account_data: Account creation data
            creator_user: User creating the account
            
        Returns:
            Created account instance
            
        Raises:
            PermissionError: If user lacks permission to create account
        """
        # Permission check: Only admin can create accounts for others
        if creator_user.role != "admin" and account_data.user_id != creator_user.id:
            raise PermissionError("Not authorized to create account for other users")
        
        # If user_id not provided, assign to current user
        if not account_data.user_id:
            account_data.user_id = creator_user.id
        
        # Validate the target user exists
        target_user = self.db.query(User).filter(User.id == account_data.user_id).first()
        if not target_user:
            raise ValueError(f"User with ID {account_data.user_id} not found")
        
        # Create account - REDESIGNED STATUS FIELDS
        db_account = Account(
            user_id=account_data.user_id,
            platform_username=account_data.platform_username,
            name=account_data.name,
            is_active=account_data.is_active,
            account_type="ebay",
            connection_status="authenticated",
            data_processing_enabled=True,
            settings='{"auto_sync": true, "notification_email": true}',
            performance_metrics='{}'
        )
        
        self.db.add(db_account)
        self.db.commit()
        self.db.refresh(db_account)
        
        # Create default permission for the account owner
        self._create_default_permission(db_account, creator_user)
        
        logger.info(f"Account created: {db_account.name} (ID: {db_account.id})")
        return db_account
    
    def update_account(
        self,
        account_id: int,
        update_data: AccountUpdateRequest,
        user: User
    ) -> Account:
        """
        Update account details with permission validation
        
        Args:
            account_id: ID of account to update
            update_data: Fields to update
            user: User making the update
            
        Returns:
            Updated account instance
            
        Raises:
            PermissionError: If user lacks permission
            ValueError: If account not found
        """
        # Get account and verify permissions
        account = self._get_account_with_permission_check(account_id, user, PermissionLevel.EDIT)
        
        # Update fields if provided
        if update_data.platform_username is not None:
            account.platform_username = update_data.platform_username
        if update_data.name is not None:
            account.name = update_data.name
        if update_data.is_active is not None:
            account.is_active = update_data.is_active
        if update_data.connection_status is not None:
            account.connection_status = update_data.connection_status.value
        if update_data.data_processing_enabled is not None:
            account.data_processing_enabled = update_data.data_processing_enabled
            
        self.db.commit()
        self.db.refresh(account)
        
        logger.info(f"Account updated: {account.name} (ID: {account.id}) by user {user.username}")
        return account
    
    def get_user_accounts(
        self,
        user: User,
        include_inactive: bool = False
    ) -> List[Account]:
        """
        Get all accounts accessible to user based on permissions
        
        Args:
            user: User requesting accounts
            include_inactive: Whether to include inactive accounts
            
        Returns:
            List of accessible accounts
        """
        if user.role == "admin":
            # Admin can see all accounts
            query = self.db.query(Account)
            if not include_inactive:
                query = query.filter(Account.is_active == True)
            return query.all()
        else:
            # Staff can only see accounts they have permissions for
            query = self.db.query(Account).join(UserAccountPermission).filter(
                and_(
                    UserAccountPermission.user_id == user.id,
                    UserAccountPermission.is_active == True
                )
            )
            if not include_inactive:
                query = query.filter(Account.is_active == True)
            return query.all()
    
    def get_account_details(
        self,
        account_id: int,
        user: User
    ) -> EnhancedAccountResponse:
        """
        Get detailed account information with permissions and settings
        
        Args:
            account_id: Account ID to retrieve
            user: User requesting details
            
        Returns:
            Enhanced account response with full details
            
        Raises:
            PermissionError: If user lacks view permission
            ValueError: If account not found
        """
        # Get account and verify permissions
        account = self._get_account_with_permission_check(account_id, user, PermissionLevel.VIEW)
        
        # Parse JSON settings safely
        try:
            settings = json.loads(account.settings) if account.settings else {}
            performance_metrics = json.loads(account.performance_metrics) if account.performance_metrics else {}
        except json.JSONDecodeError:
            settings = {}
            performance_metrics = {}
        
        # Get user permissions for this account (for admins)
        user_permissions = []
        if user.role == "admin":
            permissions = self.db.query(UserAccountPermission).filter(
                UserAccountPermission.account_id == account_id
            ).all()
            # Convert to dictionaries to avoid session issues
            user_permissions = [
                {
                    "id": perm.id,
                    "user_id": perm.user_id,
                    "account_id": perm.account_id,
                    "permission_level": perm.permission_level,
                    "granted_by": perm.granted_by,
                    "granted_at": perm.granted_at,
                    "is_active": perm.is_active
                }
                for perm in permissions
            ]
        
        # Return enhanced response
        return EnhancedAccountResponse(
            id=account.id,
            user_id=account.user_id,
            platform_username=account.platform_username,
            name=account.name,
            is_active=account.is_active,
            created_at=account.created_at,
            account_type=account.account_type,
            connection_status=account.connection_status,
            last_sync_at=account.last_sync_at,
            data_processing_enabled=account.data_processing_enabled,
            settings=settings,
            performance_metrics=performance_metrics,
            user_permissions=user_permissions
        )
    
    def deactivate_account(
        self,
        account_id: int,
        user: User
    ) -> Account:
        """
        Deactivate an account (soft delete)
        
        Args:
            account_id: Account ID to deactivate
            user: User performing deactivation
            
        Returns:
            Deactivated account
            
        Raises:
            PermissionError: If user lacks admin permission
        """
        # Get account and verify admin permissions
        account = self._get_account_with_permission_check(account_id, user, PermissionLevel.ADMIN)
        
        account.is_active = False
        self.db.commit()
        self.db.refresh(account)
        
        logger.info(f"Account deactivated: {account.name} (ID: {account.id}) by user {user.username}")
        return account
    
    def update_account_settings(
        self,
        account_id: int,
        settings_updates: List[AccountSettingsUpdate],
        user: User
    ) -> List[AccountSettings]:
        """
        Update account settings
        
        Args:
            account_id: Account ID
            settings_updates: List of setting updates
            user: User making updates
            
        Returns:
            Updated settings list
            
        Raises:
            PermissionError: If user lacks edit permission
        """
        # Verify permissions
        self._get_account_with_permission_check(account_id, user, PermissionLevel.EDIT)
        
        updated_settings = []
        
        for setting_update in settings_updates:
            # Find existing setting or create new one
            setting = self.db.query(AccountSettings).filter(
                and_(
                    AccountSettings.account_id == account_id,
                    AccountSettings.setting_key == setting_update.setting_key
                )
            ).first()
            
            if setting:
                # Update existing
                if setting_update.setting_value is not None:
                    setting.setting_value = setting_update.setting_value
                if setting_update.setting_type is not None:
                    setting.setting_type = setting_update.setting_type
                setting.updated_by = user.id
            else:
                # Create new setting
                setting = AccountSettings(
                    account_id=account_id,
                    setting_key=setting_update.setting_key,
                    setting_value=setting_update.setting_value,
                    setting_type=setting_update.setting_type or "string",
                    updated_by=user.id
                )
                self.db.add(setting)
            
            updated_settings.append(setting)
        
        self.db.commit()
        
        logger.info(f"Updated {len(updated_settings)} settings for account {account_id}")
        return updated_settings
    
    def _get_account_with_permission_check(
        self,
        account_id: int,
        user: User,
        required_permission: PermissionLevel
    ) -> Account:
        """
        Get account and verify user has required permission
        
        Args:
            account_id: Account ID to check
            user: User to check permissions for
            required_permission: Minimum required permission level
            
        Returns:
            Account instance if permission check passes
            
        Raises:
            ValueError: If account not found
            PermissionError: If user lacks required permission
        """
        # Get account
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
        
        # Admin has access to everything
        if user.role == "admin":
            return account
        
        # Check user permission for this account
        permission = self.db.query(UserAccountPermission).filter(
            and_(
                UserAccountPermission.user_id == user.id,
                UserAccountPermission.account_id == account_id,
                UserAccountPermission.is_active == True
            )
        ).first()
        
        if not permission:
            raise PermissionError(f"No permission for account {account_id}")
        
        # Check permission level
        permission_levels = {"view": 1, "edit": 2, "admin": 3}
        user_level = permission_levels.get(permission.permission_level, 0)
        required_level = permission_levels.get(required_permission.value, 3)
        
        if user_level < required_level:
            raise PermissionError(
                f"Insufficient permission: need {required_permission.value}, have {permission.permission_level}"
            )
        
        return account
    
    def _create_default_permission(
        self,
        account: Account,
        creator_user: User
    ) -> UserAccountPermission:
        """
        Create default permission for account owner
        
        Args:
            account: Account to create permission for
            creator_user: User who created the account
            
        Returns:
            Created permission record
        """
        permission_level = "admin" if creator_user.role == "admin" else "edit"
        
        permission = UserAccountPermission(
            user_id=account.user_id,
            account_id=account.id,
            permission_level=permission_level,
            granted_by=creator_user.id,
            is_active=True
        )
        
        self.db.add(permission)
        self.db.commit()
        
        return permission