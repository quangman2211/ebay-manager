"""
Email message processing and classification
Following SOLID principles - Single Responsibility for email processing operations
YAGNI compliance: Basic parsing and eBay classification only
"""

from typing import Dict, Any, List, Optional, Tuple
import email
import base64
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re

from app.models.communication import Email, EmailThread
from app.schemas.communication import EmailCreate, EmailThreadCreate


class EmailMessageParser:
    """
    SOLID: Single Responsibility - Parse Gmail message data only
    YAGNI: Basic parsing, no complex content analysis
    """
    
    def parse_gmail_message(self, gmail_message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail API message format to our internal format"""
        payload = gmail_message.get('payload', {})
        headers = payload.get('headers', [])
        
        # Extract headers
        header_dict = {h['name'].lower(): h['value'] for h in headers}
        
        # Parse message content
        body_text, body_html = self._extract_body(payload)
        
        # Extract basic info
        parsed = {
            'gmail_id': gmail_message['id'],
            'thread_id': gmail_message['threadId'],
            'subject': header_dict.get('subject', ''),
            'from_email': self._extract_email_address(header_dict.get('from', '')),
            'from_name': self._extract_name(header_dict.get('from', '')),
            'to_email': self._extract_email_address(header_dict.get('to', '')),
            'to_name': self._extract_name(header_dict.get('to', '')),
            'date': self._parse_date(header_dict.get('date')),
            'body_text': body_text,
            'body_html': body_html,
            'labels': gmail_message.get('labelIds', []),
            'snippet': gmail_message.get('snippet', ''),
            'size_estimate': gmail_message.get('sizeEstimate', 0)
        }
        
        # Extract CC and BCC if present
        if 'cc' in header_dict:
            parsed['cc_emails'] = self._extract_multiple_emails(header_dict['cc'])
        
        if 'bcc' in header_dict:
            parsed['bcc_emails'] = self._extract_multiple_emails(header_dict['bcc'])
        
        # Check for attachments
        parsed['has_attachments'] = self._has_attachments(payload)
        
        return parsed
    
    def _extract_body(self, payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Extract text and HTML body from message payload"""
        text_body = None
        html_body = None
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain':
                    text_body = self._decode_body_data(part.get('body', {}))
                elif mime_type == 'text/html':
                    html_body = self._decode_body_data(part.get('body', {}))
                elif mime_type.startswith('multipart/'):
                    # Nested multipart
                    nested_text, nested_html = self._extract_body(part)
                    if nested_text and not text_body:
                        text_body = nested_text
                    if nested_html and not html_body:
                        html_body = nested_html
        else:
            # Single part message
            mime_type = payload.get('mimeType', '')
            body_data = payload.get('body', {})
            
            if mime_type == 'text/plain':
                text_body = self._decode_body_data(body_data)
            elif mime_type == 'text/html':
                html_body = self._decode_body_data(body_data)
        
        return text_body, html_body
    
    def _decode_body_data(self, body_data: Dict[str, Any]) -> Optional[str]:
        """Decode base64 body data"""
        if 'data' in body_data:
            try:
                # Gmail API uses URL-safe base64 encoding
                decoded_bytes = base64.urlsafe_b64decode(body_data['data'])
                return decoded_bytes.decode('utf-8')
            except Exception:
                return None
        return None
    
    def _extract_email_address(self, from_field: str) -> str:
        """Extract email address from 'From' field"""
        if not from_field:
            return ""
        
        # Use regex to extract email from "Name <email@domain.com>" format
        email_match = re.search(r'<(.+?)>', from_field)
        if email_match:
            return email_match.group(1).strip()
        
        # If no angle brackets, assume it's just the email
        if '@' in from_field:
            return from_field.strip()
        
        return ""
    
    def _extract_name(self, from_field: str) -> str:
        """Extract display name from 'From' field"""
        if not from_field:
            return ""
        
        # If there are angle brackets, name is before them
        if '<' in from_field:
            name = from_field.split('<')[0].strip()
            return name.strip('"').strip("'")
        
        return ""
    
    def _extract_multiple_emails(self, email_field: str) -> List[str]:
        """Extract multiple email addresses from CC/BCC fields"""
        if not email_field:
            return []
        
        emails = []
        for part in email_field.split(','):
            email_addr = self._extract_email_address(part.strip())
            if email_addr:
                emails.append(email_addr)
        
        return emails
    
    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse email date string to datetime"""
        if not date_string:
            return None
        
        try:
            # Parse RFC 2822 format
            return email.utils.parsedate_to_datetime(date_string)
        except Exception:
            return None
    
    def _has_attachments(self, payload: Dict[str, Any]) -> bool:
        """Check if message has attachments"""
        if 'parts' in payload:
            for part in payload['parts']:
                disposition = part.get('body', {}).get('disposition')
                if disposition == 'attachment':
                    return True
                
                # Check nested parts
                if 'parts' in part:
                    if self._has_attachments(part):
                        return True
        
        return False


class EbayEmailClassifier:
    """
    SOLID: Single Responsibility - Classify eBay-related emails only
    YAGNI: Simple pattern matching, no ML classification
    """
    
    def __init__(self):
        # eBay-related patterns
        self.ebay_domains = [
            'ebay.com', 'ebay.co.uk', 'ebay.de', 'ebay.fr', 'ebay.it',
            'ebay.es', 'ebay.ca', 'ebay.au', 'ebay-kleinanzeigen.de'
        ]
        
        self.ebay_keywords = [
            'ebay', 'item you sold', 'item you bought', 'feedback', 
            'buyer message', 'seller message', 'payment received',
            'shipping label', 'item not received', 'return request'
        ]
        
        self.message_types = {
            'order_inquiry': ['when will you ship', 'shipping time', 'delivery date'],
            'payment_issue': ['payment problem', 'payment failed', 'invoice'],
            'shipping_inquiry': ['tracking number', 'shipping status', 'where is my item'],
            'return_request': ['return', 'refund', 'not as described', 'damaged'],
            'feedback_related': ['feedback', 'review', 'rating'],
            'general_inquiry': ['question about', 'more information', 'details']
        }
    
    def is_ebay_related(self, email_data: Dict[str, Any]) -> bool:
        """Check if email is eBay-related"""
        from_email = email_data.get('from_email', '').lower()
        subject = email_data.get('subject', '').lower()
        body_text = email_data.get('body_text', '').lower()
        
        # Check sender domain
        for domain in self.ebay_domains:
            if domain in from_email:
                return True
        
        # Check subject and body for eBay keywords
        content = f"{subject} {body_text}"
        for keyword in self.ebay_keywords:
            if keyword in content:
                return True
        
        return False
    
    def classify_message_type(self, email_data: Dict[str, Any]) -> Optional[str]:
        """Classify eBay email message type"""
        subject = email_data.get('subject', '').lower()
        body_text = email_data.get('body_text', '').lower()
        content = f"{subject} {body_text}"
        
        # Score each message type
        type_scores = {}
        
        for msg_type, keywords in self.message_types.items():
            score = 0
            for keyword in keywords:
                if keyword in content:
                    score += 1
            
            if score > 0:
                type_scores[msg_type] = score
        
        # Return type with highest score
        if type_scores:
            return max(type_scores, key=type_scores.get)
        
        return 'general_inquiry'  # Default classification
    
    def extract_ebay_item_id(self, email_data: Dict[str, Any]) -> Optional[str]:
        """Extract eBay item ID from email content - YAGNI: Simple regex matching"""
        subject = email_data.get('subject', '')
        body_text = email_data.get('body_text', '')
        content = f"{subject} {body_text}"
        
        # Look for eBay item ID patterns
        patterns = [
            r'item #?(\d{10,15})',
            r'item id:?\s*(\d{10,15})',
            r'listing #?(\d{10,15})',
            r'ebay item (\d{10,15})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None