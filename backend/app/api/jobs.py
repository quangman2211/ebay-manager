"""
Job Management API Endpoints
Following SOLID principles - Single Responsibility for job management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.background_jobs.core import job_manager, JobStatus, JobPriority, Job
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger("jobs_api")
router = APIRouter(prefix="/jobs", tags=["Background Jobs"])

class JobCreateRequest(BaseModel):
    """Job creation request schema"""
    job_type: str = Field(..., min_length=1, max_length=50)
    parameters: dict = Field(...)
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = Field(3, ge=0, le=10)
    timeout_seconds: int = Field(300, ge=30, le=3600)

class JobResponse(BaseModel):
    """Job response schema"""
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
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class JobStatsResponse(BaseModel):
    """Job statistics response schema"""
    queued_jobs: int
    running_jobs: int
    total_jobs_24h: int
    completed_jobs_24h: int
    failed_jobs_24h: int
    job_types: dict
    accounts_active: int

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_request: JobCreateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new background job
    Following SOLID: Single Responsibility for job creation
    """
    
    try:
        # Use first account ID or user ID (simplified for now)
        account_id = current_user.id  # This should be refined to use actual account
        
        job_id = job_manager.create_job(
            job_type=job_request.job_type,
            account_id=account_id,
            parameters=job_request.parameters,
            priority=job_request.priority,
            max_retries=job_request.max_retries,
            timeout_seconds=job_request.timeout_seconds
        )
        
        logger.info(f"Created job {job_id} of type {job_request.job_type} for user {current_user.id}")
        
        return {
            "job_id": job_id,
            "message": "Job created successfully"
        }
        
    except ValueError as e:
        logger.error(f"Job creation validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Job creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get job details by ID
    Following SOLID: Single Responsibility for job retrieval
    """
    
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check job ownership (admin can see all, user can see only their jobs)
    if current_user.role != 'admin' and job.account_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this job"
        )
    
    job_dict = job.to_dict()
    return JobResponse(**job_dict)

@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs to return"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get jobs for current user
    Following SOLID: Single Responsibility for job listing
    """
    
    try:
        # For admin users, we could potentially show all jobs
        # For now, show jobs for the user's account
        account_id = current_user.id
        
        jobs = job_manager.get_jobs_by_account(account_id, status)
        
        # Limit results
        jobs = jobs[:limit]
        
        logger.info(f"Listed {len(jobs)} jobs for user {current_user.id}")
        
        job_responses = []
        for job in jobs:
            job_dict = job.to_dict()
            job_responses.append(JobResponse(**job_dict))
        
        return job_responses
        
    except Exception as e:
        logger.error(f"Failed to list jobs for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )

@router.delete("/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Cancel a job
    Following SOLID: Single Responsibility for job cancellation
    """
    
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check job ownership
    if current_user.role != 'admin' and job.account_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this job"
        )
    
    if job_manager.cancel_job(job_id):
        logger.info(f"Job {job_id} cancelled by user {current_user.id}")
        return {"message": "Job cancelled successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be cancelled"
        )

@router.get("/system/stats", response_model=JobStatsResponse)
async def get_job_stats(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get job system statistics
    Following SOLID: Single Responsibility for statistics
    """
    
    try:
        stats = job_manager.get_job_stats()
        
        logger.info(f"Job stats requested by user {current_user.id}")
        
        return JobStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get job stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job statistics: {str(e)}"
        )

@router.get("/health/check")
async def jobs_health_check():
    """
    Job system health check
    Following SOLID: Single Responsibility for health monitoring
    """
    try:
        stats = job_manager.get_job_stats()
        
        return {
            "status": "healthy",
            "queued_jobs": stats.get("queued_jobs", 0),
            "running_jobs": stats.get("running_jobs", 0),
            "registered_handlers": len(job_manager.job_handlers),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Job system health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }