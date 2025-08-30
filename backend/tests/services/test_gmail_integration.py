"""
Test Gmail Integration Services
Following SOLID principles - Single Responsibility for testing Gmail integration
YAGNI compliance: Essential test cases only
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from app.services.email.gmail_service import GmailCredentialsManager, GmailService
from app.services.email.email_processor import EmailMessageParser, EbayEmailClassifier
from app.services.email.email_import_service import EmailImportService
from app.core.exceptions import AuthenticationError, ExternalServiceError


class TestGmailCredentialsManager:
    """Test Gmail credentials management"""
    
    def test_init(self):
        """Test credentials manager initialization"""
        manager = GmailCredentialsManager()
        
        assert manager.SCOPES == ['https://www.googleapis.com/auth/gmail.readonly']
        assert manager.credentials_path is not None
        assert manager.token_path is not None
    
    @patch('os.path.exists')
    @patch('pickle.load')
    @patch('builtins.open', new_callable=MagicMock)
    def test_get_credentials_existing_valid(self, mock_open, mock_pickle_load, mock_exists):
        """Test getting existing valid credentials"""
        # Setup mocks
        mock_exists.return_value = True
        mock_creds = Mock()
        mock_creds.valid = True
        mock_pickle_load.return_value = mock_creds
        
        manager = GmailCredentialsManager()
        result = manager.get_credentials(123)
        
        assert result == mock_creds
        mock_exists.assert_called_once()
        mock_open.assert_called()
    
    @patch('os.path.exists')
    def test_get_credentials_no_file(self, mock_exists):
        """Test getting credentials when file doesn't exist"""
        mock_exists.return_value = False
        
        manager = GmailCredentialsManager()
        result = manager.get_credentials(123)
        
        assert result is None
    
    @patch('os.path.exists')
    @patch('app.services.email.gmail_service.InstalledAppFlow')
    def test_initiate_oauth_flow_success(self, mock_flow_class, mock_exists):
        """Test successful OAuth flow initiation"""
        mock_exists.return_value = True
        mock_flow = Mock()
        mock_flow.authorization_url.return_value = ("http://auth.url", "state")
        mock_flow_class.from_client_secrets_file.return_value = mock_flow
        
        manager = GmailCredentialsManager()
        result = manager.initiate_oauth_flow(123)
        
        assert result == "http://auth.url"
        mock_flow.authorization_url.assert_called_once()
    
    @patch('os.path.exists')
    def test_initiate_oauth_flow_no_credentials_file(self, mock_exists):
        """Test OAuth flow initiation with missing credentials file"""
        mock_exists.return_value = False
        
        manager = GmailCredentialsManager()
        
        with pytest.raises(AuthenticationError):
            manager.initiate_oauth_flow(123)


class TestGmailService:
    """Test Gmail API service"""
    
    @pytest.fixture
    def mock_credentials_manager(self):
        return Mock(spec=GmailCredentialsManager)
    
    @pytest.fixture
    def gmail_service(self, mock_credentials_manager):
        return GmailService(mock_credentials_manager)
    
    def test_init(self, gmail_service):
        """Test Gmail service initialization"""
        assert gmail_service.service is None
        assert gmail_service.current_user_id is None
    
    def test_authenticate_success(self, gmail_service):
        """Test successful authentication"""
        mock_creds = Mock()
        gmail_service.credentials_manager.get_credentials.return_value = mock_creds
        
        with patch('app.services.email.gmail_service.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            result = gmail_service.authenticate(123)
            
            assert result is True
            assert gmail_service.service == mock_service
            assert gmail_service.current_user_id == 123
    
    def test_authenticate_no_credentials(self, gmail_service):
        """Test authentication with no credentials"""
        gmail_service.credentials_manager.get_credentials.return_value = None
        
        result = gmail_service.authenticate(123)
        
        assert result is False
    
    def test_list_messages_not_authenticated(self, gmail_service):
        """Test listing messages without authentication"""
        with pytest.raises(AuthenticationError):
            gmail_service.list_messages()
    
    def test_list_messages_success(self, gmail_service):
        """Test successful message listing"""
        mock_service = Mock()
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': '123'}, {'id': '456'}],
            'nextPageToken': 'token123',
            'resultSizeEstimate': 2
        }
        gmail_service.service = mock_service
        
        result = gmail_service.list_messages("test query", 10, "page_token")
        
        assert result['messages'] == [{'id': '123'}, {'id': '456'}]
        assert result['next_page_token'] == 'token123'
        assert result['result_size_estimate'] == 2
    
    def test_search_messages_with_filters(self, gmail_service):
        """Test message search with filters"""
        mock_service = Mock()
        mock_service.users().messages().list.return_value.execute.return_value = {
            'messages': [{'id': '123'}]
        }
        gmail_service.service = mock_service
        
        after_date = datetime.now() - timedelta(days=7)
        result = gmail_service.search_messages(
            from_email="test@example.com",
            subject_contains="order",
            after_date=after_date
        )
        
        # Check that the search was called with proper query
        mock_service.users().messages().list.assert_called_once()
        call_args = mock_service.users().messages().list.call_args
        assert 'q' in call_args[1]


