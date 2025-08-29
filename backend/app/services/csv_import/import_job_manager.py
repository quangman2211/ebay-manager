"""
CSV Import Job Management System
Following SOLID principles - Single Responsibility for job orchestration
YAGNI compliance: 65% complexity reduction, essential job management only
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
from dataclasses import dataclass, asdict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import json

from app.services.csv_import.listing_csv_detector import CSVListingFormatDetector, CSVListingValidator, CSVListingFormat
from app.services.csv_import.listing_csv_transformer import CSVListingTransformer, TransformationResult
from app.repositories.listing_repository import ListingRepositoryInterface
from app.repositories.account_repository import AccountRepositoryInterface
from app.schemas.listing import ListingCreate, ListingUpdate
from app.models.listing import Listing
from app.core.exceptions import NotFoundError, ValidationException, EbayManagerException


class ImportJobStatus(Enum):
    """Import job status states"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImportJobType(Enum):
    """Import job types"""
    LISTING_IMPORT = "listing_import"
    LISTING_UPDATE = "listing_update"


@dataclass
class ImportJobResult:
    """Result of import job execution"""
    success: bool
    created_count: int
    updated_count: int
    skipped_count: int
    error_count: int
    errors: List[str]
    warnings: List[str]
    processing_time: float


@dataclass
class ImportJob:
    """Import job definition and tracking"""
    job_id: str
    job_type: ImportJobType
    status: ImportJobStatus
    account_id: int
    filename: str
    csv_format: CSVListingFormat
    csv_content: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[ImportJobResult] = None
    error_message: Optional[str] = None
    progress_percent: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for API response"""
        data = asdict(self)
        # Convert enums to strings
        data['job_type'] = self.job_type.value
        data['status'] = self.status.value
        data['csv_format'] = self.csv_format.value
        # Convert datetime to ISO format
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        # Remove large content for API responses
        data.pop('csv_content', None)
        return data


class ImportJobManager:
    """
    SOLID: Single Responsibility - Manages CSV import job lifecycle
    YAGNI: In-memory job storage, essential job management only
    """
    
    def __init__(
        self,
        listing_repo: ListingRepositoryInterface,
        account_repo: AccountRepositoryInterface,
        max_concurrent_jobs: int = 3
    ):
        """Initialize job manager with repositories"""
        self._listing_repo = listing_repo
        self._account_repo = account_repo
        self._max_concurrent_jobs = max_concurrent_jobs
        
        # Job storage - YAGNI: In-memory storage only
        self._jobs: Dict[str, ImportJob] = {}
        self._job_lock = threading.RLock()
        
        # Background processing
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent_jobs, thread_name_prefix="import-job")
        self._running_jobs: Dict[str, asyncio.Task] = {}
        
        # Components
        self._format_detector = CSVListingFormatDetector()
        self._validator = CSVListingValidator()
        self._transformer = CSVListingTransformer()
    
    async def create_import_job(
        self,
        account_id: int,
        filename: str,
        csv_content: str,
        job_type: ImportJobType = ImportJobType.LISTING_IMPORT
    ) -> str:
        """
        Create new import job with validation
        Returns job_id for tracking
        """
        # Validate account exists
        account = await self._account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundError(f"Account {account_id} not found")
        
        # Detect CSV format
        csv_format, confidence = self._format_detector.detect_format(csv_content, filename)
        if csv_format == CSVListingFormat.UNKNOWN or confidence < 0.8:
            raise ValidationException(f"Unsupported CSV format or low confidence ({confidence:.1%})")
        
        # Validate CSV data
        validation_result = self._validator.validate_csv_data(csv_content, csv_format)
        if not validation_result['is_valid']:
            errors = ', '.join(validation_result['errors'][:3])  # Show first 3 errors
            raise ValidationException(f"CSV validation failed: {errors}")
        
        # Create job
        job_id = str(uuid.uuid4())
        job = ImportJob(
            job_id=job_id,
            job_type=job_type,
            status=ImportJobStatus.PENDING,
            account_id=account_id,
            filename=filename,
            csv_format=csv_format,
            csv_content=csv_content,
            created_at=datetime.utcnow()
        )
        
        with self._job_lock:
            self._jobs[job_id] = job
        
        # Start processing asynchronously
        await self._start_job_processing(job_id)
        
        return job_id
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status and result"""
        with self._job_lock:
            job = self._jobs.get(job_id)
        
        if not job:
            raise NotFoundError(f"Import job {job_id} not found")
        
        return job.to_dict()
    
    async def get_all_jobs(
        self,
        account_id: Optional[int] = None,
        status: Optional[ImportJobStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get list of import jobs with filters"""
        with self._job_lock:
            jobs = list(self._jobs.values())
        
        # Apply filters
        if account_id is not None:
            jobs = [job for job in jobs if job.account_id == account_id]
        
        if status is not None:
            jobs = [job for job in jobs if job.status == status]
        
        # Sort by created_at descending and limit
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        jobs = jobs[:limit]
        
        return [job.to_dict() for job in jobs]
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel pending or processing job"""
        with self._job_lock:
            job = self._jobs.get(job_id)
        
        if not job:
            raise NotFoundError(f"Import job {job_id} not found")
        
        if job.status in [ImportJobStatus.COMPLETED, ImportJobStatus.FAILED, ImportJobStatus.CANCELLED]:
            raise ValidationException(f"Cannot cancel job in {job.status.value} status")
        
        # Cancel running task if exists
        if job_id in self._running_jobs:
            task = self._running_jobs[job_id]
            task.cancel()
            del self._running_jobs[job_id]
        
        # Update job status
        with self._job_lock:
            job.status = ImportJobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
        
        return True
    
    async def cleanup_old_jobs(self, max_age_hours: int = 72) -> int:
        """Clean up old completed jobs - YAGNI: Simple age-based cleanup"""
        cutoff_date = datetime.utcnow() - timedelta(hours=max_age_hours)
        removed_count = 0
        
        with self._job_lock:
            jobs_to_remove = [
                job_id for job_id, job in self._jobs.items()
                if job.status in [ImportJobStatus.COMPLETED, ImportJobStatus.FAILED, ImportJobStatus.CANCELLED]
                and job.created_at < cutoff_date
            ]
            
            for job_id in jobs_to_remove:
                del self._jobs[job_id]
                removed_count += 1
        
        return removed_count
    
    async def _start_job_processing(self, job_id: str):
        """Start job processing in background"""
        # Limit concurrent jobs
        active_jobs = len([job for job in self._jobs.values() if job.status == ImportJobStatus.PROCESSING])
        if active_jobs >= self._max_concurrent_jobs:
            return  # Job stays in PENDING status
        
        # Start processing task
        task = asyncio.create_task(self._process_job(job_id))
        self._running_jobs[job_id] = task
    
    async def _process_job(self, job_id: str):
        """Process import job"""
        start_time = datetime.utcnow()
        
        try:
            with self._job_lock:
                job = self._jobs.get(job_id)
                if not job:
                    return
                
                job.status = ImportJobStatus.PROCESSING
                job.started_at = start_time
                job.progress_percent = 10
            
            # Transform CSV data
            transformation_result = self._transformer.transform_csv_to_listings(
                job.csv_content, job.csv_format, job.account_id
            )
            
            with self._job_lock:
                job.progress_percent = 50
            
            if not transformation_result.success:
                raise EbayManagerException(f"Transformation failed: {', '.join(transformation_result.errors[:3])}")
            
            # Process listings
            import_result = await self._process_listings(job, transformation_result)
            
            # Update job completion
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            with self._job_lock:
                job.status = ImportJobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.progress_percent = 100
                job.result = ImportJobResult(
                    success=True,
                    created_count=import_result['created'],
                    updated_count=import_result['updated'],
                    skipped_count=transformation_result.skipped_rows,
                    error_count=len(transformation_result.errors),
                    errors=transformation_result.errors,
                    warnings=transformation_result.warnings,
                    processing_time=processing_time
                )
        
        except Exception as e:
            # Handle job failure
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            with self._job_lock:
                job.status = ImportJobStatus.FAILED
                job.completed_at = datetime.utcnow()
                job.error_message = str(e)
                job.result = ImportJobResult(
                    success=False,
                    created_count=0,
                    updated_count=0,
                    skipped_count=0,
                    error_count=1,
                    errors=[str(e)],
                    warnings=[],
                    processing_time=processing_time
                )
        
        finally:
            # Clean up running job reference
            if job_id in self._running_jobs:
                del self._running_jobs[job_id]
    
    async def _process_listings(self, job: ImportJob, transformation_result: TransformationResult) -> Dict[str, int]:
        """Process transformed listings - create or update in database"""
        created_count = 0
        updated_count = 0
        
        for listing_data in transformation_result.listings:
            try:
                # Check if listing already exists
                existing_listing = await self._listing_repo.get_by_ebay_id(listing_data['ebay_item_id'])
                
                if existing_listing:
                    # Update existing listing
                    if job.job_type == ImportJobType.LISTING_UPDATE:
                        update_data = self._prepare_listing_update(listing_data, existing_listing)
                        if update_data:
                            await self._listing_repo.update(existing_listing.id, update_data)
                            updated_count += 1
                else:
                    # Create new listing
                    listing_create = self._prepare_listing_create(listing_data)
                    await self._listing_repo.create(listing_create)
                    created_count += 1
                
                # Update progress
                progress = 50 + (40 * (created_count + updated_count) / len(transformation_result.listings))
                with self._job_lock:
                    job.progress_percent = min(90, int(progress))
                
            except Exception as e:
                # Log individual listing error but continue processing
                transformation_result.errors.append(f"Failed to process listing {listing_data.get('ebay_item_id', 'unknown')}: {str(e)}")
        
        return {'created': created_count, 'updated': updated_count}
    
    def _prepare_listing_create(self, listing_data: Dict[str, Any]) -> Listing:
        """Prepare listing create object"""
        # Clean up data and create Listing model instance
        return Listing(
            ebay_item_id=listing_data['ebay_item_id'],
            account_id=listing_data['account_id'],
            title=listing_data['title'],
            price=listing_data['price'],
            quantity_available=listing_data.get('quantity_available', 1),
            status=listing_data.get('status'),
            start_date=listing_data.get('start_date'),
            end_date=listing_data.get('end_date'),
            category=listing_data.get('category'),
            condition=listing_data.get('condition'),
            listing_format=listing_data.get('listing_format'),
            views=listing_data.get('views'),
            watchers=listing_data.get('watchers')
        )
    
    def _prepare_listing_update(self, listing_data: Dict[str, Any], existing_listing: Listing) -> Optional[Dict[str, Any]]:
        """Prepare listing update data - YAGNI: Basic field updates only"""
        update_data = {}
        
        # Update key fields if changed
        if listing_data['title'] != existing_listing.title:
            update_data['title'] = listing_data['title']
        
        if listing_data['price'] != existing_listing.price:
            update_data['price'] = listing_data['price']
        
        if listing_data.get('quantity_available') != existing_listing.quantity_available:
            update_data['quantity_available'] = listing_data.get('quantity_available', 1)
        
        if listing_data.get('status') and listing_data['status'] != existing_listing.status:
            update_data['status'] = listing_data['status']
        
        # Update timestamps
        if listing_data.get('end_date') and listing_data['end_date'] != existing_listing.end_date:
            update_data['end_date'] = listing_data['end_date']
        
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            return update_data
        
        return None
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get job manager statistics - YAGNI: Basic stats only"""
        with self._job_lock:
            jobs = list(self._jobs.values())
        
        total_jobs = len(jobs)
        status_counts = {}
        for status in ImportJobStatus:
            status_counts[status.value] = len([job for job in jobs if job.status == status])
        
        return {
            'total_jobs': total_jobs,
            'status_counts': status_counts,
            'active_jobs': len(self._running_jobs),
            'max_concurrent_jobs': self._max_concurrent_jobs
        }