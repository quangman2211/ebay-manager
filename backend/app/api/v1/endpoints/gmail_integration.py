"""
Gmail integration API endpoints
Following SOLID principles - Single Responsibility for API request handling
YAGNI compliance: Essential endpoints for OAuth and import only
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.middleware.auth import get_db, get_current_active_user
from app.services.email.gmail_service import GmailCredentialsManager, GmailService
from app.services.email.email_import_service import EmailImportService
from app.repositories.communication_repository import EmailRepository, EmailThreadRepository
from app.schemas.communication import (
    GmailAuthResponse, 
    GmailStatusResponse,
    EmailImportRequest,
    EmailImportResponse
)
from app.core.exceptions import AuthenticationError, ExternalServiceError
from app.models.user import User

router = APIRouter()


@router.post("/auth/initiate", response_model=GmailAuthResponse)
async def initiate_gmail_auth(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Initiate Gmail OAuth flow"""
    try:
        credentials_manager = GmailCredentialsManager()
        auth_url = credentials_manager.initiate_oauth_flow(current_user.id)
        
        return GmailAuthResponse(
            auth_url=auth_url,
            message="Please visit the URL to authorize Gmail access"
        )
        
    except AuthenticationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/complete")
async def complete_gmail_auth(
    *,
    db: Session = Depends(deps.get_db),
    authorization_code: str = Body(..., embed=True),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Complete Gmail OAuth flow with authorization code"""
    try:
        credentials_manager = GmailCredentialsManager()
        success = credentials_manager.complete_oauth_flow(current_user.id, authorization_code)
        
        if success:
            return {"message": "Gmail authorization successful"}
        else:
            raise HTTPException(status_code=400, detail="Authorization failed")
            
    except AuthenticationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status", response_model=GmailStatusResponse)
async def get_gmail_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get Gmail integration status for user"""
    try:
        credentials_manager = GmailCredentialsManager()
        credentials = credentials_manager.get_credentials(current_user.id)
        
        return GmailStatusResponse(
            authenticated=credentials is not None and credentials.valid,
            needs_reauth=credentials is not None and not credentials.valid
        )
        
    except Exception as e:
        return GmailStatusResponse(
            authenticated=False,
            needs_reauth=True,
            error=str(e)
        )


@router.post("/import", response_model=EmailImportResponse)
async def import_emails(
    *,
    db: Session = Depends(deps.get_db),
    request: EmailImportRequest,
    current_user: User = Depends(deps.get_current_active_user)
):
    """Import emails from Gmail"""
    try:
        # Initialize services
        credentials_manager = GmailCredentialsManager()
        gmail_service = GmailService(credentials_manager)
        
        email_repository = EmailRepository(db)
        thread_repository = EmailThreadRepository(db)
        
        import_service = EmailImportService(
            gmail_service=gmail_service,
            email_repository=email_repository,
            thread_repository=thread_repository
        )
        
        # Execute import
        results = await import_service.import_recent_emails(
            user_id=current_user.id,
            account_id=request.account_id,
            days_back=request.days_back,
            max_emails=request.max_emails,
            ebay_only=request.ebay_only
        )
        
        return EmailImportResponse(
            success=True,
            message=f"Import completed: {results['emails_imported']} emails imported",
            results=results
        )
        
    except (AuthenticationError, ExternalServiceError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# Additional convenience endpoints for different import scenarios

@router.post("/import/quick")
async def import_recent_emails_quick(
    *,
    db: Session = Depends(deps.get_db),
    account_id: int = Body(..., embed=True),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Quick import of last 7 days eBay emails"""
    request = EmailImportRequest(
        account_id=account_id,
        days_back=7,
        max_emails=200,
        ebay_only=True
    )
    
    return await import_emails(
        db=db,
        request=request,
        current_user=current_user
    )


@router.post("/import/full")
async def import_all_emails(
    *,
    db: Session = Depends(deps.get_db),
    account_id: int = Body(..., embed=True),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Full import of last 30 days all emails"""
    request = EmailImportRequest(
        account_id=account_id,
        days_back=30,
        max_emails=1000,
        ebay_only=False
    )
    
    return await import_emails(
        db=db,
        request=request,
        current_user=current_user
    )