"""
Permission Service - Sprint 7
Handles user-account permission management following SOLID principles
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models import User, Account, UserAccountPermission
from app.schemas import (
    UserAccountPermissionCreate,
    UserAccountPermissionUpdate,
    UserAccountPermissionResponse,
    BulkPermissionRequest,
    BulkPermissionResponse,
    PermissionLevel
)

class PermissionError(Exception):
    """Custom exception for permission-related errors"""
    pass

logger = logging.getLogger(__name__)


class PermissionService:
    """
    Permission management service following SOLID principles
    
    Single Responsibility: Manages user-account permissions only
    Open/Closed: Extensible for new permission types
    Interface Segregation: Clean permission-focused interface
    Dependency Inversion: Depends on database session abstraction
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_permission(
        self,
        permission_data: UserAccountPermissionCreate,
        granting_user: User
    ) -> UserAccountPermissionResponse:
        """
        Create a new user-account permission
        
        Args:
            permission_data: Permission creation data
            granting_user: User granting the permission
            
        Returns:
            Created permission
            
        Raises:
            ValueError: If user or account not found
            PermissionError: If granting user lacks permission
        """
        # Validate user and account exist
        user = self.db.query(User).filter(User.id == permission_data.user_id).first()
        if not user:
            raise ValueError(f"User with ID {permission_data.user_id} not found")
        
        account = self.db.query(Account).filter(Account.id == permission_data.account_id).first()
        if not account:
            raise ValueError(f"Account with ID {permission_data.account_id} not found")
        
        # Check if granting user has permission to grant permissions
        self._validate_permission_grant_authority(
            granting_user, 
            permission_data.account_id, 
            permission_data.permission_level
        )
        
        # Check if permission already exists
        existing = self.db.query(UserAccountPermission).filter(
            and_(
                UserAccountPermission.user_id == permission_data.user_id,
                UserAccountPermission.account_id == permission_data.account_id
            )
        ).first()
        
        if existing:
            # Update existing permission
            existing.permission_level = permission_data.permission_level.value
            existing.is_active = permission_data.is_active
            existing.granted_by = granting_user.id
            self.db.commit()
            self.db.refresh(existing)
            
            logger.info(f"Updated permission for user {user.username} on account {account.name}")
            return UserAccountPermissionResponse.model_validate(existing)
        else:
            # Create new permission
            permission = UserAccountPermission(
                user_id=permission_data.user_id,
                account_id=permission_data.account_id,
                permission_level=permission_data.permission_level.value,
                granted_by=granting_user.id,
                is_active=permission_data.is_active
            )
            
            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)
            
            logger.info(f"Created permission for user {user.username} on account {account.name}")
            return UserAccountPermissionResponse.model_validate(permission)
    
    def update_permission(
        self,
        permission_id: int,
        update_data: UserAccountPermissionUpdate,
        updating_user: User
    ) -> UserAccountPermissionResponse:
        """
        Update an existing permission
        
        Args:
            permission_id: Permission ID to update
            update_data: Updated permission data
            updating_user: User making the update
            
        Returns:
            Updated permission
            
        Raises:
            ValueError: If permission not found
            PermissionError: If updating user lacks authority
        """
        # Get existing permission
        permission = self.db.query(UserAccountPermission).filter(
            UserAccountPermission.id == permission_id
        ).first()
        
        if not permission:
            raise ValueError(f"Permission with ID {permission_id} not found")
        
        # Validate authority to update
        if update_data.permission_level:
            self._validate_permission_grant_authority(
                updating_user,
                permission.account_id,
                update_data.permission_level
            )
        
        # Update fields
        if update_data.permission_level is not None:
            permission.permission_level = update_data.permission_level.value
        if update_data.is_active is not None:
            permission.is_active = update_data.is_active
        
        permission.granted_by = updating_user.id
        
        self.db.commit()
        self.db.refresh(permission)
        
        logger.info(f"Updated permission ID {permission_id}")
        return UserAccountPermissionResponse.from_orm(permission)
    
    def revoke_permission(
        self,
        permission_id: int,
        revoking_user: User
    ) -> bool:
        """
        Revoke (deactivate) a user permission
        
        Args:
            permission_id: Permission to revoke
            revoking_user: User revoking the permission
            
        Returns:
            True if successfully revoked
            
        Raises:
            ValueError: If permission not found
            PermissionError: If revoking user lacks authority
        """
        # Get existing permission
        permission = self.db.query(UserAccountPermission).filter(
            UserAccountPermission.id == permission_id
        ).first()
        
        if not permission:
            raise ValueError(f"Permission with ID {permission_id} not found")
        
        # Validate authority to revoke (need admin permission on account)
        self._validate_permission_grant_authority(
            revoking_user,
            permission.account_id,
            PermissionLevel.ADMIN
        )
        
        # Deactivate permission
        permission.is_active = False
        permission.granted_by = revoking_user.id
        
        self.db.commit()
        
        logger.info(f"Revoked permission ID {permission_id}")
        return True
    
    def get_user_permissions(
        self,
        user_id: int,
        requesting_user: User
    ) -> List[UserAccountPermissionResponse]:
        """
        Get all permissions for a specific user
        
        Args:
            user_id: User to get permissions for
            requesting_user: User making the request
            
        Returns:
            List of user permissions
            
        Raises:
            PermissionError: If requesting user lacks authority
        """
        # Only admin or the user themselves can view permissions
        if requesting_user.role != "admin" and requesting_user.id != user_id:
            raise PermissionError("Not authorized to view user permissions")
        
        permissions = self.db.query(UserAccountPermission).filter(
            UserAccountPermission.user_id == user_id
        ).all()
        
        return [UserAccountPermissionResponse.model_validate(p) for p in permissions]
    
    def get_account_permissions(
        self,
        account_id: int,
        requesting_user: User
    ) -> List[UserAccountPermissionResponse]:
        """
        Get all permissions for a specific account
        
        Args:
            account_id: Account to get permissions for
            requesting_user: User making the request
            
        Returns:
            List of account permissions
            
        Raises:
            PermissionError: If requesting user lacks authority
        """
        # Verify user has admin access to this account
        self._validate_permission_grant_authority(
            requesting_user,
            account_id,
            PermissionLevel.ADMIN
        )
        
        permissions = self.db.query(UserAccountPermission).filter(
            UserAccountPermission.account_id == account_id
        ).all()
        
        return [UserAccountPermissionResponse.model_validate(p) for p in permissions]
    
    def bulk_update_permissions(
        self,
        bulk_request: BulkPermissionRequest,
        updating_user: User
    ) -> BulkPermissionResponse:
        """
        Update multiple permissions at once
        
        Args:
            bulk_request: Bulk permission update request
            updating_user: User making the updates
            
        Returns:
            Bulk update response with results and errors
        """
        updated_count = 0
        errors = []
        
        # Verify user has admin access to the account
        try:
            self._validate_permission_grant_authority(
                updating_user,
                bulk_request.account_id,
                PermissionLevel.ADMIN
            )
        except Exception as e:
            return BulkPermissionResponse(
                account_id=bulk_request.account_id,
                updated_count=0,
                errors=[str(e)]
            )
        
        # Process each permission
        for permission_data in bulk_request.permissions:
            try:
                # Override account_id to ensure consistency
                permission_data.account_id = bulk_request.account_id
                
                self.create_permission(permission_data, updating_user)
                updated_count += 1
                
            except Exception as e:
                errors.append(f"User {permission_data.user_id}: {str(e)}")
        
        logger.info(f"Bulk updated {updated_count} permissions for account {bulk_request.account_id}")
        
        return BulkPermissionResponse(
            account_id=bulk_request.account_id,
            updated_count=updated_count,
            errors=errors
        )
    
    def check_user_permission(
        self,
        user_id: int,
        account_id: int,
        required_level: PermissionLevel
    ) -> bool:
        """
        Check if user has required permission level for account
        
        Args:
            user_id: User to check
            account_id: Account to check access for
            required_level: Minimum required permission level
            
        Returns:
            True if user has required permission
        """
        # Get user to check admin status
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Admin has access to everything
        if user.role == "admin":
            return True
        
        # Check specific permission
        permission = self.db.query(UserAccountPermission).filter(
            and_(
                UserAccountPermission.user_id == user_id,
                UserAccountPermission.account_id == account_id,
                UserAccountPermission.is_active == True
            )
        ).first()
        
        if not permission:
            return False
        
        # Check permission level
        permission_levels = {"view": 1, "edit": 2, "admin": 3}
        user_level = permission_levels.get(permission.permission_level, 0)
        required_level_num = permission_levels.get(required_level.value, 3)
        
        return user_level >= required_level_num
    
    def _validate_permission_grant_authority(
        self,
        granting_user: User,
        account_id: int,
        permission_level: PermissionLevel
    ):
        """
        Validate that user has authority to grant/modify permissions
        
        Args:
            granting_user: User attempting to grant permission
            account_id: Account the permission is for
            permission_level: Level of permission being granted
            
        Raises:
            PermissionError: If user lacks authority
        """
        # Global admin can grant any permission
        if granting_user.role == "admin":
            return
        
        # Check if user has admin permission on this specific account
        has_admin = self.check_user_permission(
            granting_user.id,
            account_id,
            PermissionLevel.ADMIN
        )
        
        if not has_admin:
            raise PermissionError(
                f"User {granting_user.username} lacks authority to manage permissions for account {account_id}"
            )
        
        # Users with account admin can grant view/edit but not admin to others
        if permission_level == PermissionLevel.ADMIN:
            raise PermissionError(
                "Only global admins can grant admin permissions"
            )