"""
eBay CSV Upload Strategy
Single Responsibility: Handles only eBay CSV file uploads
"""
import pandas as pd
from io import StringIO
from typing import List, Dict, Any, Tuple, Optional
import re
import logging

from app.interfaces.upload_strategy import (
    IUploadStrategy, UploadContext, UploadResult, UploadSourceType
)
from app.schemas import DataType

logger = logging.getLogger(__name__)


class EBayCSVStrategy(IUploadStrategy):
    """
    Strategy for processing eBay CSV exports
    Refactored from original CSVProcessor with SOLID principles
    """
    
    def __init__(self):
        self._max_file_size = 50 * 1024 * 1024  # 50MB
    
    @property
    def supported_types(self) -> List[UploadSourceType]:
        return [UploadSourceType.CSV_FILE]
    
    @property
    def max_file_size(self) -> int:
        return self._max_file_size
    
    def validate(self, content: str, context: UploadContext) -> Tuple[bool, List[str]]:
        """Validate eBay CSV format"""
        errors = []
        
        try:
            # Parse CSV to check format
            df = self._parse_csv_content(content)
            
            if context.data_type == 'order':
                errors = self._validate_order_csv(df)
            elif context.data_type == 'listing':
                errors = self._validate_listing_csv(df)
            else:
                errors.append(f"Unsupported data type: {context.data_type}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"CSV parsing error: {str(e)}")
            return False, errors
    
    def parse(self, content: str, context: UploadContext) -> List[Dict[str, Any]]:
        """Parse eBay CSV into standardized format"""
        df = self._parse_csv_content(content)
        
        if context.data_type == 'order':
            return self._parse_orders(df, context)
        elif context.data_type == 'listing':
            return self._parse_listings(df, context)
        else:
            raise ValueError(f"Unsupported data type: {context.data_type}")
    
    def detect_account_info(self, content: str, context: UploadContext) -> Optional[str]:
        """Detect eBay seller ID from CSV"""
        # Try to extract from CSV footer
        username = self._extract_ebay_seller_id(content)
        
        # Fallback to filename extraction
        if not username and context.filename:
            username = self._extract_username_from_filename(context.filename)
        
        return username
    
    def process(self, content: str, context: UploadContext) -> UploadResult:
        """Main processing orchestration"""
        try:
            # Validate
            is_valid, errors = self.validate(content, context)
            if not is_valid:
                return UploadResult(
                    success=False,
                    message="Validation failed",
                    errors=errors
                )
            
            # Detect account info
            detected_username = self.detect_account_info(content, context)
            
            # Parse data
            parsed_data = self.parse(content, context)
            
            # Return successful result
            return UploadResult(
                success=True,
                message="CSV processed successfully",
                total_records=len(parsed_data),
                detected_username=detected_username,
                processed_data=parsed_data
            )
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            return UploadResult(
                success=False,
                message=f"Processing failed: {str(e)}",
                errors=[str(e)]
            )
    
    # Private helper methods (refactored from original CSVProcessor)
    
    def _parse_csv_content(self, content: str) -> pd.DataFrame:
        """Parse CSV content handling eBay specific format"""
        # Handle BOM if present
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # Handle eBay CSV with empty rows at top
        lines = content.strip().split('\n')
        
        # Find header line
        header_line_idx = 0
        for i, line in enumerate(lines):
            if '"' in line and ('Order Number' in line or 'Item number' in line):
                header_line_idx = i
                break
        
        # Filter out footer lines (like "Seller ID : username")
        data_lines = []
        for line in lines[header_line_idx:]:
            # Skip empty lines and footer lines
            if not line.strip() or line.strip().replace(',', '').replace('"', '') == '':
                continue
            # Skip eBay footer lines
            if line.strip().startswith('Seller ID') or line.strip().startswith('Report'):
                continue
            data_lines.append(line)
        
        cleaned_csv = '\n'.join(data_lines)
        df = pd.read_csv(StringIO(cleaned_csv))
        return df.dropna(how='all')
    
    def _validate_order_csv(self, df: pd.DataFrame) -> List[str]:
        """Validate order CSV columns"""
        required_columns = [
            "Order Number", "Item Number", "Item Title",
            "Buyer Username", "Buyer Name", "Sale Date",
            "Sold For", "Quantity"
        ]
        
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            return [f"Missing required columns: {', '.join(missing)}"]
        return []
    
    def _validate_listing_csv(self, df: pd.DataFrame) -> List[str]:
        """Validate listing CSV columns"""
        required_columns = [
            "Item number", "Title", "Available quantity",
            "Current price", "Sold quantity", "Format"
        ]
        
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            return [f"Missing required columns: {', '.join(missing)}"]
        return []
    
    def _parse_orders(self, df: pd.DataFrame, context: UploadContext) -> List[Dict[str, Any]]:
        """Parse order data from DataFrame"""
        records = []
        for _, row in df.iterrows():
            record = {
                'account_id': context.account_id,
                'data_type': DataType.ORDER.value,
                'order_number': str(row.get('Order Number')),
                'item_number': str(row.get('Item Number')),
                'item_title': str(row.get('Item Title')),
                'buyer_username': str(row.get('Buyer Username')),
                'buyer_name': str(row.get('Buyer Name')),
                'sale_date': str(row.get('Sale Date')),
                'total_price': row.get('Sold For'),
                'quantity': row.get('Quantity')
            }
            records.append(record)
        return records
    
    def _parse_listings(self, df: pd.DataFrame, context: UploadContext) -> List[Dict[str, Any]]:
        """Parse listing data from DataFrame"""
        records = []
        for _, row in df.iterrows():
            record = {
                'account_id': context.account_id,
                'data_type': DataType.LISTING.value,
                'item_number': str(row.get('Item number')),
                'title': str(row.get('Title')),
                'available_quantity': str(row.get('Available quantity')),
                'current_price': str(row.get('Current price')),
                'sold_quantity': str(row.get('Sold quantity')),
                'format': str(row.get('Format'))
            }
            records.append(record)
        return records
    
    def _extract_ebay_seller_id(self, content: str) -> Optional[str]:
        """Extract eBay seller ID from CSV footer"""
        try:
            lines = content.strip().split('\n')
            for line in reversed(lines[-10:]):
                line = line.strip()
                if line.startswith('Seller ID') and ':' in line:
                    seller_id = line.split(':', 1)[1].strip()
                    if seller_id:
                        return seller_id
            return None
        except Exception as e:
            logger.error(f"Error extracting seller ID: {e}")
            return None
    
    def _extract_username_from_filename(self, filename: str) -> Optional[str]:
        """Extract username from filename patterns"""
        try:
            name_without_ext = filename.rsplit('.', 1)[0]
            
            # Pattern: username_orders or username_listings
            match = re.match(r'^([a-zA-Z0-9_-]+)_(orders|listings)$', name_without_ext, re.IGNORECASE)
            if match:
                return match.group(1)
            
            # Pattern: orders_username or listings_username
            match = re.match(r'^(orders|listings)_([a-zA-Z0-9_-]+)$', name_without_ext, re.IGNORECASE)
            if match:
                return match.group(2)
            
            # Pattern: just username
            if re.match(r'^[a-zA-Z0-9_-]+$', name_without_ext):
                return name_without_ext
            
            return None
        except Exception as e:
            logger.error(f"Error extracting from filename: {e}")
            return None