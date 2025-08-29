# Phase 7: Customer & Communication Management Implementation

## Overview
Implement unified customer relationship and communication system with Gmail integration, eBay message processing, and automated response capabilities. Matches Dashboard5.png inbox design with advanced message classification and template management.

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **CustomerService**: Only handle customer data and relationship management
- **MessageService**: Only manage message processing and routing
- **TemplateService**: Only handle message template management
- **EmailService**: Only manage email sending and receiving via Gmail API
- **ClassificationService**: Only classify and categorize messages
- **NotificationService**: Only handle communication notifications

### Open/Closed Principle (OCP)
- **Message Sources**: Extensible to support additional platforms (Amazon, Facebook, etc.)
- **Template Engines**: Support multiple template formats and rendering engines
- **Classification Rules**: Add new message classification algorithms
- **Notification Channels**: Support email, SMS, webhooks, etc.

### Liskov Substitution Principle (LSP)
- **IMessageProvider**: All message sources (Gmail, eBay CSV, etc.) interchangeable
- **ITemplateRenderer**: All template engines follow same contract
- **IClassifier**: All message classifiers substitutable

### Interface Segregation Principle (ISP)
- **Separate Interfaces**: Message reading vs sending vs template management
- **Client-Specific**: Customer service doesn't depend on email internals
- **Operation-Specific**: Read vs Write vs Analytics operations

### Dependency Inversion Principle (DIP)
- **Abstract Dependencies**: Services depend on interfaces
- **Injected Components**: All external APIs and services injected

## Customer & Communication Domain Models

### Customer Entity
```python
# app/models/customer.py - Single Responsibility: Customer data representation
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSON, ENUM
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from enum import Enum
from app.database import Base

class CustomerStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    VIP = "vip"

class CustomerSegment(Enum):
    NEW_BUYER = "new_buyer"
    REGULAR_BUYER = "regular_buyer"
    VIP_BUYER = "vip_buyer"
    PROBLEM_BUYER = "problem_buyer"
    WHOLESALE_BUYER = "wholesale_buyer"

class Customer(Base):
    """Customer entity with comprehensive tracking"""
    __tablename__ = "customers"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    # Basic customer information
    ebay_username = Column(String(100))
    email = Column(String(255))
    first_name = Column(String(100))
    last_name = Column(String(100))
    display_name = Column(String(200))
    
    # Contact information
    phone = Column(String(20))
    address = Column(JSON)  # Complete address object
    
    # Customer classification
    status = Column(ENUM(CustomerStatus), default=CustomerStatus.ACTIVE)
    segment = Column(ENUM(CustomerSegment), default=CustomerSegment.NEW_BUYER)
    
    # Business metrics
    total_orders = Column(Integer, default=0)
    total_spent = Column(Decimal(12, 2), default=0)
    average_order_value = Column(Decimal(10, 2), default=0)
    lifetime_value = Column(Decimal(12, 2), default=0)
    
    # Behavior tracking
    first_order_date = Column(DateTime)
    last_order_date = Column(DateTime)
    days_since_last_order = Column(Integer, default=0)
    order_frequency = Column(Decimal(5, 2), default=0)  # Orders per month
    
    # Communication preferences
    preferred_language = Column(String(10), default="en")
    communication_preferences = Column(JSON)  # Email, SMS, etc.
    timezone = Column(String(50), default="UTC")
    
    # Rating and feedback
    feedback_score = Column(Integer, default=0)
    positive_feedback_percent = Column(Decimal(5, 2), default=100.0)
    
    # Internal notes and tags
    tags = Column(JSON)  # Array of tags for organization
    internal_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contact_date = Column(DateTime)
    
    # Relationships
    account = relationship("Account", back_populates="customers")
    orders = relationship("Order", back_populates="customer")
    messages = relationship("Message", back_populates="customer")
    
class Message(Base):
    """Unified message entity for all communication channels"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    
    # Message identification
    external_id = Column(String(200))  # Gmail message ID, eBay message ID, etc.
    thread_id = Column(String(200))  # For grouping related messages
    
    # Message source and type
    source = Column(String(50), nullable=False)  # "gmail", "ebay_csv", "manual"
    message_type = Column(String(50))  # "inquiry", "complaint", "order_question", etc.
    direction = Column(String(20))  # "inbound", "outbound"
    
    # Message content
    subject = Column(String(500))
    body_text = Column(Text)
    body_html = Column(Text)
    
    # Sender/Recipient information
    from_email = Column(String(255))
    from_name = Column(String(200))
    to_email = Column(String(255))
    to_name = Column(String(200))
    cc_emails = Column(JSON)  # Array of CC emails
    bcc_emails = Column(JSON)  # Array of BCC emails
    
    # Message classification
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    category = Column(String(50))  # "sales", "support", "complaint", "inquiry"
    is_spam = Column(Boolean, default=False)
    confidence_score = Column(Decimal(3, 2))  # Classification confidence 0-1
    
    # Status and handling
    read_status = Column(Boolean, default=False)
    replied_status = Column(Boolean, default=False)
    archived_status = Column(Boolean, default=False)
    starred_status = Column(Boolean, default=False)
    
    # Response tracking
    requires_response = Column(Boolean, default=True)
    response_deadline = Column(DateTime)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Attachments and media
    has_attachments = Column(Boolean, default=False)
    attachment_info = Column(JSON)  # Array of attachment metadata
    
    # Automation
    auto_response_sent = Column(Boolean, default=False)
    template_used = Column(UUID(as_uuid=True), ForeignKey("message_templates.id"))
    
    # Timestamps
    sent_at = Column(DateTime)
    received_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account")
    customer = relationship("Customer", back_populates="messages")
    assigned_user = relationship("User")
    template = relationship("MessageTemplate")

class MessageTemplate(Base):
    """Message templates for automated and manual responses"""
    __tablename__ = "message_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    # Template identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # "auto_response", "follow_up", "complaint", etc.
    
    # Template content
    subject_template = Column(String(500))
    body_template = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    
    # Template configuration
    is_active = Column(Boolean, default=True)
    is_auto_send = Column(Boolean, default=False)  # For automated responses
    trigger_conditions = Column(JSON)  # Conditions for automatic triggering
    
    # Variables and personalization
    available_variables = Column(JSON)  # List of available template variables
    default_variables = Column(JSON)  # Default variable values
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Decimal(5, 2), default=0)  # Response rate percentage
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime)
    
    # Relationships
    account = relationship("Account")
    messages = relationship("Message", back_populates="template")
```

