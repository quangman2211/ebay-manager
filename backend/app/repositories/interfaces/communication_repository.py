"""
Communication repository interfaces
Following SOLID principles - Interface Segregation and Dependency Inversion
YAGNI compliance: Essential data access operations only
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from app.models.communication import Email, EmailThread
from app.schemas.communication import EmailCreate, EmailUpdate, EmailThreadCreate, EmailThreadUpdate


class IEmailRepository(ABC):
    """
    SOLID: Interface Segregation - Email-specific data access operations
    """

    @abstractmethod
    async def create(self, email_data: EmailCreate) -> Email:
        """Create new email"""
        pass

    @abstractmethod
    async def get_by_id(self, email_id: int) -> Optional[Email]:
        """Get email by ID"""
        pass

    @abstractmethod
    async def get_by_gmail_id(self, gmail_id: str) -> Optional[Email]:
        """Get email by Gmail ID"""
        pass

    @abstractmethod
    async def get_by_thread_id(
        self, 
        thread_id: int, 
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[Email], int]:
        """Get emails in thread with pagination"""
        pass

    @abstractmethod
    async def update(self, email_id: int, email_data: EmailUpdate) -> Optional[Email]:
        """Update email"""
        pass

    @abstractmethod
    async def delete(self, email_id: int) -> bool:
        """Delete email"""
        pass

    @abstractmethod
    async def bulk_mark_processed(self, email_ids: List[int]) -> int:
        """Mark multiple emails as processed"""
        pass

    @abstractmethod
    async def get_unprocessed_emails(
        self, 
        account_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Email]:
        """Get unprocessed emails"""
        pass


class IEmailThreadRepository(ABC):
    """
    SOLID: Interface Segregation - Email thread-specific data access operations
    """

    @abstractmethod
    async def create(self, thread_data: EmailThreadCreate) -> EmailThread:
        """Create new email thread"""
        pass

    @abstractmethod
    async def get_by_id(self, thread_id: int) -> Optional[EmailThread]:
        """Get thread by ID"""
        pass

    @abstractmethod
    async def get_by_gmail_id(self, gmail_thread_id: str) -> Optional[EmailThread]:
        """Get thread by Gmail thread ID"""
        pass

    @abstractmethod
    async def get_by_account_id(
        self, 
        account_id: int, 
        page: int = 1, 
        page_size: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[EmailThread], int]:
        """Get threads for account with pagination and filters"""
        pass

    @abstractmethod
    async def update(self, thread_id: int, thread_data: EmailThreadUpdate) -> Optional[EmailThread]:
        """Update email thread"""
        pass

    @abstractmethod
    async def delete(self, thread_id: int) -> bool:
        """Delete email thread"""
        pass

    @abstractmethod
    async def get_threads_requiring_response(
        self, 
        account_id: Optional[int] = None,
        priority: Optional[str] = None
    ) -> List[EmailThread]:
        """Get threads that require response"""
        pass

    @abstractmethod
    async def mark_as_read(self, thread_ids: List[int]) -> int:
        """Mark threads as read"""
        pass

    @abstractmethod
    async def mark_as_responded(self, thread_id: int) -> bool:
        """Mark thread as responded"""
        pass

    @abstractmethod
    async def get_ebay_threads(
        self,
        account_id: int,
        message_type: Optional[str] = None,
        ebay_item_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[EmailThread], int]:
        """Get eBay-related threads with filters"""
        pass

    @abstractmethod
    async def get_thread_statistics(
        self, 
        account_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get thread statistics for account"""
        pass