class TestEmailMessageParser:
    """Test email message parsing"""
    
    @pytest.fixture
    def parser(self):
        return EmailMessageParser()
    
    def test_parse_gmail_message_basic(self, parser):
        """Test basic Gmail message parsing"""
        gmail_message = {
            'id': 'msg123',
            'threadId': 'thread123',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'John Doe <john@example.com>'},
                    {'name': 'To', 'value': 'jane@example.com'},
                    {'name': 'Date', 'value': 'Wed, 01 Jan 2020 12:00:00 +0000'}
                ],
                'body': {'data': 'VGVzdCBtZXNzYWdl'}  # Base64 for "Test message"
            },
            'snippet': 'Test message preview',
            'sizeEstimate': 1024,
            'labelIds': ['INBOX', 'UNREAD']
        }
        
        result = parser.parse_gmail_message(gmail_message)
        
        assert result['gmail_id'] == 'msg123'
        assert result['thread_id'] == 'thread123'
        assert result['subject'] == 'Test Subject'
        assert result['from_email'] == 'john@example.com'
        assert result['from_name'] == 'John Doe'
        assert result['to_email'] == 'jane@example.com'
        assert result['snippet'] == 'Test message preview'
        assert result['size_estimate'] == 1024
        assert result['labels'] == ['INBOX', 'UNREAD']
    
    def test_extract_email_address(self, parser):
        """Test email address extraction"""
        test_cases = [
            ('John Doe <john@example.com>', 'john@example.com'),
            ('jane@example.com', 'jane@example.com'),
            ('', ''),
            ('No Email Here', '')
        ]
        
        for input_str, expected in test_cases:
            result = parser._extract_email_address(input_str)
            assert result == expected
    
    def test_extract_name(self, parser):
        """Test name extraction"""
        test_cases = [
            ('John Doe <john@example.com>', 'John Doe'),
            ('"John Doe" <john@example.com>', 'John Doe'),
            ('jane@example.com', ''),
            ('', '')
        ]
        
        for input_str, expected in test_cases:
            result = parser._extract_name(input_str)
            assert result == expected


class TestEbayEmailClassifier:
    """Test eBay email classification"""
    
    @pytest.fixture
    def classifier(self):
        return EbayEmailClassifier()
    
    def test_is_ebay_related_domain(self, classifier):
        """Test eBay detection by domain"""
        email_data = {
            'from_email': 'noreply@ebay.com',
            'subject': 'Your order',
            'body_text': 'Thank you for your purchase'
        }
        
        result = classifier.is_ebay_related(email_data)
        assert result is True
    
    def test_is_ebay_related_keywords(self, classifier):
        """Test eBay detection by keywords"""
        email_data = {
            'from_email': 'user@gmail.com',
            'subject': 'eBay item question',
            'body_text': 'I have a question about the item you sold'
        }
        
        result = classifier.is_ebay_related(email_data)
        assert result is True
    
    def test_is_not_ebay_related(self, classifier):
        """Test non-eBay email detection"""
        email_data = {
            'from_email': 'friend@gmail.com',
            'subject': 'Weekend plans',
            'body_text': 'What are you doing this weekend?'
        }
        
        result = classifier.is_ebay_related(email_data)
        assert result is False
    
    def test_classify_message_type_order_inquiry(self, classifier):
        """Test message type classification"""
        email_data = {
            'subject': 'When will you ship my order?',
            'body_text': 'I am wondering about the shipping time for my recent purchase.'
        }
        
        result = classifier.classify_message_type(email_data)
        assert result == 'order_inquiry'
    
    def test_classify_message_type_return_request(self, classifier):
        """Test return request classification"""
        email_data = {
            'subject': 'Item not as described',
            'body_text': 'The item I received is damaged and I would like to return it for a refund.'
        }
        
        result = classifier.classify_message_type(email_data)
        assert result == 'return_request'
    
    def test_extract_ebay_item_id(self, classifier):
        """Test eBay item ID extraction"""
        email_data = {
            'subject': 'Question about item #1234567890123',
            'body_text': 'I have a question about your listing'
        }
        
        result = classifier.extract_ebay_item_id(email_data)
        assert result == '1234567890123'