### Gmail Integration Service
```python
# app/services/gmail_service.py - Single Responsibility: Gmail API integration
from typing import List, Optional, Dict, Any
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.models.message import Message
from app.repositories.message import MessageRepository

class GmailService:
    """Gmail API integration service"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, message_repo: MessageRepository):
        self._message_repo = message_repo
        self._logger = logging.getLogger(__name__)
        self._service = None
    
    async def authenticate(self, credentials_path: str, token_path: str) -> bool:
        """Authenticate with Gmail API"""
        creds = None
        
        # Load existing token
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
        
        # If no valid credentials, initiate OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        # Build Gmail service
        try:
            self._service = build('gmail', 'v1', credentials=creds)
            return True
        except HttpError as error:
            self._logger.error(f"Gmail API authentication failed: {error}")
            return False
    
    async def fetch_messages(
        self, 
        account_id: UUID,
        query: str = "",
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch messages from Gmail"""
        if not self._service:
            raise ValueError("Gmail service not authenticated")
        
        try:
            # Get message list
            results = self._service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            # Fetch full message details
            full_messages = []
            for msg in messages:
                msg_detail = await self._get_message_detail(msg['id'])
                if msg_detail:
                    # Check if message already exists
                    existing = await self._message_repo.get_by_external_id(
                        account_id, msg['id'], 'gmail'
                    )
                    
                    if not existing:
                        # Convert to internal format and save
                        internal_msg = await self._convert_gmail_message(
                            account_id, msg_detail
                        )
                        await self._message_repo.create(internal_msg)
                        full_messages.append(internal_msg)
            
            return full_messages
            
        except HttpError as error:
            self._logger.error(f"Failed to fetch Gmail messages: {error}")
            return []
    
    async def send_message(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        reply_to_message_id: Optional[str] = None
    ) -> Optional[str]:
        """Send email via Gmail API"""
        if not self._service:
            raise ValueError("Gmail service not authenticated")
        
        try:
            # Create message
            message = MIMEMultipart()
            message['To'] = to_email
            message['Subject'] = subject
            if from_email:
                message['From'] = from_email
            if reply_to_message_id:
                message['In-Reply-To'] = reply_to_message_id
                message['References'] = reply_to_message_id
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            # Send message
            sent_message = self._service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return sent_message.get('id')
            
        except HttpError as error:
            self._logger.error(f"Failed to send Gmail message: {error}")
            return None
    
    async def mark_as_read(self, message_id: str) -> bool:
        """Mark Gmail message as read"""
        if not self._service:
            return False
        
        try:
            self._service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as error:
            self._logger.error(f"Failed to mark message as read: {error}")
            return False
    
    async def _get_message_detail(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed message information"""
        try:
            message = self._service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            return message
        except HttpError as error:
            self._logger.error(f"Failed to get message detail: {error}")
            return None
    
    async def _convert_gmail_message(
        self,
        account_id: UUID,
        gmail_message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert Gmail message to internal format"""
        headers = {h['name']: h['value'] for h in gmail_message['payload']['headers']}
        
        # Extract message body
        body_text = self._extract_message_body(gmail_message['payload'])
        
        # Parse date
        sent_at = datetime.fromtimestamp(
            int(gmail_message['internalDate']) / 1000
        )
        
        return {
            'account_id': account_id,
            'external_id': gmail_message['id'],
            'thread_id': gmail_message['threadId'],
            'source': 'gmail',
            'direction': 'inbound',
            'subject': headers.get('Subject', ''),
            'body_text': body_text,
            'from_email': headers.get('From', ''),
            'to_email': headers.get('To', ''),
            'sent_at': sent_at,
            'received_at': datetime.utcnow(),
            'read_status': 'UNREAD' not in gmail_message['labelIds']
        }
    
    def _extract_message_body(self, payload: Dict[str, Any]) -> str:
        """Extract text body from Gmail message payload"""
        body = ""
        
        if payload.get('body', {}).get('data'):
            body = base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8')
        elif payload.get('parts'):
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if part.get('body', {}).get('data'):
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                        break
        
        return body
```

