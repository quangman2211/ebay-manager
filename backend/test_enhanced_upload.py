"""
Enhanced Upload Service Tests - Comprehensive Coverage
Tests for SOLID-compliant enhanced upload functionality
"""
import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.upload_service import UniversalUploadService
from app.services.enhanced_upload_service import EnhancedUploadService
from app.services.upload_progress_simple import SimpleProgressTracker, UploadState
from app.utils.simple_error_handler import SimpleErrorHandler, SimpleError
from app.interfaces.upload_strategy import UploadContext, UploadSourceType, UploadResult
from app.models import Account, CSVData, OrderStatus, User
from app.schemas import DataType


class TestSimpleProgressTracker:
    """Test Simple Progress Tracker - YAGNI Compliant"""
    
    def setup_method(self):
        self.tracker = SimpleProgressTracker()
        
    def test_create_upload(self):
        upload_id = self.tracker.create_upload("test.csv")
        assert upload_id is not None
        assert len(upload_id) == 36  # UUID format
        
        progress = self.tracker.get_progress(upload_id)
        assert progress is not None
        assert progress.filename == "test.csv"
        assert progress.state == UploadState.PROCESSING
        assert progress.message == "Processing upload..."
        assert progress.progress_percent == 0.0
        
    def test_update_progress(self):
        upload_id = self.tracker.create_upload("test.csv")
        self.tracker.update_progress(upload_id, 50.0, "Half complete")
        
        progress = self.tracker.get_progress(upload_id)
        assert progress.progress_percent == 50.0
        assert progress.message == "Half complete"
        
    def test_update_nonexistent_upload(self):
        # Should not crash on nonexistent upload
        self.tracker.update_progress("nonexistent", 50.0, "test")
        # No assertion needed - should not raise exception
        
    def test_complete_upload_success(self):
        upload_id = self.tracker.create_upload("test.csv")
        self.tracker.complete_upload(upload_id, True, "Success!")
        
        progress = self.tracker.get_progress(upload_id)
        assert progress.state == UploadState.COMPLETED
        assert progress.message == "Success!"
        assert progress.progress_percent == 100.0
        
    def test_complete_upload_failure(self):
        upload_id = self.tracker.create_upload("test.csv")
        self.tracker.complete_upload(upload_id, False, "Failed!")
        
        progress = self.tracker.get_progress(upload_id)
        assert progress.state == UploadState.FAILED
        assert progress.message == "Failed!"
        assert progress.progress_percent == 100.0
        
    def test_complete_nonexistent_upload(self):
        # Should not crash on nonexistent upload
        self.tracker.complete_upload("nonexistent", True, "Success")
        # No assertion needed - should not raise exception
        
    def test_get_nonexistent_progress(self):
        progress = self.tracker.get_progress("nonexistent")
        assert progress is None


class TestSimpleErrorHandler:
    """Test Simple Error Handler - YAGNI Compliant"""
    
    def test_create_error_file_too_large(self):
        error = SimpleErrorHandler.create_error('FILE_TOO_LARGE')
        assert error.code == 'FILE_TOO_LARGE'
        assert error.message == 'File size exceeds 50MB limit'
        assert len(error.suggestions) == 2
        assert 'Try splitting the CSV file' in error.suggestions[0]
        
    def test_create_error_invalid_csv(self):
        error = SimpleErrorHandler.create_error('INVALID_CSV_FORMAT')
        assert error.code == 'INVALID_CSV_FORMAT'
        assert error.message == 'Invalid CSV file format'
        assert len(error.suggestions) == 2  # Actual number of suggestions
        
    def test_create_error_with_custom_message(self):
        error = SimpleErrorHandler.create_error('FILE_TOO_LARGE', 'Custom message')
        assert error.code == 'FILE_TOO_LARGE'
        assert error.message == 'Custom message'
        assert len(error.suggestions) == 2  # Still has suggestions
        
    def test_create_error_unknown_code(self):
        error = SimpleErrorHandler.create_error('UNKNOWN_ERROR')
        assert error.code == 'UNKNOWN_ERROR'
        assert error.message == 'Unknown error occurred'
        assert len(error.suggestions) == 1
        assert 'Please try again' in error.suggestions[0]
        
    def test_format_error_response(self):
        error = SimpleError('TEST_CODE', 'Test message', ['Suggestion 1', 'Suggestion 2'])
        response = SimpleErrorHandler.format_error_response(error)
        
        assert response['success'] is False
        assert response['error']['code'] == 'TEST_CODE'
        assert response['error']['message'] == 'Test message'
        assert len(response['error']['suggestions']) == 2


