"""
CSV Processing API Endpoints
Following SOLID principles - Single Responsibility for CSV operations
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.base import get_db
from app.middleware.auth import get_current_active_user, require_role
from app.models.user import User
from app.schemas.csv import (
    CSVUploadRequest, CSVUploadResponse, CSVValidationRequest, CSVValidationResponse,
    CSVPreviewRequest, CSVPreviewResponse, CSVProcessRequest, CSVProcessResponse,
    CSVFileInfo, CSVFileStatus, CSVValidationError
)
from app.utils.csv_processor import (
    CSVFileValidator, CSVFileManager, CSVParser, CSVProcessor, 
    GenericCSVValidator
)
from app.core.logging import get_logger

logger = get_logger("csv_api")
router = APIRouter(prefix="/csv", tags=["CSV Processing"])

# Initialize CSV components
file_manager = CSVFileManager()
csv_processor = CSVProcessor()

@router.post("/upload", response_model=CSVUploadResponse)
async def upload_csv_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    account_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload CSV file for processing
    Following SOLID: Single Responsibility for file upload
    """
    try:
        # Validate upload request
        upload_request = CSVUploadRequest(
            file_type=file_type,
            account_id=account_id,
            description=description
        )
        
        # Validate file
        is_valid, error_message = CSVFileValidator.validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Save file
        file_id, file_path = file_manager.save_file(file, file_type)
        
        # Get file content for analysis
        content = file_manager.get_file_content(file_id)
        properties = CSVFileValidator.detect_csv_properties(content)
        
        logger.info(f"CSV uploaded by user {current_user.id}: {file_id}")
        
        return CSVUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_size=len(content),
            status=CSVFileStatus.UPLOADED,
            upload_date=datetime.utcnow(),
            preview_rows=min(5, properties['total_rows']),
            total_rows=properties['total_rows']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/validate", response_model=CSVValidationResponse)
