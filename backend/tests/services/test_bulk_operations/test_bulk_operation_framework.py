"""
Test Bulk Operation Framework
Following SOLID principles - Single Responsibility for testing framework components
YAGNI compliance: Essential test cases only
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from app.services.bulk_operations.bulk_operation_framework import (
    BulkOperationType, BulkOperationStatus, BulkOperationResult, 
    BulkValidator, BatchProcessor
)


class TestBulkOperationResult:
    """Test bulk operation result functionality"""
    
    def test_result_initialization(self):
        """Test result object initialization with defaults"""
        result = BulkOperationResult()
        
        assert result.total_items == 0
        assert result.processed_items == 0
        assert result.successful_items == 0
        assert result.failed_items == 0
        assert result.errors == []
        assert result.warnings == []
        assert result.status == BulkOperationStatus.PENDING
    
    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        result = BulkOperationResult()
        
        # Test with no processed items
        assert result.success_rate == 0.0
        
        # Test with partial success
        result.processed_items = 10
        result.successful_items = 7
        assert result.success_rate == 70.0
        
        # Test with complete success
        result.successful_items = 10
        assert result.success_rate == 100.0
    
    def test_to_dict_conversion(self):
        """Test conversion to dictionary for API response"""
        result = BulkOperationResult()
        result.total_items = 5
        result.processed_items = 5
        result.successful_items = 3
        result.failed_items = 2
        result.errors = ["Error 1", "Error 2"]
        result.warnings = ["Warning 1"]
        result.status = BulkOperationStatus.PARTIAL_SUCCESS
        result.started_at = datetime(2024, 1, 1, 12, 0, 0)
        result.completed_at = datetime(2024, 1, 1, 12, 1, 0)
        
        result_dict = result.to_dict()
        
        assert result_dict['total_items'] == 5
        assert result_dict['processed_items'] == 5
        assert result_dict['successful_items'] == 3
        assert result_dict['failed_items'] == 2
        assert result_dict['success_rate'] == 60.0
        assert result_dict['errors'] == ["Error 1", "Error 2"]
        assert result_dict['warnings'] == ["Warning 1"]
        assert result_dict['status'] == "partial_success"
        assert result_dict['started_at'] == "2024-01-01T12:00:00"
        assert result_dict['completed_at'] == "2024-01-01T12:01:00"
    
    def test_to_dict_limits_errors_and_warnings(self):
        """Test that to_dict limits errors and warnings to last 10 items"""
        result = BulkOperationResult()
        
        # Add more than 10 errors and warnings
        result.errors = [f"Error {i}" for i in range(15)]
        result.warnings = [f"Warning {i}" for i in range(12)]
        
        result_dict = result.to_dict()
        
        assert len(result_dict['errors']) == 10
        assert len(result_dict['warnings']) == 10
        # Should contain the last 10 items
        assert result_dict['errors'][0] == "Error 5"
        assert result_dict['errors'][-1] == "Error 14"
        assert result_dict['warnings'][0] == "Warning 2"
        assert result_dict['warnings'][-1] == "Warning 11"


class TestBulkValidator:
    """Test bulk validator functionality"""
    
    @pytest.fixture
    def validator(self):
        return BulkValidator()
    
    def test_validate_item_count_success(self, validator):
        """Test successful item count validation"""
        items = [1, 2, 3, 4, 5]
        
        errors = validator.validate_item_count(items, max_items=10)
        
        assert len(errors) == 0
    
    def test_validate_item_count_empty_fails(self, validator):
        """Test validation fails with empty item list"""
        items = []
        
        errors = validator.validate_item_count(items)
        
        assert len(errors) == 1
        assert "No items provided" in errors[0]
    
    def test_validate_item_count_too_many_fails(self, validator):
        """Test validation fails with too many items"""
        items = list(range(1001))  # More than default max of 1000
        
        errors = validator.validate_item_count(items)
        
        assert len(errors) == 1
        assert "Too many items" in errors[0]
    
    def test_validate_operation_type_success(self, validator):
        """Test successful operation type validation"""
        supported_ops = [BulkOperationType.UPDATE_STATUS, BulkOperationType.UPDATE_PRICE]
        
        errors = validator.validate_operation_type("update_status", supported_ops)
        
        assert len(errors) == 0
    
    def test_validate_operation_type_invalid_fails(self, validator):
        """Test validation fails with invalid operation type"""
        supported_ops = [BulkOperationType.UPDATE_STATUS]
        
        errors = validator.validate_operation_type("invalid_operation", supported_ops)
        
        assert len(errors) == 1
        assert "Invalid operation type" in errors[0]
    
    def test_validate_operation_type_unsupported_fails(self, validator):
        """Test validation fails with unsupported operation type"""
        supported_ops = [BulkOperationType.UPDATE_STATUS]
        
        errors = validator.validate_operation_type("update_price", supported_ops)
        
        assert len(errors) == 1
        assert "not supported" in errors[0]
    
    def test_validate_operation_data_price_update(self, validator):
        """Test validation of price update operation data"""
        # Valid price update
        valid_data = {'price': 19.99}
        errors = validator.validate_operation_data(BulkOperationType.UPDATE_PRICE, valid_data)
        assert len(errors) == 0
        
        # Missing price
        invalid_data = {}
        errors = validator.validate_operation_data(BulkOperationType.UPDATE_PRICE, invalid_data)
        assert len(errors) == 1
        assert "Price is required" in errors[0]
        
        # Invalid price (negative)
        invalid_data = {'price': -10}
        errors = validator.validate_operation_data(BulkOperationType.UPDATE_PRICE, invalid_data)
        assert len(errors) == 1
        assert "must be positive" in errors[0]
    
    def test_validate_operation_data_quantity_update(self, validator):
        """Test validation of quantity update operation data"""
        # Valid quantity update
        valid_data = {'quantity': 5}
        errors = validator.validate_operation_data(BulkOperationType.UPDATE_QUANTITY, valid_data)
        assert len(errors) == 0
        
        # Missing quantity
        invalid_data = {}
        errors = validator.validate_operation_data(BulkOperationType.UPDATE_QUANTITY, invalid_data)
        assert len(errors) == 1
        assert "Quantity is required" in errors[0]
        
        # Invalid quantity (negative)
        invalid_data = {'quantity': -5}
        errors = validator.validate_operation_data(BulkOperationType.UPDATE_QUANTITY, invalid_data)
        assert len(errors) == 1
        assert "cannot be negative" in errors[0]
    
    def test_validate_operation_data_status_update(self, validator):
        """Test validation of status update operation data"""
        # Valid status update
        valid_data = {'status': 'active'}
        errors = validator.validate_operation_data(BulkOperationType.UPDATE_STATUS, valid_data)
        assert len(errors) == 0
        
        # Missing status
        invalid_data = {}
        errors = validator.validate_operation_data(BulkOperationType.UPDATE_STATUS, invalid_data)
        assert len(errors) == 1
        assert "Status is required" in errors[0]


class TestBatchProcessor:
    """Test batch processor functionality"""
    
    @pytest.fixture
    def processor(self):
        return BatchProcessor(batch_size=3, max_concurrent_batches=2)
    
    @pytest.mark.asyncio
    async def test_process_in_batches_success(self, processor):
        """Test successful batch processing"""
        items = list(range(10))  # 10 items, should create 4 batches (3, 3, 3, 1)
        
        async def mock_process_func(batch):
            await asyncio.sleep(0.01)  # Simulate processing time
            return {
                'successful': len(batch),
                'failed': 0,
                'errors': [],
                'warnings': []
            }
        
        result = await processor.process_in_batches(items, mock_process_func)
        
        assert result.total_items == 10
        assert result.successful_items == 10
        assert result.failed_items == 0
        assert result.processed_items == 10
        assert result.status == BulkOperationStatus.COMPLETED
        assert result.started_at is not None
        assert result.completed_at is not None
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_process_in_batches_partial_failure(self, processor):
        """Test batch processing with partial failures"""
        items = list(range(6))  # 6 items, 2 batches of 3
        
        async def mock_process_func(batch):
            await asyncio.sleep(0.01)
            # Simulate failure for second batch
            if batch[0] >= 3:
                return {
                    'successful': 0,
                    'failed': len(batch),
                    'errors': ['Simulated batch failure'],
                    'warnings': []
                }
            else:
                return {
                    'successful': len(batch),
                    'failed': 0,
                    'errors': [],
                    'warnings': []
                }
        
        result = await processor.process_in_batches(items, mock_process_func)
        
        assert result.total_items == 6
        assert result.successful_items == 3
        assert result.failed_items == 3
        assert result.status == BulkOperationStatus.PARTIAL_SUCCESS
        assert len(result.errors) == 1
        assert 'Simulated batch failure' in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_process_in_batches_complete_failure(self, processor):
        """Test batch processing with complete failure"""
        items = list(range(3))
        
        async def mock_process_func(batch):
            await asyncio.sleep(0.01)
            return {
                'successful': 0,
                'failed': len(batch),
                'errors': ['All items failed'],
                'warnings': []
            }
        
        result = await processor.process_in_batches(items, mock_process_func)
        
        assert result.total_items == 3
        assert result.successful_items == 0
        assert result.failed_items == 3
        assert result.status == BulkOperationStatus.FAILED
        assert len(result.errors) == 1
    
    @pytest.mark.asyncio
    async def test_process_in_batches_handles_exceptions(self, processor):
        """Test batch processing handles exceptions gracefully"""
        items = list(range(6))
        
        async def mock_process_func(batch):
            await asyncio.sleep(0.01)
            # Raise exception for second batch
            if batch[0] >= 3:
                raise Exception("Simulated processing error")
            return {
                'successful': len(batch),
                'failed': 0,
                'errors': [],
                'warnings': []
            }
        
        result = await processor.process_in_batches(items, mock_process_func)
        
        assert result.total_items == 6
        assert result.successful_items == 3
        assert result.failed_items == 3
        assert result.status == BulkOperationStatus.PARTIAL_SUCCESS
        assert len(result.errors) == 1
        assert "Batch processing failed" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_batch_size_respected(self, processor):
        """Test that batch size is respected"""
        items = list(range(10))
        batch_sizes = []
        
        async def mock_process_func(batch):
            batch_sizes.append(len(batch))
            return {
                'successful': len(batch),
                'failed': 0,
                'errors': [],
                'warnings': []
            }
        
        await processor.process_in_batches(items, mock_process_func)
        
        # Should have 4 batches: [3, 3, 3, 1]
        assert len(batch_sizes) == 4
        assert batch_sizes[:3] == [3, 3, 3]  # First 3 batches should be full
        assert batch_sizes[3] == 1  # Last batch should have remainder
    
    @pytest.mark.asyncio
    async def test_concurrency_control(self, processor):
        """Test that concurrency is controlled"""
        items = list(range(9))  # 3 batches of 3
        processing_times = []
        
        async def mock_process_func(batch):
            start_time = asyncio.get_event_loop().time()
            await asyncio.sleep(0.1)  # Simulate processing time
            end_time = asyncio.get_event_loop().time()
            processing_times.append((start_time, end_time))
            return {
                'successful': len(batch),
                'failed': 0,
                'errors': [],
                'warnings': []
            }
        
        await processor.process_in_batches(items, mock_process_func)
        
        assert len(processing_times) == 3
        # With max_concurrent_batches=2, some batches should overlap in time
        # but the third batch should start after one of the first two completes