class TestUniversalUploadService:
    """Test Universal Upload Service - SOLID Compliant"""
    
    def setup_method(self):
        self.mock_db = Mock(spec=Session)
        self.service = UniversalUploadService(self.mock_db)
        
    def test_init(self):
        # Dependency Injection test
        assert self.service.db == self.mock_db
        
    def test_detect_source_type_csv(self):
        mock_file = Mock()
        mock_file.filename = "test.csv"
        
        source_type = self.service.detect_source_type(mock_file)
        assert source_type == UploadSourceType.CSV
        
    def test_detect_source_type_unknown(self):
        mock_file = Mock()
        mock_file.filename = "test.txt"
        
        source_type = self.service.detect_source_type(mock_file)
        assert source_type == UploadSourceType.UNKNOWN
        
    def test_detect_source_type_no_filename(self):
        mock_file = Mock()
        mock_file.filename = None
        
        source_type = self.service.detect_source_type(mock_file)
        assert source_type == UploadSourceType.UNKNOWN
        
    @patch('app.services.upload_service.CSVProcessor')
    def test_process_upload_success(self, mock_csv_processor):
        # Setup account mock
        mock_account = Mock()
        mock_account.id = 1
        mock_account.account_type = "ebay"
        mock_account.platform_username = None
        mock_account.name = "Test Account"
        
        # Setup database query mock chain
        def side_effect_query(*args):
            if args[0] is Account:
                return Mock(**{'filter.return_value.first.return_value': mock_account})
            else:
                # For CSVData queries (existing record check)
                return Mock(**{'filter.return_value.first.return_value': None})
        
        self.mock_db.query.side_effect = side_effect_query
        
        # Setup CSV processor mocks
        mock_csv_processor.detect_platform_username.return_value = "test_user"
        mock_csv_processor.process_csv_file.return_value = ([{"Order Number": "12345"}], [])
        mock_csv_processor.check_duplicates.return_value = []
        mock_csv_processor.extract_item_id.return_value = "12345"
        
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1,
            filename="test.csv"
        )
        
        result = self.service.process_upload("test content", UploadSourceType.CSV, context)
        
        assert result.success is True
        assert result.inserted_count == 1
        assert result.duplicate_count == 0
        assert result.total_records == 1
        assert result.detected_username == "test_user"
        
    def test_process_upload_invalid_data_type(self):
        context = UploadContext(
            account_id=1,
            data_type="invalid",
            user_id=1,
            filename="test.csv"
        )
        
        result = self.service.process_upload("test content", UploadSourceType.CSV, context)
        
        assert result.success is False
        assert "Invalid data_type" in result.message
        
    def test_process_upload_account_not_found(self):
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        context = UploadContext(
            account_id=999,
            data_type="order",
            user_id=1,
            filename="test.csv"
        )
        
        result = self.service.process_upload("test content", UploadSourceType.CSV, context)
        
        assert result.success is False
        assert result.message == "Account not found"
        
    @patch('app.services.upload_service.CSVProcessor')
    def test_process_upload_csv_errors(self, mock_csv_processor):
        # Setup account mock
        mock_account = Mock()
        mock_account.id = 1
        mock_account.account_type = "ebay"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_account
        
        mock_csv_processor.detect_platform_username.return_value = None
        mock_csv_processor.process_csv_file.return_value = ([], ["CSV error"])
        
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1,
            filename="test.csv"
        )
        
        result = self.service.process_upload("test content", UploadSourceType.CSV, context)
        
        assert result.success is False
        assert "CSV processing errors" in result.message


