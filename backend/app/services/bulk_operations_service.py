"""
Bulk Operations Service
Following SOLID principles - Single Responsibility for coordinating bulk operations
YAGNI compliance: Simple delegation, no complex orchestration
"""

from typing import List, Dict, Any, Union
from enum import Enum

from app.services.bulk_operations.bulk_listing_operations import BulkListingOperations
from app.services.bulk_operations.bulk_product_operations import BulkProductOperations
from app.services.bulk_operations.bulk_operation_framework import BulkOperationResult, BulkOperationType
from app.repositories.listing_repository import ListingRepositoryInterface
from app.repositories.product_repository import ProductRepositoryInterface
from app.core.exceptions import ValidationException, EbayManagerException


class BulkEntityType(Enum):
    """Entity types that support bulk operations"""
    LISTINGS = "listings"
    PRODUCTS = "products"


class BulkOperationsService:
    """
    SOLID: Single Responsibility - Coordinate bulk operations across different entities
    YAGNI: Simple delegation, no complex orchestration
    """
    
    def __init__(
        self,
        listing_repository: ListingRepositoryInterface,
        product_repository: ProductRepositoryInterface
    ):
        """Initialize bulk operations service with repository dependencies"""
        self.bulk_listing_ops = BulkListingOperations(listing_repository)
        self.bulk_product_ops = BulkProductOperations(product_repository)
    
    async def execute_bulk_operation(
        self,
        entity_type: str,
        entity_ids: List[int],
        operation_data: Dict[str, Any]
    ) -> BulkOperationResult:
        """
        Execute bulk operation on specified entity type
        YAGNI: Simple delegation based on entity type
        """
        try:
            entity_enum = BulkEntityType(entity_type)
        except ValueError:
            raise ValidationException(f"Unsupported entity type: {entity_type}")
        
        if entity_enum == BulkEntityType.LISTINGS:
            return await self._execute_listing_operation(entity_ids, operation_data)
        elif entity_enum == BulkEntityType.PRODUCTS:
            return await self._execute_product_operation(entity_ids, operation_data)
        else:
            raise ValidationException(f"Entity type {entity_type} not implemented")
    
    async def validate_bulk_operation(
        self,
        entity_type: str,
        entity_ids: List[int],
        operation_data: Dict[str, Any]
    ) -> List[str]:
        """Validate bulk operation before execution"""
        try:
            entity_enum = BulkEntityType(entity_type)
        except ValueError:
            return [f"Unsupported entity type: {entity_type}"]
        
        if entity_enum == BulkEntityType.LISTINGS:
            return await self.bulk_listing_ops.validate_operation(entity_ids, operation_data)
        elif entity_enum == BulkEntityType.PRODUCTS:
            return await self.bulk_product_ops.validate_operation(entity_ids, operation_data)
        else:
            return [f"Entity type {entity_type} not implemented"]
    
    def get_supported_operations(self, entity_type: str) -> List[str]:
        """Get supported operations for entity type"""
        try:
            entity_enum = BulkEntityType(entity_type)
        except ValueError:
            return []
        
        if entity_enum == BulkEntityType.LISTINGS:
            return [op.value for op in self.bulk_listing_ops.get_operation_types()]
        elif entity_enum == BulkEntityType.PRODUCTS:
            return [op.value for op in self.bulk_product_ops.get_operation_types()]
        else:
            return []
    
    def get_supported_entity_types(self) -> List[str]:
        """Get all supported entity types"""
        return [entity.value for entity in BulkEntityType]
    
    async def get_operation_preview(
        self,
        entity_type: str,
        entity_ids: List[int],
        operation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get preview of bulk operation without executing
        YAGNI: Basic preview info only
        """
        validation_errors = await self.validate_bulk_operation(entity_type, entity_ids, operation_data)
        
        preview = {
            'entity_type': entity_type,
            'total_items': len(entity_ids),
            'operation_type': operation_data.get('operation_type'),
            'valid': len(validation_errors) == 0,
            'validation_errors': validation_errors,
            'estimated_time_seconds': self._estimate_processing_time(len(entity_ids))
        }
        
        return preview
    
    async def _execute_listing_operation(self, listing_ids: List[int], operation_data: Dict[str, Any]) -> BulkOperationResult:
        """Execute bulk operation on listings"""
        # Validate first
        validation_errors = await self.bulk_listing_ops.validate_operation(listing_ids, operation_data)
        if validation_errors:
            raise ValidationException(f"Validation failed: {'; '.join(validation_errors[:3])}")
        
        # Execute operation
        return await self.bulk_listing_ops.execute_operation(listing_ids, operation_data)
    
    async def _execute_product_operation(self, product_ids: List[int], operation_data: Dict[str, Any]) -> BulkOperationResult:
        """Execute bulk operation on products"""
        # Validate first
        validation_errors = await self.bulk_product_ops.validate_operation(product_ids, operation_data)
        if validation_errors:
            raise ValidationException(f"Validation failed: {'; '.join(validation_errors[:3])}")
        
        # Execute operation
        return await self.bulk_product_ops.execute_operation(product_ids, operation_data)
    
    def _estimate_processing_time(self, item_count: int) -> int:
        """
        Estimate processing time in seconds
        YAGNI: Simple linear estimation
        """
        # Rough estimates based on batch processing
        if item_count <= 50:
            return 5
        elif item_count <= 200:
            return 15
        elif item_count <= 500:
            return 30
        else:
            return 60
    
    # Convenience methods for common operations
    
    async def bulk_update_listing_status(
        self, 
        listing_ids: List[int], 
        new_status: str
    ) -> BulkOperationResult:
        """Convenience method for bulk listing status updates"""
        operation_data = {
            'operation_type': BulkOperationType.UPDATE_STATUS.value,
            'status': new_status
        }
        return await self.execute_bulk_operation('listings', listing_ids, operation_data)
    
    async def bulk_update_listing_price(
        self, 
        listing_ids: List[int], 
        new_price: float
    ) -> BulkOperationResult:
        """Convenience method for bulk listing price updates"""
        operation_data = {
            'operation_type': BulkOperationType.UPDATE_PRICE.value,
            'price': new_price
        }
        return await self.execute_bulk_operation('listings', listing_ids, operation_data)
    
    async def bulk_activate_listings(self, listing_ids: List[int]) -> BulkOperationResult:
        """Convenience method for bulk listing activation"""
        operation_data = {
            'operation_type': BulkOperationType.BULK_ACTIVATE.value
        }
        return await self.execute_bulk_operation('listings', listing_ids, operation_data)
    
    async def bulk_deactivate_listings(self, listing_ids: List[int]) -> BulkOperationResult:
        """Convenience method for bulk listing deactivation"""
        operation_data = {
            'operation_type': BulkOperationType.BULK_DEACTIVATE.value
        }
        return await self.execute_bulk_operation('listings', listing_ids, operation_data)
    
    async def bulk_update_product_prices(
        self, 
        product_ids: List[int], 
        cost_price: float = None, 
        selling_price: float = None
    ) -> BulkOperationResult:
        """Convenience method for bulk product price updates"""
        operation_data = {
            'operation_type': BulkOperationType.UPDATE_PRICE.value
        }
        
        if cost_price is not None:
            operation_data['cost_price'] = cost_price
        if selling_price is not None:
            operation_data['selling_price'] = selling_price
        
        if not cost_price and not selling_price:
            raise ValidationException("At least one price (cost or selling) must be provided")
        
        return await self.execute_bulk_operation('products', product_ids, operation_data)
    
    async def bulk_update_product_inventory(
        self, 
        product_ids: List[int], 
        quantity_adjustment: int
    ) -> BulkOperationResult:
        """Convenience method for bulk product inventory updates"""
        operation_data = {
            'operation_type': BulkOperationType.UPDATE_QUANTITY.value,
            'quantity': quantity_adjustment
        }
        return await self.execute_bulk_operation('products', product_ids, operation_data)
    
    async def bulk_activate_products(self, product_ids: List[int]) -> BulkOperationResult:
        """Convenience method for bulk product activation"""
        operation_data = {
            'operation_type': BulkOperationType.BULK_ACTIVATE.value
        }
        return await self.execute_bulk_operation('products', product_ids, operation_data)
    
    async def bulk_deactivate_products(self, product_ids: List[int]) -> BulkOperationResult:
        """Convenience method for bulk product deactivation"""
        operation_data = {
            'operation_type': BulkOperationType.BULK_DEACTIVATE.value
        }
        return await self.execute_bulk_operation('products', product_ids, operation_data)