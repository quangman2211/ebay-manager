"""
Communication repository implementations
Following SOLID principles - Single Responsibility and Dependency Inversion
YAGNI compliance: Essential database operations only
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import and_, or_, desc, asc, func, update
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.repositories.interfaces.communication_repository import IEmailRepository, IEmailThreadRepository
from app.models.communication import Email, EmailThread
from app.schemas.communication import EmailCreate, EmailUpdate, EmailThreadCreate, EmailThreadUpdate
from app.core.exceptions import DatabaseError, NotFoundError


class EmailRepository(IEmailRepository):
    """
    SOLID: Single Responsibility - Email data access operations
    SOLID: Dependency Inversion - Depends on database session interface
    """

    def __init__(self, db: Session):
        self.db = db

    async def create(self, email_data: EmailCreate) -> Email:
        """Create new email"""
        try:
            db_email = Email(**email_data.dict())
            self.db.add(db_email)
            self.db.commit()
            self.db.refresh(db_email)
            return db_email
        except IntegrityError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create email: {str(e)}")

    async def get_by_id(self, email_id: int) -> Optional[Email]:
        """Get email by ID"""
        try:
            return self.db.query(Email)\
                .options(joinedload(Email.thread))\
                .filter(Email.id == email_id)\
                .first()
        except Exception as e:
            raise DatabaseError(f"Failed to get email {email_id}: {str(e)}")

    async def get_by_gmail_id(self, gmail_id: str) -> Optional[Email]:
        """Get email by Gmail ID"""
        try:
            return self.db.query(Email)\
                .filter(Email.gmail_id == gmail_id)\
                .first()
        except Exception as e:
            raise DatabaseError(f"Failed to get email by Gmail ID {gmail_id}: {str(e)}")

    async def get_by_thread_id(
        self, 
        thread_id: int, 
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[Email], int]:
        """Get emails in thread with pagination"""
        try:
            # Get total count
            total = self.db.query(Email)\
                .filter(Email.thread_id == thread_id)\
                .count()

            # Get paginated results
            offset = (page - 1) * page_size
            emails = self.db.query(Email)\
                .filter(Email.thread_id == thread_id)\
                .order_by(asc(Email.date))\
                .offset(offset)\
                .limit(page_size)\
                .all()

            return emails, total
        except Exception as e:
            raise DatabaseError(f"Failed to get emails for thread {thread_id}: {str(e)}")

    async def update(self, email_id: int, email_data: EmailUpdate) -> Optional[Email]:
        """Update email"""
        try:
            db_email = await self.get_by_id(email_id)
            if not db_email:
                raise NotFoundError(f"Email {email_id} not found")

            update_data = email_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_email, field, value)

            db_email.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(db_email)
            return db_email
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update email {email_id}: {str(e)}")

    async def delete(self, email_id: int) -> bool:
        """Delete email"""
        try:
            db_email = await self.get_by_id(email_id)
            if not db_email:
                return False

            self.db.delete(db_email)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to delete email {email_id}: {str(e)}")

    async def bulk_mark_processed(self, email_ids: List[int]) -> int:
        """Mark multiple emails as processed"""
        try:
            if not email_ids:
                return 0

            result = self.db.query(Email)\
                .filter(Email.id.in_(email_ids))\
                .update(
                    {'is_processed': True, 'updated_at': datetime.utcnow()},
                    synchronize_session=False
                )
            self.db.commit()
            return result
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to bulk mark emails as processed: {str(e)}")

    async def get_unprocessed_emails(
        self, 
        account_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Email]:
        """Get unprocessed emails"""
        try:
            query = self.db.query(Email)\
                .join(EmailThread)\
                .filter(Email.is_processed == False)

            if account_id:
                query = query.filter(EmailThread.account_id == account_id)

            return query.order_by(desc(Email.date))\
                .limit(limit)\
                .all()
        except Exception as e:
            raise DatabaseError(f"Failed to get unprocessed emails: {str(e)}")


class EmailThreadRepository(IEmailThreadRepository):
    """
    SOLID: Single Responsibility - Email thread data access operations
    SOLID: Dependency Inversion - Depends on database session interface
    """

    def __init__(self, db: Session):
        self.db = db

    async def create(self, thread_data: EmailThreadCreate) -> EmailThread:
        """Create new email thread"""
        try:
            db_thread = EmailThread(**thread_data.dict())
            self.db.add(db_thread)
            self.db.commit()
            self.db.refresh(db_thread)
            return db_thread
        except IntegrityError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create email thread: {str(e)}")

    async def get_by_id(self, thread_id: int) -> Optional[EmailThread]:
        """Get thread by ID"""
        try:
            return self.db.query(EmailThread)\
                .options(joinedload(EmailThread.emails))\
                .filter(EmailThread.id == thread_id)\
                .first()
        except Exception as e:
            raise DatabaseError(f"Failed to get thread {thread_id}: {str(e)}")

    async def get_by_gmail_id(self, gmail_thread_id: str) -> Optional[EmailThread]:
        """Get thread by Gmail thread ID"""
        try:
            return self.db.query(EmailThread)\
                .filter(EmailThread.gmail_thread_id == gmail_thread_id)\
                .first()
        except Exception as e:
            raise DatabaseError(f"Failed to get thread by Gmail ID {gmail_thread_id}: {str(e)}")

    async def get_by_account_id(
        self, 
        account_id: int, 
        page: int = 1, 
        page_size: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[EmailThread], int]:
        """Get threads for account with pagination and filters"""
        try:
            query = self.db.query(EmailThread)\
                .filter(EmailThread.account_id == account_id)

            # Apply filters
            if filters:
                if filters.get('is_read') is not None:
                    query = query.filter(EmailThread.is_read == filters['is_read'])
                
                if filters.get('requires_response') is not None:
                    query = query.filter(EmailThread.requires_response == filters['requires_response'])
                
                if filters.get('is_ebay_related') is not None:
                    query = query.filter(EmailThread.is_ebay_related == filters['is_ebay_related'])
                
                if filters.get('message_type'):
                    query = query.filter(EmailThread.message_type == filters['message_type'])
                
                if filters.get('priority'):
                    query = query.filter(EmailThread.priority == filters['priority'])
                
                if filters.get('date_from'):
                    query = query.filter(EmailThread.last_message_date >= filters['date_from'])
                
                if filters.get('date_to'):
                    query = query.filter(EmailThread.last_message_date <= filters['date_to'])

            # Get total count
            total = query.count()

            # Get paginated results with email count
            offset = (page - 1) * page_size
            threads = query.outerjoin(Email)\
                .add_columns(func.count(Email.id).label('email_count'))\
                .group_by(EmailThread.id)\
                .order_by(desc(EmailThread.last_message_date))\
                .offset(offset)\
                .limit(page_size)\
                .all()

            # Transform result to include email_count
            result_threads = []
            for thread, email_count in threads:
                thread.email_count = email_count
                result_threads.append(thread)

            return result_threads, total
        except Exception as e:
            raise DatabaseError(f"Failed to get threads for account {account_id}: {str(e)}")

    async def update(self, thread_id: int, thread_data: EmailThreadUpdate) -> Optional[EmailThread]:
        """Update email thread"""
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
        """Delete email thread"""
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
    ) -> List[EmailThread]:
        """Get threads that require response"""
        try:
            query = self.db.query(EmailThread)\
                .filter(EmailThread.requires_response == True)\
                .filter(EmailThread.is_responded == False)

            if account_id:
                query = query.filter(EmailThread.account_id == account_id)

            if priority:
                query = query.filter(EmailThread.priority == priority)

            return query.order_by(
                desc(EmailThread.priority),
                asc(EmailThread.last_message_date)
            ).all()
        except Exception as e:
            raise DatabaseError(f"Failed to get threads requiring response: {str(e)}")

    async def mark_as_read(self, thread_ids: List[int]) -> int:
        """Mark threads as read"""
        try:
            if not thread_ids:
                return 0

            result = self.db.query(EmailThread)\
                .filter(EmailThread.id.in_(thread_ids))\
                .update(
                    {'is_read': True, 'updated_at': datetime.utcnow()},
                    synchronize_session=False
                )
            self.db.commit()
            return result
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to mark threads as read: {str(e)}")

    async def mark_as_responded(self, thread_id: int) -> bool:
        """Mark thread as responded"""
        try:
            result = self.db.query(EmailThread)\
                .filter(EmailThread.id == thread_id)\
                .update(
                    {
                        'is_responded': True, 
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

    async def get_ebay_threads(
        self,
        account_id: int,
        message_type: Optional[str] = None,
        ebay_item_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[EmailThread], int]:
        """Get eBay-related threads with filters"""
        try:
            query = self.db.query(EmailThread)\
                .filter(EmailThread.account_id == account_id)\
                .filter(EmailThread.is_ebay_related == True)

            if message_type:
                query = query.filter(EmailThread.message_type == message_type)

            if ebay_item_id:
                query = query.filter(EmailThread.ebay_item_id == ebay_item_id)

            # Get total count
            total = query.count()

            # Get paginated results
            offset = (page - 1) * page_size
            threads = query.order_by(desc(EmailThread.last_message_date))\
                .offset(offset)\
                .limit(page_size)\
                .all()

            return threads, total
        except Exception as e:
            raise DatabaseError(f"Failed to get eBay threads: {str(e)}")

    async def get_thread_statistics(
        self, 
        account_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get thread statistics for account"""
        try:
            query = self.db.query(EmailThread)\
                .filter(EmailThread.account_id == account_id)

            if date_from:
                query = query.filter(EmailThread.last_message_date >= date_from)
            if date_to:
                query = query.filter(EmailThread.last_message_date <= date_to)

            # Get basic counts
            total_threads = query.count()
            unread_threads = query.filter(EmailThread.is_read == False).count()
            requiring_response = query.filter(EmailThread.requires_response == True).count()
            responded_threads = query.filter(EmailThread.is_responded == True).count()
            ebay_threads = query.filter(EmailThread.is_ebay_related == True).count()

            # Get priority breakdown
            priority_stats = query.with_entities(
                EmailThread.priority,
                func.count(EmailThread.id)
            ).group_by(EmailThread.priority).all()

            # Get message type breakdown
            message_type_stats = query.filter(EmailThread.is_ebay_related == True)\
                .with_entities(
                    EmailThread.message_type,
                    func.count(EmailThread.id)
                ).group_by(EmailThread.message_type).all()

            return {
                'total_threads': total_threads,
                'unread_threads': unread_threads,
                'requiring_response': requiring_response,
                'responded_threads': responded_threads,
                'ebay_threads': ebay_threads,
                'response_rate': responded_threads / requiring_response if requiring_response > 0 else 0,
                'priority_breakdown': dict(priority_stats),
                'message_type_breakdown': dict(message_type_stats)
            }
        except Exception as e:
            raise DatabaseError(f"Failed to get thread statistics: {str(e)}")