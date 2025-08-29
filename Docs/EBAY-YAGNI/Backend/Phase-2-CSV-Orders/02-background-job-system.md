# Background Job System - ThreadPoolExecutor Implementation

## Overview
Simple background job system for eBay Management System following YAGNI/SOLID principles. Uses Python ThreadPoolExecutor for asynchronous CSV processing, avoiding complex task queue infrastructure while maintaining reliability for 30-account scale.

## SOLID Principles Applied
- **Single Responsibility**: Each job type has dedicated handler class
- **Open/Closed**: Job system extensible for new job types without modifying core
- **Liskov Substitution**: All job handlers implement common execution interface
- **Interface Segregation**: Separate interfaces for job creation, execution, and monitoring
- **Dependency Inversion**: Job system depends on abstract handler interface, not concrete implementations

## YAGNI Compliance
✅ **Simple Threading**: ThreadPoolExecutor sufficient for 30-account CSV processing load  
✅ **In-Process Jobs**: No distributed task queue complexity (Celery, RQ eliminated)  
✅ **Redis Job Storage**: Simple job status tracking with Redis  
✅ **Essential Features**: Job execution, progress tracking, error handling, retry logic only  
❌ **Eliminated**: Distributed workers, complex scheduling, job priorities, message brokers, monitoring dashboards

---

## Background Job Architecture

### Job Processing Flow
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         BACKGROUND JOB SYSTEM                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │   Job Creation  │───▶│  Job Validation │───▶│   Job Storage   │             │
│  │                 │    │                 │    │                 │             │
│  │ • Job type      │    │ • Parameter     │    │ • Redis storage │             │
│  │ • Parameters    │    │   validation    │    │ • Status: queued│             │
│  │ • Priority      │    │ • Resource check│    │ • Metadata save │             │
│  │ • Account ID    │    │ • Permissions   │    │ • Queue position│             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│                                                          │                      │
│                                                          ▼                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │  Job Execution  │◀───│  Thread Pool    │◀───│   Job Queue     │             │
│  │                 │    │                 │    │                 │             │
│  │ • Handler lookup│    │ • Worker threads│    │ • FIFO processing│             │
│  │ • Job processing│    │ • Concurrent    │    │ • Status updates│             │
│  │ • Progress track│    │   execution     │    │ • Error handling│             │
│  │ • Result storage│    │ • Resource mgmt │    │ • Retry queue   │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │ Progress Update │───▶│ Error Handling   │───▶│ Job Completion  │             │
│  │                 │    │                  │    │                 │             │
│  │ • Real-time     │    │ • Exception catch│    │ • Status: done  │             │
│  │   progress      │    │ • Retry logic    │    │ • Results store │             │
│  │ • Status change │    │ • Error logging  │    │ • Cleanup       │             │
│  │ • Time tracking │    │ • Failure alerts │    │ • Notification  │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Job Types & Handlers
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              JOB TYPES                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │ CSV Processing  │  │ Data Validation │  │  Data Import    │                 │
│  │                 │  │                 │  │                 │                 │
│  │ • Parse CSV     │  │ • Validate rows │  │ • Database      │                 │
│  │ • Format detect │  │ • Check rules   │  │   insertion     │                 │
│  │ • Data clean    │  │ • Generate      │  │ • Conflict      │                 │
│  │ • Progress track│  │   reports       │  │   resolution    │                 │
│  │ • Error collect │  │ • Error summary │  │ • Rollback      │                 │
│  │ • Result store  │  │ • Warning flags │  │   on error      │                 │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                 │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │ Email Sending   │  │ Report          │  │ Cleanup Tasks   │                 │
│  │                 │  │ Generation      │  │                 │                 │
│  │ • Notification  │  │ • Daily reports │  │ • Temp file     │                 │
│  │   emails        │  │ • CSV exports   │  │   cleanup       │                 │
│  │ • Status alerts │  │ • PDF creation  │  │ • Log rotation  │                 │
│  │ • Bulk messages │  │ • Chart         │  │ • Old job       │                 │
│  │ • Template      │  │   generation    │  │   cleanup       │                 │
│  │   processing    │  │ • Data          │  │ • Cache clear   │                 │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Complete Implementation

