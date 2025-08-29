"""
Test Bulk Operations Service
Following SOLID principles - Single Responsibility for testing service coordination
YAGNI compliance: Essential test cases only
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.services.bulk_operations_service import (
    BulkOperationsService, BulkEntityType
)
from app.services.bulk_operations.bulk_operation_framework import (
    BulkOperationType, BulkOperationResult, BulkOperationStatus
)
from app.core.exceptions import ValidationException


class TestBulkOperationsService:
    """Test bulk operations service coordination"""
    
    @pytest.fixture
    def mock_listing_repo(self):
        repo = Mock()
        repo.get_by_id = AsyncMock()
        repo.update = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_product_repo(self):
        repo = Mock()
        repo.get_by_id = AsyncMock()
        repo.update = AsyncMock()
        return repo
    
    @pytest.fixture
    def bulk_service(self, mock_listing_repo, mock_product_repo):
        return BulkOperationsService(mock_listing_repo, mock_product_repo)
    
    def test_get_supported_entity_types(self, bulk_service):
        """Test getting supported entity types"""
        entity_types = bulk_service.get_supported_entity_types()
        
        assert 'listings' in entity_types
        assert 'products' in entity_types
        assert len(entity_types) == 2
    
    def test_get_supported_operations_for_listings(self, bulk_service):
        """Test getting supported operations for listings"""
        operations = bulk_service.get_supported_operations('listings')
        
        assert 'update_status' in operations
        assert 'update_price' in operations
        assert 'update_quantity' in operations
        assert 'bulk_activate' in operations
        assert 'bulk_deactivate' in operations
    
    def test_get_supported_operations_for_products(self, bulk_service):
        """Test getting supported operations for products"""
        operations = bulk_service.get_supported_operations('products')
        
        assert 'update_status' in operations
        assert 'update_price' in operations
        assert 'update_quantity' in operations
        assert 'bulk_activate' in operations
        assert 'bulk_deactivate' in operations
    
    def test_get_supported_operations_invalid_entity(self, bulk_service):
        """Test getting operations for invalid entity type returns empty list"""
        operations = bulk_service.get_supported_operations('invalid_entity')
        
        assert operations == []
    
    @pytest.mark.asyncio
    async def test_validate_bulk_operation_success(self, bulk_service):
        """Test successful bulk operation validation"""
        entity_ids = [1, 2, 3]
        operation_data = {
            'operation_type': 'update_status',
            'status': 'active'
        }
        
        # Mock validation to return no errors
        with patch.object(bulk_service.bulk_listing_ops, 'validate_operation') as mock_validate:
            mock_validate.return_value = []
            
            errors = await bulk_service.validate_bulk_operation('listings', entity_ids, operation_data)
            
            assert len(errors) == 0
            mock_validate.assert_called_once_with(entity_ids, operation_data)
    
    @pytest.mark.asyncio
    async def test_validate_bulk_operation_invalid_entity_type(self, bulk_service):
        """Test validation with invalid entity type"""
        entity_ids = [1, 2, 3]
        operation_data = {'operation_type': 'update_status', 'status': 'active'}
        
        errors = await bulk_service.validate_bulk_operation('invalid_entity', entity_ids, operation_data)
        
        assert len(errors) == 1
        assert 'Unsupported entity type' in errors[0]
    
    @pytest.mark.asyncio
    async def test_execute_bulk_operation_listings_success(self, bulk_service):
        """Test successful execution of bulk operation on listings"""
        entity_ids = [1, 2, 3]
        operation_data = {
            'operation_type': 'update_status',
            'status': 'active'
        }
        
        # Mock validation and execution
        mock_result = BulkOperationResult()
        mock_result.successful_items = 3
        mock_result.status = BulkOperationStatus.COMPLETED
        
        with patch.object(bulk_service.bulk_listing_ops, 'validate_operation') as mock_validate:
            with patch.object(bulk_service.bulk_listing_ops, 'execute_operation') as mock_execute:
                mock_validate.return_value = []
                mock_execute.return_value = mock_result
                
                result = await bulk_service.execute_bulk_operation('listings', entity_ids, operation_data)
                
                assert result == mock_result
                mock_validate.assert_called_once_with(entity_ids, operation_data)
                mock_execute.assert_called_once_with(entity_ids, operation_data)
    
    @pytest.mark.asyncio
    async def test_execute_bulk_operation_products_success(self, bulk_service):
        """Test successful execution of bulk operation on products"""
        entity_ids = [1, 2, 3]
        operation_data = {
            'operation_type': 'update_price',
            'cost_price': 10.0,
            'selling_price': 20.0
        }
        
        # Mock validation and execution
        mock_result = BulkOperationResult()
        mock_result.successful_items = 3
        mock_result.status = BulkOperationStatus.COMPLETED
        
        with patch.object(bulk_service.bulk_product_ops, 'validate_operation') as mock_validate:
            with patch.object(bulk_service.bulk_product_ops, 'execute_operation') as mock_execute:
                mock_validate.return_value = []
                mock_execute.return_value = mock_result
                
                result = await bulk_service.execute_bulk_operation('products', entity_ids, operation_data)
                
                assert result == mock_result
                mock_validate.assert_called_once_with(entity_ids, operation_data)
                mock_execute.assert_called_once_with(entity_ids, operation_data)
    
    @pytest.mark.asyncio
    async def test_execute_bulk_operation_invalid_entity_type(self, bulk_service):
        """Test execution with invalid entity type fails"""
        entity_ids = [1, 2, 3]
        operation_data = {'operation_type': 'update_status', 'status': 'active'}
        
        with pytest.raises(ValidationException) as exc_info:
            await bulk_service.execute_bulk_operation('invalid_entity', entity_ids, operation_data)
        
        assert 'Unsupported entity type' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_bulk_operation_validation_fails(self, bulk_service):
        """Test execution fails when validation fails"""
        entity_ids = [1, 2, 3]
        operation_data = {
            'operation_type': 'update_status',
            'status': 'active'
        }
        
        # Mock validation to return errors
        with patch.object(bulk_service.bulk_listing_ops, 'validate_operation') as mock_validate:
            mock_validate.return_value = ['Validation error 1', 'Validation error 2']
            
            with pytest.raises(ValidationException) as exc_info:
                await bulk_service.execute_bulk_operation('listings', entity_ids, operation_data)
            
            assert 'Validation failed' in str(exc_info.value)
            assert 'Validation error 1' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_operation_preview_success(self, bulk_service):
        """Test getting operation preview"""
        entity_ids = [1, 2, 3, 4, 5]
        operation_data = {
            'operation_type': 'update_status',
            'status': 'active'
        }
        
        # Mock validation to return no errors
        with patch.object(bulk_service, 'validate_bulk_operation') as mock_validate:
            mock_validate.return_value = []
            
            preview = await bulk_service.get_operation_preview('listings', entity_ids, operation_data)
            
            assert preview['entity_type'] == 'listings'
            assert preview['total_items'] == 5
            assert preview['operation_type'] == 'update_status'
            assert preview['valid'] is True
            assert preview['validation_errors'] == []
            assert 'estimated_time_seconds' in preview
    
    @pytest.mark.asyncio
    async def test_get_operation_preview_with_validation_errors(self, bulk_service):
        """Test getting operation preview with validation errors"""
        entity_ids = [1, 2]
        operation_data = {
            'operation_type': 'update_price',
            'price': -10  # Invalid price
        }
        
        # Mock validation to return errors
        with patch.object(bulk_service, 'validate_bulk_operation') as mock_validate:
            mock_validate.return_value = ['Price must be positive']
            
            preview = await bulk_service.get_operation_preview('listings', entity_ids, operation_data)
            
            assert preview['valid'] is False
            assert len(preview['validation_errors']) == 1
            assert 'Price must be positive' in preview['validation_errors']
    
    def test_estimate_processing_time(self, bulk_service):
        """Test processing time estimation"""
        # Test different item counts
        assert bulk_service._estimate_processing_time(10) == 5
        assert bulk_service._estimate_processing_time(100) == 15
        assert bulk_service._estimate_processing_time(300) == 30
        assert bulk_service._estimate_processing_time(1000) == 60
    
    @pytest.mark.asyncio
    async def test_bulk_update_listing_status_convenience(self, bulk_service):
        """Test convenience method for bulk listing status update"""
        listing_ids = [1, 2, 3]
        new_status = 'active'
        
        mock_result = BulkOperationResult()
        mock_result.successful_items = 3
        
        with patch.object(bulk_service, 'execute_bulk_operation') as mock_execute:
            mock_execute.return_value = mock_result
            
            result = await bulk_service.bulk_update_listing_status(listing_ids, new_status)
            
            assert result == mock_result
            mock_execute.assert_called_once_with(
                'listings', 
                listing_ids, 
                {'operation_type': 'update_status', 'status': new_status}
            )
    
    @pytest.mark.asyncio
    async def test_bulk_update_listing_price_convenience(self, bulk_service):
        """Test convenience method for bulk listing price update"""
        listing_ids = [1, 2, 3]
        new_price = 29.99
        
        mock_result = BulkOperationResult()
        mock_result.successful_items = 3
        
        with patch.object(bulk_service, 'execute_bulk_operation') as mock_execute:
            mock_execute.return_value = mock_result
            
            result = await bulk_service.bulk_update_listing_price(listing_ids, new_price)
            
            assert result == mock_result
            mock_execute.assert_called_once_with(
                'listings',
                listing_ids,
                {'operation_type': 'update_price', 'price': new_price}
            )
    
    @pytest.mark.asyncio
    async def test_bulk_activate_listings_convenience(self, bulk_service):
        """Test convenience method for bulk listing activation"""
        listing_ids = [1, 2, 3]
        
        mock_result = BulkOperationResult()
        mock_result.successful_items = 3
        
        with patch.object(bulk_service, 'execute_bulk_operation') as mock_execute:
            mock_execute.return_value = mock_result
            
            result = await bulk_service.bulk_activate_listings(listing_ids)
            
            assert result == mock_result
            mock_execute.assert_called_once_with(
                'listings',
                listing_ids,
                {'operation_type': 'bulk_activate'}
            )
    
    @pytest.mark.asyncio
    async def test_bulk_update_product_prices_convenience(self, bulk_service):
        """Test convenience method for bulk product price update"""
        product_ids = [1, 2, 3]
        cost_price = 10.0
        selling_price = 20.0
        
        mock_result = BulkOperationResult()
        mock_result.successful_items = 3
        
        with patch.object(bulk_service, 'execute_bulk_operation') as mock_execute:
            mock_execute.return_value = mock_result
            
            result = await bulk_service.bulk_update_product_prices(
                product_ids, cost_price, selling_price
            )
            
            assert result == mock_result
            mock_execute.assert_called_once_with(
                'products',
                product_ids,
                {
                    'operation_type': 'update_price',
                    'cost_price': cost_price,
                    'selling_price': selling_price
                }
            )
    
    @pytest.mark.asyncio
    async def test_bulk_update_product_prices_no_prices_fails(self, bulk_service):
        """Test bulk product price update fails with no prices provided"""
        product_ids = [1, 2, 3]
        
        with pytest.raises(ValidationException) as exc_info:
            await bulk_service.bulk_update_product_prices(product_ids, None, None)
        
        assert 'At least one price' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_bulk_update_product_inventory_convenience(self, bulk_service):
        """Test convenience method for bulk product inventory update"""
        product_ids = [1, 2, 3]
        quantity_adjustment = 5
        
        mock_result = BulkOperationResult()
        mock_result.successful_items = 3
        
        with patch.object(bulk_service, 'execute_bulk_operation') as mock_execute:
            mock_execute.return_value = mock_result
            
            result = await bulk_service.bulk_update_product_inventory(
                product_ids, quantity_adjustment
            )
            
            assert result == mock_result
            mock_execute.assert_called_once_with(
                'products',
                product_ids,
                {
                    'operation_type': 'update_quantity',
                    'quantity': quantity_adjustment
                }
            )
    
    @pytest.mark.asyncio
    async def test_bulk_activate_products_convenience(self, bulk_service):
        """Test convenience method for bulk product activation"""
        product_ids = [1, 2, 3]
        
        mock_result = BulkOperationResult()
        mock_result.successful_items = 3
        
        with patch.object(bulk_service, 'execute_bulk_operation') as mock_execute:
            mock_execute.return_value = mock_result
            
            result = await bulk_service.bulk_activate_products(product_ids)
            
            assert result == mock_result
            mock_execute.assert_called_once_with(
                'products',
                product_ids,
                {'operation_type': 'bulk_activate'}
            )
    
    @pytest.mark.asyncio
    async def test_bulk_deactivate_products_convenience(self, bulk_service):
        """Test convenience method for bulk product deactivation"""
        product_ids = [1, 2, 3]
        
        mock_result = BulkOperationResult()
        mock_result.successful_items = 3
        
        with patch.object(bulk_service, 'execute_bulk_operation') as mock_execute:
            mock_execute.return_value = mock_result
            
            result = await bulk_service.bulk_deactivate_products(product_ids)
            
            assert result == mock_result
            mock_execute.assert_called_once_with(
                'products',
                product_ids,
                {'operation_type': 'bulk_deactivate'}
            )