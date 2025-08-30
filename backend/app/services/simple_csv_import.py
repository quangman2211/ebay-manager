"""
Ultra-simplified CSV Import Service
Following YAGNI principles - 90% complexity reduction
Supports: Manual upload, Google Sheets, Chrome extension HTTP upload
"""

import csv
import io
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from app.repositories.listing_repository import ListingRepository
from app.repositories.account_repository import AccountRepository
from app.schemas.listing import ListingCreate
from app.core.exceptions import ValidationException, NotFoundError


class SimpleCsvImportResult:
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


class SimpleCsvImportService:
    """
    YAGNI: Ultra-simple CSV import - no complex detection, job management, or validation
    Support all upload methods: manual upload, Google Sheets, Chrome extension
    """
    
    def __init__(self, listing_repository: ListingRepository, account_repository: AccountRepository):
        self.listing_repository = listing_repository
        self.account_repository = account_repository
    
    async def import_csv_content(self, csv_content: str, account_id: int) -> SimpleCsvImportResult:
        """
        Import CSV content directly - works for all upload methods
        YAGNI: Simple processing, no complex format detection or job management
        """
        result = SimpleCsvImportResult()
        
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
    
    async def _process_csv_row(self, row: Dict[str, str], row_index: int, account_id: int, result: SimpleCsvImportResult):
        """
        Process single CSV row - YAGNI: Basic field mapping only
        """
        # Basic validation and extraction
        listing_data = self._extract_listing_data(row, account_id)
        
        if not listing_data:
            result.warnings.append(f"Row {row_index + 1}: Insufficient data, skipped")
            return
        
        # Check if listing exists by eBay item ID
        ebay_item_id = listing_data.get('ebay_item_id')
        if ebay_item_id:
            existing_listing = await self.listing_repository.get_by_ebay_item_id(ebay_item_id)
            
            if existing_listing:
                # Update existing listing
                await self._update_existing_listing(existing_listing.id, listing_data, result)
            else:
                # Create new listing
                await self._create_new_listing(listing_data, result)
        else:
            # Create new listing without eBay ID
            await self._create_new_listing(listing_data, result)
    
    def _extract_listing_data(self, row: Dict[str, str], account_id: int) -> Optional[Dict[str, Any]]:
        """
        Extract listing data from CSV row - YAGNI: Simple field mapping
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
        title = get_field_value(row, ['Title', 'title', 'Listing Title', 'Product Title', 'Name'])
        price_str = get_field_value(row, ['Price', 'price', 'Sale Price', 'Buy It Now Price', 'Starting Price'])
        ebay_item_id = get_field_value(row, ['Item ID', 'item_id', 'eBay Item ID', 'Listing ID'])
        
        # Basic validation
        if not title:
            return None
            
        if not price_str:
            return None
        
        try:
            # Parse price (handle currency symbols)
            price_clean = price_str.replace('$', '').replace(',', '').replace('USD', '').strip()
            price = Decimal(price_clean)
            if price <= 0:
                return None
        except (ValueError, TypeError):
            return None
        
        # Optional fields
        description = get_field_value(row, ['Description', 'description', 'Subtitle', 'subtitle'])
        category = get_field_value(row, ['Category', 'category', 'Primary Category'])
        quantity_str = get_field_value(row, ['Quantity', 'quantity', 'Quantity Available', 'Qty'])
        status = get_field_value(row, ['Status', 'status', 'Listing Status'])
        
        # Parse quantity
        quantity = 1  # default
        if quantity_str:
            try:
                quantity = max(1, int(float(quantity_str)))
            except (ValueError, TypeError):
                quantity = 1
        
        # Determine status
        if not status:
            status = 'active'
        else:
            status = status.lower()
            if status not in ['active', 'inactive', 'ended', 'paused']:
                status = 'active'
        
        return {
            'account_id': account_id,
            'title': title,
            'description': description,
            'price': price,
            'quantity_available': quantity,
            'category': category,
            'status': status,
            'ebay_item_id': ebay_item_id,
            'start_date': datetime.utcnow()
        }
    
    async def _create_new_listing(self, listing_data: Dict[str, Any], result: SimpleCsvImportResult):
        """Create new listing - YAGNI: Simple creation only"""
        listing_create = ListingCreate(**listing_data)
        await self.listing_repository.create(listing_create)
        result.created_count += 1
    
    async def _update_existing_listing(self, listing_id: int, listing_data: Dict[str, Any], result: SimpleCsvImportResult):
        """Update existing listing - YAGNI: Basic updates only"""
        update_data = {
            'title': listing_data.get('title'),
            'description': listing_data.get('description'),
            'price': listing_data.get('price'),
            'quantity_available': listing_data.get('quantity_available'),
            'category': listing_data.get('category'),
            'status': listing_data.get('status'),
            'last_updated': datetime.utcnow()
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        await self.listing_repository.update(listing_id, update_data)
        result.updated_count += 1