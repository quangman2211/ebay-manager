"""
Account Repository Implementation
Following SOLID principles - Single Responsibility for account data access
YAGNI: Essential account queries only
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.account import Account
from app.repositories.base import BaseRepository
from app.core.exceptions import EbayManagerException

class AccountRepositoryInterface(ABC):
    """
    SOLID: Interface Segregation & Dependency Inversion
    Essential account repository operations
    """
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[Account]:
        """Get account by ID"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> List[Account]:
        """Get accounts for specific user"""
        pass
    
    @abstractmethod
    async def get_by_ebay_user_id(self, ebay_user_id: str) -> Optional[Account]:
        """Get account by eBay user ID"""
        pass

class AccountRepository(BaseRepository[Account], AccountRepositoryInterface):
    """
    SOLID: Single Responsibility - Account data access only
    YAGNI: Essential operations only
    """
    
    def __init__(self, db: Session):
        super().__init__(db, Account)
    
    async def get_by_user_id(self, user_id: int) -> List[Account]:
        """Get accounts for specific user"""
        try:
            return self.db.query(Account).filter(
                Account.user_id == user_id
            ).all()
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get user accounts: {str(e)}")
    
    async def get_by_ebay_user_id(self, ebay_user_id: str) -> Optional[Account]:
        """Get account by eBay user ID"""
        try:
            return self.db.query(Account).filter(
                Account.ebay_user_id == ebay_user_id
            ).first()
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get account by eBay user ID: {str(e)}")
    
    async def is_active(self, account_id: int) -> bool:
        """Check if account is active"""
        try:
            account = await self.get_by_id(account_id)
            return account and account.status == 'active'
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to check account status: {str(e)}")