### Message Classification Service
```python
# app/services/message_classifier.py - Single Responsibility: Message classification
from typing import Dict, List, Optional, Tuple
import re
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import logging

class MessageClassifier:
    """AI-powered message classification service"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self._classifier = MultinomialNB()
        self._is_trained = False
        
        # Predefined patterns for quick classification
        self._patterns = {
            'complaint': [
                r'\b(complain|complaint|dissatisfied|unhappy|terrible|awful)\b',
                r'\b(refund|return|money back)\b',
                r'\b(damaged|broken|defective|faulty)\b'
            ],
            'inquiry': [
                r'\b(question|ask|wondering|curious|info|information)\b',
                r'\b(how|when|where|what|why)\b',
                r'\b(available|stock|availability)\b'
            ],
            'order_question': [
                r'\b(order|shipment|shipping|delivery|tracking)\b',
                r'\b(when will|where is|status)\b',
                r'\b(received|arrived|delivered)\b'
            ],
            'praise': [
                r'\b(thank|thanks|grateful|appreciate|excellent|great|perfect)\b',
                r'\b(love|awesome|amazing|fantastic|wonderful)\b',
                r'\b(recommend|satisfied|happy|pleased)\b'
            ]
        }
    
    async def classify_message(
        self,
        subject: str,
        body: str,
        sender_history: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Classify message and determine priority"""
        
        # Combine subject and body for analysis
        full_text = f"{subject} {body}".lower()
        
        # Pattern-based classification (fast)
        category = self._classify_by_patterns(full_text)
        
        # Sentiment analysis
        sentiment = self._analyze_sentiment(full_text)
        
        # Priority determination
        priority = self._determine_priority(category, sentiment, sender_history)
        
        # Confidence scoring
        confidence = self._calculate_confidence(category, sentiment, full_text)
        
        # Response requirement
        requires_response = self._requires_response(category, sentiment)
        
        return {
            'category': category,
            'priority': priority,
            'sentiment': sentiment,
            'confidence_score': confidence,
            'requires_response': requires_response,
            'suggested_response_time': self._suggest_response_time(priority),
            'auto_response_eligible': self._is_auto_response_eligible(category, sentiment)
        }
    
    def _classify_by_patterns(self, text: str) -> str:
        """Classify message using predefined patterns"""
        scores = {}
        
        for category, patterns in self._patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            scores[category] = score
        
        # Return category with highest score, default to 'general'
        if scores:
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0:
                return best_category
        
        return 'general'
    
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze message sentiment"""
        try:
            blob = TextBlob(text)
            sentiment = blob.sentiment
            
            return {
                'polarity': sentiment.polarity,  # -1 to 1 (negative to positive)
                'subjectivity': sentiment.subjectivity,  # 0 to 1 (objective to subjective)
                'label': self._sentiment_label(sentiment.polarity)
            }
        except Exception as e:
            self._logger.warning(f"Sentiment analysis failed: {e}")
            return {'polarity': 0, 'subjectivity': 0, 'label': 'neutral'}
    
    def _sentiment_label(self, polarity: float) -> str:
        """Convert polarity to label"""
        if polarity > 0.1:
            return 'positive'
        elif polarity < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def _determine_priority(
        self,
        category: str,
        sentiment: Dict,
        sender_history: Optional[Dict]
    ) -> str:
        """Determine message priority"""
        priority_score = 0
        
        # Category-based priority
        category_priorities = {
            'complaint': 3,
            'order_question': 2,
            'inquiry': 1,
            'praise': 0,
            'general': 1
        }
        priority_score += category_priorities.get(category, 1)
        
        # Sentiment-based priority
        if sentiment['label'] == 'negative':
            priority_score += 2
        elif sentiment['polarity'] < -0.5:  # Very negative
            priority_score += 3
        
        # Sender history-based priority
        if sender_history:
            if sender_history.get('is_vip_customer'):
                priority_score += 2
            if sender_history.get('has_recent_complaints', 0) > 1:
                priority_score += 1
        
        # Convert score to priority label
        if priority_score >= 5:
            return 'urgent'
        elif priority_score >= 3:
            return 'high'
        elif priority_score >= 1:
            return 'normal'
        else:
            return 'low'
    
    def _calculate_confidence(
        self,
        category: str,
        sentiment: Dict,
        text: str
    ) -> float:
        """Calculate classification confidence"""
        confidence = 0.5  # Base confidence
        
        # Pattern matching confidence
        pattern_matches = sum(
            len(re.findall(pattern, text, re.IGNORECASE))
            for pattern in self._patterns.get(category, [])
        )
        confidence += min(pattern_matches * 0.1, 0.3)
        
        # Sentiment confidence
        confidence += abs(sentiment.get('polarity', 0)) * 0.2
        
        return min(confidence, 1.0)
    
    def _requires_response(self, category: str, sentiment: Dict) -> bool:
        """Determine if message requires response"""
        # Categories that always require response
        always_respond = ['complaint', 'order_question', 'inquiry']
        
        # Negative sentiment usually requires response
        if sentiment['label'] == 'negative':
            return True
        
        # Category-based response requirement
        if category in always_respond:
            return True
        
        # Praise might not require immediate response
        if category == 'praise':
            return False
        
        return True  # Default to requiring response
    
    def _suggest_response_time(self, priority: str) -> int:
        """Suggest response time in hours"""
        response_times = {
            'urgent': 1,
            'high': 4,
            'normal': 24,
            'low': 72
        }
        return response_times.get(priority, 24)
    
    def _is_auto_response_eligible(self, category: str, sentiment: Dict) -> bool:
        """Check if message is eligible for auto-response"""
        # Don't auto-respond to complaints or very negative messages
        if category == 'complaint' or sentiment['polarity'] < -0.3:
            return False
        
        # Good candidates for auto-response
        auto_eligible = ['inquiry', 'order_question', 'praise']
        return category in auto_eligible
```