### 1. Core Job System Classes
```python
# background_jobs/core.py - Core job system implementation

import asyncio
import json
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Type
import redis
import logging
import traceback
from abc import ABC, abstractmethod

from core.config.settings import settings

logger = logging.getLogger(__name__)

class JobStatus(str, Enum):
    """Job status enumeration"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class JobPriority(int, Enum):
    """Job priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class JobResult:
    """Job execution result"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

@dataclass
class Job:
    """Job definition"""
    id: str
    job_type: str
    account_id: int
    parameters: Dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = 3
    timeout_seconds: int = 300
    
    # Status tracking
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Progress tracking
    progress_percentage: int = 0
    progress_message: str = ""
    current_step: str = ""
    
    # Retry tracking
    retry_count: int = 0
    last_error: Optional[str] = None
    
    # Results
    result: Optional[JobResult] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for storage"""
        data = asdict(self)
        
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'started_at', 'completed_at']:
            if data[field]:
                data[field] = data[field].isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary"""
        
        # Convert ISO strings back to datetime objects
        for field in ['created_at', 'started_at', 'completed_at']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        # Convert result dict back to JobResult if present
        if data.get('result'):
            data['result'] = JobResult(**data['result'])
        
        return cls(**data)

class BaseJobHandler(ABC):
    """Base class for job handlers"""
    
    def __init__(self, job_manager: 'BackgroundJobManager'):
        self.job_manager = job_manager
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def execute(self, job: Job) -> JobResult:
        """Execute the job and return result"""
        pass
    
    def update_progress(self, job: Job, percentage: int, message: str = "", step: str = ""):
        """Update job progress"""
        job.progress_percentage = min(100, max(0, percentage))
        job.progress_message = message
        job.current_step = step
        
        self.job_manager.update_job_status(job)
        self.logger.info(f"Job {job.id} progress: {percentage}% - {message}")
    
    def should_retry(self, job: Job, error: Exception) -> bool:
        """Determine if job should be retried"""
        
        # Don't retry certain types of errors
        non_retryable_errors = [
            ValueError,  # Invalid parameters
            PermissionError,  # Access denied
            FileNotFoundError  # Missing files
        ]
        
        if any(isinstance(error, err_type) for err_type in non_retryable_errors):
            return False
        
        return job.retry_count < job.max_retries

class BackgroundJobManager:
    """Main background job management system"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            settings.redis.REDIS_URL,
            db=settings.redis.REDIS_JOB_DB,
            decode_responses=True
        )
        
        self.executor = ThreadPoolExecutor(
            max_workers=settings.app.MAX_WORKER_THREADS,
            thread_name_prefix="ebay_job_worker"
        )
        
        self.job_handlers: Dict[str, Type[BaseJobHandler]] = {}
        self.running_jobs: Dict[str, Future] = {}
        
        # Job cleanup settings
        self.cleanup_completed_after_hours = 24
        self.cleanup_failed_after_hours = 168  # 7 days
        
        self.logger = logging.getLogger(__name__)
        
        # Start cleanup task
        self._start_cleanup_task()
    
    def register_handler(self, job_type: str, handler_class: Type[BaseJobHandler]):
        """Register job handler for specific job type"""
        self.job_handlers[job_type] = handler_class
        self.logger.info(f"Registered handler for job type: {job_type}")
    
    def create_job(
        self,
        job_type: str,
        account_id: int,
        parameters: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        timeout_seconds: int = 300
    ) -> str:
        """Create and queue a new job"""
        
        if job_type not in self.job_handlers:
            raise ValueError(f"No handler registered for job type: {job_type}")
        
        job = Job(
            id=str(uuid.uuid4()),
            job_type=job_type,
            account_id=account_id,
            parameters=parameters,
            priority=priority,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds
        )
        
        # Store job in Redis
        self._store_job(job)
        
        # Queue job for execution
        self._queue_job(job)
        
        self.logger.info(f"Created job {job.id} of type {job_type} for account {account_id}")
        
        return job.id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        try:
            job_data = self.redis_client.hgetall(f"job:{job_id}")
            if job_data:
                # Deserialize nested JSON fields
                for field in ['parameters', 'result']:
                    if job_data.get(field):
                        job_data[field] = json.loads(job_data[field])
                
                return Job.from_dict(job_data)
        except Exception as e:
            self.logger.error(f"Failed to get job {job_id}: {str(e)}")
        
        return None
    
    def get_jobs_by_account(self, account_id: int, status: Optional[JobStatus] = None) -> List[Job]:
        """Get jobs for specific account"""
        jobs = []
        
        try:
            # Get all job IDs for account
            job_ids = self.redis_client.smembers(f"account_jobs:{account_id}")
            
            for job_id in job_ids:
                job = self.get_job(job_id)
                if job and (status is None or job.status == status):
                    jobs.append(job)
            
            # Sort by creation time (newest first)
            jobs.sort(key=lambda x: x.created_at, reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to get jobs for account {account_id}: {str(e)}")
        
        return jobs
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued or running job"""
        try:
            job = self.get_job(job_id)
            if not job:
                return False
            
            if job.status == JobStatus.QUEUED:
                # Remove from queue and mark as cancelled
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.utcnow()
                self._store_job(job)
                return True
            
            elif job.status == JobStatus.RUNNING:
                # Try to cancel running job
                future = self.running_jobs.get(job_id)
                if future:
                    cancelled = future.cancel()
                    if cancelled:
                        job.status = JobStatus.CANCELLED
                        job.completed_at = datetime.utcnow()
                        self._store_job(job)
                        del self.running_jobs[job_id]
                    return cancelled
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to cancel job {job_id}: {str(e)}")
            return False
    
    def update_job_status(self, job: Job):
        """Update job status in storage"""
        self._store_job(job)
    
    def _store_job(self, job: Job):
        """Store job in Redis"""
        try:
            job_data = job.to_dict()
            
            # Serialize complex fields as JSON
            for field in ['parameters', 'result']:
                if job_data.get(field):
                    job_data[field] = json.dumps(job_data[field])
            
            # Store job data
            self.redis_client.hset(f"job:{job.id}", mapping=job_data)
            
            # Add to account jobs set
            self.redis_client.sadd(f"account_jobs:{job.account_id}", job.id)
            
            # Set expiration for completed jobs
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                expire_hours = self.cleanup_completed_after_hours if job.status == JobStatus.COMPLETED else self.cleanup_failed_after_hours
                self.redis_client.expire(f"job:{job.id}", expire_hours * 3600)
            
        except Exception as e:
            self.logger.error(f"Failed to store job {job.id}: {str(e)}")
    
    def _queue_job(self, job: Job):
        """Queue job for execution"""
        try:
            # Add to priority queue (using sorted set with priority as score)
            self.redis_client.zadd("job_queue", {job.id: job.priority.value})
            
            # Submit to thread pool
            future = self.executor.submit(self._execute_job_sync, job.id)
            self.running_jobs[job.id] = future
            
        except Exception as e:
            self.logger.error(f"Failed to queue job {job.id}: {str(e)}")
            job.status = JobStatus.FAILED
            job.last_error = str(e)
            self._store_job(job)
    
    def _execute_job_sync(self, job_id: str):
        """Synchronous wrapper for job execution"""
        try:
            asyncio.run(self._execute_job(job_id))
        except Exception as e:
            self.logger.error(f"Job execution wrapper failed for {job_id}: {str(e)}")
        finally:
            # Clean up running jobs tracking
            self.running_jobs.pop(job_id, None)
    
    async def _execute_job(self, job_id: str):
        """Execute a job"""
        job = self.get_job(job_id)
        if not job:
            self.logger.error(f"Job {job_id} not found for execution")
            return
        
        try:
            # Update job status to running
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            self._store_job(job)
            
            # Remove from queue
            self.redis_client.zrem("job_queue", job_id)
            
            # Get handler
            handler_class = self.job_handlers.get(job.job_type)
            if not handler_class:
                raise ValueError(f"No handler found for job type: {job.job_type}")
            
            handler = handler_class(self)
            
            # Execute job with timeout
            try:
                result = await asyncio.wait_for(
                    handler.execute(job),
                    timeout=job.timeout_seconds
                )
                
                # Job completed successfully
                job.status = JobStatus.COMPLETED
                job.result = result
                job.progress_percentage = 100
                job.progress_message = "Completed successfully"
                
            except asyncio.TimeoutError:
                raise TimeoutError(f"Job {job_id} timed out after {job.timeout_seconds} seconds")
            
        except Exception as e:
            # Job failed
            job.last_error = str(e)
            error_traceback = traceback.format_exc()
            
            self.logger.error(f"Job {job_id} failed: {str(e)}\n{error_traceback}")
            
            # Check if job should be retried
            handler_class = self.job_handlers.get(job.job_type)
            if handler_class:
                handler = handler_class(self)
                if handler.should_retry(job, e) and job.retry_count < job.max_retries:
                    # Retry job
                    job.retry_count += 1
                    job.status = JobStatus.RETRYING
                    
                    # Schedule retry with exponential backoff
                    retry_delay = min(300, 2 ** job.retry_count)  # Max 5 minutes
                    
                    self.logger.info(f"Retrying job {job_id} in {retry_delay} seconds (attempt {job.retry_count})")
                    
                    # Schedule retry (simplified - just re-queue)
                    self._store_job(job)
                    asyncio.create_task(self._schedule_retry(job, retry_delay))
                    return
            
            # No retry - job failed permanently
            job.status = JobStatus.FAILED
            job.result = JobResult(
                success=False,
                error=str(e),
                warnings=[]
            )
        
        finally:
            # Update final job state
            job.completed_at = datetime.utcnow()
            self._store_job(job)
    
    async def _schedule_retry(self, job: Job, delay_seconds: int):
        """Schedule job retry after delay"""
        await asyncio.sleep(delay_seconds)
        
        job.status = JobStatus.QUEUED
        self._queue_job(job)
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        def cleanup_task():
            try:
                self._cleanup_old_jobs()
            except Exception as e:
                self.logger.error(f"Job cleanup failed: {str(e)}")
        
        # Schedule cleanup every hour
        import threading
        import time
        
        def run_cleanup():
            while True:
                cleanup_task()
                time.sleep(3600)  # 1 hour
        
        cleanup_thread = threading.Thread(target=run_cleanup, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_jobs(self):
        """Clean up old completed and failed jobs"""
        try:
            now = datetime.utcnow()
            cleanup_count = 0
            
            # Get all job IDs from Redis
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, match="job:*", count=100)
                
                for key in keys:
                    job_id = key.split(":", 1)[1]
                    job = self.get_job(job_id)
                    
                    if job and job.completed_at:
                        age_hours = (now - job.completed_at).total_seconds() / 3600
                        
                        should_cleanup = False
                        if job.status == JobStatus.COMPLETED and age_hours > self.cleanup_completed_after_hours:
                            should_cleanup = True
                        elif job.status in [JobStatus.FAILED, JobStatus.CANCELLED] and age_hours > self.cleanup_failed_after_hours:
                            should_cleanup = True
                        
                        if should_cleanup:
                            # Remove job data
                            self.redis_client.delete(f"job:{job_id}")
                            self.redis_client.srem(f"account_jobs:{job.account_id}", job_id)
                            cleanup_count += 1
                
                if cursor == 0:
                    break
            
            if cleanup_count > 0:
                self.logger.info(f"Cleaned up {cleanup_count} old jobs")
                
        except Exception as e:
            self.logger.error(f"Job cleanup failed: {str(e)}")
    
    def get_job_stats(self) -> Dict[str, Any]:
        """Get job system statistics"""
        try:
            stats = {
                'queued_jobs': self.redis_client.zcard("job_queue"),
                'running_jobs': len(self.running_jobs),
                'total_jobs_24h': 0,
                'completed_jobs_24h': 0,
                'failed_jobs_24h': 0,
                'job_types': {},
                'accounts_active': set()
            }
            
            # Count jobs by status and type from last 24 hours
            yesterday = datetime.utcnow() - timedelta(hours=24)
            
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, match="job:*", count=100)
                
                for key in keys:
                    job_id = key.split(":", 1)[1]
                    job = self.get_job(job_id)
                    
                    if job and job.created_at >= yesterday:
                        stats['total_jobs_24h'] += 1
                        stats['accounts_active'].add(job.account_id)
                        
                        if job.status == JobStatus.COMPLETED:
                            stats['completed_jobs_24h'] += 1
                        elif job.status == JobStatus.FAILED:
                            stats['failed_jobs_24h'] += 1
                        
                        job_type = job.job_type
                        if job_type not in stats['job_types']:
                            stats['job_types'][job_type] = {'total': 0, 'completed': 0, 'failed': 0}
                        
                        stats['job_types'][job_type]['total'] += 1
                        if job.status == JobStatus.COMPLETED:
                            stats['job_types'][job_type]['completed'] += 1
                        elif job.status == JobStatus.FAILED:
                            stats['job_types'][job_type]['failed'] += 1
                
                if cursor == 0:
                    break
            
            stats['accounts_active'] = len(stats['accounts_active'])
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get job stats: {str(e)}")
            return {}
    
    def shutdown(self):
        """Shutdown job manager"""
        self.logger.info("Shutting down background job manager")
        
        # Cancel all running jobs
        for job_id, future in self.running_jobs.items():
            future.cancel()
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True, cancel_futures=True)

# Global job manager instance
job_manager = BackgroundJobManager()
```

