"""
eBay Message CSV Format Detection and Validation
Following SOLID principles - Single Responsibility for format detection and validation
YAGNI compliance: Simple format detection based on column patterns
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import pandas as pd
import re
from datetime import datetime


class EbayMessageCSVFormat(Enum):
    """
    YAGNI: Support common eBay message export formats only
    """
    EBAY_BUYER_MESSAGES = "ebay_buyer_messages"
    EBAY_SELLER_MESSAGES = "ebay_seller_messages"
    EBAY_ALL_MESSAGES = "ebay_all_messages"
    UNKNOWN = "unknown"


class EbayMessageFormatDetector:
    """
    SOLID: Single Responsibility - Detect and validate eBay message CSV format
    YAGNI: Simple format detection based on column patterns
    """
    
    # Standard column mappings for different eBay message export formats
    FORMAT_SIGNATURES = {
        EbayMessageCSVFormat.EBAY_BUYER_MESSAGES: {
            'required_columns': [
                'Message ID', 'Seller Username', 'Item ID', 'Item Title',
                'Message Date', 'Message', 'Response Status'
            ],
            'optional_columns': [
                'Order ID', 'Buyer Username', 'Response Date', 'Response Message'
            ]
        },
        EbayMessageCSVFormat.EBAY_SELLER_MESSAGES: {
            'required_columns': [
                'Message ID', 'Buyer Username', 'Item ID', 'Item Title',
                'Message Date', 'Message', 'Message Type'
            ],
            'optional_columns': [
                'Order ID', 'Response Required', 'Read Status', 'Priority'
            ]
        },
        EbayMessageCSVFormat.EBAY_ALL_MESSAGES: {
            'required_columns': [
                'Message ID', 'Sender', 'Recipient', 'Item ID',
                'Message Date', 'Message Content', 'Direction'
            ],
            'optional_columns': [
                'Item Title', 'Order ID', 'Message Type', 'Read Status'
            ]
        }
    }
    
    def detect_format(self, df: pd.DataFrame) -> Tuple[EbayMessageCSVFormat, float]:
        """
        Detect eBay message CSV format based on column presence
        Returns (format, confidence_score)
        """
        if df.empty:
            return EbayMessageCSVFormat.UNKNOWN, 0.0
        
        columns = set(df.columns)
        best_format = EbayMessageCSVFormat.UNKNOWN
        best_score = 0.0
        
        for format_type, signature in self.FORMAT_SIGNATURES.items():
            required_cols = set(signature['required_columns'])
            optional_cols = set(signature['optional_columns'])
            
            # Calculate match score
            required_matches = len(required_cols.intersection(columns))
            optional_matches = len(optional_cols.intersection(columns))
            
            # Must have all required columns
            if required_matches < len(required_cols):
                continue
            
            # Calculate confidence score
            confidence = (required_matches * 2 + optional_matches) / (len(required_cols) * 2 + len(optional_cols))
            
            if confidence > best_score:
                best_score = confidence
                best_format = format_type
        
        return best_format, best_score
    
    def validate_format_compatibility(self, df: pd.DataFrame, expected_format: EbayMessageCSVFormat) -> Dict[str, Any]:
        """Validate CSV compatibility with expected format"""
        if expected_format not in self.FORMAT_SIGNATURES:
            return {'valid': False, 'errors': ['Unsupported format']}
        
        signature = self.FORMAT_SIGNATURES[expected_format]
        columns = set(df.columns)
        required_cols = set(signature['required_columns'])
        
        missing_required = required_cols - columns
        validation_result = {
            'valid': len(missing_required) == 0,
            'missing_required_columns': list(missing_required),
            'extra_columns': list(columns - set(signature['required_columns']) - set(signature['optional_columns'])),
            'row_count': len(df),
            'detected_format': expected_format.value
        }
        
        if missing_required:
            validation_result['errors'] = [f"Missing required columns: {', '.join(missing_required)}"]
        else:
            validation_result['errors'] = []
        
        return validation_result


class EbayMessageValidator:
    """
    SOLID: Single Responsibility - Validate eBay message data only
    YAGNI: Basic validation rules, no complex message content validation
    """
    
    def __init__(self):
        self.validation_rules = {
            'message_id': self._validate_message_id,
            'item_id': self._validate_item_id,
            'usernames': self._validate_usernames,
            'message_content': self._validate_message_content,
            'dates': self._validate_dates
        }
    
    def validate_row(self, row_data: Dict[str, Any], row_index: int, csv_format: EbayMessageCSVFormat) -> List[str]:
        """
        Validate single row of eBay message data
        Returns list of error messages
        """
        errors = []
        
        try:
            # Message ID validation
            if 'Message ID' in row_data:
                message_id_errors = self._validate_message_id(row_data['Message ID'])
                errors.extend([f"Row {row_index + 1} Message ID: {err}" for err in message_id_errors])
            
            # Item ID validation
            if 'Item ID' in row_data:
                item_id_errors = self._validate_item_id(row_data['Item ID'])
                errors.extend([f"Row {row_index + 1} Item ID: {err}" for err in item_id_errors])
            
            # Username validation
            username_errors = self._validate_usernames(row_data, csv_format)
            errors.extend([f"Row {row_index + 1}: {err}" for err in username_errors])
            
            # Message content validation
            message_column = self._get_message_column(csv_format)
            if message_column in row_data:
                content_errors = self._validate_message_content(row_data[message_column])
                errors.extend([f"Row {row_index + 1} Message: {err}" for err in content_errors])
            
            # Date validation
            date_errors = self._validate_dates(row_data, csv_format)
            errors.extend([f"Row {row_index + 1}: {err}" for err in date_errors])
            
        except Exception as e:
            errors.append(f"Row {row_index + 1}: Validation error - {str(e)}")
        
        return errors
    
    def _validate_message_id(self, message_id: Any) -> List[str]:
        """Validate eBay message ID format"""
        errors = []
        
        if pd.isna(message_id) or str(message_id).strip() == '':
            errors.append("Message ID is required")
            return errors
        
        message_id_str = str(message_id).strip()
        
        # eBay message IDs are typically alphanumeric strings
        if len(message_id_str) < 5:
            errors.append("Invalid Message ID format (too short)")
        
        return errors
    
    def _validate_item_id(self, item_id: Any) -> List[str]:
        """Validate eBay item ID format"""
        errors = []
        
        if pd.isna(item_id) or str(item_id).strip() == '':
            errors.append("Item ID is required")
            return errors
        
        item_id_str = str(item_id).strip()
        
        # eBay item IDs are typically 12-digit numbers
        if not re.match(r'^\d{10,15}$', item_id_str):
            errors.append("Invalid Item ID format (should be 10-15 digits)")
        
        return errors
    
    def _validate_usernames(self, row_data: Dict[str, Any], csv_format: EbayMessageCSVFormat) -> List[str]:
        """Validate eBay usernames"""
        errors = []
        
        if csv_format == EbayMessageCSVFormat.EBAY_BUYER_MESSAGES:
            if 'Seller Username' in row_data:
                seller = row_data['Seller Username']
                if pd.isna(seller) or str(seller).strip() == '':
                    errors.append("Seller Username is required")
        
        elif csv_format == EbayMessageCSVFormat.EBAY_SELLER_MESSAGES:
            if 'Buyer Username' in row_data:
                buyer = row_data['Buyer Username']
                if pd.isna(buyer) or str(buyer).strip() == '':
                    errors.append("Buyer Username is required")
        
        elif csv_format == EbayMessageCSVFormat.EBAY_ALL_MESSAGES:
            for field in ['Sender', 'Recipient']:
                if field in row_data:
                    username = row_data[field]
                    if pd.isna(username) or str(username).strip() == '':
                        errors.append(f"{field} is required")
        
        return errors
    
    def _validate_message_content(self, message_content: Any) -> List[str]:
        """Validate message content"""
        errors = []
        
        if pd.isna(message_content) or str(message_content).strip() == '':
            errors.append("Message content is required")
            return errors
        
        content_str = str(message_content).strip()
        
        if len(content_str) < 1:
            errors.append("Message content cannot be empty")
        
        if len(content_str) > 10000:
            errors.append("Message content too long (maximum 10,000 characters)")
        
        return errors
    
    def _validate_dates(self, row_data: Dict[str, Any], csv_format: EbayMessageCSVFormat) -> List[str]:
        """Validate date fields based on CSV format"""
        errors = []
        
        date_columns = ['Message Date']
        if 'Response Date' in row_data:
            date_columns.append('Response Date')
        
        for date_col in date_columns:
            if date_col in row_data and not pd.isna(row_data[date_col]):
                try:
                    # Try to parse various date formats eBay might use
                    date_str = str(row_data[date_col]).strip()
                    if date_str:
                        pd.to_datetime(date_str)
                except (ValueError, TypeError):
                    errors.append(f"Invalid {date_col} format")
        
        return errors
    
    def _get_message_column(self, csv_format: EbayMessageCSVFormat) -> str:
        """Get the message content column name based on CSV format"""
        if csv_format == EbayMessageCSVFormat.EBAY_ALL_MESSAGES:
            return 'Message Content'
        else:
            return 'Message'