### Template Service Implementation
```python
# app/services/template_service.py - Single Responsibility: Template management
from typing import Dict, List, Optional, Any
from uuid import UUID
import re
from jinja2 import Template, Environment, BaseLoader
from app.repositories.template import TemplateRepository
from app.models.message import MessageTemplate
from app.schemas.template import TemplateCreate, TemplateUpdate

class TemplateService:
    """Message template management and rendering service"""
    
    def __init__(self, template_repo: TemplateRepository):
        self._template_repo = template_repo
        self._jinja_env = Environment(loader=BaseLoader())
    
    async def render_template(
        self,
        template_id: UUID,
        variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """Render template with variables"""
        template_record = await self._template_repo.get_by_id(template_id)
        if not template_record:
            raise ValueError(f"Template {template_id} not found")
        
        # Add default variables
        all_variables = {**template_record.default_variables or {}, **variables}
        
        # Render subject and body
        subject_template = Template(template_record.subject_template)
        body_template = Template(template_record.body_template)
        
        rendered_subject = subject_template.render(**all_variables)
        rendered_body = body_template.render(**all_variables)
        
        # Track template usage
        await self._template_repo.increment_usage(template_id)
        
        return {
            'subject': rendered_subject,
            'body': rendered_body,
            'template_id': str(template_id)
        }
    
    async def create_template(self, template_data: TemplateCreate) -> MessageTemplate:
        """Create new message template"""
        # Validate template syntax
        self._validate_template_syntax(
            template_data.subject_template,
            template_data.body_template
        )
        
        # Extract available variables
        variables = self._extract_template_variables(
            f"{template_data.subject_template} {template_data.body_template}"
        )
        
        # Add extracted variables to template data
        template_data.available_variables = list(variables)
        
        return await self._template_repo.create(template_data)
    
    async def get_suggested_template(
        self,
        category: str,
        sentiment: str,
        customer_data: Optional[Dict] = None
    ) -> Optional[MessageTemplate]:
        """Suggest appropriate template based on message classification"""
        
        # Template selection logic based on category and sentiment
        template_criteria = {
            'category': category,
            'is_active': True
        }
        
        # Get matching templates
        templates = await self._template_repo.get_by_criteria(template_criteria)
        
        if not templates:
            return None
        
        # Score templates based on relevance
        best_template = self._score_templates(templates, category, sentiment)
        
        return best_template
    
    def _validate_template_syntax(self, subject: str, body: str) -> None:
        """Validate Jinja2 template syntax"""
        try:
            Template(subject)
            Template(body)
        except Exception as e:
            raise ValueError(f"Invalid template syntax: {e}")
    
    def _extract_template_variables(self, template_text: str) -> set:
        """Extract variable names from template"""
        # Find Jinja2 variable patterns: {{ variable_name }}
        pattern = r'\\{\\{\\s*([a-zA-Z_][a-zA-Z0-9_]*)\\s*\\}\\}'
        variables = set(re.findall(pattern, template_text))
        return variables
    
    def _score_templates(
        self,
        templates: List[MessageTemplate],
        category: str,
        sentiment: str
    ) -> Optional[MessageTemplate]:
        """Score and select best template"""
        if not templates:
            return None
        
        best_template = None
        best_score = 0
        
        for template in templates:
            score = 0
            
            # Category match
            if template.category == category:
                score += 10
            
            # Usage success rate
            score += template.success_rate or 0
            
            # Recent usage (prefer frequently used templates)
            if template.usage_count > 0:
                score += min(template.usage_count / 10, 5)
            
            if score > best_score:
                best_score = score
                best_template = template
        
        return best_template

# Standard template variables available in all templates
STANDARD_TEMPLATE_VARIABLES = {
    'customer_name': 'Customer name',
    'customer_email': 'Customer email address', 
    'order_id': 'Order ID',
    'product_name': 'Product name',
    'company_name': 'Company name',
    'support_email': 'Support email address',
    'current_date': 'Current date',
    'tracking_number': 'Shipping tracking number'
}
```