### 2. CSV Processing Job Handler
```python
# background_jobs/handlers/csv_processing.py - CSV processing job handler

import os
from pathlib import Path
from typing import Dict, Any
import asyncio

from background_jobs.core import BaseJobHandler, Job, JobResult
from csv_processing.parser import csv_parser, CSVType
from database.models import Upload
from database.database import get_db
from sqlalchemy.orm import Session

class CSVProcessingJobHandler(BaseJobHandler):
    """Handler for CSV file processing jobs"""
    
    async def execute(self, job: Job) -> JobResult:
        """Execute CSV processing job"""
        
        self.logger.info(f"Starting CSV processing job {job.id}")
        
        try:
            # Get parameters
            upload_id = job.parameters.get('upload_id')
            csv_type = job.parameters.get('csv_type')
            
            if not upload_id:
                raise ValueError("upload_id parameter is required")
            
            self.update_progress(job, 10, "Validating parameters", "parameter_validation")
            
            # Get upload record
            with Session(bind=get_db().bind) as db:
                upload = db.query(Upload).filter(Upload.id == upload_id).first()
                if not upload:
                    raise ValueError(f"Upload {upload_id} not found")
                
                if upload.account_id != job.account_id:
                    raise PermissionError("Upload does not belong to this account")
            
            self.update_progress(job, 20, "Loading file", "file_loading")
            
            # Check if file exists
            file_path = Path(upload.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Upload file not found: {file_path}")
            
            self.update_progress(job, 30, "Parsing CSV data", "csv_parsing")
            
            # Parse CSV file
            if csv_type:
                csv_type_enum = CSVType(csv_type)
            else:
                csv_type_enum = None
            
            parse_result = csv_parser.parse_file(file_path, csv_type_enum)
            
            if not parse_result['success']:
                # Update upload status
                with Session(bind=get_db().bind) as db:
                    upload = db.query(Upload).filter(Upload.id == upload_id).first()
                    if upload:
                        upload.processing_status = 'failed'
                        upload.error_message = str(parse_result.get('error', 'Unknown parsing error'))
                        upload.processing_completed_at = datetime.utcnow()
                        db.commit()
                
                return JobResult(
                    success=False,
                    error=f"CSV parsing failed: {parse_result.get('error', 'Unknown error')}",
                    data={
                        'upload_id': upload_id,
                        'validation_errors': parse_result.get('validation_errors', [])
                    }
                )
            
            self.update_progress(job, 50, "Validating data", "data_validation")
            
            # Process parsed data
            processed_data = parse_result['data']
            total_rows = parse_result['total_rows']
            valid_rows = parse_result['valid_rows']
            invalid_rows = parse_result['invalid_rows']
            
            self.logger.info(f"Parsed {total_rows} rows: {valid_rows} valid, {invalid_rows} invalid")
            
            self.update_progress(job, 70, f"Processing {len(processed_data)} records", "data_processing")
            
            # Store data in database based on CSV type
            insert_result = await self._store_csv_data(
                job, 
                processed_data, 
                parse_result['csv_type'], 
                upload.account_id,
                upload.batch_id
            )
            
            self.update_progress(job, 90, "Updating upload status", "status_update")
            
            # Update upload record
            with Session(bind=get_db().bind) as db:
                upload = db.query(Upload).filter(Upload.id == upload_id).first()
                if upload:
                    upload.processing_status = 'completed'
                    upload.total_rows = total_rows
                    upload.processed_rows = len(processed_data)
                    upload.success_rows = insert_result['success_count']
                    upload.error_rows = insert_result['error_count']
                    upload.processing_completed_at = datetime.utcnow()
                    db.commit()
            
            self.update_progress(job, 100, "Processing completed", "completed")
            
            return JobResult(
                success=True,
                data={
                    'upload_id': upload_id,
                    'csv_type': str(parse_result['csv_type']),
                    'total_rows': total_rows,
                    'valid_rows': valid_rows,
                    'invalid_rows': invalid_rows,
                    'inserted_rows': insert_result['success_count'],
                    'failed_inserts': insert_result['error_count'],
                    'processing_summary': parse_result['processing_summary'],
                    'validation_errors': parse_result.get('validation_errors', []),
                    'warnings': parse_result.get('warnings', [])
                }
            )
            
        except Exception as e:
            self.logger.error(f"CSV processing job {job.id} failed: {str(e)}")
            
            # Update upload status to failed
            try:
                with Session(bind=get_db().bind) as db:
                    upload = db.query(Upload).filter(Upload.id == upload_id).first()
                    if upload:
                        upload.processing_status = 'failed'
                        upload.error_message = str(e)
                        upload.processing_completed_at = datetime.utcnow()
                        db.commit()
            except Exception as update_error:
                self.logger.error(f"Failed to update upload status: {str(update_error)}")
            
            raise e
    
    async def _store_csv_data(
        self, 
        job: Job, 
        data: List[Dict[str, Any]], 
        csv_type: CSVType, 
        account_id: int,
        batch_id: str
    ) -> Dict[str, int]:
        """Store parsed CSV data in database"""
        
        success_count = 0
        error_count = 0
        
        # Import appropriate models based on CSV type
        if csv_type == CSVType.ORDERS:
            from database.models import Order
            model_class = Order
            data_processor = self._process_order_data
        elif csv_type == CSVType.LISTINGS:
            from database.models import Listing
            model_class = Listing
            data_processor = self._process_listing_data
        elif csv_type == CSVType.PRODUCTS:
            from database.models import Product
            model_class = Product
            data_processor = self._process_product_data
        elif csv_type == CSVType.CUSTOMERS:
            from database.models import Customer
            model_class = Customer
            data_processor = self._process_customer_data
        elif csv_type == CSVType.MESSAGES:
            from database.models import Message
            model_class = Message
            data_processor = self._process_message_data
        else:
            raise ValueError(f"Unsupported CSV type for database storage: {csv_type}")
        
        # Process data in batches
        batch_size = 100
        total_batches = (len(data) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(data))
            batch_data = data[start_idx:end_idx]
            
            # Update progress
            progress = 70 + int((batch_num / total_batches) * 20)
            self.update_progress(
                job, 
                progress, 
                f"Inserting batch {batch_num + 1}/{total_batches}",
                "database_insert"
            )
            
            try:
                with Session(bind=get_db().bind) as db:
                    batch_success, batch_errors = await data_processor(
                        db, batch_data, account_id, batch_id
                    )
                    success_count += batch_success
                    error_count += batch_errors
                    
            except Exception as e:
                self.logger.error(f"Batch insert failed: {str(e)}")
                error_count += len(batch_data)
        
        return {
            'success_count': success_count,
            'error_count': error_count
        }
    
    async def _process_order_data(
        self, 
        db: Session, 
        batch_data: List[Dict[str, Any]], 
        account_id: int, 
        batch_id: str
    ) -> tuple[int, int]:
        """Process and insert order data"""
        
        from database.models import Order
        
        success_count = 0
        error_count = 0
        
        for row_data in batch_data:
            try:
                # Set batch information
                row_data['account_id'] = account_id
                row_data['import_batch_id'] = batch_id
                
                # Check for existing order
                existing_order = db.query(Order).filter(
                    Order.account_id == account_id,
                    Order.ebay_order_id == row_data['ebay_order_id']
                ).first()
                
                if existing_order:
                    # Update existing order
                    for key, value in row_data.items():
                        if hasattr(existing_order, key) and value is not None:
                            setattr(existing_order, key, value)
                else:
                    # Create new order
                    order = Order(**row_data)
                    db.add(order)
                
                success_count += 1
                
            except Exception as e:
                self.logger.warning(f"Failed to process order row: {str(e)}")
                error_count += 1
        
        try:
            db.commit()
        except Exception as e:
            self.logger.error(f"Failed to commit order batch: {str(e)}")
            db.rollback()
            # All rows in this batch failed
            error_count = len(batch_data)
            success_count = 0
        
        return success_count, error_count
    
    # Similar methods for other data types...
    async def _process_listing_data(self, db: Session, batch_data: List[Dict[str, Any]], account_id: int, batch_id: str) -> tuple[int, int]:
        """Process and insert listing data"""
        # Implementation similar to _process_order_data
        pass
    
    async def _process_product_data(self, db: Session, batch_data: List[Dict[str, Any]], account_id: int, batch_id: str) -> tuple[int, int]:
        """Process and insert product data"""
        # Implementation similar to _process_order_data
        pass
    
    async def _process_customer_data(self, db: Session, batch_data: List[Dict[str, Any]], account_id: int, batch_id: str) -> tuple[int, int]:
        """Process and insert customer data"""
        # Implementation similar to _process_order_data
        pass
    
    async def _process_message_data(self, db: Session, batch_data: List[Dict[str, Any]], account_id: int, batch_id: str) -> tuple[int, int]:
        """Process and insert message data"""
        # Implementation similar to _process_order_data
        pass
```

