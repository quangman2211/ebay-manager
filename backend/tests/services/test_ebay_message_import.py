"""
Test eBay Message Import Services
Following SOLID principles - Single Responsibility for testing eBay message import
YAGNI compliance: Essential test cases only
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import pandas as pd
import tempfile
import os

from app.services.csv_import.ebay_message_csv_detector import (
    EbayMessageFormatDetector, 
    EbayMessageValidator, 
    EbayMessageCSVFormat
)
from app.services.csv_import.ebay_message_transformer import (
    EbayMessageTransformer, 
    MessageDirection, 
    MessageType, 
    MessagePriority
)
from app.services.csv_import.ebay_message_import_service import EbayMessageImportService
from app.core.exceptions import ValidationError, NotFoundError


class TestEbayMessageFormatDetector:
    """Test eBay message CSV format detection"""
    
    @pytest.fixture
    def detector(self):
        return EbayMessageFormatDetector()
    
    def test_detect_buyer_messages_format(self, detector):
        """Test detection of buyer messages format"""
        df = pd.DataFrame(columns=[
            'Message ID', 'Seller Username', 'Item ID', 'Item Title',
            'Message Date', 'Message', 'Response Status', 'Order ID'
        ])
        
        format_type, confidence = detector.detect_format(df)
        
        assert format_type == EbayMessageCSVFormat.EBAY_BUYER_MESSAGES
        assert confidence > 0.7
    
    def test_detect_seller_messages_format(self, detector):
        """Test detection of seller messages format"""
        df = pd.DataFrame(columns=[
            'Message ID', 'Buyer Username', 'Item ID', 'Item Title',
            'Message Date', 'Message', 'Message Type'
        ])
        
        format_type, confidence = detector.detect_format(df)
        
        assert format_type == EbayMessageCSVFormat.EBAY_SELLER_MESSAGES
        assert confidence > 0.7
    
    def test_detect_all_messages_format(self, detector):
        """Test detection of all messages format"""
        df = pd.DataFrame(columns=[
            'Message ID', 'Sender', 'Recipient', 'Item ID',
            'Message Date', 'Message Content', 'Direction'
        ])
        
        format_type, confidence = detector.detect_format(df)
        
        assert format_type == EbayMessageCSVFormat.EBAY_ALL_MESSAGES
        assert confidence > 0.7
    
    def test_detect_unknown_format(self, detector):
        """Test detection of unknown format"""
        df = pd.DataFrame(columns=['Random Column 1', 'Random Column 2'])
        
        format_type, confidence = detector.detect_format(df)
        
        assert format_type == EbayMessageCSVFormat.UNKNOWN
        assert confidence == 0.0
    
    def test_validate_format_compatibility_valid(self, detector):
        """Test format compatibility validation - valid case"""
        df = pd.DataFrame(columns=[
            'Message ID', 'Seller Username', 'Item ID', 'Item Title',
            'Message Date', 'Message', 'Response Status'
        ])
        
        result = detector.validate_format_compatibility(df, EbayMessageCSVFormat.EBAY_BUYER_MESSAGES)
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_format_compatibility_invalid(self, detector):
        """Test format compatibility validation - invalid case"""
        df = pd.DataFrame(columns=['Message ID', 'Item ID'])  # Missing required columns
        
        result = detector.validate_format_compatibility(df, EbayMessageCSVFormat.EBAY_BUYER_MESSAGES)
        
        assert result['valid'] is False
        assert len(result['errors']) > 0


class TestEbayMessageValidator:
    """Test eBay message data validation"""
    
    @pytest.fixture
    def validator(self):
        return EbayMessageValidator()
    
    def test_validate_row_valid(self, validator):
        """Test valid row validation"""
        row_data = {
            'Message ID': 'MSG123456',
            'Item ID': '1234567890123',
            'Seller Username': 'test_seller',
            'Message': 'This is a test message',
            'Message Date': '2024-01-15 10:30:00'
        }
        
        errors = validator.validate_row(row_data, 0, EbayMessageCSVFormat.EBAY_BUYER_MESSAGES)
        
        assert len(errors) == 0
    
    def test_validate_message_id_missing(self, validator):
        """Test validation with missing message ID"""
        errors = validator._validate_message_id('')
        
        assert len(errors) == 1
        assert 'required' in errors[0].lower()
    
    def test_validate_message_id_too_short(self, validator):
        """Test validation with too short message ID"""
        errors = validator._validate_message_id('123')
        
        assert len(errors) == 1
        assert 'too short' in errors[0].lower()
    
    def test_validate_item_id_invalid_format(self, validator):
        """Test validation with invalid item ID format"""
        errors = validator._validate_item_id('invalid_item_id')
        
        assert len(errors) == 1
        assert 'invalid' in errors[0].lower()
    
    def test_validate_message_content_empty(self, validator):
        """Test validation with empty message content"""
        errors = validator._validate_message_content('')
        
        assert len(errors) == 1
        assert 'required' in errors[0].lower()
    
    def test_validate_message_content_too_long(self, validator):
        """Test validation with too long message content"""
        long_message = 'x' * 10001  # Exceeds 10,000 character limit
        
        errors = validator._validate_message_content(long_message)
        
        assert len(errors) == 1
        assert 'too long' in errors[0].lower()


class TestEbayMessageTransformer:
    """Test eBay message data transformation"""
    
    @pytest.fixture
    def transformer(self):
        return EbayMessageTransformer()
    
    def test_transform_buyer_message_row(self, transformer):
        """Test transformation of buyer message row"""
        row_data = {
            'Message ID': 'MSG123456',
            'Item ID': '1234567890123',
            'Item Title': 'Test Product',
            'Buyer Username': 'test_buyer',
            'Seller Username': 'test_seller',
            'Message': 'When will you ship this item?',
            'Message Date': '2024-01-15 10:30:00',
            'Order ID': 'ORDER123'
        }
        
        result = transformer.transform_row_to_message(
            row_data, 
            EbayMessageCSVFormat.EBAY_BUYER_MESSAGES,
            1,
            'test_seller'
        )
        
        assert result['ebay_message_id'] == 'MSG123456'
        assert result['item_id'] == '1234567890123'
        assert result['sender_username'] == 'test_buyer'
        assert result['recipient_username'] == 'test_seller'
        assert result['direction'] == MessageDirection.INCOMING
        assert result['message_type'] == MessageType.SHIPPING_INQUIRY
    
    def test_determine_direction_incoming(self, transformer):
        """Test direction determination - incoming message"""
        direction = transformer._determine_direction(
            'test_buyer', 'test_seller', 'test_seller', 
            {}, EbayMessageCSVFormat.EBAY_SELLER_MESSAGES
        )
        
        assert direction == MessageDirection.INCOMING
    
    def test_determine_direction_outgoing(self, transformer):
        """Test direction determination - outgoing message"""
        direction = transformer._determine_direction(
            'test_seller', 'test_buyer', 'test_seller',
            {}, EbayMessageCSVFormat.EBAY_SELLER_MESSAGES
        )
        
        assert direction == MessageDirection.OUTGOING
    
    def test_classify_shipping_inquiry(self, transformer):
        """Test message type classification - shipping inquiry"""
        message_type = transformer._classify_message_type("When will you ship my item?")
        
        assert message_type == MessageType.SHIPPING_INQUIRY
    
    def test_classify_return_request(self, transformer):
        """Test message type classification - return request"""
        message_type = transformer._classify_message_type("I want to return this damaged item")
        
        assert message_type == MessageType.RETURN_REQUEST
    
    def test_classify_payment_issue(self, transformer):
        """Test message type classification - payment issue"""
        message_type = transformer._classify_message_type("I'm having payment problems with this order")
        
        assert message_type == MessageType.PAYMENT_ISSUE
    
    def test_determine_priority_urgent(self, transformer):
        """Test priority determination - urgent"""
        priority = transformer._determine_priority("URGENT: Need immediate help!", MessageType.GENERAL_INQUIRY)
        
        assert priority == MessagePriority.URGENT
    
    def test_determine_priority_high(self, transformer):
        """Test priority determination - high"""
        priority = transformer._determine_priority("I have a problem with my order", MessageType.ORDER_ISSUE)
        
        assert priority == MessagePriority.HIGH
    
    def test_determine_priority_normal(self, transformer):
        """Test priority determination - normal"""
        priority = transformer._determine_priority("Can you provide more details?", MessageType.GENERAL_INQUIRY)
        
        assert priority == MessagePriority.NORMAL
    
    def test_extract_thread_context(self, transformer):
        """Test thread context extraction"""
        row_data = {
            'Item ID': '1234567890123',
            'Item Title': 'Test Product',
            'Sender': 'test_buyer',
            'Recipient': 'test_seller',
            'Order ID': 'ORDER123'
        }
        
        context = transformer.extract_thread_context(row_data, EbayMessageCSVFormat.EBAY_ALL_MESSAGES)
        
        assert context['item_id'] == '1234567890123'
        assert context['item_title'] == 'Test Product'
        assert context['sender_username'] == 'test_buyer'
        assert context['recipient_username'] == 'test_seller'
        assert context['order_id'] == 'ORDER123'


class TestEbayMessageImportService:
    """Test eBay message import service"""
    
    @pytest.fixture
    def mock_ebay_message_repo(self):
        return Mock()
    
    @pytest.fixture
    def mock_thread_repo(self):
        return Mock()
    
    @pytest.fixture
    def import_service(self, mock_ebay_message_repo, mock_thread_repo):
        return EbayMessageImportService(mock_ebay_message_repo, mock_thread_repo)
    
    def create_test_csv(self, data, filename='test.csv'):
        """Helper to create test CSV file"""
        df = pd.DataFrame(data)
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df.to_csv(temp_file.name, index=False)
        return temp_file.name
    
    @pytest.mark.asyncio
    async def test_validate_csv_format_valid(self, import_service):
        """Test CSV format validation - valid file"""
        test_data = [
            {
                'Message ID': 'MSG123',
                'Seller Username': 'test_seller',
                'Item ID': '1234567890123',
                'Item Title': 'Test Item',
                'Message Date': '2024-01-15',
                'Message': 'Test message',
                'Response Status': 'Pending'
            }
        ]
        
        temp_file = self.create_test_csv(test_data)
        
        try:
            result = await import_service.validate_csv_format(temp_file)
            
            assert result['valid'] is True
            assert result['detected_format'] == 'ebay_buyer_messages'
            assert result['confidence'] > 0.7
            assert result['row_count'] == 1
        
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_validate_csv_format_invalid(self, import_service):
        """Test CSV format validation - invalid file"""
        test_data = [{'Invalid Column': 'Invalid Data'}]
        
        temp_file = self.create_test_csv(test_data)
        
        try:
            result = await import_service.validate_csv_format(temp_file)
            
            assert result['valid'] is False
            assert result['detected_format'] == 'unknown'
            assert result['confidence'] == 0.0
        
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_import_messages_file_not_found(self, import_service):
        """Test import with non-existent file"""
        with pytest.raises(NotFoundError):
            await import_service.import_messages_from_csv(
                'non_existent_file.csv', 1, 'test_seller'
            )
    
    @pytest.mark.asyncio
    async def test_import_messages_success(self, import_service, mock_ebay_message_repo, mock_thread_repo):
        """Test successful message import"""
        # Setup test data
        test_data = [
            {
                'Message ID': 'MSG123',
                'Seller Username': 'test_seller',
                'Item ID': '1234567890123',
                'Item Title': 'Test Item',
                'Message Date': '2024-01-15 10:30:00',
                'Message': 'When will you ship?',
                'Response Status': 'Pending',
                'Buyer Username': 'test_buyer',
                'Order ID': 'ORDER123'
            }
        ]
        
        temp_file = self.create_test_csv(test_data)
        
        # Setup mocks
        mock_ebay_message_repo.get_by_ebay_id = AsyncMock(return_value=None)
        mock_ebay_message_repo.create = AsyncMock()
        
        mock_thread = Mock()
        mock_thread.id = 1
        mock_thread_repo.find_by_item_and_customer = AsyncMock(return_value=None)
        mock_thread_repo.create = AsyncMock(return_value=mock_thread)
        mock_thread_repo.update = AsyncMock()
        
        try:
            results = await import_service.import_messages_from_csv(
                temp_file, 1, 'test_seller', EbayMessageCSVFormat.EBAY_BUYER_MESSAGES
            )
            
            assert results['total_rows'] == 1
            assert results['messages_created'] == 1
            assert results['threads_created'] == 1
            assert len(results['errors']) == 0
            
            # Verify repository calls
            mock_ebay_message_repo.create.assert_called_once()
            mock_thread_repo.create.assert_called_once()
        
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_get_import_summary(self, import_service, mock_ebay_message_repo, mock_thread_repo):
        """Test getting import summary"""
        # Setup mocks
        mock_ebay_message_repo.get_counts_by_type = AsyncMock(return_value={
            'shipping_inquiry': 5,
            'general_inquiry': 3
        })
        mock_thread_repo.get_counts_by_status = AsyncMock(return_value={
            'open': 4,
            'responded': 4
        })
        mock_ebay_message_repo.get_pending_response_count = AsyncMock(return_value=2)
        
        result = await import_service.get_import_summary(1, 30)
        
        assert result['total_messages'] == 8
        assert result['message_counts_by_type']['shipping_inquiry'] == 5
        assert result['thread_counts_by_status']['open'] == 4
        assert result['pending_responses'] == 2
        assert result['period_days'] == 30