## Implementation Tasks

### Task 1: Customer Management System
1. **Create Customer Models**
   - Customer entity with comprehensive tracking
   - Customer segmentation and classification
   - Relationship with orders and messages

2. **Customer Service Implementation**
   - CRUD operations with business logic
   - Segmentation algorithms
   - Performance metrics calculation

### Task 2: Gmail Integration
1. **OAuth2 Authentication**
   - Google API credentials setup
   - Token management and refresh
   - Permission scope configuration

2. **Message Synchronization**
   - Fetch messages from Gmail API
   - Convert to internal format
   - Duplicate prevention

3. **Email Sending**
   - Send emails via Gmail API
   - Reply functionality
   - Threading support

### Task 3: Message Processing
1. **eBay CSV Import**
   - Parse eBay message CSV files
   - Convert to internal message format
   - Merge with Gmail messages

2. **Message Classification**
   - AI-powered category detection
   - Sentiment analysis
   - Priority assignment

3. **Template System**
   - Template creation and management
   - Variable substitution
   - Auto-response functionality

### Task 4: Communication Dashboard
1. **Inbox Interface** (Dashboard5.png)
   - Message list with filtering
   - Category and priority indicators
   - Search and sort functionality

2. **Message Management**
   - Read/unread status
   - Response tracking
   - Assignment to team members

3. **Analytics and Reporting**
   - Response time metrics
   - Customer satisfaction tracking
   - Communication volume analysis

## Quality Gates

### Integration Requirements
- [ ] Gmail API authentication working
- [ ] Message synchronization accurate
- [ ] eBay CSV import processing correctly
- [ ] Customer data properly linked
- [ ] Templates rendering correctly

### Performance Requirements
- [ ] Message fetching: <2 seconds for 100 messages
- [ ] Classification: <100ms per message
- [ ] Template rendering: <50ms
- [ ] Dashboard loading: <1 second
- [ ] Support 50,000+ messages per account

### SOLID Compliance Checklist
- [ ] Single responsibility per service
- [ ] Extensible message sources and templates
- [ ] Interchangeable classification algorithms
- [ ] Separated communication channels
- [ ] Dependency injection throughout

### Security Requirements
- [ ] OAuth2 tokens securely stored
- [ ] Message content encrypted at rest
- [ ] Access control for sensitive communications
- [ ] Audit trail for all message operations
- [ ] Customer data privacy compliance

---
**Implementation Complete**: All 7 phases of the eBay management system now have ultra-detailed implementation plans following strict SOLID/YAGNI principles.