class TestEnhancedUploadService:
    """Test Enhanced Upload Service - SOLID Compliant"""
    
    def setup_method(self):
        self.mock_upload_service = Mock(spec=UniversalUploadService)
        self.enhanced_service = EnhancedUploadService(self.mock_upload_service)
        
    def test_init_dependency_injection(self):
        # Test Dependency Inversion
        assert self.enhanced_service.upload_service == self.mock_upload_service
        
    @patch('app.services.enhanced_upload_service.progress_tracker')
    def test_upload_with_progress_success(self, mock_progress_tracker):
        # Setup mocks
        mock_upload_id = str(uuid.uuid4())
        mock_progress_tracker.create_upload.return_value = mock_upload_id
        
        mock_result = UploadResult(
            success=True,
            message="Upload successful",
            inserted_count=10,
            duplicate_count=2,
            total_records=12,
            detected_username="test_user"
        )
        self.mock_upload_service.process_upload.return_value = mock_result
        
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1,
            filename="test.csv"
        )
        
        result = self.enhanced_service.upload_with_progress(
            content="test content",
            filename="test.csv",
            source_type=UploadSourceType.CSV,
            context=context
        )
        
        assert result['success'] is True
        assert result['upload_id'] == mock_upload_id
        assert result['inserted_count'] == 10
        assert result['duplicate_count'] == 2
        assert result['total_records'] == 12
        assert result['detected_username'] == "test_user"
        
        # Verify progress tracking calls
        mock_progress_tracker.create_upload.assert_called_once_with("test.csv")
        mock_progress_tracker.update_progress.assert_called_with(mock_upload_id, 75, "Processing data...")
        mock_progress_tracker.complete_upload.assert_called_with(
            mock_upload_id, True, "Successfully processed 12 records"
        )
        
    @patch('app.services.enhanced_upload_service.progress_tracker')
    def test_upload_with_progress_file_too_large(self, mock_progress_tracker):
        mock_upload_id = str(uuid.uuid4())
        mock_progress_tracker.create_upload.return_value = mock_upload_id
        
        # Create content larger than 50MB
        large_content = "x" * (51 * 1024 * 1024)  # 51MB
        
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1,
            filename="large.csv"
        )
        
        result = self.enhanced_service.upload_with_progress(
            content=large_content,
            filename="large.csv",
            source_type=UploadSourceType.CSV,
            context=context
        )
        
        assert result['success'] is False
        assert result['error']['code'] == 'FILE_TOO_LARGE'
        mock_progress_tracker.complete_upload.assert_called_with(
            mock_upload_id, False, 'File size exceeds 50MB limit'
        )
        
    @patch('app.services.enhanced_upload_service.progress_tracker')
    def test_upload_with_progress_upload_failure(self, mock_progress_tracker):
        mock_upload_id = str(uuid.uuid4())
        mock_progress_tracker.create_upload.return_value = mock_upload_id
        
        mock_result = UploadResult(
            success=False,
            message="Upload failed",
            errors=["Error 1", "Error 2"]
        )
        self.mock_upload_service.process_upload.return_value = mock_result
        
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1,
            filename="test.csv"
        )
        
        result = self.enhanced_service.upload_with_progress(
            content="test content",
            filename="test.csv",
            source_type=UploadSourceType.CSV,
            context=context
        )
        
        assert result['success'] is False
        assert result['message'] == "Upload failed"
        assert result['errors'] == ["Error 1", "Error 2"]
        
    @patch('app.services.enhanced_upload_service.progress_tracker')
    def test_upload_with_progress_exception(self, mock_progress_tracker):
        mock_upload_id = str(uuid.uuid4())
        mock_progress_tracker.create_upload.return_value = mock_upload_id
        
        # Mock service to raise exception
        self.mock_upload_service.process_upload.side_effect = Exception("Service error")
        
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1,
            filename="test.csv"
        )
        
        result = self.enhanced_service.upload_with_progress(
            content="test content",
            filename="test.csv",
            source_type=UploadSourceType.CSV,
            context=context
        )
        
        assert result['success'] is False
        assert "Processing failed: Service error" in result['error']['message']
        mock_progress_tracker.complete_upload.assert_called()
        
    @patch('app.services.enhanced_upload_service.progress_tracker')
    def test_get_upload_progress_success(self, mock_progress_tracker):
        mock_progress = Mock()
        mock_progress.upload_id = "test-id"
        mock_progress.filename = "test.csv"
        mock_progress.state = UploadState.PROCESSING
        mock_progress.message = "Processing..."
        mock_progress.progress_percent = 50.0
        mock_progress.started_at = datetime.now()
        
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        result = self.enhanced_service.get_upload_progress("test-id")
        
        assert result['success'] is True
        assert result['upload_id'] == "test-id"
        assert result['filename'] == "test.csv"
        assert result['state'] == 'processing'
        assert result['message'] == "Processing..."
        assert result['progress_percent'] == 50.0
        
    @patch('app.services.enhanced_upload_service.progress_tracker')
    def test_get_upload_progress_not_found(self, mock_progress_tracker):
        mock_progress_tracker.get_progress.return_value = None
        
        result = self.enhanced_service.get_upload_progress("nonexistent")
        
        assert result['success'] is False
        assert result['error'] == 'Upload not found'


