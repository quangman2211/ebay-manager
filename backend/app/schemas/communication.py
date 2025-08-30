"""
Communication schemas for API validation and serialization
Following SOLID principles - Single Responsibility for data validation
YAGNI compliance: Essential validation fields only
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageDirectionEnum(str, Enum):
    """Message direction from account perspective"""
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class MessageTypeEnum(str, Enum):
    """eBay message types"""
    SHIPPING_INQUIRY = "shipping_inquiry"
    PAYMENT_ISSUE = "payment_issue"
    RETURN_REQUEST = "return_request"
    GENERAL_INQUIRY = "general_inquiry"
    FEEDBACK_RELATED = "feedback_related"
    ORDER_ISSUE = "order_issue"


class MessagePriorityEnum(str, Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailCreate(BaseModel):
    """Email creation schema"""
    gmail_id: str
    thread_id: int
    from_email: str = Field(..., max_length=255)
    from_name: Optional[str] = None
    to_email: str = Field(..., max_length=255)
    to_name: Optional[str] = None
    cc_emails: Optional[List[str]] = None
    bcc_emails: Optional[List[str]] = None
    subject: str = Field(..., max_length=500)
    date: datetime
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    snippet: Optional[str] = None
    has_attachments: bool = False
    size_estimate: Optional[int] = None
    gmail_labels: Optional[List[str]] = None


class EmailUpdate(BaseModel):
    """Email update schema"""
    is_processed: Optional[bool] = None
    processing_notes: Optional[str] = None


class EmailResponse(BaseModel):
    """Email response schema"""
    id: int
    gmail_id: str
    from_email: str
    from_name: Optional[str]
    to_email: str
    to_name: Optional[str]
    subject: str
    date: datetime
    snippet: Optional[str]
    has_attachments: bool
    is_processed: bool
    created_at: datetime

    class Config:
        orm_mode = True


class EmailThreadCreate(BaseModel):
    """Email thread creation schema"""
    gmail_thread_id: str
    account_id: int
    subject: str = Field(..., max_length=500)
    participant_emails: List[str]
    is_ebay_related: bool = False
    ebay_item_id: Optional[str] = None
    message_type: Optional[str] = None
    first_message_date: datetime
    last_message_date: datetime


class EmailThreadUpdate(BaseModel):
    """Email thread update schema"""
    subject: Optional[str] = None
    is_read: Optional[bool] = None
    requires_response: Optional[bool] = None
    is_responded: Optional[bool] = None
    priority: Optional[str] = None
    last_message_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None


class EmailThreadResponse(BaseModel):
    """Email thread response schema"""
    id: int
    gmail_thread_id: str
    account_id: int
    subject: str
    is_ebay_related: bool
    ebay_item_id: Optional[str]
    message_type: Optional[str]
    is_read: bool
    requires_response: bool
    is_responded: bool
    priority: str
    first_message_date: datetime
    last_message_date: datetime
    email_count: Optional[int] = None

    class Config:
        orm_mode = True


class EmailThreadDetailResponse(EmailThreadResponse):
    """Detailed email thread response with emails"""
    emails: List[EmailResponse] = []


class GmailAuthResponse(BaseModel):
    """Gmail authentication response"""
    auth_url: str
    message: str


class GmailStatusResponse(BaseModel):
    """Gmail authentication status response"""
    authenticated: bool
    needs_reauth: bool
    error: Optional[str] = None


class EmailImportRequest(BaseModel):
    """Email import request schema"""
    account_id: int
    days_back: int = Field(default=7, ge=1, le=30)
    max_emails: int = Field(default=500, ge=1, le=1000)
    ebay_only: bool = True


class EmailImportResponse(BaseModel):
    """Email import response schema"""
    success: bool
    message: str
    results: dict


# eBay Message Schemas

class EbayMessageCreate(BaseModel):
    """eBay message creation schema"""
    ebay_message_id: str
    account_id: int
    thread_id: Optional[int] = None  # Will be set during processing
    item_id: str = Field(..., max_length=50)
    item_title: Optional[str] = None
    order_id: Optional[str] = None
    sender_username: str = Field(..., max_length=100)
    recipient_username: str = Field(..., max_length=100)
    direction: MessageDirectionEnum
    message_content: str
    message_date: datetime
    message_type: MessageTypeEnum = MessageTypeEnum.GENERAL_INQUIRY
    priority: MessagePriorityEnum = MessagePriorityEnum.NORMAL
    has_response: bool = False
    response_content: Optional[str] = None
    response_date: Optional[datetime] = None
    requires_response: bool = False


class EbayMessageUpdate(BaseModel):
    """eBay message update schema"""
    is_processed: Optional[bool] = None
    processing_notes: Optional[str] = None
    requires_response: Optional[bool] = None


class EbayMessageResponse(BaseModel):
    """eBay message response schema"""
    id: int
    ebay_message_id: str
    item_id: str
    item_title: Optional[str]
    sender_username: str
    recipient_username: str
    direction: str
    message_content: str
    message_date: datetime
    message_type: str
    priority: str
    has_response: bool
    requires_response: bool
    created_at: datetime

    class Config:
        orm_mode = True


class MessageThreadCreate(BaseModel):
    """Message thread creation schema"""
    account_id: int
    external_thread_id: Optional[str] = None
    thread_type: str = Field(..., max_length=20)
    item_id: Optional[str] = None
    item_title: Optional[str] = None
    order_id: Optional[str] = None
    customer_email: Optional[str] = None
    customer_username: Optional[str] = None
    subject: str = Field(..., max_length=500)
    message_type: Optional[MessageTypeEnum] = None
    priority: MessagePriorityEnum = MessagePriorityEnum.NORMAL
    first_message_date: datetime
    last_message_date: datetime


class MessageThreadUpdate(BaseModel):
    """Message thread update schema"""
    subject: Optional[str] = None
    status: Optional[str] = None
    requires_response: Optional[bool] = None
    last_response_date: Optional[datetime] = None
    response_due_date: Optional[datetime] = None
    last_message_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None


class MessageThreadResponse(BaseModel):
    """Message thread response schema"""
    id: int
    account_id: int
    thread_type: str
    item_id: Optional[str]
    item_title: Optional[str]
    order_id: Optional[str]
    customer_email: Optional[str]
    customer_username: Optional[str]
    subject: str
    message_type: Optional[str]
    priority: str
    status: str
    requires_response: bool
    first_message_date: datetime
    last_message_date: datetime
    message_count: Optional[int] = None

    class Config:
        orm_mode = True


class MessageThreadDetailResponse(MessageThreadResponse):
    """Detailed message thread response with messages"""
    ebay_messages: List[EbayMessageResponse] = []
    emails: List[EmailResponse] = []


# CSV Import Schemas

class EbayMessageImportRequest(BaseModel):
    """eBay message import request schema"""
    account_id: int
    expected_format: Optional[str] = None


class EbayMessageImportResponse(BaseModel):
    """eBay message import response schema"""
    success: bool
    message: str
    results: dict


# Communication Center Schemas

class CommunicationFilter(BaseModel):
    """Communication thread filter schema"""
    status: Optional[str] = None
    priority: Optional[str] = None
    message_type: Optional[str] = None
    requires_response: Optional[bool] = None
    thread_type: Optional[str] = None  # email, ebay_message, mixed
    customer_email: Optional[str] = None
    customer_username: Optional[str] = None
    item_id: Optional[str] = None
    order_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None


class ThreadUpdateRequest(BaseModel):
    """Thread update request schema"""
    status: Optional[str] = None
    priority: Optional[str] = None
    requires_response: Optional[bool] = None
    response_due_date: Optional[datetime] = None


class UnifiedThreadResponse(BaseModel):
    """Unified thread response schema"""
    id: int
    account_id: int
    external_thread_id: Optional[str]
    thread_type: str
    item_id: Optional[str]
    item_title: Optional[str]
    order_id: Optional[str]
    customer_email: Optional[str]
    customer_username: Optional[str]
    subject: str
    message_type: Optional[str]
    priority: str
    status: str
    requires_response: bool
    response_due_date: Optional[datetime]
    first_message_date: datetime
    last_message_date: datetime
    last_activity_date: datetime
    email_count: int
    ebay_message_count: int
    total_message_count: int
    unread_count: int
    latest_message: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True




class CommunicationDashboard(BaseModel):
    """Communication dashboard response schema"""
    threads_by_status: Dict[str, int]
    threads_by_priority: Dict[str, int]
    pending_responses: int
    overdue_responses: int
    recent_activity: int
    message_types: Dict[str, int]