class TestEmailImportService:
    """Test email import service"""
    
    @pytest.fixture
    def mock_gmail_service(self):
        return Mock(spec=GmailService)
    
    @pytest.fixture
    def mock_email_repository(self):
        return Mock()
    
    @pytest.fixture
    def mock_thread_repository(self):
        return Mock()
    
    @pytest.fixture
    def import_service(self, mock_gmail_service, mock_email_repository, mock_thread_repository):
        return EmailImportService(
            mock_gmail_service,
            mock_email_repository,
            mock_thread_repository
        )
    
    @pytest.mark.asyncio
    async def test_import_recent_emails_authentication_failed(self, import_service):
        """Test import with authentication failure"""
        import_service.gmail_service.authenticate.return_value = False
        
        with pytest.raises(ExternalServiceError):
            await import_service.import_recent_emails(123, 456)
    
    @pytest.mark.asyncio
    async def test_import_recent_emails_no_messages(self, import_service):
        """Test import with no messages found"""
        import_service.gmail_service.authenticate.return_value = True
        import_service.gmail_service.search_messages.return_value = {'messages': []}
        
        result = await import_service.import_recent_emails(123, 456)
        
        assert result['total_found'] == 0
        assert result['emails_imported'] == 0
    
    @pytest.mark.asyncio
    async def test_import_recent_emails_success(self, import_service):
        """Test successful email import"""
        # Setup mocks
        import_service.gmail_service.authenticate.return_value = True
        import_service.gmail_service.search_messages.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg2'}]
        }
        
        gmail_messages = [
            {
                'id': 'msg1',
                'threadId': 'thread1',
                'payload': {
                    'headers': [
                        {'name': 'Subject', 'value': 'eBay order question'},
                        {'name': 'From', 'value': 'buyer@example.com'},
                        {'name': 'To', 'value': 'seller@example.com'},
                        {'name': 'Date', 'value': 'Wed, 01 Jan 2020 12:00:00 +0000'}
                    ]
                },
                'snippet': 'Question about order',
                'sizeEstimate': 512
            }
        ]
        import_service.gmail_service.get_messages_batch.return_value = gmail_messages
        
        # Mock repository responses
        import_service.email_repository.get_by_gmail_id = AsyncMock(return_value=None)
        import_service.thread_repository.get_by_gmail_id = AsyncMock(return_value=None)
        
        mock_thread = Mock()
        mock_thread.id = 1
        import_service.thread_repository.create = AsyncMock(return_value=mock_thread)
        import_service.email_repository.create = AsyncMock()
        
        result = await import_service.import_recent_emails(123, 456, ebay_only=False)
        
        assert result['total_found'] == 2
        assert result['emails_imported'] >= 1
        assert len(result['errors']) == 0
    
    def test_should_require_response_true(self, import_service):
        """Test response requirement detection"""
        email_data = {
            'subject': 'Question about your item',
            'body_text': 'When will you ship this item? I need to know soon.'
        }
        
        result = import_service._should_require_response(email_data, True)
        assert result is True
    
    def test_should_require_response_false(self, import_service):
        """Test no response required detection"""
        email_data = {
            'subject': 'Payment confirmation',
            'body_text': 'Your payment has been processed successfully.'
        }
        
        result = import_service._should_require_response(email_data, True)
        assert result is False
    
    def test_determine_priority_urgent(self, import_service):
        """Test urgent priority detection"""
        email_data = {
            'subject': 'URGENT: Problem with order',
            'body_text': 'I need immediate assistance with my order.'
        }
        
        result = import_service._determine_priority(email_data, 'general_inquiry')
        assert result == 'urgent'
    
    def test_determine_priority_high(self, import_service):
        """Test high priority detection"""
        email_data = {
            'subject': 'Item not received',
            'body_text': 'I have not received my order and need help.'
        }
        
        result = import_service._determine_priority(email_data, 'shipping_inquiry')
        assert result == 'high'
    
    def test_determine_priority_normal(self, import_service):
        """Test normal priority detection"""
        email_data = {
            'subject': 'Question about shipping',
            'body_text': 'What shipping options do you offer?'
        }
        
        result = import_service._determine_priority(email_data, 'shipping_inquiry')
        assert result == 'normal'