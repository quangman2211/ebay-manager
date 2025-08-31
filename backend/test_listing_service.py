import pytest
import json
from unittest.mock import Mock, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.listing_service import (
    ListingRepository, 
    ListingValidator, 
    PriceHistoryLogger, 
    ListingService,
    create_listing_service
)
from app.models import CSVData, User, Account


class TestListingValidator:
    """Test ListingValidator following Single Responsibility Principle"""

    def test_validate_price_valid(self):
        validator = ListingValidator()
        
        assert validator.validate_price("19.99") == True
        assert validator.validate_price("$19.99") == True
        assert validator.validate_price("1,299.99") == True
        assert validator.validate_price("0.01") == True

    def test_validate_price_invalid(self):
        validator = ListingValidator()
        
        assert validator.validate_price("0") == False
        assert validator.validate_price("-1") == False
        assert validator.validate_price("abc") == False
        assert validator.validate_price("") == False
        assert validator.validate_price(None) == False

    def test_validate_quantity_valid(self):
        validator = ListingValidator()
        
        assert validator.validate_quantity("0") == True
        assert validator.validate_quantity("10") == True
        assert validator.validate_quantity("999") == True

    def test_validate_quantity_invalid(self):
        validator = ListingValidator()
        
        assert validator.validate_quantity("-1") == False
        assert validator.validate_quantity("abc") == False
        assert validator.validate_quantity("1.5") == False
        assert validator.validate_quantity("") == False

    def test_validate_title_valid(self):
        validator = ListingValidator()
        
        assert validator.validate_title("Valid Title") == True
        assert validator.validate_title("A" * 255) == True

    def test_validate_title_invalid(self):
        validator = ListingValidator()
        
        assert validator.validate_title("") == False
        assert validator.validate_title("   ") == False
        assert validator.validate_title("A" * 256) == False
        assert validator.validate_title(None) == False

    def test_validate_status_valid(self):
        validator = ListingValidator()
        
        assert validator.validate_status("active") == True
        assert validator.validate_status("ACTIVE") == True
        assert validator.validate_status("inactive") == True
        assert validator.validate_status("ended") == True
        assert validator.validate_status("sold") == True

    def test_validate_status_invalid(self):
        validator = ListingValidator()
        
        assert validator.validate_status("invalid") == False
        assert validator.validate_status("") == False
        assert validator.validate_status("deleted") == False


