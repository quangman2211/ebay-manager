"""
eBay Message repository interfaces
Following SOLID principles - Interface Segregation and Dependency Inversion
YAGNI compliance: Essential data access operations only
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from app.models.communication import EbayMessage, MessageThread
from app.schemas.communication import EbayMessageCreate, EbayMessageUpdate, MessageThreadCreate, MessageThreadUpdate


class IEbayMessageRepository(ABC):
    """
    SOLID: Interface Segregation - eBay message-specific data access operations
    """

    @abstractmethod
    async def create(self, message_data: EbayMessageCreate) -> EbayMessage:
        """Create new eBay message"""
        pass

    @abstractmethod
    async def get_by_id(self, message_id: int) -> Optional[EbayMessage]:
        """Get eBay message by ID"""
        pass

    @abstractmethod
    async def get_by_ebay_id(self, ebay_message_id: str) -> Optional[EbayMessage]:
        """Get eBay message by eBay message ID"""
        pass

    @abstractmethod
    async def get_by_thread_id(
        self, 
        thread_id: int, 
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[EbayMessage], int]:
        """Get eBay messages in thread with pagination"""
        pass

    @abstractmethod
    async def get_by_account_id(
        self, 
        account_id: int, 
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[EbayMessage], int]:
        """Get eBay messages for account with pagination and filters"""
        pass

    @abstractmethod
    async def update(self, message_id: int, message_data: EbayMessageUpdate) -> Optional[EbayMessage]:
        """Update eBay message"""
        pass

    @abstractmethod
    async def delete(self, message_id: int) -> bool:
        """Delete eBay message"""
        pass

    @abstractmethod
    async def get_pending_response_count(self, account_id: int) -> int:
        """Get count of messages requiring response"""
        pass

    @abstractmethod
    async def get_counts_by_type(
        self, 
        account_id: int, 
        date_from: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Get message counts by type for account"""
        pass

    @abstractmethod
    async def bulk_mark_processed(self, message_ids: List[int]) -> int:
        """Mark multiple messages as processed"""
        pass

    @abstractmethod
    async def get_messages_by_item(
        self, 
        account_id: int, 
        item_id: str,
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[EbayMessage], int]:
        """Get messages for specific item"""
        pass


class IMessageThreadRepository(ABC):
    """
    SOLID: Interface Segregation - Message thread-specific data access operations
    """

    @abstractmethod
    async def create(self, thread_data: MessageThreadCreate) -> MessageThread:
        """Create new message thread"""
        pass

    @abstractmethod
    async def get_by_id(self, thread_id: int) -> Optional[MessageThread]:
        """Get thread by ID"""
        pass

    @abstractmethod
    async def get_by_account_id(
        self, 
        account_id: int, 
        page: int = 1, 
        page_size: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[MessageThread], int]:
        """Get threads for account with pagination and filters"""
        pass

    @abstractmethod
    async def find_by_item_and_customer(
        self, 
        account_id: int, 
        item_id: str, 
        customer_username: str
    ) -> Optional[MessageThread]:
        """Find thread by item and customer for eBay messages"""
        pass

    @abstractmethod
    async def update(self, thread_id: int, thread_data: MessageThreadUpdate) -> Optional[MessageThread]:
        """Update message thread"""
        pass

    @abstractmethod
    async def delete(self, thread_id: int) -> bool:
        """Delete message thread"""
        pass

    @abstractmethod
    async def get_threads_requiring_response(
        self, 
        account_id: Optional[int] = None,
        priority: Optional[str] = None
    ) -> List[MessageThread]:
        """Get threads that require response"""
        pass

    @abstractmethod
    async def mark_as_responded(self, thread_id: int) -> bool:
        """Mark thread as responded"""
        pass

    @abstractmethod
    async def get_counts_by_status(
        self, 
        account_id: int,
        date_from: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Get thread counts by status for account"""
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