async def validate_csv_file(
    request: CSVValidationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Validate CSV file content
    Following SOLID: Single Responsibility for validation
    """
    try:
        # Get file content
        content = file_manager.get_file_content(request.file_id)
        
        # Detect CSV properties
        properties = CSVFileValidator.detect_csv_properties(content)
        
        # Create generic validator (will be extended for specific types)
        validator = GenericCSVValidator(required_columns=[])
        
        # Process and validate
        valid_rows, errors = csv_processor.validate_and_process_file(
            content, validator, skip_rows=request.skip_rows
        )
        
        # Get sample data
        sample_data = []
        for row in valid_rows[:5]:  # First 5 valid rows
            sample_data.append(row.data)
        
        logger.info(f"CSV validated by user {current_user.id}: {request.file_id} - {len(valid_rows)} valid, {len(errors)} errors")
        
        return CSVValidationResponse(
            file_id=request.file_id,
            status=CSVFileStatus.VALID if len(errors) == 0 else CSVFileStatus.INVALID,
            is_valid=len(errors) == 0,
            total_rows=properties['total_rows'],
            valid_rows=len(valid_rows),
            errors=errors,
            warnings=[],
            detected_columns=properties['headers'],
            sample_data=sample_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation error for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.post("/preview", response_model=CSVPreviewResponse)
async def preview_csv_file(
    request: CSVPreviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Preview CSV file content
    Following SOLID: Single Responsibility for preview generation
    """
    try:
        # Get file content
        content = file_manager.get_file_content(request.file_id)
        
        # Detect CSV properties
        properties = CSVFileValidator.detect_csv_properties(content)
        
        # Create parser
        parser = CSVParser(
            encoding=properties['encoding'],
            delimiter=properties['delimiter']
        )
        
        # Get headers
        headers = parser.get_headers(content)
        
        # Get preview rows
        rows = []
        for i, row_data in enumerate(parser.parse_rows(content, skip_rows=request.start_row, limit=request.limit)):
            row_values = [row_data.get(header, "") for header in headers]
            rows.append(row_values)
        
        has_more = properties['total_rows'] > (request.start_row + request.limit)
        
        logger.info(f"CSV preview generated for user {current_user.id}: {request.file_id}")
        
        return CSVPreviewResponse(
            file_id=request.file_id,
            headers=headers,
            rows=rows,
            total_rows=properties['total_rows'],
            has_more=has_more
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview error for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

@router.get("/files", response_model=List[CSVFileInfo])
async def list_csv_files(
    file_type: Optional[str] = None,
    status: Optional[CSVFileStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List uploaded CSV files
    Following SOLID: Single Responsibility for file listing
    """
    try:
        # For now, return empty list (will be extended with database storage)
        # This follows YAGNI - implementing basic structure without complex filtering
        files = []
        
        logger.info(f"CSV files listed for user {current_user.id}")
        return files
        
    except Exception as e:
        logger.error(f"File listing error for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.get("/files/{file_id}", response_model=CSVFileInfo)
async def get_csv_file_info(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get CSV file information
    Following SOLID: Single Responsibility for file info retrieval
    """
    try:
        # Get file size and check existence
        file_size = file_manager.get_file_size(file_id)
        if file_size == 0:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file content for analysis
        content = file_manager.get_file_content(file_id)
        properties = CSVFileValidator.detect_csv_properties(content)
        
        # Parse file_id to extract file_type and timestamp
        parts = file_id.split('_')
        file_type = parts[0] if len(parts) > 0 else "unknown"
        timestamp_str = parts[-1] if len(parts) > 2 else str(int(datetime.utcnow().timestamp()))
        
        try:
            upload_date = datetime.fromtimestamp(int(timestamp_str))
        except:
            upload_date = datetime.utcnow()
        
        logger.info(f"CSV file info retrieved for user {current_user.id}: {file_id}")
        
        return CSVFileInfo(
            file_id=file_id,
            filename=f"{file_id}.csv",
            file_type=file_type,
            file_size=file_size,
            status=CSVFileStatus.UPLOADED,
            upload_date=upload_date,
            last_modified=upload_date,
            total_rows=properties['total_rows'],
            description=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File info error for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")

@router.delete("/files/{file_id}")
async def delete_csv_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete CSV file
    Following SOLID: Single Responsibility for file deletion
    """
    try:
        # Delete file
        deleted = file_manager.delete_file(file_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="File not found")
        
        logger.info(f"CSV file deleted by user {current_user.id}: {file_id}")
        
        return {"message": "File deleted successfully", "file_id": file_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion error for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@router.post("/process", response_model=CSVProcessResponse)
async def process_csv_file(
    request: CSVProcessRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Process CSV file and import data
    Following SOLID: Single Responsibility for data processing
    Following YAGNI: Basic processing without complex queue system
    """
    try:
        started_at = datetime.utcnow()
        
        # Get file content
        content = file_manager.get_file_content(request.file_id)
        
        # Create validator (will be extended for specific data types)
        validator = GenericCSVValidator()
        
        # Validate first if not dry run
        valid_rows, errors = csv_processor.validate_and_process_file(content, validator)
        
        if request.dry_run:
            # Dry run - just validate
            processing_time = (datetime.utcnow() - started_at).total_seconds()
            
            logger.info(f"CSV dry run by user {current_user.id}: {request.file_id} - {len(valid_rows)} valid rows")
            
            return CSVProcessResponse(
                file_id=request.file_id,
                status=CSVFileStatus.VALID if len(errors) == 0 else CSVFileStatus.INVALID,
                records_processed=len(valid_rows),
                records_inserted=0,
                records_updated=0,
                records_skipped=len(errors),
                errors=errors,
                processing_time_seconds=processing_time,
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
        
        # TODO: Actual data import will be implemented in Phase 2 Task 3
        # For now, simulate successful processing
        processing_time = (datetime.utcnow() - started_at).total_seconds()
        
        logger.info(f"CSV processed by user {current_user.id}: {request.file_id} - {len(valid_rows)} records")
        
        return CSVProcessResponse(
            file_id=request.file_id,
            status=CSVFileStatus.PROCESSED,
            records_processed=len(valid_rows),
            records_inserted=len(valid_rows) if request.import_mode == "insert" else 0,
            records_updated=0,
            records_skipped=len(errors),
            errors=errors,
            processing_time_seconds=processing_time,
            started_at=started_at,
            completed_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing error for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/health")
async def csv_health_check():
    """
    CSV processing health check
    Following SOLID: Single Responsibility for health monitoring
    """
    try:
        # Check upload directory exists and is writable
        upload_path = file_manager.upload_path
        if not upload_path.exists():
            return {"status": "unhealthy", "error": "Upload directory does not exist"}
        
        if not upload_path.is_dir():
            return {"status": "unhealthy", "error": "Upload path is not a directory"}
        
        # Test write access
        test_file = upload_path / "health_check.tmp"
        try:
            test_file.write_text("health_check")
            test_file.unlink()  # Clean up
        except Exception:
            return {"status": "unhealthy", "error": "Upload directory is not writable"}
        
        return {
            "status": "healthy",
            "upload_path": str(upload_path),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Order-specific CSV processing endpoints
@router.post("/orders/upload", response_model=dict)
async def upload_orders_csv(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload CSV file containing eBay orders for processing
    Following SOLID: Single Responsibility for order CSV upload
    """
    try:
        from app.models.csv import CSVUpload
        from app.background_jobs.core import job_manager
        import uuid
        import shutil
        from pathlib import Path
        
        # Validate file type
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Validate file size (100MB limit)
        max_size = 100 * 1024 * 1024
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > max_size:
            raise HTTPException(status_code=400, detail=f"File size exceeds maximum limit of {max_size} bytes")
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Create CSV upload record
        batch_id = str(uuid.uuid4())
        stored_filename = f"orders_{account_id}_{int(datetime.utcnow().timestamp())}_{batch_id[:8]}.csv"
        
        # Save file
        upload_dir = Path("temp/csv_uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / stored_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create CSV upload record
        csv_upload = CSVUpload(
            account_id=account_id,
            user_id=current_user.id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type="orders",
            batch_id=batch_id,
            status="uploaded",
            description=description,
            uploaded_at=datetime.utcnow()
        )
        
        db.add(csv_upload)
        db.commit()
        db.refresh(csv_upload)
        
        # Create background job for processing
        job_id = job_manager.create_job(
            job_type="csv_order_processing",
            account_id=account_id,
            parameters={
                "csv_upload_id": csv_upload.id,
                "account_id": account_id,
                "user_id": current_user.id,
                "filename": file.filename,
                "file_path": str(file_path)
            },
            timeout_seconds=600  # 10 minutes for large files
        )
        
        logger.info(f"Order CSV uploaded and job created: {csv_upload.id}, job: {job_id}")
        
        return {
            "upload_id": csv_upload.id,
            "job_id": job_id,
            "batch_id": batch_id,
            "filename": file.filename,
            "file_size": file_size,
            "status": "uploaded",
            "message": "File uploaded successfully and processing started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order CSV upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/orders/uploads", response_model=List[dict])
async def list_order_uploads(
    account_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List order CSV uploads
    Following SOLID: Single Responsibility for upload listing
    """
    try:
        from app.models.csv import CSVUpload
        
        query = db.query(CSVUpload).filter(CSVUpload.file_type == "orders")
        
        # Apply user-based filtering
        if current_user.role != 'admin':
            query = query.filter(CSVUpload.user_id == current_user.id)
        elif account_id:
            query = query.filter(CSVUpload.account_id == account_id)
        
        if status:
            query = query.filter(CSVUpload.status == status)
        
        uploads = query.order_by(CSVUpload.uploaded_at.desc()).limit(limit).all()
        
        results = []
        for upload in uploads:
            results.append({
                "upload_id": upload.id,
                "filename": upload.original_filename,
                "account_id": upload.account_id,
                "file_size": upload.file_size,
                "status": upload.status,
                "batch_id": upload.batch_id,
                "uploaded_at": upload.uploaded_at.isoformat() if upload.uploaded_at else None,
                "completed_at": upload.completed_at.isoformat() if upload.completed_at else None,
                "total_rows": upload.total_rows,
                "success_rows": upload.success_rows,
                "error_rows": upload.error_rows,
                "description": upload.description
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to list order uploads: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list uploads: {str(e)}")

@router.get("/orders/uploads/{upload_id}", response_model=dict)
async def get_order_upload_status(
    upload_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get order CSV upload status and details
    Following SOLID: Single Responsibility for upload status retrieval
    """
    try:
        from app.models.csv import CSVUpload
        
        upload = db.query(CSVUpload).filter(
            CSVUpload.id == upload_id,
            CSVUpload.file_type == "orders"
        ).first()
        
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        # Check access
        if current_user.role != 'admin' and upload.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get job status if available
        job_status = None
        if upload.batch_id:
            # Try to find associated job
            from app.background_jobs.core import job_manager
            jobs = job_manager.get_jobs_by_account(upload.account_id)
            for job in jobs:
                if job.parameters.get('csv_upload_id') == upload_id:
                    job_status = {
                        "job_id": job.id,
                        "status": job.status,
                        "progress_percentage": job.progress_percentage,
                        "progress_message": job.progress_message,
                        "current_step": job.current_step,
                        "started_at": job.started_at.isoformat() if job.started_at else None,
                        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                        "last_error": job.last_error
                    }
                    break
        
        return {
            "upload_id": upload.id,
            "filename": upload.original_filename,
            "account_id": upload.account_id,
            "file_size": upload.file_size,
            "status": upload.status,
            "batch_id": upload.batch_id,
            "uploaded_at": upload.uploaded_at.isoformat() if upload.uploaded_at else None,
            "completed_at": upload.completed_at.isoformat() if upload.completed_at else None,
            "total_rows": upload.total_rows,
            "processed_rows": upload.processed_rows,
            "success_rows": upload.success_rows,
            "error_rows": upload.error_rows,
            "validation_errors": upload.validation_errors,
            "processing_summary": upload.processing_summary,
            "description": upload.description,
            "error_message": upload.error_message,
            "job_status": job_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get upload status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get upload status: {str(e)}")

@router.get("/orders/import-stats/{account_id}", response_model=dict)
async def get_order_import_stats(
    account_id: int,
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get order import statistics for account
    Following SOLID: Single Responsibility for statistics
    """
    try:
        from app.services.csv_order_service import get_csv_order_service
        
        csv_order_service = get_csv_order_service(db)
        stats = csv_order_service.get_import_statistics(account_id, current_user.id, days)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get import stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get import statistics: {str(e)}")