class TestListingRepository:
    """Test ListingRepository following Repository Pattern"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def repository(self, mock_db):
        return ListingRepository(mock_db)

    def test_get_listing_by_id(self, repository, mock_db):
        # Mock data
        mock_listing = Mock(spec=CSVData)
        mock_listing.id = 1
        mock_listing.data_type = "listing"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_listing
        
        result = repository.get_listing_by_id(1)
        
        assert result == mock_listing
        mock_db.query.assert_called_once_with(CSVData)

    def test_get_listings_by_account(self, repository, mock_db):
        # Mock data
        mock_listings = [Mock(spec=CSVData) for _ in range(3)]
        for i, listing in enumerate(mock_listings):
            listing.id = i + 1
            listing.account_id = 1
            listing.data_type = "listing"
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_listings
        
        result = repository.get_listings_by_account(1)
        
        assert result == mock_listings
        assert len(result) == 3
        mock_db.query.assert_called_once_with(CSVData)

    def test_update_listing(self, repository, mock_db):
        mock_listing = Mock(spec=CSVData)
        
        result = repository.update_listing(mock_listing)
        
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_listing)
        assert result == mock_listing

    def test_get_user_accounts(self, repository, mock_db):
        mock_accounts = [Mock(spec=Account) for _ in range(2)]
        mock_accounts[0].id = 1
        mock_accounts[1].id = 2
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_accounts
        
        result = repository.get_user_accounts(1)
        
        assert result == [1, 2]
        mock_db.query.assert_called_once_with(Account)


class TestListingService:
    """Test ListingService following Dependency Inversion Principle"""

    @pytest.fixture
    def mock_repository(self):
        return Mock(spec=ListingRepository)

    @pytest.fixture
    def mock_validator(self):
        return Mock(spec=ListingValidator)

    @pytest.fixture
    def mock_price_logger(self):
        return Mock(spec=PriceHistoryLogger)

    @pytest.fixture
    def service(self, mock_repository, mock_validator, mock_price_logger):
        return ListingService(mock_repository, mock_validator, mock_price_logger)

    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 1
        user.role = "staff"
        return user

    @pytest.fixture
    def mock_admin_user(self):
        user = Mock(spec=User)
        user.id = 1
        user.role = "admin"
        return user

    @pytest.fixture
    def mock_listing(self):
        listing = Mock(spec=CSVData)
        listing.id = 1
        listing.account_id = 1
        listing.csv_row = {
            'Title': 'Test Product',
            'Current price': '19.99',
            'Available quantity': '10',
            'Status': 'active'
        }
        return listing

    def test_get_listing_success(self, service, mock_repository, mock_user, mock_listing):
        mock_repository.get_listing_by_id.return_value = mock_listing
        mock_repository.get_user_accounts.return_value = [1, 2]
        
        result = service.get_listing(1, mock_user)
        
        assert result == mock_listing
        mock_repository.get_listing_by_id.assert_called_once_with(1)
        mock_repository.get_user_accounts.assert_called_once_with(mock_user.id)

    def test_get_listing_permission_denied(self, service, mock_repository, mock_user, mock_listing):
        mock_repository.get_listing_by_id.return_value = mock_listing
        mock_repository.get_user_accounts.return_value = [2, 3]  # User doesn't have access to account 1
        
        with pytest.raises(PermissionError, match="Access denied"):
            service.get_listing(1, mock_user)

    def test_get_listing_admin_access(self, service, mock_repository, mock_admin_user, mock_listing):
        mock_repository.get_listing_by_id.return_value = mock_listing
        
        result = service.get_listing(1, mock_admin_user)
        
        assert result == mock_listing
        # Admin should not need account permission check
        mock_repository.get_user_accounts.assert_not_called()

    def test_update_listing_field_price(self, service, mock_repository, mock_validator, mock_price_logger, mock_user, mock_listing):
        mock_repository.get_listing_by_id.return_value = mock_listing
        mock_repository.get_user_accounts.return_value = [1]
        mock_validator.validate_price.return_value = True
        mock_repository.update_listing.return_value = mock_listing
        
        result = service.update_listing_field(1, 'price', '$29.99', mock_user)
        
        assert result == mock_listing
        mock_validator.validate_price.assert_called_once_with('$29.99')
        mock_price_logger.log_price_change.assert_called_once_with(1, '19.99', '$29.99', mock_user.id)
        assert mock_listing.csv_row['Current price'] == '29.99'
        mock_repository.update_listing.assert_called_once_with(mock_listing)

    def test_update_listing_field_quantity(self, service, mock_repository, mock_validator, mock_user, mock_listing):
        mock_repository.get_listing_by_id.return_value = mock_listing
        mock_repository.get_user_accounts.return_value = [1]
        mock_validator.validate_quantity.return_value = True
        mock_repository.update_listing.return_value = mock_listing
        
        result = service.update_listing_field(1, 'quantity', '20', mock_user)
        
        assert result == mock_listing
        mock_validator.validate_quantity.assert_called_once_with('20')
        assert mock_listing.csv_row['Available quantity'] == '20'
        mock_repository.update_listing.assert_called_once_with(mock_listing)

    def test_update_listing_field_invalid_price(self, service, mock_repository, mock_validator, mock_user, mock_listing):
        mock_repository.get_listing_by_id.return_value = mock_listing
        mock_repository.get_user_accounts.return_value = [1]
        mock_validator.validate_price.return_value = False
        
        with pytest.raises(ValueError, match="Invalid price format"):
            service.update_listing_field(1, 'price', 'invalid', mock_user)

    def test_update_listing_field_invalid_field(self, service, mock_repository, mock_user, mock_listing):
        mock_repository.get_listing_by_id.return_value = mock_listing
        mock_repository.get_user_accounts.return_value = [1]
        
        with pytest.raises(ValueError, match="Field 'invalid_field' is not allowed"):
            service.update_listing_field(1, 'invalid_field', 'value', mock_user)

    def test_update_listing_bulk_fields(self, service, mock_repository, mock_validator, mock_price_logger, mock_user, mock_listing):
        mock_repository.get_listing_by_id.return_value = mock_listing
        mock_repository.get_user_accounts.return_value = [1]
        mock_validator.validate_price.return_value = True
        mock_validator.validate_quantity.return_value = True
        mock_validator.validate_title.return_value = True
        mock_repository.update_listing.return_value = mock_listing
        
        updates = {
            'price': '$39.99',
            'quantity': '5',
            'title': 'Updated Title'
        }
        
        result = service.update_listing_bulk_fields(1, updates, mock_user)
        
        assert result == mock_listing
        assert mock_listing.csv_row['Current price'] == '39.99'
        assert mock_listing.csv_row['Available quantity'] == '5'
        assert mock_listing.csv_row['Title'] == 'Updated Title'
        mock_price_logger.log_price_change.assert_called_once()

    def test_get_listing_performance_metrics(self, service, mock_repository, mock_user, mock_listing):
        mock_listing.csv_row.update({
            'Sold quantity': '8',
            'Available quantity': '2',
            'Watchers': '15',
            'Start date': '2024-01-01'
        })
        mock_repository.get_listing_by_id.return_value = mock_listing
        mock_repository.get_user_accounts.return_value = [1]
        
        result = service.get_listing_performance_metrics(1, mock_user)
        
        assert 'sell_through_rate' in result
        assert 'watchers_count' in result
        assert 'stock_status' in result
        assert 'days_listed' in result
        assert 'price_competitiveness' in result
        
        assert result['sell_through_rate'] == 80.0  # 8/(8+2) * 100
        assert result['watchers_count'] == 15
        assert result['stock_status'] == 'low_stock'  # quantity <= 5


class TestCreateListingService:
    """Test factory function"""

    def test_create_listing_service(self):
        mock_db = Mock(spec=Session)
        
        service = create_listing_service(mock_db)
        
        assert isinstance(service, ListingService)
        assert isinstance(service.repository, ListingRepository)
        assert isinstance(service.validator, ListingValidator)
        assert isinstance(service.price_logger, PriceHistoryLogger)


# Integration tests
class TestListingServiceIntegration:
    """Integration tests for the complete workflow"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    def test_complete_listing_update_workflow(self, mock_db):
        """Test complete workflow from service creation to listing update"""
        # Setup mock data
        mock_listing = Mock(spec=CSVData)
        mock_listing.id = 1
        mock_listing.account_id = 1
        mock_listing.csv_row = {
            'Title': 'Original Title',
            'Current price': '19.99',
            'Available quantity': '10'
        }
        
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.role = "staff"
        
        mock_accounts = [Mock(spec=Account)]
        mock_accounts[0].id = 1
        
        # Setup mock behavior
        mock_db.query.return_value.filter.return_value.first.return_value = mock_listing
        mock_db.query.return_value.filter.return_value.all.return_value = mock_accounts
        
        # Create service
        service = create_listing_service(mock_db)
        
        # Test update
        result = service.update_listing_field(1, 'price', '29.99', mock_user)
        
        # Verify
        assert result == mock_listing
        assert mock_listing.csv_row['Current price'] == '29.99'
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_listing)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.services.listing_service", "--cov-report=term-missing"])