"""
Bulk Product Operations Implementation
Following SOLID principles - Single Responsibility for product bulk operations
YAGNI compliance: Essential bulk operations only
"""

from typing import List, Dict, Any
from decimal import Decimal
from datetime import datetime

from app.repositories.product_repository import ProductRepositoryInterface
from app.models.product import Product, ProductStatus
from app.services.bulk_operations.bulk_operation_framework import (
    BulkOperationInterface, BulkOperationType, BulkOperationResult, 
    BulkValidator, BatchProcessor, BulkOperationStatus
)
from app.core.exceptions import ValidationException, EbayManagerException


class BulkProductOperations(BulkOperationInterface[Product]):
    """
    SOLID: Single Responsibility - Handle bulk operations for products only
    YAGNI: Essential bulk operations only
    """
    
    def __init__(self, product_repository: ProductRepositoryInterface):
        self.product_repository = product_repository
        self.validator = BulkValidator()
        self.batch_processor = BatchProcessor(batch_size=100)
        
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
    
    async def validate_operation(self, product_ids: List[int], operation_data: Dict[str, Any]) -> List[str]:
        """Validate bulk product operation"""
        errors = []
        
        # Validate item count
        errors.extend(self.validator.validate_item_count(product_ids, max_items=1000))
        
        # Validate operation type
        operation_type = operation_data.get('operation_type')
        if operation_type:
            errors.extend(self.validator.validate_operation_type(operation_type, self.supported_operations))
            
            if not errors:
                op_type = BulkOperationType(operation_type)
                errors.extend(self.validator.validate_operation_data(op_type, operation_data))
        else:
            errors.append("Operation type is required")
        
        # Additional validation for product-specific operations
        if operation_type == BulkOperationType.UPDATE_PRICE.value:
            # Validate price data structure for products
            price_data = operation_data
            if 'cost_price' in price_data and price_data['cost_price'] <= 0:
                errors.append("Cost price must be positive")
            if 'selling_price' in price_data and price_data['selling_price'] <= 0:
                errors.append("Selling price must be positive")
            if ('cost_price' in price_data and 'selling_price' in price_data and 
                price_data['selling_price'] <= price_data['cost_price']):
                errors.append("Selling price must be higher than cost price")
        
        return errors
    
    async def execute_operation(self, product_ids: List[int], operation_data: Dict[str, Any]) -> BulkOperationResult:
        """Execute bulk product operation"""
        operation_type = BulkOperationType(operation_data['operation_type'])
        
        if operation_type == BulkOperationType.UPDATE_STATUS:
            return await self._bulk_update_status(product_ids, operation_data['status'])
        elif operation_type == BulkOperationType.UPDATE_PRICE:
            return await self._bulk_update_prices(product_ids, operation_data)
        elif operation_type == BulkOperationType.UPDATE_QUANTITY:
            return await self._bulk_update_quantity(product_ids, operation_data['quantity'])
        elif operation_type == BulkOperationType.BULK_ACTIVATE:
            return await self._bulk_update_status(product_ids, ProductStatus.ACTIVE.value)
        elif operation_type == BulkOperationType.BULK_DEACTIVATE:
            return await self._bulk_update_status(product_ids, ProductStatus.INACTIVE.value)
        else:
            raise ValidationException(f"Unsupported operation type: {operation_type}")
    
    async def _bulk_update_status(self, product_ids: List[int], new_status: str) -> BulkOperationResult:
        """Bulk update product status"""
        if new_status not in [s.value for s in ProductStatus]:
            raise ValidationException(f"Invalid status: {new_status}")
        
        async def process_batch(batch_ids: List[int]) -> Dict[str, Any]:
            successful = 0
            failed = 0
            errors = []
            warnings = []
            
            try:
                # Use repository bulk update if available
                if hasattr(self.product_repository, 'bulk_update'):
                    updated_count = await self.product_repository.bulk_update(batch_ids, {
                        'status': new_status,
                        'updated_at': datetime.utcnow()
                    })
                    successful = updated_count
                    
                    if updated_count < len(batch_ids):
                        failed = len(batch_ids) - updated_count
                        errors.append(f"Some products in batch were not updated")
                else:
                    # Fallback to individual updates
                    for product_id in batch_ids:
                        try:
                            await self.product_repository.update(product_id, {
                                'status': new_status,
                                'updated_at': datetime.utcnow()
                            })
                            successful += 1
                        except Exception as e:
                            failed += 1
                            errors.append(f"Failed to update product {product_id}: {str(e)}")
                
            except Exception as e:
                failed = len(batch_ids)
                errors.append(f"Batch update failed: {str(e)}")
            
            return {
                'successful': successful,
                'failed': failed,
                'errors': errors,
                'warnings': warnings
            }
        
        return await self.batch_processor.process_in_batches(product_ids, process_batch)
    
    async def _bulk_update_prices(self, product_ids: List[int], price_data: Dict[str, Any]) -> BulkOperationResult:
        """Bulk update product prices (cost and/or selling price)"""
        async def process_batch(batch_ids: List[int]) -> Dict[str, Any]:
            successful = 0
            failed = 0
            errors = []
            warnings = []
            
            for product_id in batch_ids:
                try:
                    product = await self.product_repository.get_by_id(product_id)
                    if not product:
                        failed += 1
                        errors.append(f"Product {product_id} not found")
                        continue
                    
                    update_data = {'updated_at': datetime.utcnow()}
                    
                    # Update cost price if provided
                    if 'cost_price' in price_data:
                        update_data['cost_price'] = Decimal(str(price_data['cost_price']))
                    
                    # Update selling price if provided
                    if 'selling_price' in price_data:
                        update_data['selling_price'] = Decimal(str(price_data['selling_price']))
                    
                    # Handle single price field (backward compatibility)
                    if 'price' in price_data:
                        update_data['selling_price'] = Decimal(str(price_data['price']))
                    
                    # Recalculate margin if both prices are being updated or available
                    cost_price = update_data.get('cost_price', product.cost_price)
                    selling_price = update_data.get('selling_price', product.selling_price)
                    
                    if cost_price and selling_price and cost_price > 0:
                        update_data['margin_percent'] = ((selling_price - cost_price) / cost_price) * 100
                    
                    await self.product_repository.update(product_id, update_data)
                    successful += 1
                    
                except Exception as e:
                    failed += 1
                    errors.append(f"Failed to update product {product_id}: {str(e)}")
            
            return {
                'successful': successful,
                'failed': failed,
                'errors': errors,
                'warnings': warnings
            }
        
        return await self.batch_processor.process_in_batches(product_ids, process_batch)
    
    async def _bulk_update_quantity(self, product_ids: List[int], quantity_adjustment: int) -> BulkOperationResult:
        """Bulk update product inventory quantities"""
        async def process_batch(batch_ids: List[int]) -> Dict[str, Any]:
            successful = 0
            failed = 0
            errors = []
            warnings = []
            
            for product_id in batch_ids:
                try:
                    # Use repository method if available
                    if hasattr(self.product_repository, 'update_inventory'):
                        success = await self.product_repository.update_inventory(product_id, quantity_adjustment)
                        if success:
                            successful += 1
                        else:
                            failed += 1
                            errors.append(f"Failed to update inventory for product {product_id}")
                    else:
                        # Fallback to manual inventory update
                        product = await self.product_repository.get_by_id(product_id)
                        if not product:
                            failed += 1
                            errors.append(f"Product {product_id} not found")
                            continue
                        
                        new_quantity = product.quantity_on_hand + quantity_adjustment
                        if new_quantity < 0:
                            failed += 1
                            errors.append(f"Cannot reduce inventory below zero for product {product_id}")
                            continue
                        
                        update_data = {
                            'quantity_on_hand': new_quantity,
                            'updated_at': datetime.utcnow()
                        }
                        
                        # Auto-update status based on quantity
                        if new_quantity == 0 and product.status == ProductStatus.ACTIVE.value:
                            update_data['status'] = ProductStatus.OUT_OF_STOCK.value
                            warnings.append(f"Product {product_id} set to out of stock due to zero quantity")
                        elif new_quantity > 0 and product.status == ProductStatus.OUT_OF_STOCK.value:
                            update_data['status'] = ProductStatus.ACTIVE.value
                            warnings.append(f"Product {product_id} reactivated due to positive quantity")
                        
                        await self.product_repository.update(product_id, update_data)
                        successful += 1
                        
                except Exception as e:
                    failed += 1
                    errors.append(f"Inventory update failed for product {product_id}: {str(e)}")
            
            return {
                'successful': successful,
                'failed': failed,
                'errors': errors,
                'warnings': warnings
            }
        
        return await self.batch_processor.process_in_batches(product_ids, process_batch)
    
    async def _bulk_activate(self, product_ids: List[int]) -> BulkOperationResult:
        """Bulk activate products with business rule validation"""
        async def process_batch(batch_ids: List[int]) -> Dict[str, Any]:
            successful = 0
            failed = 0
            errors = []
            warnings = []
            
            for product_id in batch_ids:
                try:
                    product = await self.product_repository.get_by_id(product_id)
                    if not product:
                        failed += 1
                        errors.append(f"Product {product_id} not found")
                        continue
                    
                    # Business rule: Can't activate if quantity is 0
                    if product.quantity_on_hand == 0:
                        failed += 1
                        warnings.append(f"Cannot activate product {product_id}: Zero inventory")
                        continue
                    
                    # Business rule: Check if supplier is active
                    if hasattr(product, 'supplier') and product.supplier and not product.supplier.is_active:
                        failed += 1
                        warnings.append(f"Cannot activate product {product_id}: Supplier is inactive")
                        continue
                    
                    # Don't activate already active products
                    if product.status == ProductStatus.ACTIVE.value:
                        warnings.append(f"Product {product_id} already active")
                        successful += 1  # Count as successful (no-op)
                        continue
                    
                    await self.product_repository.update(product_id, {
                        'status': ProductStatus.ACTIVE.value,
                        'updated_at': datetime.utcnow()
                    })
                    successful += 1
                    
                except Exception as e:
                    failed += 1
                    errors.append(f"Failed to activate product {product_id}: {str(e)}")
            
            return {
                'successful': successful,
                'failed': failed,
                'errors': errors,
                'warnings': warnings
            }
        
        return await self.batch_processor.process_in_batches(product_ids, process_batch)