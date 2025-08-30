"""
Ultra-simplified Communication API endpoints
Following SOLID/YAGNI principles - basic CRUD operations only
YAGNI: Essential endpoints only - list, view, mark read
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.communication.unified_communication_service import UnifiedCommunicationService
from app.repositories.communication_repository import CommunicationRepository
from app.schemas.communication import (
    MessageThreadResponse,
    MessageThreadDetailResponse,
    CommunicationFilter,
    ThreadUpdateRequest
)
from app.models.user import User


router = APIRouter(prefix="/communication", tags=["communication"])


def get_communication_service(db: Session = Depends(get_db)) -> UnifiedCommunicationService:
    """Dependency injection for communication service"""
    communication_repository = CommunicationRepository(db)
    return UnifiedCommunicationService(communication_repository)


@router.get("/threads", response_model=List[MessageThreadResponse])
async def get_threads(
    account_id: int = Query(..., description="Account ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    requires_response: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """
    Get communication threads with basic filtering
    YAGNI: Simple listing with essential filters only
    """
    try:
        # Build basic filters
        filters = CommunicationFilter()
        if status:
            filters.status = status
        if priority:
            filters.priority = priority
        if requires_response is not None:
            filters.requires_response = requires_response
        
        threads = await service.get_threads(
            account_id=account_id,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return threads
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads/{thread_id}", response_model=MessageThreadDetailResponse)
async def get_thread_detail(
    thread_id: int,
    account_id: int = Query(..., description="Account ID"),
    current_user: User = Depends(get_current_user),
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """
    Get thread detail with messages
    YAGNI: Basic detail view only
    """
    try:
        thread = await service.get_thread_detail(thread_id, account_id)
        return thread
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/threads/{thread_id}/read")
async def mark_thread_read(
    thread_id: int,
    account_id: int = Query(..., description="Account ID"),
    is_read: bool = Query(True),
    current_user: User = Depends(get_current_user),
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """
    Mark thread as read/unread
    YAGNI: Simple status toggle only
    """
    try:
        thread = await service.mark_read(thread_id, account_id, is_read)
        return {"success": True, "thread": thread}
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/threads/{thread_id}/status", response_model=MessageThreadResponse)
async def update_thread_status(
    thread_id: int,
    update_request: ThreadUpdateRequest,
    account_id: int = Query(..., description="Account ID"),
    current_user: User = Depends(get_current_user),
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """
    Update thread status and properties
    YAGNI: Basic status updates only
    """
    try:
        thread = await service.update_thread_status(thread_id, account_id, update_request)
        return thread
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads/counts")
async def get_thread_counts(
    account_id: int = Query(..., description="Account ID"),
    current_user: User = Depends(get_current_user),
    service: UnifiedCommunicationService = Depends(get_communication_service)
):
    """
    Get basic thread counts
    YAGNI: Essential counters only
    """
    try:
        counts = await service.get_thread_count(account_id)
        return counts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))