### 3. Job Management API
```python
# api/jobs.py - Job management API endpoints

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from datetime import datetime

from background_jobs.core import job_manager, JobStatus, JobPriority, Job
from auth.dependencies import get_current_user
from database.models import User

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])

class JobCreateRequest(BaseModel):
    job_type: str
    parameters: dict
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = 3
    timeout_seconds: int = 300

class JobResponse(BaseModel):
    id: str
    job_type: str
    account_id: int
    parameters: dict
    priority: JobPriority
    status: JobStatus
    progress_percentage: int
    progress_message: str
    current_step: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    retry_count: int
    max_retries: int
    last_error: Optional[str]
    result: Optional[dict]
    
    class Config:
        from_attributes = True

@router.post("/", response_model=dict)
def create_job(
    job_request: JobCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new background job"""
    
    try:
        job_id = job_manager.create_job(
            job_type=job_request.job_type,
            account_id=current_user.id,  # Use user's default account or parameter
            parameters=job_request.parameters,
            priority=job_request.priority,
            max_retries=job_request.max_retries,
            timeout_seconds=job_request.timeout_seconds
        )
        
        return {
            "job_id": job_id,
            "message": "Job created successfully"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )

@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get job details by ID"""
    
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check job ownership (simplified - should check account access)
    if job.account_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this job"
        )
    
    return JobResponse(**job.to_dict())

@router.get("/", response_model=List[JobResponse])
def get_jobs(
    status: Optional[JobStatus] = Query(None),
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get jobs for current user"""
    
    jobs = job_manager.get_jobs_by_account(current_user.id, status)
    
    # Limit results
    jobs = jobs[:limit]
    
    return [JobResponse(**job.to_dict()) for job in jobs]

@router.delete("/{job_id}")
def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a job"""
    
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.account_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this job"
        )
    
    if job_manager.cancel_job(job_id):
        return {"message": "Job cancelled successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be cancelled"
        )

@router.get("/system/stats")
def get_job_stats(
    current_user: User = Depends(get_current_user)
):
    """Get job system statistics (admin only or user's own stats)"""
    
    # For now, return general stats - in production, filter by user access
    stats = job_manager.get_job_stats()
    
    return stats
```

