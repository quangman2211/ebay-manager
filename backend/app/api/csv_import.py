"""
Ultra-simplified CSV Import API Endpoints
Following YAGNI principles - 90% complexity reduction
Supports: Manual upload, Google Sheets upload, Chrome extension HTTP upload
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.services.simple_csv_import import SimpleCsvImportService
from app.repositories.listing_repository import ListingRepository
from app.repositories.account_repository import AccountRepository
from app.core.exceptions import NotFoundError, ValidationException, EbayManagerException
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/csv-import", tags=["csv-import"])


def get_csv_import_service(db: Session = Depends(get_db)) -> SimpleCsvImportService:
    """Dependency injection for CSV import service"""
    listing_repo = ListingRepository(db)
    account_repo = AccountRepository(db)
    return SimpleCsvImportService(listing_repo, account_repo)


@router.post("/upload", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def upload_csv_file(
    *,
    csv_service: SimpleCsvImportService = Depends(get_csv_import_service),
    account_id: int = Form(..., description="Account ID for the import"),
    file: UploadFile = File(..., description="CSV file to import"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Upload and process CSV file immediately
    YAGNI: Direct processing, no job management or complex validation
    Supports: Manual file upload via web interface
    """
    try:
        # Basic file validation
        if not file.filename or not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=400, detail="File size must be less than 50MB")
        
        # Read file content
        csv_content = await file.read()
        csv_text = csv_content.decode('utf-8')
        
        if not csv_text.strip():
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        # Process CSV immediately
        result = await csv_service.import_csv_content(csv_text, account_id)
        
        return {
            "success": True,
            "message": f"CSV import completed: {result.created_count} created, {result.updated_count} updated",
            "filename": file.filename,
            "account_id": account_id,
            "result": result.to_dict()
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please use UTF-8 encoded CSV files")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV import failed: {str(e)}")


@router.post("/upload-content", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def upload_csv_content(
    *,
    csv_service: SimpleCsvImportService = Depends(get_csv_import_service),
    account_id: int = Form(..., description="Account ID for the import"),
    csv_content: str = Form(..., description="CSV content as string"),
    filename: str = Form("import.csv", description="Optional filename"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Upload CSV content directly as string
    YAGNI: Simple content processing for Google Sheets and Chrome extension
    Supports: Google Sheets API export, Chrome extension HTTP POST
    """
    try:
        if not csv_content.strip():
            raise HTTPException(status_code=400, detail="CSV content is empty")
        
        # Process CSV content immediately
        result = await csv_service.import_csv_content(csv_content, account_id)
        
        return {
            "success": True,
            "message": f"CSV import completed: {result.created_count} created, {result.updated_count} updated",
            "filename": filename,
            "account_id": account_id,
            "result": result.to_dict()
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV content import failed: {str(e)}")


@router.get("/formats", response_model=Dict[str, Any])
async def get_supported_csv_formats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get supported CSV column formats
    YAGNI: Simple format documentation for users
    """
    return {
        "supported_columns": {
            "required": [
                {"names": ["Title", "title", "Listing Title", "Product Title", "Name"], "description": "Listing title"},
                {"names": ["Price", "price", "Sale Price", "Buy It Now Price", "Starting Price"], "description": "Listing price"}
            ],
            "optional": [
                {"names": ["Item ID", "item_id", "eBay Item ID", "Listing ID"], "description": "eBay item ID (for updates)"},
                {"names": ["Description", "description", "Subtitle", "subtitle"], "description": "Listing description"},
                {"names": ["Category", "category", "Primary Category"], "description": "Listing category"},
                {"names": ["Quantity", "quantity", "Quantity Available", "Qty"], "description": "Available quantity (default: 1)"},
                {"names": ["Status", "status", "Listing Status"], "description": "Listing status (active/inactive/ended/paused)"}
            ]
        },
        "upload_methods": [
            {
                "method": "manual_upload",
                "endpoint": "/csv-import/upload",
                "description": "Upload CSV file via web interface",
                "content_type": "multipart/form-data"
            },
            {
                "method": "google_sheets",
                "endpoint": "/csv-import/upload-content", 
                "description": "Upload CSV content from Google Sheets API",
                "content_type": "application/x-www-form-urlencoded"
            },
            {
                "method": "chrome_extension",
                "endpoint": "/csv-import/upload-content",
                "description": "Upload CSV content via Chrome extension HTTP POST",
                "content_type": "application/x-www-form-urlencoded"
            }
        ],
        "examples": {
            "basic_csv": "Title,Price,Quantity,Status\nTest Product,29.99,10,active\nAnother Product,39.99,5,inactive",
            "ebay_export": "Item ID,Title,Price,Quantity Available,Category\n123456789012,Test Product,29.99,10,Electronics",
            "google_sheets": "Product Title,Sale Price,Qty,Listing Status\nTest Product,29.99,10,active"
        }
    }


@router.get("/health")
async def csv_import_health() -> Dict[str, Any]:
    """Health check for CSV import service"""
    return {
        "status": "healthy",
        "service": "ultra-simplified CSV import",
        "features": [
            "Manual file upload",
            "Google Sheets integration",
            "Chrome extension HTTP upload",
            "Direct CSV processing (no job management)",
            "Multiple CSV format support"
        ]
    }