"""
Test Bulk Listing Operations
Following SOLID principles - Single Responsibility for testing listing bulk operations
YAGNI compliance: Essential test cases only
"""

import pytest
from unittest.mock import Mock, AsyncMock
from decimal import Decimal

from app.services.bulk_operations.bulk_listing_operations import BulkListingOperations
from app.services.bulk_operations.bulk_operation_framework import (
    BulkOperationType, BulkOperationStatus
)
from app.models.listing import Listing, ListingStatus
from app.core.exceptions import ValidationException


class TestBulkListingOperations:
    """Test bulk listing operations functionality"""
    
    @pytest.fixture
    def mock_listing_repo(self):
        repo = Mock()
        repo.get_by_id = AsyncMock()
        repo.update = AsyncMock()
        repo.bulk_update_status = AsyncMock()
        return repo
    
    @pytest.fixture
    def bulk_listing_ops(self, mock_listing_repo):
        return BulkListingOperations(mock_listing_repo)
    
    def test_get_operation_types(self, bulk_listing_ops):
        """Test getting supported operation types"""
        supported_ops = bulk_listing_ops.get_operation_types()
        
        assert BulkOperationType.UPDATE_STATUS in supported_ops
        assert BulkOperationType.UPDATE_PRICE in supported_ops
        assert BulkOperationType.UPDATE_QUANTITY in supported_ops
        assert BulkOperationType.BULK_ACTIVATE in supported_ops
        assert BulkOperationType.BULK_DEACTIVATE in supported_ops
    
    @pytest.mark.asyncio
    async def test_validate_operation_success(self, bulk_listing_ops, mock_listing_repo):
        """Test successful operation validation"""
        listing_ids = [1, 2, 3]
        operation_data = {
            'operation_type': 'update_price',
            'price': 19.99
        }
        
        # Mock existing listings
        mock_listing = Mock(id=1, status=ListingStatus.ACTIVE.value)
        mock_listing_repo.get_by_id.return_value = mock_listing
        
        errors = await bulk_listing_ops.validate_operation(listing_ids, operation_data)
        
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_operation_too_many_items(self, bulk_listing_ops):
        """Test validation fails with too many items"""
        listing_ids = list(range(501))  # More than max 500
        operation_data = {
            'operation_type': 'update_status',
            'status': 'active'
        }
        
        errors = await bulk_listing_ops.validate_operation(listing_ids, operation_data)
        
        assert len(errors) > 0
        assert any("Too many items" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_validate_operation_missing_operation_type(self, bulk_listing_ops):
        """Test validation fails with missing operation type"""
        listing_ids = [1, 2, 3]
        operation_data = {'price': 19.99}  # Missing operation_type
        
        errors = await bulk_listing_ops.validate_operation(listing_ids, operation_data)
        
        assert len(errors) > 0
        assert any("Operation type is required" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_validate_operation_invalid_operation_type(self, bulk_listing_ops):
        """Test validation fails with invalid operation type"""
        listing_ids = [1, 2, 3]
        operation_data = {
            'operation_type': 'invalid_operation',
            'price': 19.99
        }
        
        errors = await bulk_listing_ops.validate_operation(listing_ids, operation_data)
        
        assert len(errors) > 0
        assert any("Invalid operation type" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_validate_operation_missing_listing(self, bulk_listing_ops, mock_listing_repo):
        """Test validation detects missing listings"""
        listing_ids = [1, 2, 3]
        operation_data = {
            'operation_type': 'update_price',
            'price': 19.99
        }
        
        # Mock first listing not found
        mock_listing_repo.get_by_id.return_value = None
        
        errors = await bulk_listing_ops.validate_operation(listing_ids, operation_data)
        
        assert len(errors) > 0
        assert any("not found" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_bulk_update_status_success(self, bulk_listing_ops, mock_listing_repo):
        """Test successful bulk status update"""
        listing_ids = [1, 2, 3]
        new_status = ListingStatus.ACTIVE.value
        
        # Mock bulk update returns count of updated items
        mock_listing_repo.bulk_update_status.return_value = 3
        
        result = await bulk_listing_ops._bulk_update_status(listing_ids, new_status)
        
        assert result.status == BulkOperationStatus.COMPLETED
        assert result.successful_items == 3
        assert result.failed_items == 0
        assert result.total_items == 3
        assert result.success_rate == 100.0
        
        mock_listing_repo.bulk_update_status.assert_called_once_with(listing_ids, new_status)
    
    @pytest.mark.asyncio
    async def test_bulk_update_status_invalid_status(self, bulk_listing_ops):
        """Test bulk status update with invalid status"""
        listing_ids = [1, 2, 3]
        invalid_status = "invalid_status"
        
        with pytest.raises(ValidationException) as exc_info:
            await bulk_listing_ops._bulk_update_status(listing_ids, invalid_status)
        
        assert "Invalid status" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_bulk_update_price_success(self, bulk_listing_ops, mock_listing_repo):
        """Test successful bulk price update"""
        listing_ids = [1, 2]
        new_price = 29.99
        
        # Mock existing listings
        active_listing = Mock(id=1, status=ListingStatus.ACTIVE.value)
        active_listing2 = Mock(id=2, status=ListingStatus.INACTIVE.value)
        
        mock_listing_repo.get_by_id.side_effect = [active_listing, active_listing2]
        mock_listing_repo.update.return_value = None
        
        result = await bulk_listing_ops._bulk_update_price(listing_ids, new_price)
        
        assert result.successful_items == 2
        assert result.failed_items == 0
        
        # Verify update was called for both listings
        assert mock_listing_repo.update.call_count == 2
        
        # Verify price was converted to Decimal
        call_args = mock_listing_repo.update.call_args_list[0][0]
        update_data = call_args[1]
        assert update_data['price'] == Decimal('29.99')
    
    @pytest.mark.asyncio
    async def test_bulk_update_price_skips_ended_listings(self, bulk_listing_ops, mock_listing_repo):
        """Test bulk price update skips ended listings with warnings"""
        listing_ids = [1, 2]
        new_price = 29.99
        
        # Mock one active and one ended listing
        active_listing = Mock(id=1, status=ListingStatus.ACTIVE.value)
        ended_listing = Mock(id=2, status=ListingStatus.ENDED.value)
        
        mock_listing_repo.get_by_id.side_effect = [active_listing, ended_listing]
        mock_listing_repo.update.return_value = None
        
        result = await bulk_listing_ops._bulk_update_price(listing_ids, new_price)
        
        assert result.successful_items == 1
        assert result.failed_items == 1
        assert len(result.warnings) > 0
        assert any("Cannot update price for ended listing" in warning for warning in result.warnings)
        
        # Should only update the active listing
        mock_listing_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_bulk_update_price_invalid_price(self, bulk_listing_ops):
        """Test bulk price update with invalid price"""
        listing_ids = [1, 2]
        invalid_price = -10.0
        
        with pytest.raises(ValidationException) as exc_info:
            await bulk_listing_ops._bulk_update_price(listing_ids, invalid_price)
        
        assert "Price must be positive" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_bulk_update_quantity_success(self, bulk_listing_ops, mock_listing_repo):
        """Test successful bulk quantity update"""
        listing_ids = [1, 2]
        new_quantity = 10
        
        # Mock existing listings
        active_listing = Mock(id=1, status=ListingStatus.ACTIVE.value, quantity_available=5)
        out_of_stock_listing = Mock(id=2, status=ListingStatus.OUT_OF_STOCK.value, quantity_available=0)
        
        mock_listing_repo.get_by_id.side_effect = [active_listing, out_of_stock_listing]
        mock_listing_repo.update.return_value = None
        
        result = await bulk_listing_ops._bulk_update_quantity(listing_ids, new_quantity)
        
        assert result.successful_items == 2
        assert result.failed_items == 0
        assert len(result.warnings) > 0  # Should warn about reactivated listing
        
        # Verify both listings were updated
        assert mock_listing_repo.update.call_count == 2
        
        # Check that out-of-stock listing was reactivated
        second_call_args = mock_listing_repo.update.call_args_list[1][0]
        update_data = second_call_args[1]
        assert update_data['quantity_available'] == 10
        assert update_data['status'] == ListingStatus.ACTIVE.value
    
    @pytest.mark.asyncio
    async def test_bulk_update_quantity_zero_sets_out_of_stock(self, bulk_listing_ops, mock_listing_repo):
        """Test bulk quantity update with zero quantity sets out of stock"""
        listing_ids = [1]
        new_quantity = 0
        
        # Mock active listing
        active_listing = Mock(id=1, status=ListingStatus.ACTIVE.value, quantity_available=5)
        mock_listing_repo.get_by_id.return_value = active_listing
        mock_listing_repo.update.return_value = None
        
        result = await bulk_listing_ops._bulk_update_quantity(listing_ids, new_quantity)
        
        assert result.successful_items == 1
        assert len(result.warnings) > 0
        assert any("out of stock due to zero quantity" in warning for warning in result.warnings)
        
        # Verify status was changed to out of stock
        call_args = mock_listing_repo.update.call_args[0]
        update_data = call_args[1]
        assert update_data['quantity_available'] == 0
        assert update_data['status'] == ListingStatus.OUT_OF_STOCK.value
    
    @pytest.mark.asyncio
    async def test_bulk_update_quantity_negative_fails(self, bulk_listing_ops):
        """Test bulk quantity update with negative quantity fails"""
        listing_ids = [1]
        invalid_quantity = -5
        
        with pytest.raises(ValidationException) as exc_info:
            await bulk_listing_ops._bulk_update_quantity(listing_ids, invalid_quantity)
        
        assert "Quantity cannot be negative" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_bulk_activate_success(self, bulk_listing_ops, mock_listing_repo):
        """Test successful bulk activation"""
        listing_ids = [1, 2]
        
        # Mock one inactive and one active listing with inventory
        inactive_listing = Mock(id=1, status=ListingStatus.INACTIVE.value, quantity_available=5)
        active_listing = Mock(id=2, status=ListingStatus.ACTIVE.value, quantity_available=3)
        
        mock_listing_repo.get_by_id.side_effect = [inactive_listing, active_listing]
        mock_listing_repo.update.return_value = None
        
        result = await bulk_listing_ops._bulk_activate(listing_ids)
        
        assert result.successful_items == 2  # Both count as successful
        assert result.failed_items == 0
        assert len(result.warnings) > 0  # Warning about already active listing
        
        # Should only update the inactive listing
        mock_listing_repo.update.assert_called_once_with(1, {
            'status': ListingStatus.ACTIVE.value,
            'updated_at': result.completed_at  # Approximately
        })
    
    @pytest.mark.asyncio
    async def test_bulk_activate_fails_zero_quantity(self, bulk_listing_ops, mock_listing_repo):
        """Test bulk activation fails for zero quantity listings"""
        listing_ids = [1]
        
        # Mock inactive listing with zero quantity
        inactive_listing = Mock(id=1, status=ListingStatus.INACTIVE.value, quantity_available=0)
        mock_listing_repo.get_by_id.return_value = inactive_listing
        
        result = await bulk_listing_ops._bulk_activate(listing_ids)
        
        assert result.successful_items == 0
        assert result.failed_items == 1
        assert len(result.warnings) > 0
        assert any("Zero quantity" in warning for warning in result.warnings)
        
        # Should not call update
        mock_listing_repo.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_bulk_deactivate_calls_update_status(self, bulk_listing_ops):
        """Test bulk deactivate delegates to bulk update status"""
        listing_ids = [1, 2, 3]
        
        # Mock the _bulk_update_status method
        with pytest.mock.patch.object(bulk_listing_ops, '_bulk_update_status') as mock_update_status:
            mock_result = Mock()
            mock_update_status.return_value = mock_result
            
            result = await bulk_listing_ops._bulk_deactivate(listing_ids)
            
            assert result == mock_result
            mock_update_status.assert_called_once_with(listing_ids, ListingStatus.INACTIVE.value)
    
    @pytest.mark.asyncio
    async def test_execute_operation_delegates_correctly(self, bulk_listing_ops):
        """Test execute_operation delegates to correct methods"""
        listing_ids = [1, 2]
        
        # Test different operation types
        test_cases = [
            ('update_status', {'status': 'active'}, '_bulk_update_status'),
            ('update_price', {'price': 19.99}, '_bulk_update_price'),
            ('update_quantity', {'quantity': 5}, '_bulk_update_quantity'),
            ('bulk_activate', {}, '_bulk_activate'),
            ('bulk_deactivate', {}, '_bulk_deactivate')
        ]
        
        for operation_type, extra_data, expected_method in test_cases:
            operation_data = {'operation_type': operation_type, **extra_data}
            
            with pytest.mock.patch.object(bulk_listing_ops, expected_method) as mock_method:
                mock_result = Mock()
                mock_method.return_value = mock_result
                
                result = await bulk_listing_ops.execute_operation(listing_ids, operation_data)
                
                assert result == mock_result
                mock_method.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_operation_unsupported_type_fails(self, bulk_listing_ops):
        """Test execute_operation fails with unsupported operation type"""
        listing_ids = [1, 2]
        operation_data = {'operation_type': 'unsupported_operation'}
        
        with pytest.raises(ValidationException) as exc_info:
            await bulk_listing_ops.execute_operation(listing_ids, operation_data)
        
        assert "Unsupported operation type" in str(exc_info.value)