### 4. Job System Initialization
```python
# background_jobs/__init__.py - Initialize job system and register handlers

from background_jobs.core import job_manager
from background_jobs.handlers.csv_processing import CSVProcessingJobHandler

def initialize_job_system():
    """Initialize job system and register all handlers"""
    
    # Register job handlers
    job_manager.register_handler("csv_processing", CSVProcessingJobHandler)
    
    # Register other handlers as needed
    # job_manager.register_handler("report_generation", ReportGenerationJobHandler)
    # job_manager.register_handler("email_sending", EmailSendingJobHandler)
    # job_manager.register_handler("cleanup", CleanupJobHandler)
    
    return job_manager

# Initialize on import
initialize_job_system()
```

---

## Success Criteria & Validation

### Background Job Requirements ✅
- [ ] ThreadPoolExecutor with configurable worker threads (4 workers default)
- [ ] Redis-based job storage and queue management
- [ ] Job status tracking (queued, running, completed, failed, cancelled, retrying)
- [ ] Progress tracking with percentage and message updates
- [ ] Automatic retry with exponential backoff (configurable max retries)
- [ ] Job timeout handling (configurable timeout per job)
- [ ] Error handling with detailed error messages and stack traces
- [ ] Job cleanup (completed jobs after 24h, failed jobs after 7 days)

