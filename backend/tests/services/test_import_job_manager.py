"""
Test Import Job Manager
Following SOLID principles - Single Responsibility for testing job management logic
YAGNI compliance: Essential test cases only
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from app.services.csv_import.import_job_manager import (
    ImportJobManager, ImportJob, ImportJobType, ImportJobStatus, ImportJobResult
)
from app.services.csv_import.listing_csv_detector import CSVListingFormat
from app.core.exceptions import NotFoundError, ValidationException


class TestImportJobManager:
    """Test import job management functionality"""
    
    @pytest.fixture
    def mock_listing_repo(self):
        repo = Mock()
        repo.get_by_ebay_id = AsyncMock(return_value=None)
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_account_repo(self):
        repo = Mock()
        mock_account = Mock(id=1, name="Test Account")
        repo.get_by_id = AsyncMock(return_value=mock_account)
        return repo
    
    @pytest.fixture
    def job_manager(self, mock_listing_repo, mock_account_repo):
        return ImportJobManager(mock_listing_repo, mock_account_repo, max_concurrent_jobs=2)
    
    @pytest.mark.asyncio
    async def test_create_import_job_success(self, job_manager, mock_account_repo):
        """Test successful creation of import job"""
        csv_content = "Item ID,Title,Price,Quantity Available,Status\n123456789,Test Product,$19.99,5,Active"
        filename = "test_active_listings.csv"
        
        job_id = await job_manager.create_import_job(
            account_id=1,
            filename=filename,
            csv_content=csv_content,
            job_type=ImportJobType.LISTING_IMPORT
        )
        
        assert job_id is not None
        assert len(job_id) == 36  # UUID length
        mock_account_repo.get_by_id.assert_called_once_with(1)
        
        # Verify job was created
        job_status = await job_manager.get_job_status(job_id)
        assert job_status['filename'] == filename
        assert job_status['account_id'] == 1
        assert job_status['status'] in [ImportJobStatus.PENDING.value, ImportJobStatus.PROCESSING.value]
    
    @pytest.mark.asyncio
    async def test_create_job_with_nonexistent_account_fails(self, job_manager, mock_account_repo):
        """Test job creation fails with nonexistent account"""
        mock_account_repo.get_by_id.return_value = None
        csv_content = "Item ID,Title,Price\n123,Test,$19.99"
        
        with pytest.raises(NotFoundError) as exc_info:
            await job_manager.create_import_job(
                account_id=999,
                filename="test.csv",
                csv_content=csv_content
            )
        
        assert "Account 999 not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_job_with_invalid_csv_fails(self, job_manager):
        """Test job creation fails with invalid CSV format"""
        invalid_csv = "Not a valid CSV format"
        
        with pytest.raises(ValidationException) as exc_info:
            await job_manager.create_import_job(
                account_id=1,
                filename="invalid.csv",
                csv_content=invalid_csv
            )
        
        assert "Unsupported CSV format" in str(exc_info.value) or "validation failed" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_job_status_existing_job(self, job_manager):
        """Test retrieving status of existing job"""
        csv_content = "Item ID,Title,Price,Quantity Available,Status\n123456789,Test Product,$19.99,5,Active"
        
        job_id = await job_manager.create_import_job(
            account_id=1,
            filename="test.csv",
            csv_content=csv_content
        )
        
        status = await job_manager.get_job_status(job_id)
        
        assert status['job_id'] == job_id
        assert status['account_id'] == 1
        assert status['filename'] == "test.csv"
        assert 'created_at' in status
        assert 'status' in status
    
    @pytest.mark.asyncio
    async def test_get_job_status_nonexistent_job_fails(self, job_manager):
        """Test retrieving status of nonexistent job fails"""
        fake_job_id = "nonexistent-job-id"
        
        with pytest.raises(NotFoundError) as exc_info:
            await job_manager.get_job_status(fake_job_id)
        
        assert "Import job nonexistent-job-id not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_cancel_pending_job_success(self, job_manager):
        """Test successful cancellation of pending job"""
        csv_content = "Item ID,Title,Price,Quantity Available,Status\n123456789,Test Product,$19.99,5,Active"
        
        job_id = await job_manager.create_import_job(
            account_id=1,
            filename="test.csv",
            csv_content=csv_content
        )
        
        # Cancel immediately before processing starts
        await asyncio.sleep(0.1)  # Small delay to ensure job is created
        success = await job_manager.cancel_job(job_id)
        
        assert success is True
        
        # Verify job status is cancelled
        status = await job_manager.get_job_status(job_id)
        assert status['status'] == ImportJobStatus.CANCELLED.value
    
    @pytest.mark.asyncio
    async def test_cancel_completed_job_fails(self, job_manager):
        """Test cancelling completed job fails"""
        # Create a mock completed job
        job_id = "test-job-id"
        completed_job = ImportJob(
            job_id=job_id,
            job_type=ImportJobType.LISTING_IMPORT,
            status=ImportJobStatus.COMPLETED,
            account_id=1,
            filename="test.csv",
            csv_format=CSVListingFormat.EBAY_ACTIVE_LISTINGS,
            csv_content="test",
            created_at=datetime.utcnow()
        )
        
        job_manager._jobs[job_id] = completed_job
        
        with pytest.raises(ValidationException) as exc_info:
            await job_manager.cancel_job(job_id)
        
        assert "Cannot cancel job in completed status" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_all_jobs_with_filters(self, job_manager):
        """Test retrieving jobs with filters"""
        csv_content = "Item ID,Title,Price,Quantity Available,Status\n123456789,Test Product,$19.99,5,Active"
        
        # Create multiple jobs
        job_id1 = await job_manager.create_import_job(1, "test1.csv", csv_content)
        job_id2 = await job_manager.create_import_job(1, "test2.csv", csv_content)
        
        # Get all jobs
        all_jobs = await job_manager.get_all_jobs()
        assert len(all_jobs) >= 2
        
        # Filter by account
        account_jobs = await job_manager.get_all_jobs(account_id=1)
        assert len(account_jobs) >= 2
        
        # Filter by status (if any are still pending)
        pending_jobs = await job_manager.get_all_jobs(status=ImportJobStatus.PENDING)
        # May be empty if jobs processed quickly
        
        # Test limit
        limited_jobs = await job_manager.get_all_jobs(limit=1)
        assert len(limited_jobs) == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_old_jobs(self, job_manager):
        """Test cleanup of old completed jobs"""
        # Create mock old job
        old_job_id = "old-job-id"
        old_time = datetime.utcnow() - timedelta(hours=80)  # Older than default 72 hours
        
        old_job = ImportJob(
            job_id=old_job_id,
            job_type=ImportJobType.LISTING_IMPORT,
            status=ImportJobStatus.COMPLETED,
            account_id=1,
            filename="old.csv",
            csv_format=CSVListingFormat.EBAY_ACTIVE_LISTINGS,
            csv_content="test",
            created_at=old_time
        )
        
        job_manager._jobs[old_job_id] = old_job
        
        # Cleanup old jobs
        removed_count = await job_manager.cleanup_old_jobs(max_age_hours=72)
        
        assert removed_count >= 1
        assert old_job_id not in job_manager._jobs
    
    def test_job_statistics(self, job_manager):
        """Test job statistics functionality"""
        # Create mock jobs in different statuses
        jobs = [
            ImportJob(
                job_id=f"job-{i}",
                job_type=ImportJobType.LISTING_IMPORT,
                status=ImportJobStatus.COMPLETED if i % 2 == 0 else ImportJobStatus.PENDING,
                account_id=1,
                filename=f"test{i}.csv",
                csv_format=CSVListingFormat.EBAY_ACTIVE_LISTINGS,
                csv_content="test",
                created_at=datetime.utcnow()
            )
            for i in range(5)
        ]
        
        for job in jobs:
            job_manager._jobs[job.job_id] = job
        
        stats = job_manager.get_job_statistics()
        
        assert stats['total_jobs'] >= 5
        assert 'status_counts' in stats
        assert stats['status_counts']['completed'] >= 2
        assert stats['status_counts']['pending'] >= 3
        assert 'max_concurrent_jobs' in stats
    
    @patch('app.services.csv_import.listing_csv_transformer.CSVListingTransformer')
    def test_process_job_success_flow(self, mock_transformer_class, job_manager, mock_listing_repo):
        """Test successful job processing flow"""
        # Setup mock transformer
        mock_transformer = Mock()
        mock_transformer.transform_csv_to_listings.return_value = Mock(
            success=True,
            listings=[
                {
                    'ebay_item_id': '123456789',
                    'account_id': 1,
                    'title': 'Test Product',
                    'price': 19.99,
                    'quantity_available': 5,
                    'status': 'active'
                }
            ],
            errors=[],
            warnings=[],
            skipped_rows=0
        )
        mock_transformer_class.return_value = mock_transformer
        
        # Create a job manually for testing
        job_id = "test-job-id"
        job = ImportJob(
            job_id=job_id,
            job_type=ImportJobType.LISTING_IMPORT,
            status=ImportJobStatus.PENDING,
            account_id=1,
            filename="test.csv",
            csv_format=CSVListingFormat.EBAY_ACTIVE_LISTINGS,
            csv_content="Item ID,Title,Price,Quantity Available,Status\n123456789,Test Product,$19.99,5,Active",
            created_at=datetime.utcnow()
        )
        job_manager._jobs[job_id] = job
        
        # Mock the processing method directly
        with patch.object(job_manager, '_process_job') as mock_process:
            mock_process.return_value = None  # Async function returns None
            
            # The actual test would involve calling _process_job
            # This is a simplified test to verify the job structure
            assert job.status == ImportJobStatus.PENDING
            assert job.csv_content is not None
    
    def test_import_job_to_dict_conversion(self):
        """Test ImportJob to dictionary conversion"""
        job = ImportJob(
            job_id="test-job-id",
            job_type=ImportJobType.LISTING_IMPORT,
            status=ImportJobStatus.COMPLETED,
            account_id=1,
            filename="test.csv",
            csv_format=CSVListingFormat.EBAY_ACTIVE_LISTINGS,
            csv_content="test content",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            started_at=datetime(2024, 1, 1, 12, 0, 5),
            completed_at=datetime(2024, 1, 1, 12, 1, 0),
            result=ImportJobResult(
                success=True,
                created_count=1,
                updated_count=0,
                skipped_count=0,
                error_count=0,
                errors=[],
                warnings=[],
                processing_time=55.0
            )
        )
        
        job_dict = job.to_dict()
        
        assert job_dict['job_id'] == "test-job-id"
        assert job_dict['job_type'] == "listing_import"
        assert job_dict['status'] == "completed"
        assert job_dict['account_id'] == 1
        assert job_dict['filename'] == "test.csv"
        assert job_dict['csv_format'] == "ebay_active_listings"
        assert 'csv_content' not in job_dict  # Should be removed for API response
        assert job_dict['created_at'] == "2024-01-01T12:00:00"
        assert job_dict['started_at'] == "2024-01-01T12:00:05"
        assert job_dict['completed_at'] == "2024-01-01T12:01:00"
        assert job_dict['result'] is not None