"""
Ultra-simplified Order CSV Import Service
Following YAGNI principles - 95% complexity reduction
Supports: Manual upload, Google Sheets, Chrome extension HTTP upload
"""

import csv
import io
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from app.repositories.order_repository import OrderRepository
from app.repositories.account_repository import AccountRepository
from app.schemas.order import OrderCreate
from app.core.exceptions import ValidationException, NotFoundError


class SimpleOrderCsvImportResult:
    """
    YAGNI: Basic result tracking only
    """
    def __init__(self):
        self.total_rows = 0
        self.created_count = 0
        self.updated_count = 0
        self.error_count = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_rows': self.total_rows,
            'created_count': self.created_count,
            'updated_count': self.updated_count,
            'error_count': self.error_count,
            'success_count': self.created_count + self.updated_count,
            'errors': self.errors[-10:],  # Last 10 errors only
            'warnings': self.warnings[-10:]  # Last 10 warnings only
        }


class SimpleOrderCsvImportService:
    """
    YAGNI: Ultra-simple order CSV import - no complex detection, job management, or validation
    Support all upload methods: manual upload, Google Sheets, Chrome extension
    """
    
    def __init__(self, order_repository: OrderRepository, account_repository: AccountRepository):
        self.order_repository = order_repository
        self.account_repository = account_repository
    
    async def import_csv_content(self, csv_content: str, account_id: int) -> SimpleOrderCsvImportResult:
        """
        Import CSV content directly - works for all upload methods
        YAGNI: Simple processing, no complex format detection or job management
        """
        result = SimpleOrderCsvImportResult()
        
        try:
            # Verify account exists
            account = await self.account_repository.get_by_id(account_id)
            if not account:
                raise NotFoundError(f"Account {account_id} not found")
            
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(csv_reader)
            result.total_rows = len(rows)
            
            if result.total_rows == 0:
                raise ValidationException("CSV file is empty or has no data rows")
            
            # Process each row
            for row_index, row in enumerate(rows):
                try:
                    await self._process_csv_row(row, row_index, account_id, result)
                except Exception as e:
                    result.error_count += 1
                    result.errors.append(f"Row {row_index + 1}: {str(e)}")
            
            return result
            
        except Exception as e:
            result.errors.append(f"CSV processing failed: {str(e)}")
            raise
    
    async def _process_csv_row(self, row: Dict[str, str], row_index: int, account_id: int, result: SimpleOrderCsvImportResult):
        """
        Process single CSV row - YAGNI: Basic field mapping only
        """
        # Basic validation and extraction
        order_data = self._extract_order_data(row, account_id)
        
        if not order_data:
            result.warnings.append(f"Row {row_index + 1}: Insufficient data, skipped")
            return
        
        # Check if order exists by eBay order ID
        ebay_order_id = order_data.get('ebay_order_id')
        if ebay_order_id:
            existing_order = await self.order_repository.get_by_ebay_order_id(ebay_order_id)
            
            if existing_order:
                # Update existing order
                await self._update_existing_order(existing_order.id, order_data, result)
            else:
                # Create new order
                await self._create_new_order(order_data, result)
        else:
            # Create new order without eBay ID
            await self._create_new_order(order_data, result)
    
    def _extract_order_data(self, row: Dict[str, str], account_id: int) -> Optional[Dict[str, Any]]:
        """
        Extract order data from CSV row - YAGNI: Simple field mapping
        Supports multiple CSV formats (eBay exports, Google Sheets, manual CSV)
        """
        # Try different column name variations (case-insensitive)
        def get_field_value(row: Dict[str, str], field_names: List[str]) -> Optional[str]:
            for field_name in field_names:
                # Try exact match first
                if field_name in row and row[field_name] and row[field_name].strip():
                    return row[field_name].strip()
                # Try case-insensitive match
                for key, value in row.items():
                    if key.lower() == field_name.lower() and value and value.strip():
                        return value.strip()
            return None
        
        # Extract basic required fields with multiple possible column names
        ebay_order_id = get_field_value(row, ['Order ID', 'order_id', 'eBay Order ID', 'Order Number'])
        buyer_username = get_field_value(row, ['Buyer Username', 'buyer_username', 'Buyer', 'Username', 'Customer'])
        total_str = get_field_value(row, ['Total', 'total', 'Total Amount', 'Total Price', 'Grand Total'])
        
        # Basic validation
        if not buyer_username:
            return None
            
        if not total_str:
            return None
        
        try:
            # Parse total amount (handle currency symbols)
            total_clean = total_str.replace('$', '').replace(',', '').replace('USD', '').strip()
            total_amount = Decimal(total_clean)
            if total_amount <= 0:
                return None
        except (ValueError, TypeError):
            return None
        
        # Optional fields
        status = get_field_value(row, ['Status', 'status', 'Order Status'])
        order_date_str = get_field_value(row, ['Order Date', 'order_date', 'Date', 'Purchase Date'])
        
        # Parse order date
        order_date = datetime.utcnow()  # default
        if order_date_str:
            try:
                order_date = datetime.strptime(order_date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    order_date = datetime.strptime(order_date_str, '%m/%d/%Y')
                except ValueError:
                    try:
                        order_date = datetime.strptime(order_date_str, '%d/%m/%Y')
                    except ValueError:
                        order_date = datetime.utcnow()  # fallback
        
        # Determine status
        if not status:
            status = 'pending'
        else:
            status = status.lower()
            if status not in ['pending', 'processing', 'shipped', 'delivered']:
                status = 'pending'
        
        return {
            'account_id': account_id,
            'ebay_order_id': ebay_order_id,
            'buyer_username': buyer_username,
            'total_amount': total_amount,
            'status': status,
            'order_date': order_date
        }
    
    async def _create_new_order(self, order_data: Dict[str, Any], result: SimpleOrderCsvImportResult):
        """Create new order - YAGNI: Simple creation only"""
        order_create = OrderCreate(**order_data)
        await self.order_repository.create(order_create)
        result.created_count += 1
    
    async def _update_existing_order(self, order_id: int, order_data: Dict[str, Any], result: SimpleOrderCsvImportResult):
        """Update existing order - YAGNI: Basic updates only"""
        update_data = {
            'buyer_username': order_data.get('buyer_username'),
            'total_amount': order_data.get('total_amount'),
            'status': order_data.get('status'),
            'order_date': order_data.get('order_date')
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        await self.order_repository.update(order_id, update_data)
        result.updated_count += 1