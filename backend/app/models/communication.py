"""
Communication models for email threads and messages
Following SOLID principles - Single Responsibility for data structure representation
YAGNI compliance: Essential communication data only
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class MessageDirection(Enum):
    """Message direction from account perspective"""
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class MessageType(Enum):
    """eBay message types"""
    SHIPPING_INQUIRY = "shipping_inquiry"
    PAYMENT_ISSUE = "payment_issue"
    RETURN_REQUEST = "return_request"
    GENERAL_INQUIRY = "general_inquiry"
    FEEDBACK_RELATED = "feedback_related"
    ORDER_ISSUE = "order_issue"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailThread(BaseModel):
    """
    SOLID: Single Responsibility - Represents email thread data structure
    """
    __tablename__ = "email_threads"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    gmail_thread_id = Column(String(100), unique=True, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    # Thread info
    subject = Column(String(500), nullable=False, index=True)
    participant_emails = Column(JSON)  # List of email addresses in thread
    
    # eBay context
    is_ebay_related = Column(Boolean, default=False, index=True)
    ebay_item_id = Column(String(50), index=True)
    message_type = Column(String(50), index=True)  # order_inquiry, payment_issue, etc.
    
    # Status tracking
    is_read = Column(Boolean, default=False)
    requires_response = Column(Boolean, default=False)
    is_responded = Column(Boolean, default=False)
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    
    # Timestamps
    first_message_date = Column(DateTime, nullable=False)
    last_message_date = Column(DateTime, nullable=False)
    last_activity_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="email_threads")
    emails = relationship("Email", back_populates="thread", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_thread_account_status', 'account_id', 'is_read', 'requires_response'),
        Index('idx_thread_ebay', 'is_ebay_related', 'message_type'),
        Index('idx_thread_dates', 'first_message_date', 'last_message_date'),
    )


class Email(BaseModel):
    """
    SOLID: Single Responsibility - Represents individual email data
    """
    __tablename__ = "emails"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    gmail_id = Column(String(100), unique=True, nullable=False, index=True)
    thread_id = Column(Integer, ForeignKey("email_threads.id"), nullable=False, index=True)
    
    # Email headers
    from_email = Column(String(255), nullable=False, index=True)
    from_name = Column(String(255))
    to_email = Column(String(255), nullable=False)
    to_name = Column(String(255))
    cc_emails = Column(JSON)  # List of CC email addresses
    bcc_emails = Column(JSON)  # List of BCC email addresses
    
    subject = Column(String(500), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    
    # Email content
    body_text = Column(Text)
    body_html = Column(Text)
    snippet = Column(Text)
    
    # Email metadata
    has_attachments = Column(Boolean, default=False)
    size_estimate = Column(Integer)
    gmail_labels = Column(JSON)  # Gmail label IDs
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_notes = Column(Text)
    
    # Relationships
    thread = relationship("EmailThread", back_populates="emails")
    
    # Indexes
    __table_args__ = (
        Index('idx_email_thread_date', 'thread_id', 'date'),
        Index('idx_email_participants', 'from_email', 'to_email'),
    )


class MessageThread(BaseModel):
    """
    SOLID: Single Responsibility - Unified thread for both email and eBay messages
    """
    __tablename__ = "message_threads"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    # Thread identification
    external_thread_id = Column(String(100), index=True)  # Gmail thread ID or generated ID
    thread_type = Column(String(20), nullable=False, index=True)  # email, ebay_message, mixed
    
    # eBay context (for eBay messages)
    item_id = Column(String(50), index=True)
    item_title = Column(String(500))
    order_id = Column(String(50), index=True)
    
    # Participants
    customer_email = Column(String(255), index=True)
    customer_username = Column(String(100), index=True)  # eBay username
    subject = Column(String(500), nullable=False)
    
    # Status and classification
    message_type = Column(String(50), index=True)
    priority = Column(String(20), default=MessagePriority.NORMAL.value, index=True)
    status = Column(String(20), default='open', index=True)  # open, pending, resolved, closed
    
    # Response tracking
    requires_response = Column(Boolean, default=False)
    last_response_date = Column(DateTime)
    response_due_date = Column(DateTime)
    
    # Timestamps
    first_message_date = Column(DateTime, nullable=False)
    last_message_date = Column(DateTime, nullable=False)
    last_activity_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="message_threads")
    emails = relationship("Email", back_populates="message_thread")
    ebay_messages = relationship("EbayMessage", back_populates="thread")

    # Indexes for performance
    __table_args__ = (
        Index('idx_thread_account_type', 'account_id', 'thread_type'),
        Index('idx_thread_item_customer', 'item_id', 'customer_username'),
        Index('idx_thread_status_priority', 'status', 'priority'),
        Index('idx_thread_response_due', 'requires_response', 'response_due_date'),
    )


class EbayMessage(BaseModel):
    """
    SOLID: Single Responsibility - Represents eBay message data structure
    """
    __tablename__ = "ebay_messages"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    ebay_message_id = Column(String(100), unique=True, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    thread_id = Column(Integer, ForeignKey("message_threads.id"), nullable=False, index=True)
    
    # eBay context
    item_id = Column(String(50), nullable=False, index=True)
    item_title = Column(String(500))
    order_id = Column(String(50), index=True)
    
    # Message participants
    sender_username = Column(String(100), nullable=False, index=True)
    recipient_username = Column(String(100), nullable=False, index=True)
    direction = Column(String(20), nullable=False, index=True)  # incoming, outgoing
    
    # Message content
    message_content = Column(Text, nullable=False)
    message_date = Column(DateTime, nullable=False, index=True)
    
    # Classification
    message_type = Column(String(50), index=True)
    priority = Column(String(20), default=MessagePriority.NORMAL.value, index=True)
    
    # Response handling
    has_response = Column(Boolean, default=False)
    response_content = Column(Text)
    response_date = Column(DateTime)
    requires_response = Column(Boolean, default=False)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_notes = Column(Text)
    
    # Relationships
    account = relationship("Account", back_populates="ebay_messages")
    thread = relationship("MessageThread", back_populates="ebay_messages")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_ebay_message_account_item', 'account_id', 'item_id'),
        Index('idx_ebay_message_thread_date', 'thread_id', 'message_date'),
        Index('idx_ebay_message_type_priority', 'message_type', 'priority'),
        Index('idx_ebay_message_response', 'requires_response', 'has_response'),
    )


