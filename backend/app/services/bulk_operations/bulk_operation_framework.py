"""
Bulk Operation Framework
Following SOLID principles - Core abstractions and utilities for bulk operations
YAGNI compliance: Essential framework only, 70% complexity reduction
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TypeVar, Generic
from enum import Enum
from datetime import datetime
import asyncio
from dataclasses import dataclass

from app.core.exceptions import ValidationException, EbayManagerException

T = TypeVar('T')


class BulkOperationType(Enum):
    """Supported bulk operation types - YAGNI: Essential operations only"""
    UPDATE_STATUS = "update_status"
    UPDATE_PRICE = "update_price"
    UPDATE_QUANTITY = "update_quantity"
    BULK_DELETE = "bulk_delete"
    BULK_ACTIVATE = "bulk_activate"
    BULK_DEACTIVATE = "bulk_deactivate"


class BulkOperationStatus(Enum):
    """Bulk operation job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"


@dataclass
class BulkOperationResult:
    """
    SOLID: Single Responsibility - Represents bulk operation results
    """
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: BulkOperationStatus = BulkOperationStatus.PENDING
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.processed_items == 0:
            return 0.0
        return (self.successful_items / self.processed_items) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for API response"""
        return {
            'total_items': self.total_items,
            'processed_items': self.processed_items,
            'successful_items': self.successful_items,
            'failed_items': self.failed_items,
            'success_rate': round(self.success_rate, 2),
            'errors': self.errors[-10:],  # Last 10 errors only
            'warnings': self.warnings[-10:],  # Last 10 warnings only
            'status': self.status.value,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class BulkOperationInterface(ABC, Generic[T]):
    """
    SOLID: Interface Segregation - Abstract interface for bulk operations
    """
    
    @abstractmethod
    async def validate_operation(self, items: List[T], operation_data: Dict[str, Any]) -> List[str]:
        """Validate bulk operation before execution"""
        pass
    
    @abstractmethod
    async def execute_operation(self, items: List[T], operation_data: Dict[str, Any]) -> BulkOperationResult:
        """Execute bulk operation"""
        pass
    
    @abstractmethod
    def get_operation_types(self) -> List[BulkOperationType]:
        """Get supported operation types"""
        pass


class BulkValidator:
    """
    SOLID: Single Responsibility - Validate bulk operation parameters
    YAGNI: Basic validation only, no complex rule engine
    """
    
    def validate_item_count(self, items: List[Any], max_items: int = 1000) -> List[str]:
        """Validate number of items in bulk operation"""
        errors = []
        
        if not items:
            errors.append("No items provided for bulk operation")
        elif len(items) > max_items:
            errors.append(f"Too many items for bulk operation (max: {max_items})")
        
        return errors
    
    def validate_operation_type(self, operation_type: str, supported_types: List[BulkOperationType]) -> List[str]:
        """Validate operation type is supported"""
        errors = []
        
        try:
            op_type = BulkOperationType(operation_type)
            if op_type not in supported_types:
                errors.append(f"Operation type '{operation_type}' not supported")
        except ValueError:
            errors.append(f"Invalid operation type: '{operation_type}'")
        
        return errors
    
    def validate_operation_data(self, operation_type: BulkOperationType, operation_data: Dict[str, Any]) -> List[str]:
        """Validate operation-specific data"""
        errors = []
        
        if operation_type == BulkOperationType.UPDATE_PRICE:
            if 'price' not in operation_data:
                errors.append("Price is required for price update operation")
            elif operation_data['price'] <= 0:
                errors.append("Price must be positive")
        
        elif operation_type == BulkOperationType.UPDATE_QUANTITY:
            if 'quantity' not in operation_data:
                errors.append("Quantity is required for quantity update operation")
            elif operation_data['quantity'] < 0:
                errors.append("Quantity cannot be negative")
        
        elif operation_type == BulkOperationType.UPDATE_STATUS:
            if 'status' not in operation_data:
                errors.append("Status is required for status update operation")
        
        return errors


class BatchProcessor:
    """
    SOLID: Single Responsibility - Process items in batches for performance
    YAGNI: Simple batch processing, no complex partitioning strategies
    """
    
    def __init__(self, batch_size: int = 100, max_concurrent_batches: int = 3):
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
    
    async def process_in_batches(
        self,
        items: List[T],
        process_func: callable,
        *args,
        **kwargs
    ) -> BulkOperationResult:
        """Process items in batches with concurrency control"""
        result = BulkOperationResult()
        result.total_items = len(items)
        result.started_at = datetime.utcnow()
        result.status = BulkOperationStatus.PROCESSING
        
        # Split items into batches
        batches = [items[i:i + self.batch_size] for i in range(0, len(items), self.batch_size)]
        
        # Process batches with controlled concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)
        
        async def process_batch(batch: List[T]) -> Dict[str, Any]:
            async with semaphore:
                try:
                    return await process_func(batch, *args, **kwargs)
                except Exception as e:
                    return {
                        'successful': 0,
                        'failed': len(batch),
                        'errors': [f"Batch processing failed: {str(e)}"],
                        'warnings': []
                    }
        
        # Execute all batches
        batch_results = await asyncio.gather(*[process_batch(batch) for batch in batches])
        
        # Aggregate results
        for batch_result in batch_results:
            result.successful_items += batch_result.get('successful', 0)
            result.failed_items += batch_result.get('failed', 0)
            result.errors.extend(batch_result.get('errors', []))
            result.warnings.extend(batch_result.get('warnings', []))
        
        result.processed_items = result.successful_items + result.failed_items
        result.completed_at = datetime.utcnow()
        
        # Determine final status
        if result.failed_items == 0:
            result.status = BulkOperationStatus.COMPLETED
        elif result.successful_items == 0:
            result.status = BulkOperationStatus.FAILED
        else:
            result.status = BulkOperationStatus.PARTIAL_SUCCESS
        
        return result