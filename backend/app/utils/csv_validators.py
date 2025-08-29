"""
Order-Specific CSV Validators
Following SOLID principles - Single Responsibility for order validation
Extends existing CSV infrastructure for eBay order processing
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
from abc import ABC, abstractmethod

from app.schemas.csv import GenericCSVRow, CSVValidationError
from app.models.order import OrderStatus, PaymentStatus, ShippingStatus
from app.core.exceptions import EbayManagerException
from app.core.logging import get_logger

logger = get_logger("csv_validators")

class OrderCSVRowValidator:
    """
    Order CSV row validator
    Following SOLID: Single Responsibility for order row validation
    """
    
    # Expected eBay order CSV columns
    REQUIRED_COLUMNS = [
        'Order ID', 'Buyer Username', 'Total Price', 'Order Date'
    ]
    
    OPTIONAL_COLUMNS = [
        'Transaction ID', 'Item ID', 'Item Title', 'Quantity', 
        'Sale Price', 'Shipping Cost', 'Payment Method', 'Order Status',
        'Shipping Address', 'Buyer Email', 'Tracking Number', 'Payment Status',
        'Shipping Status', 'Currency', 'Shipped Date', 'Delivered Date',
        'Buyer Notes', 'Seller Notes', 'Payment Date'
    ]
    
    def validate_row(self, row_data: Dict[str, str], row_number: int) -> GenericCSVRow:
        """
        Validate a single order CSV row
        Following SOLID: Single method responsibility
        """
        errors = []
        warnings = []
        processed_data = {}
        
        try:
            # Validate required fields
            errors.extend(self._validate_required_fields(row_data, row_number))
            
            # Process and validate each field
            processed_data, field_errors, field_warnings = self._process_order_fields(row_data, row_number)
            errors.extend(field_errors)
            warnings.extend(field_warnings)
            
            # Business rule validations
            business_errors = self._validate_business_rules(processed_data, row_number)
            errors.extend(business_errors)
            
            return GenericCSVRow(
                row_number=row_number,
                raw_data=row_data,
                processed_data=processed_data,
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Unexpected error validating row {row_number}: {str(e)}")
            errors.append(f"Row {row_number}: Unexpected validation error: {str(e)}")
            
            return GenericCSVRow(
                row_number=row_number,
                raw_data=row_data,
                processed_data={},
                is_valid=False,
                errors=errors,
                warnings=warnings
            )
    
    def _validate_required_fields(self, row_data: Dict[str, str], row_number: int) -> List[str]:
        """Validate required fields are present and not empty"""
        errors = []
        
        for field in self.REQUIRED_COLUMNS:
            if field not in row_data or not str(row_data[field]).strip():
                errors.append(f"Row {row_number}: Required field '{field}' is missing or empty")
        
        return errors
    
    def _process_order_fields(self, row_data: Dict[str, str], row_number: int) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """Process and validate all order fields"""
        processed = {}
        errors = []
        warnings = []
        
        # Process Order ID
        processed['ebay_order_id'] = str(row_data.get('Order ID', '')).strip()
        if len(processed['ebay_order_id']) > 100:
            warnings.append(f"Row {row_number}: Order ID is longer than 100 characters")
            processed['ebay_order_id'] = processed['ebay_order_id'][:100]
        
        # Process Buyer Information
        processed['buyer_username'] = str(row_data.get('Buyer Username', '')).strip()
        processed['buyer_email'] = self._process_optional_email(row_data.get('Buyer Email'), row_number, errors)
        
        # Process Financial Information
        processed['total_amount'], total_errors = self._process_decimal_field(
            row_data.get('Total Price'), 'Total Price', row_number
        )
        errors.extend(total_errors)
        
        processed['shipping_cost'] = self._process_decimal_field(
            row_data.get('Shipping Cost', '0'), 'Shipping Cost', row_number
        )[0] or Decimal('0.00')
        
        processed['currency'] = self._process_currency(row_data.get('Currency', 'USD'), row_number, warnings)
        
        # Process Status Fields
        processed['status'] = self._process_order_status(row_data.get('Order Status', 'pending'), row_number, warnings)
        processed['payment_status'] = self._process_payment_status(row_data.get('Payment Status', 'pending'), row_number, warnings)
        processed['shipping_status'] = self._process_shipping_status(row_data.get('Shipping Status', 'not_shipped'), row_number, warnings)
        
        # Process Dates
        processed['order_date'], date_errors = self._process_datetime_field(
            row_data.get('Order Date'), 'Order Date', row_number
        )
        errors.extend(date_errors)
        
        processed['payment_date'] = self._process_datetime_field(
            row_data.get('Payment Date'), 'Payment Date', row_number
        )[0]
        
        processed['shipping_date'] = self._process_datetime_field(
            row_data.get('Shipped Date'), 'Shipped Date', row_number
        )[0]
        
        processed['actual_delivery_date'] = self._process_datetime_field(
            row_data.get('Delivered Date'), 'Delivered Date', row_number
        )[0]
        
        # Process Shipping Address
        processed.update(self._process_shipping_address(row_data, row_number, warnings))
        
        # Process Optional Fields
        processed['payment_method'] = str(row_data.get('Payment Method', '')).strip() or None
        processed['tracking_number'] = str(row_data.get('Tracking Number', '')).strip() or None
        processed['notes'] = str(row_data.get('Buyer Notes', '')).strip() or None
        processed['internal_notes'] = str(row_data.get('Seller Notes', '')).strip() or None
        
        return processed, errors, warnings
    
    def _process_decimal_field(self, value: str, field_name: str, row_number: int) -> Tuple[Optional[Decimal], List[str]]:
        """Process decimal field with validation"""
        errors = []
        
        if not value or str(value).strip() == '':
            return None, errors
        
        try:
            # Clean currency symbols and formatting
            clean_value = str(value).strip()
            clean_value = re.sub(r'[^\d.,\-]', '', clean_value)
            clean_value = clean_value.replace(',', '')
            
            decimal_value = Decimal(clean_value)
            
            if field_name in ['Total Price', 'Shipping Cost'] and decimal_value < 0:
                errors.append(f"Row {row_number}: {field_name} cannot be negative")
                return None, errors
            
            return decimal_value, errors
            
        except (InvalidOperation, ValueError):
            errors.append(f"Row {row_number}: Invalid {field_name} format: {value}")
            return None, errors
    
    def _process_datetime_field(self, value: str, field_name: str, row_number: int) -> Tuple[Optional[datetime], List[str]]:
        """Process datetime field with multiple format support"""
        errors = []
        
        if not value or str(value).strip() == '':
            return None, errors
        
        # Common eBay date formats
        date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ'
        ]
        
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(str(value).strip(), date_format)
                
                # Validate date is not too far in the future
                if parsed_date > datetime.utcnow().replace(hour=23, minute=59, second=59):
                    errors.append(f"Row {row_number}: {field_name} cannot be in the future: {value}")
                    return None, errors
                
                return parsed_date, errors
                
            except ValueError:
                continue
        
        errors.append(f"Row {row_number}: Invalid {field_name} format: {value}")
        return None, errors
    
    def _process_optional_email(self, value: str, row_number: int, errors: List[str]) -> Optional[str]:
        """Process optional email field with validation"""
        if not value or str(value).strip() == '':
            return None
        
        email = str(value).strip()
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        if not email_pattern.match(email):
            errors.append(f"Row {row_number}: Invalid email format: {email}")
            return None
        
        return email
    
    def _process_currency(self, value: str, row_number: int, warnings: List[str]) -> str:
        """Process currency field with normalization"""
        if not value or str(value).strip() == '':
            return 'USD'
        
        currency = str(value).strip().upper()
        
        # Common currency codes
        valid_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY']
        
        if currency not in valid_currencies:
            warnings.append(f"Row {row_number}: Unknown currency '{currency}', defaulting to USD")
            return 'USD'
        
        return currency
    
    def _process_order_status(self, value: str, row_number: int, warnings: List[str]) -> OrderStatus:
        """Process order status with normalization"""
        if not value:
            return OrderStatus.PENDING
        
        status_mapping = {
            'pending': OrderStatus.PENDING,
            'confirmed': OrderStatus.CONFIRMED,
            'processing': OrderStatus.PROCESSING,
            'shipped': OrderStatus.SHIPPED,
            'delivered': OrderStatus.DELIVERED,
            'completed': OrderStatus.DELIVERED,
            'cancelled': OrderStatus.CANCELLED,
            'canceled': OrderStatus.CANCELLED,
            'refunded': OrderStatus.REFUNDED,
            'returned': OrderStatus.RETURNED
        }
        
        normalized_status = str(value).lower().strip()
        
        if normalized_status in status_mapping:
            return status_mapping[normalized_status]
        
        warnings.append(f"Row {row_number}: Unknown order status '{value}', defaulting to pending")
        return OrderStatus.PENDING
    
    def _process_payment_status(self, value: str, row_number: int, warnings: List[str]) -> PaymentStatus:
        """Process payment status with normalization"""
        if not value:
            return PaymentStatus.PENDING
        
        status_mapping = {
            'pending': PaymentStatus.PENDING,
            'paid': PaymentStatus.PAID,
            'completed': PaymentStatus.PAID,
            'partial': PaymentStatus.PARTIALLY_PAID,
            'partially_paid': PaymentStatus.PARTIALLY_PAID,
            'failed': PaymentStatus.FAILED,
            'cancelled': PaymentStatus.CANCELLED,
            'canceled': PaymentStatus.CANCELLED,
            'refunded': PaymentStatus.REFUNDED
        }
        
        normalized_status = str(value).lower().strip()
        
        if normalized_status in status_mapping:
            return status_mapping[normalized_status]
        
        warnings.append(f"Row {row_number}: Unknown payment status '{value}', defaulting to pending")
        return PaymentStatus.PENDING
    
    def _process_shipping_status(self, value: str, row_number: int, warnings: List[str]) -> ShippingStatus:
        """Process shipping status with normalization"""
        if not value:
            return ShippingStatus.NOT_SHIPPED
        
        status_mapping = {
            'not_shipped': ShippingStatus.NOT_SHIPPED,
            'preparing': ShippingStatus.PREPARING,
            'shipped': ShippingStatus.SHIPPED,
            'in_transit': ShippingStatus.IN_TRANSIT,
            'delivered': ShippingStatus.DELIVERED,
            'returned': ShippingStatus.RETURNED,
            'lost': ShippingStatus.LOST
        }
        
        normalized_status = str(value).lower().strip().replace(' ', '_')
        
        if normalized_status in status_mapping:
            return status_mapping[normalized_status]
        
        warnings.append(f"Row {row_number}: Unknown shipping status '{value}', defaulting to not shipped")
        return ShippingStatus.NOT_SHIPPED
    
    def _process_shipping_address(self, row_data: Dict[str, str], row_number: int, warnings: List[str]) -> Dict[str, Any]:
        """Process shipping address fields"""
        address_data = {}
        
        # Try to parse single address field or individual components
        single_address = row_data.get('Shipping Address', '')
        
        if single_address:
            # Try to parse single address field
            address_parts = [part.strip() for part in single_address.split(',')]
            
            if len(address_parts) >= 3:
                address_data['shipping_name'] = address_parts[0] if len(address_parts) > 3 else row_data.get('Buyer Username', '')
                address_data['shipping_address_line1'] = address_parts[0] if len(address_parts) <= 3 else address_parts[1]
                address_data['shipping_city'] = address_parts[-3] if len(address_parts) >= 3 else ''
                address_data['shipping_state'] = address_parts[-2] if len(address_parts) >= 2 else ''
                address_data['shipping_postal_code'] = address_parts[-1] if len(address_parts) >= 1 else ''
                address_data['shipping_country'] = 'US'  # Default
            else:
                warnings.append(f"Row {row_number}: Could not parse shipping address format")
                address_data['shipping_name'] = row_data.get('Buyer Username', '')
                address_data['shipping_address_line1'] = single_address
                address_data['shipping_city'] = ''
                address_data['shipping_state'] = ''
                address_data['shipping_postal_code'] = ''
                address_data['shipping_country'] = 'US'
        else:
            # Use individual address components if available
            address_data['shipping_name'] = str(row_data.get('Shipping Name', row_data.get('Buyer Username', ''))).strip()
            address_data['shipping_address_line1'] = str(row_data.get('Shipping Address Line 1', '')).strip()
            address_data['shipping_address_line2'] = str(row_data.get('Shipping Address Line 2', '')).strip() or None
            address_data['shipping_city'] = str(row_data.get('Shipping City', '')).strip()
            address_data['shipping_state'] = str(row_data.get('Shipping State', '')).strip() or None
            address_data['shipping_postal_code'] = str(row_data.get('Shipping Postal Code', '')).strip()
            address_data['shipping_country'] = str(row_data.get('Shipping Country', 'US')).strip()
        
        # Validate required address fields
        if not address_data['shipping_name']:
            address_data['shipping_name'] = address_data.get('buyer_username', 'Unknown')
        
        return address_data
    
    def _validate_business_rules(self, processed_data: Dict[str, Any], row_number: int) -> List[str]:
        """Validate business rules for order data"""
        errors = []
        
        # Total amount must be positive
        if processed_data.get('total_amount') and processed_data['total_amount'] <= 0:
            errors.append(f"Row {row_number}: Total amount must be greater than 0")
        
        # Order date should not be too far in the past (more than 5 years)
        if processed_data.get('order_date'):
            five_years_ago = datetime.utcnow().replace(year=datetime.utcnow().year - 5)
            if processed_data['order_date'] < five_years_ago:
                errors.append(f"Row {row_number}: Order date is too far in the past")
        
        # Payment date should not be before order date
        if (processed_data.get('payment_date') and processed_data.get('order_date') and 
            processed_data['payment_date'] < processed_data['order_date']):
            errors.append(f"Row {row_number}: Payment date cannot be before order date")
        
        # Shipping date should not be before order date
        if (processed_data.get('shipping_date') and processed_data.get('order_date') and 
            processed_data['shipping_date'] < processed_data['order_date']):
            errors.append(f"Row {row_number}: Shipping date cannot be before order date")
        
        # Delivered date should not be before shipping date
        if (processed_data.get('actual_delivery_date') and processed_data.get('shipping_date') and 
            processed_data['actual_delivery_date'] < processed_data['shipping_date']):
            errors.append(f"Row {row_number}: Delivery date cannot be before shipping date")
        
        return errors

class OrderCSVBatchValidator:
    """
    Batch validator for order CSV files
    Following SOLID: Single Responsibility for batch validation
    """
    
    def __init__(self):
        self.row_validator = OrderCSVRowValidator()
    
    def validate_batch(self, csv_data: List[Dict[str, str]]) -> Dict[str, Any]:
        """Validate a batch of order CSV rows"""
        
        results = {
            'total_rows': len(csv_data),
            'valid_rows': 0,
            'invalid_rows': 0,
            'validated_data': [],
            'errors': [],
            'warnings': [],
            'duplicate_orders': [],
            'summary': {}
        }
        
        seen_order_ids = set()
        
        for row_number, row_data in enumerate(csv_data, start=1):
            validated_row = self.row_validator.validate_row(row_data, row_number)
            
            if validated_row.is_valid:
                results['valid_rows'] += 1
                
                # Check for duplicates within batch
                order_id = validated_row.processed_data.get('ebay_order_id')
                if order_id and order_id in seen_order_ids:
                    results['duplicate_orders'].append({
                        'row_number': row_number,
                        'order_id': order_id,
                        'error': 'Duplicate order ID within batch'
                    })
                    results['invalid_rows'] += 1
                    results['errors'].append(f"Row {row_number}: Duplicate order ID '{order_id}' found in batch")
                else:
                    if order_id:
                        seen_order_ids.add(order_id)
                    results['validated_data'].append(validated_row.processed_data)
            else:
                results['invalid_rows'] += 1
            
            results['errors'].extend(validated_row.errors)
            results['warnings'].extend(validated_row.warnings)
        
        # Generate summary
        results['summary'] = {
            'success_rate': (results['valid_rows'] / results['total_rows']) * 100 if results['total_rows'] > 0 else 0,
            'error_count': len(results['errors']),
            'warning_count': len(results['warnings']),
            'duplicate_count': len(results['duplicate_orders'])
        }
        
        return results

# Global instances for dependency injection
order_csv_validator = OrderCSVBatchValidator()