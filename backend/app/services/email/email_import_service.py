"""
Email import service for coordinating Gmail email import process
Following SOLID principles - Single Responsibility for import coordination
YAGNI compliance: Simple import logic, no complex synchronization
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.email.gmail_service import GmailService
from app.services.email.email_processor import EmailMessageParser, EbayEmailClassifier
from app.repositories.communication_repository import EmailRepository, EmailThreadRepository
from app.schemas.communication import EmailCreate, EmailThreadCreate
from app.core.exceptions import ExternalServiceError, ValidationError


class EmailImportService:
    """
    SOLID: Single Responsibility - Coordinate email import process
    YAGNI: Simple import logic, no complex synchronization
    """
    
    def __init__(
        self,
        gmail_service: GmailService,
        email_repository: EmailRepository,
        thread_repository: EmailThreadRepository
    ):
        self.gmail_service = gmail_service
        self.email_repository = email_repository
        self.thread_repository = thread_repository
        self.parser = EmailMessageParser()
        self.classifier = EbayEmailClassifier()
    
    async def import_recent_emails(
        self,
        user_id: int,
        account_id: int,
        days_back: int = 7,
        max_emails: int = 500,
        ebay_only: bool = True
    ) -> Dict[str, Any]:
        """
        Import recent emails from Gmail
        YAGNI: Simple date-based import, no complex incremental sync
        """
        # Authenticate with Gmail
        authenticated = self.gmail_service.authenticate(user_id)
        if not authenticated:
            raise ExternalServiceError("Gmail authentication failed")
        
        results = {
            'total_found': 0,
            'threads_created': 0,
            'threads_updated': 0,
            'emails_imported': 0,
            'emails_skipped': 0,
            'errors': []
        }
        
        try:
            # Search for recent emails
            after_date = datetime.utcnow() - timedelta(days=days_back)
            
            search_result = self.gmail_service.search_messages(
                after_date=after_date,
                max_results=max_emails
            )
            
            messages = search_result.get('messages', [])
            results['total_found'] = len(messages)
            
            if not messages:
                return results
            
            # Get message IDs
            message_ids = [msg['id'] for msg in messages]
            
            # Fetch messages in batch
            gmail_messages = self.gmail_service.get_messages_batch(message_ids)
            
            # Process each message
            for gmail_message in gmail_messages:
                try:
                    await self._process_single_message(
                        gmail_message, account_id, results, ebay_only
                    )
                except Exception as e:
                    results['errors'].append(f"Failed to process message: {str(e)}")
            
        except Exception as e:
            results['errors'].append(f"Import failed: {str(e)}")
        
        return results
    
    async def _process_single_message(
        self,
        gmail_message: Dict[str, Any],
        account_id: int,
        results: Dict[str, Any],
        ebay_only: bool
    ):
        """Process a single Gmail message"""
        # Parse message
        email_data = self.parser.parse_gmail_message(gmail_message)
        
        # Check if eBay-related (if filtering enabled)
        if ebay_only:
            if not self.classifier.is_ebay_related(email_data):
                results['emails_skipped'] += 1
                return
        
        # Check if email already exists
        existing_email = await self.email_repository.get_by_gmail_id(email_data['gmail_id'])
        if existing_email:
            results['emails_skipped'] += 1
            return
        
        # Get or create thread
        thread = await self._get_or_create_thread(email_data, account_id, results)
        
        # Create email record
        email_create = EmailCreate(
            gmail_id=email_data['gmail_id'],
            thread_id=thread.id,
            from_email=email_data['from_email'],
            from_name=email_data.get('from_name'),
            to_email=email_data['to_email'],
            to_name=email_data.get('to_name'),
            cc_emails=email_data.get('cc_emails'),
            bcc_emails=email_data.get('bcc_emails'),
            subject=email_data['subject'],
            date=email_data['date'] or datetime.utcnow(),
            body_text=email_data.get('body_text'),
            body_html=email_data.get('body_html'),
            snippet=email_data.get('snippet'),
            has_attachments=email_data.get('has_attachments', False),
            size_estimate=email_data.get('size_estimate'),
            gmail_labels=email_data.get('labels')
        )
        
        await self.email_repository.create(email_create)
        results['emails_imported'] += 1
    
    async def _get_or_create_thread(
        self,
        email_data: Dict[str, Any],
        account_id: int,
        results: Dict[str, Any]
    ) -> EmailThread:
        """Get existing thread or create new one"""
        gmail_thread_id = email_data['thread_id']
        
        # Check if thread already exists
        existing_thread = await self.thread_repository.get_by_gmail_id(gmail_thread_id)
        
        if existing_thread:
            # Update thread last message date
            from app.schemas.communication import EmailThreadUpdate
            await self.thread_repository.update(existing_thread.id, EmailThreadUpdate(
                last_message_date=email_data['date'] or datetime.utcnow(),
                last_activity_date=datetime.utcnow()
            ))
            results['threads_updated'] += 1
            return existing_thread
        
        # Create new thread
        is_ebay_related = self.classifier.is_ebay_related(email_data)
        message_type = None
        ebay_item_id = None
        
        if is_ebay_related:
            message_type = self.classifier.classify_message_type(email_data)
            ebay_item_id = self.classifier.extract_ebay_item_id(email_data)
        
        # Determine participants
        participants = [email_data['from_email'], email_data['to_email']]
        if email_data.get('cc_emails'):
            participants.extend(email_data['cc_emails'])
        participants = list(set(filter(None, participants)))  # Remove duplicates and None values
        
        # Determine if requires response (simple heuristic)
        requires_response = self._should_require_response(email_data, is_ebay_related)
        
        thread_create = EmailThreadCreate(
            gmail_thread_id=gmail_thread_id,
            account_id=account_id,
            subject=email_data['subject'],
            participant_emails=participants,
            is_ebay_related=is_ebay_related,
            ebay_item_id=ebay_item_id,
            message_type=message_type,
            first_message_date=email_data['date'] or datetime.utcnow(),
            last_message_date=email_data['date'] or datetime.utcnow()
        )
        
        thread = await self.thread_repository.create(thread_create)
        results['threads_created'] += 1
        
        # Set requires_response flag after creation
        if requires_response:
            from app.schemas.communication import EmailThreadUpdate
            await self.thread_repository.update(thread.id, EmailThreadUpdate(
                requires_response=True,
                priority=self._determine_priority(email_data, message_type)
            ))
        
        return thread
    
    def _should_require_response(self, email_data: Dict[str, Any], is_ebay_related: bool) -> bool:
        """Determine if email requires response - YAGNI: Simple heuristics"""
        if not is_ebay_related:
            return False
        
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body_text', '').lower()
        content = f"{subject} {body}"
        
        # Keywords that indicate response needed
        response_keywords = [
            'question', 'when will', 'where is', 'can you',
            'please confirm', 'need to know', 'problem with',
            'issue with', 'not working', 'not received'
        ]
        
        for keyword in response_keywords:
            if keyword in content:
                return True
        
        return False
    
    def _determine_priority(self, email_data: Dict[str, Any], message_type: Optional[str]) -> str:
        """Determine email priority - YAGNI: Simple priority rules"""
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body_text', '').lower()
        content = f"{subject} {body}"
        
        # High priority keywords
        urgent_keywords = ['urgent', 'asap', 'immediately', 'complaint', 'dispute']
        high_keywords = ['problem', 'issue', 'not received', 'damaged', 'refund']
        
        for keyword in urgent_keywords:
            if keyword in content:
                return 'urgent'
        
        for keyword in high_keywords:
            if keyword in content:
                return 'high'
        
        # Message type-based priority
        if message_type in ['return_request', 'payment_issue']:
            return 'high'
        elif message_type in ['shipping_inquiry', 'order_inquiry']:
            return 'normal'
        
        return 'normal'