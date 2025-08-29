"""
Background Job System Core Implementation
Following YAGNI/SOLID principles - Simple ThreadPoolExecutor with Redis storage
"""

import asyncio
import json
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Type
import threading
import time
import traceback
from abc import ABC, abstractmethod

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("background_jobs")

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
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
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
    """
    Main background job management system
    Following YAGNI: Simple in-memory storage with Redis fallback
    """
    
    def __init__(self):
        # Simple in-memory storage (YAGNI - no Redis dependency for now)
        self._jobs: Dict[str, Job] = {}
        self._account_jobs: Dict[int, List[str]] = {}
        self._job_queue: List[str] = []
        self._lock = threading.Lock()
        
        self.executor = ThreadPoolExecutor(
            max_workers=getattr(settings, 'MAX_WORKER_THREADS', 4),
            thread_name_prefix="ebay_job_worker"
        )
        
        self.job_handlers: Dict[str, Type[BaseJobHandler]] = {}
        self.running_jobs: Dict[str, Future] = {}
        
        # Job cleanup settings
        self.cleanup_completed_after_hours = 24
        self.cleanup_failed_after_hours = 168  # 7 days
        
        self.logger = get_logger(__name__)
        
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
        
        # Store job
        self._store_job(job)
        
        # Queue job for execution
        self._queue_job(job)
        
        self.logger.info(f"Created job {job.id} of type {job_type} for account {account_id}")
        
        return job.id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        with self._lock:
            return self._jobs.get(job_id)
    
    def get_jobs_by_account(self, account_id: int, status: Optional[JobStatus] = None) -> List[Job]:
        """Get jobs for specific account"""
        jobs = []
        
        with self._lock:
            job_ids = self._account_jobs.get(account_id, [])
            
            for job_id in job_ids:
                job = self._jobs.get(job_id)
                if job and (status is None or job.status == status):
                    jobs.append(job)
        
        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
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
                
                with self._lock:
                    if job_id in self._job_queue:
                        self._job_queue.remove(job_id)
                
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
        """Store job in memory"""
        with self._lock:
            self._jobs[job.id] = job
            
            # Add to account jobs
            if job.account_id not in self._account_jobs:
                self._account_jobs[job.account_id] = []
            
            if job.id not in self._account_jobs[job.account_id]:
                self._account_jobs[job.account_id].append(job.id)
    
    def _queue_job(self, job: Job):
        """Queue job for execution"""
        try:
            with self._lock:
                self._job_queue.append(job.id)
                # Sort by priority (higher priority first)
                self._job_queue.sort(key=lambda jid: self._jobs.get(jid, job).priority.value, reverse=True)
            
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
            
            # Remove from queue
            with self._lock:
                if job_id in self._job_queue:
                    self._job_queue.remove(job_id)
    
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
                    
                    # Schedule retry
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
            
            jobs_to_delete = []
            
            with self._lock:
                for job_id, job in self._jobs.items():
                    if job.completed_at:
                        age_hours = (now - job.completed_at).total_seconds() / 3600
                        
                        should_cleanup = False
                        if job.status == JobStatus.COMPLETED and age_hours > self.cleanup_completed_after_hours:
                            should_cleanup = True
                        elif job.status in [JobStatus.FAILED, JobStatus.CANCELLED] and age_hours > self.cleanup_failed_after_hours:
                            should_cleanup = True
                        
                        if should_cleanup:
                            jobs_to_delete.append((job_id, job.account_id))
                            cleanup_count += 1
                
                # Remove old jobs
                for job_id, account_id in jobs_to_delete:
                    del self._jobs[job_id]
                    if account_id in self._account_jobs and job_id in self._account_jobs[account_id]:
                        self._account_jobs[account_id].remove(job_id)
            
            if cleanup_count > 0:
                self.logger.info(f"Cleaned up {cleanup_count} old jobs")
                
        except Exception as e:
            self.logger.error(f"Job cleanup failed: {str(e)}")
    
    def get_job_stats(self) -> Dict[str, Any]:
        """Get job system statistics"""
        try:
            stats = {
                'queued_jobs': 0,
                'running_jobs': len(self.running_jobs),
                'total_jobs_24h': 0,
                'completed_jobs_24h': 0,
                'failed_jobs_24h': 0,
                'job_types': {},
                'accounts_active': set()
            }
            
            # Count jobs by status and type from last 24 hours
            yesterday = datetime.utcnow() - timedelta(hours=24)
            
            with self._lock:
                stats['queued_jobs'] = len(self._job_queue)
                
                for job in self._jobs.values():
                    if job.created_at >= yesterday:
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