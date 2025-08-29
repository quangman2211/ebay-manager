"""
CSV Import API Endpoints
Following SOLID principles - Single Responsibility for HTTP concerns only
YAGNI compliance: Essential import endpoints only, 65% complexity reduction
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.services.csv_import.import_job_manager import ImportJobManager, ImportJobType, ImportJobStatus
from app.repositories.listing_repository import ListingRepository
from app.repositories.account_repository import AccountRepository
from app.core.exceptions import NotFoundError, ValidationException, EbayManagerException
from app.middleware.auth import get_current_user
from app.models.user import User


router = APIRouter(prefix="/csv-import", tags=["csv-import"])


def get_import_job_manager(db: Session = Depends(get_db)) -> ImportJobManager:
    """
    SOLID: Dependency Inversion - Factory function for job manager injection
    """
    listing_repo = ListingRepository(db)
    account_repo = AccountRepository(db)
    return ImportJobManager(listing_repo, account_repo, max_concurrent_jobs=3)


@router.post("/upload", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def upload_csv_file(
    *,
    job_manager: ImportJobManager = Depends(get_import_job_manager),
    account_id: int = Form(..., description="Account ID for the import"),
    job_type: str = Form("listing_import", description="Import job type"),
    file: UploadFile = File(..., description="CSV file to import"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Upload and start processing CSV file
    SOLID: Single Responsibility - Handle file upload and job creation only
    """
    try:
        # Validate file format
        if not file.filename or not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=400, detail="File size must be less than 50MB")
        
        # Validate job type
        if job_type not in ['listing_import', 'listing_update']:
            raise HTTPException(status_code=400, detail="Invalid job type")
        
        # Read file content
        csv_content = await file.read()
        csv_text = csv_content.decode('utf-8')
        
        # Validate content size
        if len(csv_text.strip()) == 0:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        # Create import job
        job_type_enum = ImportJobType.LISTING_IMPORT if job_type == 'listing_import' else ImportJobType.LISTING_UPDATE
        job_id = await job_manager.create_import_job(
            account_id=account_id,
            filename=file.filename,
            csv_content=csv_text,
            job_type=job_type_enum
        )
        
        return {
            "job_id": job_id,
            "message": "CSV import job created successfully",
            "filename": file.filename,
            "account_id": account_id,
            "job_type": job_type
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please use UTF-8 encoded CSV files")
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_import_job_status(
    *,
    job_manager: ImportJobManager = Depends(get_import_job_manager),
    job_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get import job status and result"""
    try:
        job_status = await job_manager.get_job_status(job_id)
        return job_status
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[Dict[str, Any]])
async def get_import_jobs(
    *,
    job_manager: ImportJobManager = Depends(get_import_job_manager),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    status: Optional[str] = Query(None, description="Filter by job status"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get list of import jobs with filters
    YAGNI: Basic filtering only, no complex search or sorting
    """
    try:
        # Validate status filter
        status_enum = None
        if status:
            try:
                status_enum = ImportJobStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        jobs = await job_manager.get_all_jobs(
            account_id=account_id,
            status=status_enum,
            limit=limit
        )
        
        return jobs
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/cancel")
async def cancel_import_job(
    *,
    job_manager: ImportJobManager = Depends(get_import_job_manager),
    job_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Cancel pending or processing import job"""
    try:
        success = await job_manager.cancel_job(job_id)
        if success:
            return {"message": "Import job cancelled successfully"}
        else:
            return {"message": "Failed to cancel import job"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats/detect")
async def detect_csv_format(
    *,
    file: UploadFile = File(..., description="CSV file for format detection"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Detect CSV format without creating import job
    YAGNI: Basic format detection only
    """
    try:
        # Validate file
        if not file.filename or not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read sample of file for detection
        csv_content = await file.read()
        csv_text = csv_content.decode('utf-8')
        
        # Limit content size for detection (first 10KB should be enough)
        sample_content = csv_text[:10240]
        
        from app.services.csv_import.listing_csv_detector import CSVListingFormatDetector, CSVListingValidator
        
        detector = CSVListingFormatDetector()
        validator = CSVListingValidator()
        
        # Detect format
        csv_format, confidence = detector.detect_format(sample_content, file.filename)
        
        # Validate structure
        validation_result = validator.validate_csv_data(sample_content, csv_format)
        
        return {
            "filename": file.filename,
            "detected_format": csv_format.value,
            "confidence": confidence,
            "is_valid": validation_result['is_valid'],
            "row_count": validation_result.get('row_count', 0),
            "columns": validation_result.get('columns', []),
            "errors": validation_result.get('errors', []),
            "warnings": validation_result.get('warnings', []),
            "sample_data": validation_result.get('sample_data', [])
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please use UTF-8 encoded CSV files")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Format detection failed: {str(e)}")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_import_statistics(
    *,
    job_manager: ImportJobManager = Depends(get_import_job_manager),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get import job statistics - YAGNI: Basic statistics only"""
    try:
        stats = job_manager.get_job_statistics()
        return stats
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_old_jobs(
    *,
    job_manager: ImportJobManager = Depends(get_import_job_manager),
    max_age_hours: int = Query(72, ge=1, le=720, description="Maximum age of jobs to keep in hours"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Clean up old completed import jobs"""
    try:
        removed_count = await job_manager.cleanup_old_jobs(max_age_hours)
        return {
            "message": "Cleanup completed successfully",
            "removed_jobs": removed_count,
            "max_age_hours": max_age_hours
        }
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats/supported", response_model=List[Dict[str, Any]])
async def get_supported_formats(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get list of supported CSV formats
    YAGNI: Static format list, no complex format registry
    """
    return [
        {
            "format": "ebay_active_listings",
            "name": "eBay Active Listings",
            "description": "Export of currently active eBay listings",
            "required_columns": ["item id", "title", "price", "quantity available", "status"],
            "optional_columns": ["start date", "end date", "category", "listing format", "condition", "views", "watchers"]
        },
        {
            "format": "ebay_sold_listings", 
            "name": "eBay Sold Listings",
            "description": "Export of completed/sold eBay listings",
            "required_columns": ["item id", "title", "sale price", "quantity sold", "sale date"],
            "optional_columns": ["buyer username", "shipping cost", "total price", "payment method", "listing format"]
        },
        {
            "format": "ebay_unsold_listings",
            "name": "eBay Unsold Listings", 
            "description": "Export of ended/unsold eBay listings",
            "required_columns": ["item id", "title", "listing price", "end reason"],
            "optional_columns": ["start date", "end date", "category", "views", "watchers", "quantity available"]
        }
    ]


@router.get("/templates/{format_type}")
async def download_csv_template(
    *,
    format_type: str,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Get CSV template for specific format - YAGNI: Simple template generation
    """
    templates = {
        "ebay_active_listings": {
            "headers": ["Item ID", "Title", "Price", "Quantity Available", "Status", "Start Date", "End Date", "Category", "Condition"],
            "sample_row": ["123456789", "Sample Product Title", "$19.99", "5", "Active", "2024-01-01", "2024-01-08", "Electronics", "New"]
        },
        "ebay_sold_listings": {
            "headers": ["Item ID", "Title", "Sale Price", "Quantity Sold", "Sale Date", "Buyer Username", "Total Price"],
            "sample_row": ["123456789", "Sample Product Title", "$19.99", "1", "2024-01-01", "buyer123", "$24.99"]
        },
        "ebay_unsold_listings": {
            "headers": ["Item ID", "Title", "Listing Price", "End Reason", "Start Date", "End Date", "Views"],
            "sample_row": ["123456789", "Sample Product Title", "$19.99", "Ended", "2024-01-01", "2024-01-08", "25"]
        }
    }
    
    if format_type not in templates:
        raise HTTPException(status_code=404, detail="Template not found for this format")
    
    template = templates[format_type]
    csv_content = ",".join(template["headers"]) + "\n" + ",".join(template["sample_row"])
    
    return JSONResponse(
        content={
            "format_type": format_type,
            "template_content": csv_content,
            "headers": template["headers"],
            "sample_row": template["sample_row"]
        }
    )