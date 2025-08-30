"""
eBay Message repository implementations
Following SOLID principles - Single Responsibility and Dependency Inversion
YAGNI compliance: Essential database operations only
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import and_, or_, desc, asc, func, update
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.repositories.interfaces.ebay_message_repository import IEbayMessageRepository, IMessageThreadRepository
from app.models.communication import EbayMessage, MessageThread
from app.schemas.communication import EbayMessageCreate, EbayMessageUpdate, MessageThreadCreate, MessageThreadUpdate
from app.core.exceptions import DatabaseError, NotFoundError


class EbayMessageRepository(IEbayMessageRepository):
    """
    SOLID: Single Responsibility - eBay message data access operations
    SOLID: Dependency Inversion - Depends on database session interface
    """

    def __init__(self, db: Session):
        self.db = db

    async def create(self, message_data: EbayMessageCreate) -> EbayMessage:
        """Create new eBay message"""
        try:
            # Convert Pydantic model to dict, handling enums
            message_dict = message_data.dict()
            
            # Convert enum values to strings
            if 'direction' in message_dict and hasattr(message_dict['direction'], 'value'):
                message_dict['direction'] = message_dict['direction'].value
            if 'message_type' in message_dict and hasattr(message_dict['message_type'], 'value'):
                message_dict['message_type'] = message_dict['message_type'].value
            if 'priority' in message_dict and hasattr(message_dict['priority'], 'value'):
                message_dict['priority'] = message_dict['priority'].value

            db_message = EbayMessage(**message_dict)
            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)
            return db_message
        except IntegrityError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create eBay message: {str(e)}")

    async def get_by_id(self, message_id: int) -> Optional[EbayMessage]:
        """Get eBay message by ID"""
        try:
            return self.db.query(EbayMessage)\
                .options(joinedload(EbayMessage.thread))\
                .filter(EbayMessage.id == message_id)\
                .first()
        except Exception as e:
            raise DatabaseError(f"Failed to get eBay message {message_id}: {str(e)}")

    async def get_by_ebay_id(self, ebay_message_id: str) -> Optional[EbayMessage]:
        """Get eBay message by eBay message ID"""
        try:
            return self.db.query(EbayMessage)\
                .filter(EbayMessage.ebay_message_id == ebay_message_id)\
                .first()
        except Exception as e:
            raise DatabaseError(f"Failed to get eBay message by eBay ID {ebay_message_id}: {str(e)}")

    async def get_by_thread_id(
        self, 
        thread_id: int, 
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[EbayMessage], int]:
        """Get eBay messages in thread with pagination"""
        try:
            # Get total count
            total = self.db.query(EbayMessage)\
                .filter(EbayMessage.thread_id == thread_id)\
                .count()

            # Get paginated results
            offset = (page - 1) * page_size
            messages = self.db.query(EbayMessage)\
                .filter(EbayMessage.thread_id == thread_id)\
                .order_by(asc(EbayMessage.message_date))\
                .offset(offset)\
                .limit(page_size)\
                .all()

            return messages, total
        except Exception as e:
            raise DatabaseError(f"Failed to get eBay messages for thread {thread_id}: {str(e)}")

    async def get_by_account_id(
        self, 
        account_id: int, 
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[EbayMessage], int]:
        """Get eBay messages for account with pagination and filters"""
        try:
            query = self.db.query(EbayMessage)\
                .filter(EbayMessage.account_id == account_id)

            # Apply filters
            if filters:
                if filters.get('message_type'):
                    query = query.filter(EbayMessage.message_type == filters['message_type'])
                
                if filters.get('priority'):
                    query = query.filter(EbayMessage.priority == filters['priority'])
                
                if filters.get('direction'):
                    query = query.filter(EbayMessage.direction == filters['direction'])
                
                if filters.get('requires_response') is not None:
                    query = query.filter(EbayMessage.requires_response == filters['requires_response'])
                
                if filters.get('item_id'):
                    query = query.filter(EbayMessage.item_id == filters['item_id'])
                
                if filters.get('date_from'):
                    query = query.filter(EbayMessage.message_date >= filters['date_from'])
                
                if filters.get('date_to'):
                    query = query.filter(EbayMessage.message_date <= filters['date_to'])

            # Get total count
            total = query.count()

            # Get paginated results
            offset = (page - 1) * page_size
            messages = query.order_by(desc(EbayMessage.message_date))\
                .offset(offset)\
                .limit(page_size)\
                .all()

            return messages, total
        except Exception as e:
            raise DatabaseError(f"Failed to get eBay messages for account {account_id}: {str(e)}")

    async def update(self, message_id: int, message_data: EbayMessageUpdate) -> Optional[EbayMessage]:
        """Update eBay message"""
        try:
            db_message = await self.get_by_id(message_id)
            if not db_message:
                raise NotFoundError(f"eBay message {message_id} not found")

            update_data = message_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_message, field, value)

            db_message.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(db_message)
            return db_message
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update eBay message {message_id}: {str(e)}")

    async def delete(self, message_id: int) -> bool:
        """Delete eBay message"""
        try:
            db_message = await self.get_by_id(message_id)
            if not db_message:
                return False

            self.db.delete(db_message)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to delete eBay message {message_id}: {str(e)}")

    async def get_pending_response_count(self, account_id: int) -> int:
        """Get count of messages requiring response"""
        try:
            return self.db.query(EbayMessage)\
                .filter(EbayMessage.account_id == account_id)\
                .filter(EbayMessage.requires_response == True)\
                .filter(EbayMessage.has_response == False)\
                .count()
        except Exception as e:
            raise DatabaseError(f"Failed to get pending response count: {str(e)}")

    async def get_counts_by_type(
        self, 
        account_id: int, 
        date_from: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Get message counts by type for account"""
        try:
            query = self.db.query(EbayMessage.message_type, func.count(EbayMessage.id))\
                .filter(EbayMessage.account_id == account_id)

            if date_from:
                query = query.filter(EbayMessage.message_date >= date_from)

            results = query.group_by(EbayMessage.message_type).all()
            return {message_type or 'unknown': count for message_type, count in results}
        except Exception as e:
            raise DatabaseError(f"Failed to get message counts by type: {str(e)}")

    async def bulk_mark_processed(self, message_ids: List[int]) -> int:
        """Mark multiple messages as processed"""
        try:
            if not message_ids:
                return 0

            result = self.db.query(EbayMessage)\
                .filter(EbayMessage.id.in_(message_ids))\
                .update(
                    {'is_processed': True, 'updated_at': datetime.utcnow()},
                    synchronize_session=False
                )
            self.db.commit()
            return result
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to bulk mark eBay messages as processed: {str(e)}")

    async def get_messages_by_item(
        self, 
        account_id: int, 
        item_id: str,
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[EbayMessage], int]:
        """Get messages for specific item"""
        try:
            query = self.db.query(EbayMessage)\
                .filter(EbayMessage.account_id == account_id)\
                .filter(EbayMessage.item_id == item_id)

            # Get total count
            total = query.count()

            # Get paginated results
            offset = (page - 1) * page_size
            messages = query.order_by(desc(EbayMessage.message_date))\
                .offset(offset)\
                .limit(page_size)\
                .all()

            return messages, total
        except Exception as e:
            raise DatabaseError(f"Failed to get messages for item {item_id}: {str(e)}")


