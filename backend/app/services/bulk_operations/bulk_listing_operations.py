"""
Bulk Listing Operations Implementation
Following SOLID principles - Single Responsibility for listing bulk operations
YAGNI compliance: Essential bulk operations only, no complex workflow management
"""

from typing import List, Dict, Any
from decimal import Decimal
from datetime import datetime

from app.repositories.listing_repository import ListingRepositoryInterface
from app.models.listing import Listing, ListingStatus
from app.services.bulk_operations.bulk_operation_framework import (
    BulkOperationInterface, BulkOperationType, BulkOperationResult, 
    BulkValidator, BatchProcessor, BulkOperationStatus
)
from app.core.exceptions import ValidationException, EbayManagerException


class BulkListingOperations(BulkOperationInterface[Listing]):
    """
    SOLID: Single Responsibility - Handle bulk operations for listings only
    YAGNI: Essential bulk operations only, no complex workflow management
    """
    
    def __init__(self, listing_repository: ListingRepositoryInterface):
        self.listing_repository = listing_repository
        self.validator = BulkValidator()
        self.batch_processor = BatchProcessor(batch_size=50)  # Smaller batches for database operations
        
        self.supported_operations = [
            BulkOperationType.UPDATE_STATUS,
            BulkOperationType.UPDATE_PRICE,
            BulkOperationType.UPDATE_QUANTITY,
            BulkOperationType.BULK_ACTIVATE,
            BulkOperationType.BULK_DEACTIVATE
        ]
    
    def get_operation_types(self) -> List[BulkOperationType]:
        """Get supported bulk operation types"""
        return self.supported_operations
    
    async def validate_operation(self, listing_ids: List[int], operation_data: Dict[str, Any]) -> List[str]:
        """
        Validate bulk listing operation before execution
        YAGNI: Basic validation, no complex business rule validation
        """
        errors = []
        
        # Validate item count
        errors.extend(self.validator.validate_item_count(listing_ids, max_items=500))
        
        # Validate operation type
        operation_type = operation_data.get('operation_type')
        if operation_type:
            errors.extend(self.validator.validate_operation_type(operation_type, self.supported_operations))
            
            # Validate operation-specific data
            if not errors:  # Only if operation type is valid
                op_type = BulkOperationType(operation_type)
                errors.extend(self.validator.validate_operation_data(op_type, operation_data))
        else:
            errors.append("Operation type is required")
        
        # Validate listings exist and are accessible
        if not errors and listing_ids:
            try:
                # Sample validation - check first 10 listings exist
                sample_ids = listing_ids[:10]
                for listing_id in sample_ids:
                    listing = await self.listing_repository.get_by_id(listing_id)
                    if not listing:
                        errors.append(f"Listing {listing_id} not found")
                        break  # Stop after first missing listing
            except Exception as e:
                errors.append(f"Failed to validate listings: {str(e)}")
        
        return errors
    
    async def execute_operation(self, listing_ids: List[int], operation_data: Dict[str, Any]) -> BulkOperationResult:
        """Execute bulk listing operation with batch processing"""
        operation_type = BulkOperationType(operation_data['operation_type'])
        
        if operation_type == BulkOperationType.UPDATE_STATUS:
            return await self._bulk_update_status(listing_ids, operation_data['status'])
        elif operation_type == BulkOperationType.UPDATE_PRICE:
            return await self._bulk_update_price(listing_ids, operation_data['price'])
        elif operation_type == BulkOperationType.UPDATE_QUANTITY:
            return await self._bulk_update_quantity(listing_ids, operation_data['quantity'])
        elif operation_type == BulkOperationType.BULK_ACTIVATE:
            return await self._bulk_activate(listing_ids)
        elif operation_type == BulkOperationType.BULK_DEACTIVATE:
            return await self._bulk_deactivate(listing_ids)
        else:
            raise ValidationException(f"Unsupported operation type: {operation_type}")
    
    async def _bulk_update_status(self, listing_ids: List[int], new_status: str) -> BulkOperationResult:
        """Bulk update listing status"""
        # Validate status
        if new_status not in [s.value for s in ListingStatus]:
            raise ValidationException(f"Invalid status: {new_status}")
        
        async def process_batch(batch_ids: List[int]) -> Dict[str, Any]:
            """Process a batch of status updates"""
            successful = 0
            failed = 0
            errors = []
            warnings = []
            
            try:
                # Use repository bulk update for efficiency if available
                if hasattr(self.listing_repository, 'bulk_update_status'):
                    updated_count = await self.listing_repository.bulk_update_status(batch_ids, new_status)
                    successful = updated_count
                    
                    # Check if all items were updated
                    if updated_count < len(batch_ids):
                        failed = len(batch_ids) - updated_count
                        errors.append(f"Some listings in batch were not updated (possibly not found)")
                else:
                    # Fallback to individual updates
                    for listing_id in batch_ids:
                        try:
                            await self.listing_repository.update(listing_id, {
                                'status': new_status,
                                'updated_at': datetime.utcnow()
                            })
                            successful += 1
                        except Exception as e:
                            failed += 1
                            errors.append(f"Failed to update listing {listing_id}: {str(e)}")
                
            except Exception as e:
                failed = len(batch_ids)
                errors.append(f"Batch update failed: {str(e)}")
            
            return {
                'successful': successful,
                'failed': failed,
                'errors': errors,
                'warnings': warnings
            }
        
        return await self.batch_processor.process_in_batches(listing_ids, process_batch)
    
    async def _bulk_update_price(self, listing_ids: List[int], new_price: float) -> BulkOperationResult:
        """Bulk update listing price"""
        if new_price <= 0:
            raise ValidationException("Price must be positive")
        
        price_decimal = Decimal(str(new_price))
        
        async def process_batch(batch_ids: List[int]) -> Dict[str, Any]:
            """Process a batch of price updates"""
            successful = 0
            failed = 0
            errors = []
            warnings = []
            
            for listing_id in batch_ids:
                try:
                    listing = await self.listing_repository.get_by_id(listing_id)
                    if not listing:
                        failed += 1
                        errors.append(f"Listing {listing_id} not found")
                        continue
                    
                    # Business rule: Don't update price for ended listings
                    if listing.status in [ListingStatus.ENDED.value, ListingStatus.SOLD.value]:
                        failed += 1
                        warnings.append(f"Skipped listing {listing_id}: Cannot update price for {listing.status} listing")
                        continue
                    
                    # Update price
                    await self.listing_repository.update(listing_id, {
                        'price': price_decimal,
                        'updated_at': datetime.utcnow()
                    })
                    successful += 1
                    
                except Exception as e:
                    failed += 1
                    errors.append(f"Failed to update listing {listing_id}: {str(e)}")
            
            return {
                'successful': successful,
                'failed': failed,
                'errors': errors,
                'warnings': warnings
            }
        
        return await self.batch_processor.process_in_batches(listing_ids, process_batch)
    
    async def _bulk_update_quantity(self, listing_ids: List[int], new_quantity: int) -> BulkOperationResult:
        """Bulk update listing quantity"""
        if new_quantity < 0:
            raise ValidationException("Quantity cannot be negative")
        
        async def process_batch(batch_ids: List[int]) -> Dict[str, Any]:
            """Process a batch of quantity updates"""
            successful = 0
            failed = 0
            errors = []
            warnings = []
            
            for listing_id in batch_ids:
                try:
                    listing = await self.listing_repository.get_by_id(listing_id)
                    if not listing:
                        failed += 1
                        errors.append(f"Listing {listing_id} not found")
                        continue
                    
                    # Auto-update status based on quantity
                    update_data = {
                        'quantity_available': new_quantity,
                        'updated_at': datetime.utcnow()
                    }
                    
                    if new_quantity == 0 and listing.status == ListingStatus.ACTIVE.value:
                        update_data['status'] = ListingStatus.OUT_OF_STOCK.value
                        warnings.append(f"Listing {listing_id} set to out of stock due to zero quantity")
                    elif new_quantity > 0 and listing.status == ListingStatus.OUT_OF_STOCK.value:
                        update_data['status'] = ListingStatus.ACTIVE.value
                        warnings.append(f"Listing {listing_id} reactivated due to positive quantity")
                    
                    await self.listing_repository.update(listing_id, update_data)
                    successful += 1
                    
                except Exception as e:
                    failed += 1
                    errors.append(f"Failed to update listing {listing_id}: {str(e)}")
            
            return {
                'successful': successful,
                'failed': failed,
                'errors': errors,
                'warnings': warnings
            }
        
        return await self.batch_processor.process_in_batches(listing_ids, process_batch)
    
    async def _bulk_activate(self, listing_ids: List[int]) -> BulkOperationResult:
        """Bulk activate listings"""
        async def process_batch(batch_ids: List[int]) -> Dict[str, Any]:
            """Process a batch of activations"""
            successful = 0
            failed = 0
            errors = []
            warnings = []
            
            for listing_id in batch_ids:
                try:
                    listing = await self.listing_repository.get_by_id(listing_id)
                    if not listing:
                        failed += 1
                        errors.append(f"Listing {listing_id} not found")
                        continue
                    
                    # Business rule: Can't activate if quantity is 0
                    if listing.quantity_available == 0:
                        failed += 1
                        warnings.append(f"Cannot activate listing {listing_id}: Zero quantity")
                        continue
                    
                    # Business rule: Don't activate already active listings
                    if listing.status == ListingStatus.ACTIVE.value:
                        warnings.append(f"Listing {listing_id} already active")
                        successful += 1  # Count as successful (no-op)
                        continue
                    
                    await self.listing_repository.update(listing_id, {
                        'status': ListingStatus.ACTIVE.value,
                        'updated_at': datetime.utcnow()
                    })
                    successful += 1
                    
                except Exception as e:
                    failed += 1
                    errors.append(f"Failed to activate listing {listing_id}: {str(e)}")
            
            return {
                'successful': successful,
                'failed': failed,
                'errors': errors,
                'warnings': warnings
            }
        
        return await self.batch_processor.process_in_batches(listing_ids, process_batch)
    
    async def _bulk_deactivate(self, listing_ids: List[int]) -> BulkOperationResult:
        """Bulk deactivate listings"""
        return await self._bulk_update_status(listing_ids, ListingStatus.INACTIVE.value)