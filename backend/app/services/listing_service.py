from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import CSVData, User, Account
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ListingRepository:
    """Repository for listing data access - Single Responsibility Principle"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_listing_by_id(self, listing_id: int) -> Optional[CSVData]:
        return self.db.query(CSVData).filter(
            and_(CSVData.id == listing_id, CSVData.data_type == "listing")
        ).first()
    
    def get_listings_by_account(self, account_id: int) -> List[CSVData]:
        return self.db.query(CSVData).filter(
            and_(CSVData.account_id == account_id, CSVData.data_type == "listing")
        ).all()
    
    def update_listing(self, listing: CSVData) -> CSVData:
        self.db.commit()
        self.db.refresh(listing)
        return listing
    
    def get_user_accounts(self, user_id: int) -> List[int]:
        accounts = self.db.query(Account).filter(Account.user_id == user_id).all()
        return [account.id for account in accounts]


class ListingValidator:
    """Validator for listing data - Single Responsibility Principle"""
    
    @staticmethod
    def validate_price(price: str) -> bool:
        try:
            price_float = float(price.replace('$', '').replace(',', ''))
            return price_float > 0
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def validate_quantity(quantity: str) -> bool:
        try:
            qty = int(quantity)
            return qty >= 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_title(title: str) -> bool:
        return title and len(title.strip()) > 0 and len(title) <= 255
    
    @staticmethod
    def validate_status(status: str) -> bool:
        valid_statuses = ['active', 'inactive', 'ended', 'sold']
        return status.lower() in valid_statuses


class PriceHistoryLogger:
    """Logger for price changes - Single Responsibility Principle"""
    
    @staticmethod
    def log_price_change(listing_id: int, old_price: str, new_price: str, updated_by: int):
        logger.info(f"Price change for listing {listing_id}: {old_price} -> {new_price} by user {updated_by}")
        # In future, this could write to a separate price_history table


class ListingService:
    """Main service for listing operations - Dependency Inversion Principle"""
    
    def __init__(self, repository: ListingRepository, validator: ListingValidator, price_logger: PriceHistoryLogger):
        self.repository = repository
        self.validator = validator
        self.price_logger = price_logger
    
    def get_listing(self, listing_id: int, user: User) -> Optional[CSVData]:
        listing = self.repository.get_listing_by_id(listing_id)
        if not listing:
            return None
        
        # Check if user has access to this listing's account
        user_accounts = self.repository.get_user_accounts(user.id)
        if user.role != "admin" and listing.account_id not in user_accounts:
            raise PermissionError("Access denied to this listing")
        
        return listing
    
    def update_listing_field(self, listing_id: int, field: str, value: str, user: User) -> CSVData:
        listing = self.get_listing(listing_id, user)
        if not listing:
            raise ValueError("Listing not found")
        
        # Validate the update based on field type
        if field == 'price':
            if not self.validator.validate_price(value):
                raise ValueError("Invalid price format")
            
            old_price = listing.csv_row.get('Current price', listing.csv_row.get('Start price', ''))
            self.price_logger.log_price_change(listing_id, old_price, value, user.id)
            
            # Update both current price and start price if applicable
            listing.csv_row['Current price'] = value.replace('$', '')
            if 'Start price' in listing.csv_row:
                listing.csv_row['Start price'] = value.replace('$', '')
        
        elif field == 'quantity':
            if not self.validator.validate_quantity(value):
                raise ValueError("Invalid quantity")
            listing.csv_row['Available quantity'] = value
        
        elif field == 'title':
            if not self.validator.validate_title(value):
                raise ValueError("Invalid title")
            listing.csv_row['Title'] = value
        
        elif field == 'status':
            if not self.validator.validate_status(value):
                raise ValueError("Invalid status")
            listing.csv_row['Status'] = value
        
        else:
            raise ValueError(f"Field '{field}' is not allowed for update")
        
        # Mark as modified
        listing.csv_row = dict(listing.csv_row)  # Trigger SQLAlchemy dirty tracking
        
        return self.repository.update_listing(listing)
    
    def update_listing_bulk_fields(self, listing_id: int, updates: Dict[str, str], user: User) -> CSVData:
        listing = self.get_listing(listing_id, user)
        if not listing:
            raise ValueError("Listing not found")
        
        # Validate all fields before making any changes
        for field, value in updates.items():
            if field == 'price' and not self.validator.validate_price(value):
                raise ValueError(f"Invalid price: {value}")
            elif field == 'quantity' and not self.validator.validate_quantity(value):
                raise ValueError(f"Invalid quantity: {value}")
            elif field == 'title' and not self.validator.validate_title(value):
                raise ValueError(f"Invalid title: {value}")
            elif field == 'status' and not self.validator.validate_status(value):
                raise ValueError(f"Invalid status: {value}")
        
        # Apply all updates
        for field, value in updates.items():
            if field == 'price':
                old_price = listing.csv_row.get('Current price', listing.csv_row.get('Start price', ''))
                self.price_logger.log_price_change(listing_id, old_price, value, user.id)
                listing.csv_row['Current price'] = value.replace('$', '')
                if 'Start price' in listing.csv_row:
                    listing.csv_row['Start price'] = value.replace('$', '')
            elif field == 'quantity':
                listing.csv_row['Available quantity'] = value
            elif field == 'title':
                listing.csv_row['Title'] = value
            elif field == 'status':
                listing.csv_row['Status'] = value
        
        # Mark as modified
        listing.csv_row = dict(listing.csv_row)
        
        return self.repository.update_listing(listing)
    
    def get_listing_performance_metrics(self, listing_id: int, user: User) -> Dict[str, Any]:
        listing = self.get_listing(listing_id, user)
        if not listing:
            raise ValueError("Listing not found")
        
        csv_row = listing.csv_row
        
        # Calculate performance metrics
        sold_quantity = int(csv_row.get('Sold quantity', 0))
        watchers = int(csv_row.get('Watchers', 0))
        available_quantity = int(csv_row.get('Available quantity', 0))
        
        total_quantity = sold_quantity + available_quantity
        sell_through_rate = (sold_quantity / total_quantity * 100) if total_quantity > 0 else 0
        
        # Stock status
        stock_status = 'out_of_stock' if available_quantity == 0 else \
                      'low_stock' if available_quantity <= 5 else 'in_stock'
        
        return {
            'sell_through_rate': round(sell_through_rate, 2),
            'watchers_count': watchers,
            'stock_status': stock_status,
            'days_listed': self._calculate_days_listed(csv_row.get('Start date')),
            'price_competitiveness': self._assess_price_competitiveness(csv_row),
        }
    
    def _calculate_days_listed(self, start_date: str) -> int:
        if not start_date:
            return 0
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            return (datetime.now() - start).days
        except (ValueError, TypeError):
            return 0
    
    def _assess_price_competitiveness(self, csv_row: Dict[str, Any]) -> str:
        # Simplified price competitiveness assessment
        # In real implementation, this would compare with market data
        watchers = int(csv_row.get('Watchers', 0))
        sold_quantity = int(csv_row.get('Sold quantity', 0))
        
        if sold_quantity > 10 and watchers > 5:
            return 'competitive'
        elif watchers > 10:
            return 'attractive'
        elif sold_quantity == 0 and watchers == 0:
            return 'needs_review'
        else:
            return 'moderate'


def create_listing_service(db: Session) -> ListingService:
    """Factory function for creating ListingService with dependencies - Dependency Inversion"""
    repository = ListingRepository(db)
    validator = ListingValidator()
    price_logger = PriceHistoryLogger()
    return ListingService(repository, validator, price_logger)