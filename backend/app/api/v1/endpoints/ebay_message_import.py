"""
eBay Message Import API endpoints
Following SOLID principles - Single Responsibility for API request handling
YAGNI compliance: Essential endpoints for CSV upload and import only
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
import tempfile
import os

from app.middleware.auth import get_db, get_current_active_user
from app.services.csv_import.ebay_message_import_service import EbayMessageImportService
from app.services.csv_import.ebay_message_csv_detector import EbayMessageCSVFormat
from app.repositories.ebay_message_repository import EbayMessageRepository, MessageThreadRepository
from app.schemas.communication import EbayMessageImportRequest, EbayMessageImportResponse
from app.core.exceptions import ValidationError, NotFoundError
from app.models.user import User
from app.core.config import settings

router = APIRouter()


def get_ebay_message_import_service(db: Session = Depends(get_db)) -> EbayMessageImportService:
    """Dependency to get eBay message import service"""
    ebay_message_repo = EbayMessageRepository(db)
    thread_repo = MessageThreadRepository(db)
    return EbayMessageImportService(ebay_message_repo, thread_repo)


@router.post("/upload", response_model=EbayMessageImportResponse)
async def upload_ebay_messages_csv(
    *,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    import_service: EbayMessageImportService = Depends(get_ebay_message_import_service),
    file: UploadFile = File(...),
    account_id: int = Form(...),
    account_username: str = Form(...),
    expected_format: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload and process eBay message CSV file
    SOLID: Single Responsibility - Handle file upload and import initiation
    """
    # Validate file
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Check file size (10MB limit)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
            tmp_file.write(file_content)
            temp_file_path = tmp_file.name
        
        try:
            # Parse expected format
            csv_format = None
            if expected_format:
                try:
                    csv_format = EbayMessageCSVFormat(expected_format)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid CSV format: {expected_format}")
            
            # Process import
            results = await import_service.import_messages_from_csv(
                temp_file_path,
                account_id,
                account_username,
                csv_format
            )
            
            return EbayMessageImportResponse(
                success=True,
                message=f"Import completed: {results['messages_created']} messages imported",
                results=results
            )
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/validate", response_model=dict)
async def validate_ebay_messages_csv(
    *,
    db: Session = Depends(get_db),
    import_service: EbayMessageImportService = Depends(get_ebay_message_import_service),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Validate eBay message CSV file without importing"""
    # Validate file
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
            tmp_file.write(file_content)
            temp_file_path = tmp_file.name
        
        try:
            # Validate format
            validation_result = await import_service.validate_csv_format(temp_file_path)
            return validation_result
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/summary/{account_id}", response_model=dict)
async def get_import_summary(
    *,
    db: Session = Depends(get_db),
    import_service: EbayMessageImportService = Depends(get_ebay_message_import_service),
    account_id: int,
    days_back: int = 30,
    current_user: User = Depends(get_current_active_user)
):
    """Get import summary for account"""
    try:
        summary = await import_service.get_import_summary(account_id, days_back)
        return summary
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/formats", response_model=dict)
async def get_supported_message_formats(
    *,
    current_user: User = Depends(get_current_active_user)
):
    """Get list of supported eBay message CSV formats"""
    return {
        "formats": [
            {
                "value": format_type.value,
                "name": format_type.value.replace('_', ' ').title(),
                "description": f"eBay {format_type.value.split('_')[-1]} export format"
            }
            for format_type in EbayMessageCSVFormat
            if format_type != EbayMessageCSVFormat.UNKNOWN
        ]
    }


@router.get("/messages/{account_id}", response_model=dict)
async def get_ebay_messages(
    *,
    db: Session = Depends(get_db),
    account_id: int,
    page: int = 1,
    page_size: int = 50,
    message_type: Optional[str] = None,
    priority: Optional[str] = None,
    direction: Optional[str] = None,
    item_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get eBay messages for account with filters"""
    try:
        ebay_message_repo = EbayMessageRepository(db)
        
        filters = {}
        if message_type:
            filters['message_type'] = message_type
        if priority:
            filters['priority'] = priority
        if direction:
            filters['direction'] = direction
        if item_id:
            filters['item_id'] = item_id
        
        messages, total = await ebay_message_repo.get_by_account_id(
            account_id, filters, page, page_size
        )
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "ebay_message_id": msg.ebay_message_id,
                    "item_id": msg.item_id,
                    "item_title": msg.item_title,
                    "sender_username": msg.sender_username,
                    "recipient_username": msg.recipient_username,
                    "direction": msg.direction,
                    "message_content": msg.message_content,
                    "message_date": msg.message_date,
                    "message_type": msg.message_type,
                    "priority": msg.priority,
                    "requires_response": msg.requires_response,
                    "has_response": msg.has_response
                }
                for msg in messages
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.get("/threads/{account_id}", response_model=dict)
async def get_message_threads(
    *,
    db: Session = Depends(get_db),
    account_id: int,
    page: int = 1,
    page_size: int = 50,
    thread_type: Optional[str] = None,
    status: Optional[str] = None,
    requires_response: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get message threads for account with filters"""
    try:
        thread_repo = MessageThreadRepository(db)
        
        filters = {}
        if thread_type:
            filters['thread_type'] = thread_type
        if status:
            filters['status'] = status
        if requires_response is not None:
            filters['requires_response'] = requires_response
        
        threads, total = await thread_repo.get_by_account_id(
            account_id, page, page_size, filters
        )
        
        return {
            "threads": [
                {
                    "id": thread.id,
                    "thread_type": thread.thread_type,
                    "item_id": thread.item_id,
                    "item_title": thread.item_title,
                    "customer_username": thread.customer_username,
                    "subject": thread.subject,
                    "message_type": thread.message_type,
                    "priority": thread.priority,
                    "status": thread.status,
                    "requires_response": thread.requires_response,
                    "first_message_date": thread.first_message_date,
                    "last_message_date": thread.last_message_date,
                    "message_count": getattr(thread, 'message_count', 0)
                }
                for thread in threads
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get threads: {str(e)}")