class MessageThreadRepository(IMessageThreadRepository):
    """
    SOLID: Single Responsibility - Message thread data access operations
    SOLID: Dependency Inversion - Depends on database session interface
    """

    def __init__(self, db: Session):
        self.db = db

    async def create(self, thread_data: MessageThreadCreate) -> MessageThread:
        """Create new message thread"""
        try:
            # Convert Pydantic model to dict, handling enums
            thread_dict = thread_data.dict()
            
            # Convert enum values to strings
            if 'message_type' in thread_dict and hasattr(thread_dict['message_type'], 'value'):
                thread_dict['message_type'] = thread_dict['message_type'].value
            if 'priority' in thread_dict and hasattr(thread_dict['priority'], 'value'):
                thread_dict['priority'] = thread_dict['priority'].value

            db_thread = MessageThread(**thread_dict)
            self.db.add(db_thread)
            self.db.commit()
            self.db.refresh(db_thread)
            return db_thread
        except IntegrityError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create message thread: {str(e)}")

    async def get_by_id(self, thread_id: int) -> Optional[MessageThread]:
        """Get thread by ID"""
        try:
            return self.db.query(MessageThread)\
                .options(
                    joinedload(MessageThread.ebay_messages),
                    joinedload(MessageThread.emails)
                )\
                .filter(MessageThread.id == thread_id)\
                .first()
        except Exception as e:
            raise DatabaseError(f"Failed to get thread {thread_id}: {str(e)}")

    async def get_by_account_id(
        self, 
        account_id: int, 
        page: int = 1, 
        page_size: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[MessageThread], int]:
        """Get threads for account with pagination and filters"""
        try:
            query = self.db.query(MessageThread)\
                .filter(MessageThread.account_id == account_id)

            # Apply filters
            if filters:
                if filters.get('thread_type'):
                    query = query.filter(MessageThread.thread_type == filters['thread_type'])
                
                if filters.get('status'):
                    query = query.filter(MessageThread.status == filters['status'])
                
                if filters.get('requires_response') is not None:
                    query = query.filter(MessageThread.requires_response == filters['requires_response'])
                
                if filters.get('message_type'):
                    query = query.filter(MessageThread.message_type == filters['message_type'])
                
                if filters.get('priority'):
                    query = query.filter(MessageThread.priority == filters['priority'])
                
                if filters.get('item_id'):
                    query = query.filter(MessageThread.item_id == filters['item_id'])
                
                if filters.get('customer_username'):
                    query = query.filter(MessageThread.customer_username == filters['customer_username'])

            # Get total count
            total = query.count()

            # Get paginated results with message count
            offset = (page - 1) * page_size
            threads = query.outerjoin(EbayMessage)\
                .add_columns(func.count(EbayMessage.id).label('message_count'))\
                .group_by(MessageThread.id)\
                .order_by(desc(MessageThread.last_message_date))\
                .offset(offset)\
                .limit(page_size)\
                .all()

            # Transform result to include message_count
            result_threads = []
            for thread, message_count in threads:
                thread.message_count = message_count
                result_threads.append(thread)

            return result_threads, total
        except Exception as e:
            raise DatabaseError(f"Failed to get threads for account {account_id}: {str(e)}")

    async def find_by_item_and_customer(
        self, 
        account_id: int, 
        item_id: str, 
        customer_username: str
    ) -> Optional[MessageThread]:
        """Find thread by item and customer for eBay messages"""
        try:
            return self.db.query(MessageThread)\
                .filter(MessageThread.account_id == account_id)\
                .filter(MessageThread.item_id == item_id)\
                .filter(MessageThread.customer_username == customer_username)\
                .first()
        except Exception as e:
            raise DatabaseError(f"Failed to find thread by item and customer: {str(e)}")

    async def update(self, thread_id: int, thread_data: MessageThreadUpdate) -> Optional[MessageThread]:
        """Update message thread"""
        try:
            db_thread = await self.get_by_id(thread_id)
            if not db_thread:
                raise NotFoundError(f"Thread {thread_id} not found")

            update_data = thread_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_thread, field, value)

            db_thread.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(db_thread)
            return db_thread
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update thread {thread_id}: {str(e)}")

    async def delete(self, thread_id: int) -> bool:
        """Delete message thread"""
        try:
            db_thread = await self.get_by_id(thread_id)
            if not db_thread:
                return False

            self.db.delete(db_thread)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to delete thread {thread_id}: {str(e)}")

    async def get_threads_requiring_response(
        self, 
        account_id: Optional[int] = None,
        priority: Optional[str] = None
    ) -> List[MessageThread]:
        """Get threads that require response"""
        try:
            query = self.db.query(MessageThread)\
                .filter(MessageThread.requires_response == True)

            if account_id:
                query = query.filter(MessageThread.account_id == account_id)

            if priority:
                query = query.filter(MessageThread.priority == priority)

            return query.order_by(
                desc(MessageThread.priority),
                asc(MessageThread.last_message_date)
            ).all()
        except Exception as e:
            raise DatabaseError(f"Failed to get threads requiring response: {str(e)}")

    async def mark_as_responded(self, thread_id: int) -> bool:
        """Mark thread as responded"""
        try:
            result = self.db.query(MessageThread)\
                .filter(MessageThread.id == thread_id)\
                .update(
                    {
                        'last_response_date': datetime.utcnow(),
                        'requires_response': False,
                        'status': 'responded',
                        'last_activity_date': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    },
                    synchronize_session=False
                )
            self.db.commit()
            return result > 0
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to mark thread {thread_id} as responded: {str(e)}")

    async def get_counts_by_status(
        self, 
        account_id: int,
        date_from: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Get thread counts by status for account"""
        try:
            query = self.db.query(MessageThread.status, func.count(MessageThread.id))\
                .filter(MessageThread.account_id == account_id)

            if date_from:
                query = query.filter(MessageThread.last_message_date >= date_from)

            results = query.group_by(MessageThread.status).all()
            return {status or 'unknown': count for status, count in results}
        except Exception as e:
            raise DatabaseError(f"Failed to get thread counts by status: {str(e)}")

    async def get_thread_statistics(
        self, 
        account_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get thread statistics for account"""
        try:
            query = self.db.query(MessageThread)\
                .filter(MessageThread.account_id == account_id)

            if date_from:
                query = query.filter(MessageThread.last_message_date >= date_from)
            if date_to:
                query = query.filter(MessageThread.last_message_date <= date_to)

            # Get basic counts
            total_threads = query.count()
            requiring_response = query.filter(MessageThread.requires_response == True).count()
            responded_threads = query.filter(MessageThread.status == 'responded').count()
            ebay_threads = query.filter(MessageThread.thread_type == 'ebay_message').count()

            # Get priority breakdown
            priority_stats = query.with_entities(
                MessageThread.priority,
                func.count(MessageThread.id)
            ).group_by(MessageThread.priority).all()

            # Get message type breakdown
            message_type_stats = query.filter(MessageThread.message_type.isnot(None))\
                .with_entities(
                    MessageThread.message_type,
                    func.count(MessageThread.id)
                ).group_by(MessageThread.message_type).all()

            return {
                'total_threads': total_threads,
                'requiring_response': requiring_response,
                'responded_threads': responded_threads,
                'ebay_threads': ebay_threads,
                'response_rate': responded_threads / requiring_response if requiring_response > 0 else 0,
                'priority_breakdown': dict(priority_stats),
                'message_type_breakdown': dict(message_type_stats)
            }
        except Exception as e:
            raise DatabaseError(f"Failed to get thread statistics: {str(e)}")