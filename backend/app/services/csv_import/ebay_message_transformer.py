"""
eBay Message Data Transformation
Following SOLID principles - Single Responsibility for data transformation
YAGNI compliance: Direct mapping, no complex transformation rules
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import pandas as pd
import re

from app.services.csv_import.ebay_message_csv_detector import EbayMessageCSVFormat


class MessageDirection(Enum):
    """Message direction from account perspective"""
    INCOMING = "incoming"  # Received by account holder
    OUTGOING = "outgoing"  # Sent by account holder


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


class EbayMessageTransformer:
    """
    SOLID: Single Responsibility - Transform eBay CSV data to message objects
    YAGNI: Direct mapping, no complex transformation rules
    """
    
    def __init__(self):
        # Mapping between CSV formats and our internal format
        self.column_mappings = {
            EbayMessageCSVFormat.EBAY_BUYER_MESSAGES: {
                'message_id': 'Message ID',
                'item_id': 'Item ID',
                'item_title': 'Item Title',
                'sender_username': 'Buyer Username',
                'recipient_username': 'Seller Username',
                'message_content': 'Message',
                'message_date': 'Message Date',
                'order_id': 'Order ID',
                'response_message': 'Response Message',
                'response_date': 'Response Date'
            },
            EbayMessageCSVFormat.EBAY_SELLER_MESSAGES: {
                'message_id': 'Message ID',
                'item_id': 'Item ID',
                'item_title': 'Item Title',
                'sender_username': 'Buyer Username',
                'recipient_username': 'Seller Username',  # Assumed
                'message_content': 'Message',
                'message_date': 'Message Date',
                'message_type': 'Message Type',
                'order_id': 'Order ID'
            },
            EbayMessageCSVFormat.EBAY_ALL_MESSAGES: {
                'message_id': 'Message ID',
                'item_id': 'Item ID',
                'item_title': 'Item Title',
                'sender_username': 'Sender',
                'recipient_username': 'Recipient',
                'message_content': 'Message Content',
                'message_date': 'Message Date',
                'direction': 'Direction',
                'order_id': 'Order ID'
            }
        }
        
        # Message type classification patterns
        self.message_type_patterns = {
            MessageType.SHIPPING_INQUIRY: [
                'when will you ship', 'shipping time', 'tracking number',
                'where is my item', 'not shipped', 'ship asap'
            ],
            MessageType.PAYMENT_ISSUE: [
                'payment problem', 'payment failed', 'unpaid',
                'invoice', 'billing', 'charge'
            ],
            MessageType.RETURN_REQUEST: [
                'return', 'refund', 'not as described', 'damaged',
                'defective', 'wrong item', 'money back'
            ],
            MessageType.GENERAL_INQUIRY: [
                'question', 'information', 'details', 'clarification',
                'can you tell me', 'i need to know'
            ],
            MessageType.FEEDBACK_RELATED: [
                'feedback', 'review', 'rating', 'negative feedback',
                'positive feedback', 'leave feedback'
            ]
        }
    
    def transform_row_to_message(
        self, 
        row_data: Dict[str, Any], 
        csv_format: EbayMessageCSVFormat,
        account_id: int,
        account_username: str
    ) -> Dict[str, Any]:
        """
        Transform CSV row to message data dictionary
        YAGNI: Direct field mapping, no complex business rules
        """
        mapping = self.column_mappings.get(csv_format, {})
        
        # Extract basic message data
        message_data = {
            'ebay_message_id': self._extract_value(row_data, mapping.get('message_id')),
            'account_id': account_id,
            'item_id': self._extract_value(row_data, mapping.get('item_id')),
            'item_title': self._extract_value(row_data, mapping.get('item_title')),
            'sender_username': self._extract_value(row_data, mapping.get('sender_username')),
            'recipient_username': self._extract_value(row_data, mapping.get('recipient_username')),
            'message_content': self._extract_value(row_data, mapping.get('message_content')),
            'message_date': self._extract_datetime(row_data, mapping.get('message_date')),
            'order_id': self._extract_value(row_data, mapping.get('order_id'))
        }
        
        # Determine message direction
        direction = self._determine_direction(
            message_data['sender_username'], 
            message_data['recipient_username'], 
            account_username,
            row_data,
            csv_format
        )
        message_data['direction'] = direction
        
        # Classify message type
        message_type = self._classify_message_type(message_data['message_content'])
        message_data['message_type'] = message_type
        
        # Determine priority
        priority = self._determine_priority(message_data['message_content'], message_type)
        message_data['priority'] = priority
        
        # Handle response data if available
        if csv_format == EbayMessageCSVFormat.EBAY_BUYER_MESSAGES:
            response_content = self._extract_value(row_data, mapping.get('response_message'))
            response_date = self._extract_datetime(row_data, mapping.get('response_date'))
            
            if response_content:
                message_data['response_content'] = response_content
                message_data['response_date'] = response_date
                message_data['has_response'] = True
            else:
                message_data['has_response'] = False
        else:
            message_data['has_response'] = False
        
        return message_data
    
    def extract_thread_context(
        self, 
        row_data: Dict[str, Any], 
        csv_format: EbayMessageCSVFormat
    ) -> Dict[str, Any]:
        """Extract information for thread creation/matching"""
        mapping = self.column_mappings.get(csv_format, {})
        
        context = {
            'item_id': self._extract_value(row_data, mapping.get('item_id')),
            'item_title': self._extract_value(row_data, mapping.get('item_title')),
            'sender_username': self._extract_value(row_data, mapping.get('sender_username')),
            'recipient_username': self._extract_value(row_data, mapping.get('recipient_username')),
            'order_id': self._extract_value(row_data, mapping.get('order_id'))
        }
        
        return context
    
    def _extract_value(self, row_data: Dict[str, Any], column_name: Optional[str]) -> Optional[str]:
        """Extract string value from row data"""
        if not column_name or column_name not in row_data:
            return None
        
        value = row_data[column_name]
        if pd.isna(value):
            return None
        
        return str(value).strip() if str(value).strip() else None
    
    def _extract_datetime(self, row_data: Dict[str, Any], column_name: Optional[str]) -> Optional[datetime]:
        """Extract datetime value from row data"""
        if not column_name or column_name not in row_data:
            return None
        
        value = row_data[column_name]
        if pd.isna(value):
            return None
        
        try:
            return pd.to_datetime(str(value))
        except (ValueError, TypeError):
            return None
    
    def _determine_direction(
        self, 
        sender: Optional[str], 
        recipient: Optional[str], 
        account_username: str,
        row_data: Dict[str, Any],
        csv_format: EbayMessageCSVFormat
    ) -> MessageDirection:
        """
        Determine message direction from account perspective
        YAGNI: Simple username matching
        """
        # If direction is explicitly provided in CSV
        if csv_format == EbayMessageCSVFormat.EBAY_ALL_MESSAGES and 'Direction' in row_data:
            direction_value = str(row_data['Direction']).lower()
            if 'incoming' in direction_value or 'received' in direction_value:
                return MessageDirection.INCOMING
            elif 'outgoing' in direction_value or 'sent' in direction_value:
                return MessageDirection.OUTGOING
        
        # Determine from sender/recipient
        if sender and sender.lower() == account_username.lower():
            return MessageDirection.OUTGOING
        elif recipient and recipient.lower() == account_username.lower():
            return MessageDirection.INCOMING
        
        # Default logic based on CSV format
        if csv_format == EbayMessageCSVFormat.EBAY_BUYER_MESSAGES:
            return MessageDirection.OUTGOING  # Messages from buyers to sellers
        elif csv_format == EbayMessageCSVFormat.EBAY_SELLER_MESSAGES:
            return MessageDirection.INCOMING  # Messages from buyers to sellers
        
        return MessageDirection.INCOMING  # Default assumption
    
    def _classify_message_type(self, message_content: Optional[str]) -> MessageType:
        """
        Classify message type based on content
        YAGNI: Simple keyword matching
        """
        if not message_content:
            return MessageType.GENERAL_INQUIRY
        
        content_lower = message_content.lower()
        
        # Score each message type
        type_scores = {}
        
        for msg_type, keywords in self.message_type_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in content_lower:
                    score += 1
            
            if score > 0:
                type_scores[msg_type] = score
        
        # Return type with highest score
        if type_scores:
            return max(type_scores, key=type_scores.get)
        
        return MessageType.GENERAL_INQUIRY
    
    def _determine_priority(self, message_content: Optional[str], message_type: MessageType) -> MessagePriority:
        """
        Determine message priority based on content and type
        YAGNI: Simple priority rules
        """
        if not message_content:
            return MessagePriority.NORMAL
        
        content_lower = message_content.lower()
        
        # Urgent keywords
        urgent_keywords = ['urgent', 'asap', 'immediately', 'emergency', 'dispute']
        high_keywords = ['problem', 'issue', 'not received', 'damaged', 'complaint']
        
        for keyword in urgent_keywords:
            if keyword in content_lower:
                return MessagePriority.URGENT
        
        for keyword in high_keywords:
            if keyword in content_lower:
                return MessagePriority.HIGH
        
        # Priority based on message type
        if message_type in [MessageType.RETURN_REQUEST, MessageType.PAYMENT_ISSUE]:
            return MessagePriority.HIGH
        elif message_type == MessageType.SHIPPING_INQUIRY:
            return MessagePriority.NORMAL
        
        return MessagePriority.NORMAL