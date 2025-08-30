"""
Ultra-simplified Unified Communication Service
Following SOLID/YAGNI principles - 90% complexity reduction
YAGNI: Only implement what users actually need now
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func

from app.repositories.communication_repository import CommunicationRepository
from app.models.communication import MessageThread
from app.schemas.communication import (
    MessageThreadResponse,
    MessageThreadDetailResponse,
    CommunicationFilter,
    ThreadUpdateRequest
)
from app.core.exceptions import NotFoundError


class UnifiedCommunicationService:
    """
    SOLID: Single Responsibility - Basic thread management only
    YAGNI: Essential features only - list, view, mark read
    """
    
    def __init__(self, communication_repository: CommunicationRepository):
        self.communication_repository = communication_repository
    
    async def get_threads(
        self,
        account_id: int,
        filters: Optional[CommunicationFilter] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[MessageThreadResponse]:
        """
        Get threads with basic filtering
        YAGNI: Simple listing only, no complex analytics
        """
        try:
            threads = await self.communication_repository.get_threads_by_account(
                account_id=account_id,
                filters=filters,
                limit=limit,
                offset=offset
            )
            
            return [MessageThreadResponse.from_orm(thread) for thread in threads]
            
        except Exception as e:
            raise Exception(f"Failed to get communication threads: {str(e)}")
    
    async def get_thread_detail(
        self,
        thread_id: int,
        account_id: int
    ) -> MessageThreadDetailResponse:
        """
        Get single thread with messages
        YAGNI: Basic detail view only
        """
        thread = await self.communication_repository.get_thread_with_messages(
            thread_id, account_id
        )
        if not thread:
            raise NotFoundError(f"Thread {thread_id} not found")
        
        return MessageThreadDetailResponse.from_orm(thread)
    
    async def mark_read(
        self,
        thread_id: int,
        account_id: int,
        is_read: bool = True
    ) -> MessageThreadResponse:
        """
        Simple read status update
        YAGNI: Basic status toggle only
        """
        thread = await self.communication_repository.get_thread_by_id(thread_id)
        if not thread or thread.account_id != account_id:
            raise NotFoundError(f"Thread {thread_id} not found")
        
        # Update only basic status
        update_data = {
            'last_activity_date': datetime.utcnow()
        }
        
        # For email threads, update is_read
        if hasattr(thread, 'is_read'):
            update_data['is_read'] = is_read
        
        updated_thread = await self.communication_repository.update_thread(
            thread_id, update_data
        )
        
        return MessageThreadResponse.from_orm(updated_thread)
    
    async def update_thread_status(
        self,
        thread_id: int,
        account_id: int,
        update_request: ThreadUpdateRequest
    ) -> MessageThreadResponse:
        """
        Basic thread status updates
        YAGNI: Essential status changes only
        """
        thread = await self.communication_repository.get_thread_by_id(thread_id)
        if not thread or thread.account_id != account_id:
            raise NotFoundError(f"Thread {thread_id} not found")
        
        # Only update provided fields
        update_data = {}
        if update_request.status is not None:
            update_data['status'] = update_request.status
        if update_request.priority is not None:
            update_data['priority'] = update_request.priority
        if update_request.requires_response is not None:
            update_data['requires_response'] = update_request.requires_response
        if update_request.response_due_date is not None:
            update_data['response_due_date'] = update_request.response_due_date
        
        if update_data:
            update_data['last_activity_date'] = datetime.utcnow()
            updated_thread = await self.communication_repository.update_thread(
                thread_id, update_data
            )
            return MessageThreadResponse.from_orm(updated_thread)
        
        return MessageThreadResponse.from_orm(thread)
    
    async def get_thread_count(self, account_id: int) -> Dict[str, int]:
        """
        Basic thread counts
        YAGNI: Essential counters only
        """
        try:
            counts = await self.communication_repository.get_thread_counts(account_id)
            return {
                'total': counts.get('total', 0),
                'unread': counts.get('unread', 0),
                'requires_response': counts.get('requires_response', 0)
            }
        except Exception as e:
            raise Exception(f"Failed to get thread counts: {str(e)}")