"""
Test suite for Universal Upload Strategy Pattern
Testing SOLID principles implementation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import pandas as pd

from app.interfaces.upload_strategy import (
    IUploadStrategy, UploadContext, UploadResult, UploadSourceType
)
from app.strategies.ebay_csv_strategy import EBayCSVStrategy
from app.services.upload_service import UniversalUploadService, StrategyFactory


class TestUploadInterfaces:
    """Test the upload strategy interfaces"""
    
    def test_upload_context_creation(self):
        """Test UploadContext dataclass"""
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=2,
            filename="test.csv"
        )
        
        assert context.account_id == 1
        assert context.data_type == "order"
        assert context.user_id == 2
        assert context.filename == "test.csv"
    
    def test_upload_result_creation(self):
        """Test UploadResult dataclass"""
        result = UploadResult(
            success=True,
            message="Success",
            inserted_count=10,
            duplicate_count=2
        )
        
        assert result.success == True
        assert result.message == "Success"
        assert result.inserted_count == 10
        assert result.duplicate_count == 2
    
    def test_upload_source_types(self):
        """Test UploadSourceType enum"""
        assert UploadSourceType.CSV_FILE.value == "csv_file"
        assert UploadSourceType.GOOGLE_SHEETS.value == "google_sheets"
        assert UploadSourceType.HTTP_URL.value == "http_url"


class TestEBayCSVStrategy:
    """Test eBay CSV Strategy implementation"""
    
    @pytest.fixture
    def strategy(self):
        return EBayCSVStrategy()
    
    @pytest.fixture
    def sample_order_csv(self):
        return '''
"Order Number","Item Number","Item Title","Buyer Username","Buyer Name","Sale Date","Sold For","Quantity"
"12345","98765","Test Item","buyer123","John Doe","2024-01-01","99.99","1"
"12346","98766","Another Item","buyer456","Jane Smith","2024-01-02","149.99","2"
Seller ID : testebayseller
'''
    
    @pytest.fixture
    def sample_listing_csv(self):
        return '''
"Item number","Title","Available quantity","Current price","Sold quantity","Format"
"98765","Test Item","10","99.99","5","Fixed Price"
"98766","Another Item","20","149.99","8","Auction"
'''
    
    def test_supported_types(self, strategy):
        """Test strategy supports correct source types"""
        assert UploadSourceType.CSV_FILE in strategy.supported_types
        assert len(strategy.supported_types) == 1
    
    def test_max_file_size(self, strategy):
        """Test max file size property"""
        assert strategy.max_file_size == 50 * 1024 * 1024  # 50MB
    
    def test_validate_order_csv_success(self, strategy, sample_order_csv):
        """Test successful order CSV validation"""
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1
        )
        
        is_valid, errors = strategy.validate(sample_order_csv, context)
        
        assert is_valid == True
        assert len(errors) == 0
    
    def test_validate_listing_csv_success(self, strategy, sample_listing_csv):
        """Test successful listing CSV validation"""
        context = UploadContext(
            account_id=1,
            data_type="listing",
            user_id=1
        )
        
        is_valid, errors = strategy.validate(sample_listing_csv, context)
        
        assert is_valid == True
        assert len(errors) == 0
    
    def test_validate_invalid_csv(self, strategy):
        """Test validation with invalid CSV"""
        invalid_csv = "This is not a valid CSV"
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1
        )
        
        is_valid, errors = strategy.validate(invalid_csv, context)
        
        assert is_valid == False
        assert len(errors) > 0
    
    def test_detect_account_info_from_content(self, strategy, sample_order_csv):
        """Test detecting eBay seller ID from CSV content"""
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1
        )
        
        username = strategy.detect_account_info(sample_order_csv, context)
        
        assert username == "testebayseller"
    
    def test_detect_account_info_from_filename(self, strategy):
        """Test detecting username from filename"""
        csv_without_seller = '"Order Number"\n"12345"'
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1,
            filename="selleruser_orders.csv"
        )
        
        username = strategy.detect_account_info(csv_without_seller, context)
        
        assert username == "selleruser"
    
    def test_parse_orders(self, strategy, sample_order_csv):
        """Test parsing order data"""
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1
        )
        
        parsed_data = strategy.parse(sample_order_csv, context)
        
        assert len(parsed_data) == 2
        assert parsed_data[0]['order_number'] == "12345"
        assert parsed_data[0]['item_number'] == "98765"
        assert parsed_data[0]['buyer_username'] == "buyer123"
    
    def test_parse_listings(self, strategy, sample_listing_csv):
        """Test parsing listing data"""
        context = UploadContext(
            account_id=1,
            data_type="listing",
            user_id=1
        )
        
        parsed_data = strategy.parse(sample_listing_csv, context)
        
        assert len(parsed_data) == 2
        assert parsed_data[0]['item_number'] == "98765"
        assert parsed_data[0]['title'] == "Test Item"
        assert parsed_data[0]['available_quantity'] == "10"
    
    def test_process_complete_flow(self, strategy, sample_order_csv):
        """Test complete processing flow"""
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1
        )
        
        result = strategy.process(sample_order_csv, context)
        
        assert result.success == True
        assert result.total_records == 2
        assert result.detected_username == "testebayseller"
        assert len(result.processed_data) == 2


class TestStrategyFactory:
    """Test Strategy Factory pattern"""
    
    def test_create_csv_strategy(self):
        """Test factory creates correct strategy"""
        strategy = StrategyFactory.create_strategy(UploadSourceType.CSV_FILE)
        
        assert isinstance(strategy, EBayCSVStrategy)
    
    def test_create_unknown_strategy_raises_error(self):
        """Test factory raises error for unknown strategy"""
        with pytest.raises(ValueError) as exc_info:
            StrategyFactory.create_strategy(UploadSourceType.FTP)
        
        assert "No strategy available" in str(exc_info.value)
    
    def test_register_new_strategy(self):
        """Test registering a new strategy"""
        # Create a mock strategy
        class MockStrategy(IUploadStrategy):
            def validate(self, content, context):
                return True, []
            
            def parse(self, content, context):
                return []
            
            def detect_account_info(self, content, context):
                return None
            
            def process(self, content, context):
                return UploadResult(success=True, message="Mock")
            
            @property
            def supported_types(self):
                return [UploadSourceType.FTP]
            
            @property
            def max_file_size(self):
                return 1024
        
        # Register the strategy
        StrategyFactory.register_strategy(UploadSourceType.FTP, MockStrategy)
        
        # Create instance
        strategy = StrategyFactory.create_strategy(UploadSourceType.FTP)
        
        assert isinstance(strategy, MockStrategy)


class TestUniversalUploadService:
    """Test Universal Upload Service"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        return UniversalUploadService(mock_db)
    
    @pytest.fixture
    def sample_csv(self):
        return '''
"Order Number","Item Number","Item Title","Buyer Username","Buyer Name","Sale Date","Sold For","Quantity"
"12345","98765","Test Item","buyer123","John Doe","2024-01-01","99.99","1"
'''
    
    def test_process_upload_success(self, service, sample_csv):
        """Test successful upload processing"""
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1,
            filename="test.csv"
        )
        
        result = service.process_upload(sample_csv, UploadSourceType.CSV_FILE, context)
        
        assert result.success == True
        assert result.total_records == 1
    
    def test_detect_source_type_csv(self, service):
        """Test detecting CSV source type from file"""
        mock_file = Mock()
        mock_file.filename = "test.csv"
        
        source_type = service.detect_source_type(mock_file)
        
        assert source_type == UploadSourceType.CSV_FILE
    
    def test_detect_source_type_excel(self, service):
        """Test detecting Excel source type from file"""
        mock_file = Mock()
        mock_file.filename = "test.xlsx"
        
        source_type = service.detect_source_type(mock_file)
        
        assert source_type == UploadSourceType.EXCEL_FILE
    
    def test_get_account_suggestions(self, service, sample_csv, mock_db):
        """Test getting account suggestions"""
        # Setup mock account
        mock_account = Mock()
        mock_account.id = 1
        mock_account.name = "Test Account"
        mock_account.ebay_username = "testuser"
        mock_account.platform_username = "testebayseller"
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_account]
        
        context = UploadContext(
            account_id=0,
            data_type="order",
            user_id=1,
            filename="test.csv"
        )
        
        suggestions = service.get_account_suggestions(
            sample_csv + "\nSeller ID : testebayseller",
            UploadSourceType.CSV_FILE,
            context
        )
        
        assert suggestions['detected_username'] == "testebayseller"
        assert suggestions['total_suggestions'] >= 0
    
    def test_file_size_limit_check(self, service, mock_db):
        """Test file size limit validation"""
        large_content = "x" * (60 * 1024 * 1024)  # 60MB
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1
        )
        
        result = service.process_upload(large_content, UploadSourceType.CSV_FILE, context)
        
        assert result.success == False
        assert "size exceeds maximum" in result.message


# Integration test
class TestIntegration:
    """Integration tests for the complete upload flow"""
    
    @pytest.fixture
    def complete_csv(self):
        return '''
"Order Number","Item Number","Item Title","Buyer Username","Buyer Name","Sale Date","Sold For","Quantity"
"12345","98765","Test Item","buyer123","John Doe","2024-01-01","99.99","1"
"12346","98766","Another Item","buyer456","Jane Smith","2024-01-02","149.99","2"
"12347","98767","Third Item","buyer789","Bob Johnson","2024-01-03","79.99","1"
Seller ID : integrationtest
'''
    
    def test_end_to_end_upload_flow(self, complete_csv):
        """Test complete upload flow from file to database"""
        # Create mock database
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Create service
        service = UniversalUploadService(mock_db)
        
        # Create context
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1,
            filename="integration_orders.csv"
        )
        
        # Process upload
        result = service.process_upload(complete_csv, UploadSourceType.CSV_FILE, context)
        
        # Verify results
        assert result.success == True
        assert result.total_records == 3
        assert result.detected_username == "integrationtest"
        assert result.message == "CSV processed successfully"
        
        # Verify database calls were made
        assert mock_db.add.called
        assert mock_db.commit.called