class TestUploadResult:
    """Test UploadResult dataclass"""
    
    def test_upload_result_default_values(self):
        result = UploadResult(success=True, message="Test")
        assert result.success is True
        assert result.message == "Test"
        assert result.errors == []  # Default empty list
        assert result.inserted_count == 0
        assert result.duplicate_count == 0
        assert result.total_records == 0
        assert result.detected_username is None
        
    def test_upload_result_with_values(self):
        result = UploadResult(
            success=True,
            message="Success",
            errors=["Error1"],
            inserted_count=5,
            duplicate_count=2,
            total_records=7,
            detected_username="test_user"
        )
        assert result.inserted_count == 5
        assert result.duplicate_count == 2
        assert result.total_records == 7
        assert result.detected_username == "test_user"
        assert result.errors == ["Error1"]


class TestUploadContext:
    """Test UploadContext dataclass"""
    
    def test_upload_context_required_fields(self):
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=2
        )
        assert context.account_id == 1
        assert context.data_type == "order"
        assert context.user_id == 2
        assert context.filename is None  # Optional field
        
    def test_upload_context_with_filename(self):
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=2,
            filename="test.csv"
        )
        assert context.filename == "test.csv"


# Integration Tests
class TestIntegrationEnhancedUpload:
    """Integration tests for enhanced upload flow"""
    
    @patch('app.services.upload_service.CSVProcessor')
    @patch('app.services.enhanced_upload_service.progress_tracker')
    def test_full_enhanced_upload_flow(self, mock_progress_tracker, mock_csv_processor):
        # Setup database mocks
        mock_db = Mock(spec=Session)
        mock_account = Mock()
        mock_account.id = 1
        mock_account.account_type = "ebay"
        mock_account.platform_username = None
        mock_account.name = "Test Account"
        
        # Setup database query mock chain
        def side_effect_query(*args):
            if args[0] is Account:
                return Mock(**{'filter.return_value.first.return_value': mock_account})
            else:
                # For CSVData queries (existing record check)
                return Mock(**{'filter.return_value.first.return_value': None})
        
        mock_db.query.side_effect = side_effect_query
        
        # Setup CSV processor mocks
        mock_csv_processor.detect_platform_username.return_value = "test_user"
        mock_csv_processor.process_csv_file.return_value = ([{"Order Number": "12345"}], [])
        mock_csv_processor.check_duplicates.return_value = []
        mock_csv_processor.extract_item_id.return_value = "12345"
        
        # Setup progress tracker mocks
        mock_upload_id = str(uuid.uuid4())
        mock_progress_tracker.create_upload.return_value = mock_upload_id
        
        # Create services
        upload_service = UniversalUploadService(mock_db)
        enhanced_service = EnhancedUploadService(upload_service)
        
        # Execute upload
        context = UploadContext(
            account_id=1,
            data_type="order",
            user_id=1,
            filename="test.csv"
        )
        
        result = enhanced_service.upload_with_progress(
            content="test content",
            filename="test.csv",
            source_type=UploadSourceType.CSV,
            context=context
        )
        
        # Verify results
        assert result['success'] is True
        assert result['upload_id'] == mock_upload_id
        assert result['detected_username'] == "test_user"
        
        # Verify all services were called correctly
        mock_progress_tracker.create_upload.assert_called_once_with("test.csv")
        mock_csv_processor.process_csv_file.assert_called_once()
        mock_csv_processor.detect_platform_username.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])