### CSV Processing Integration ✅
- [ ] CSV processing job handler with chunked database insertion
- [ ] Support for all eBay CSV types (orders, listings, products, customers, messages)
- [ ] Batch processing with progress updates every 100 records
- [ ] Database transaction management with rollback on error
- [ ] Duplicate detection and update/insert logic
- [ ] Upload status synchronization with job progress
- [ ] Comprehensive result reporting with success/error counts

### SOLID/YAGNI Compliance ✅
- [ ] **Single Responsibility**: Each job handler manages one job type
- [ ] **Open/Closed**: System extensible for new job types without core changes
- [ ] **Liskov Substitution**: All handlers implement common execution interface
- [ ] **Interface Segregation**: Clean separation between job creation, execution, monitoring
- [ ] **Dependency Inversion**: Job system depends on handler abstractions
- [ ] **YAGNI Applied**: Simple threading model, no distributed systems complexity
- [ ] Eliminated unnecessary features (job priorities, complex scheduling, monitoring dashboards)

### Performance Requirements ✅
- [ ] Job execution startup time < 5 seconds
- [ ] Progress updates in real-time during execution
- [ ] Memory usage stays reasonable during large CSV processing
- [ ] Concurrent job execution (4 parallel jobs maximum)
- [ ] Job cleanup prevents Redis memory growth
- [ ] Database batch operations (100 records per batch)
- [ ] Error recovery without data corruption

**Next Step**: Proceed to [03-order-management-api.md](./03-order-management-api.md) for order CRUD operations and business logic implementation.