"""
Listing Service Implementation
Following SOLID principles - Single Responsibility for listing business logic
YAGNI compliance: Essential business operations only
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from app.repositories.listing_repository import ListingRepositoryInterface
from app.repositories.account_repository import AccountRepositoryInterface
from app.schemas.listing import ListingCreate, ListingUpdate, ListingFilter, ListingBulkUpdate
from app.models.listing import Listing, ListingStatus
from app.core.exceptions import NotFoundError, ValidationException, EbayManagerException

class ListingService:
    """
    SOLID: Single Responsibility - Business logic for listing management
    YAGNI: Essential business operations only
    """
    
    def __init__(
        self,
        listing_repo: ListingRepositoryInterface,
        account_repo: AccountRepositoryInterface
    ):
        """SOLID: Dependency Inversion - Depends on abstractions"""
        self._listing_repo = listing_repo
        self._account_repo = account_repo
    
    async def create_listing(self, listing_data: ListingCreate) -> Listing:
        """Create new listing with validation"""
        # Verify account exists and is active
        account = await self._account_repo.get_by_id(listing_data.account_id)
        if not account:
            raise NotFoundError(f"Account {listing_data.account_id} not found")
        
        if account.status != 'active':
            raise ValidationException(f"Account {listing_data.account_id} is not active")
        
        # Check for duplicate eBay item ID
        existing = await self._listing_repo.get_by_ebay_id(listing_data.ebay_item_id)
        if existing:
            raise ValidationException(f"Listing with eBay ID {listing_data.ebay_item_id} already exists")
        
        # Validate end date if provided
        if listing_data.end_date and listing_data.end_date <= listing_data.start_date:
            raise ValidationException("End date must be after start date")
        
        # YAGNI: Basic business rule validation only
        if listing_data.price <= 0:
            raise ValidationException("Price must be positive")
        
        if listing_data.quantity_available < 0:
            raise ValidationException("Quantity cannot be negative")
        
        # Create listing
        listing = Listing(
            ebay_item_id=listing_data.ebay_item_id,
            account_id=listing_data.account_id,
            title=listing_data.title,
            description=listing_data.description,
            category=listing_data.category,
            price=listing_data.price,
            quantity_available=listing_data.quantity_available,
            format_type=listing_data.format_type,
            duration_days=listing_data.duration_days,
            start_date=listing_data.start_date,
            end_date=listing_data.end_date,
            status=ListingStatus.ACTIVE.value
        )
        
        return await self._listing_repo.create(listing)
    
    async def get_listing(self, listing_id: int) -> Listing:
        """Get listing by ID"""
        listing = await self._listing_repo.get_by_id(listing_id)
        if not listing:
            raise NotFoundError(f"Listing {listing_id} not found")
        return listing
    
    async def get_listing_by_ebay_id(self, ebay_item_id: str) -> Optional[Listing]:
        """Get listing by eBay item ID"""
        return await self._listing_repo.get_by_ebay_id(ebay_item_id)
    
    async def update_listing(self, listing_id: int, update_data: ListingUpdate) -> Listing:
        """Update listing with validation"""
        listing = await self.get_listing(listing_id)
        
        # Validate status change
        if update_data.status and update_data.status.value not in [s.value for s in ListingStatus]:
            raise ValidationException(f"Invalid status: {update_data.status}")
        
        # Business rule: Can't activate if quantity is 0
        if (update_data.status == ListingStatus.ACTIVE and 
            (update_data.quantity_available == 0 or 
             (update_data.quantity_available is None and listing.quantity_available == 0))):
            raise ValidationException("Cannot activate listing with 0 quantity")
        
        # Business rule: Can't activate if listing has expired
        if (update_data.status == ListingStatus.ACTIVE and 
            listing.end_date and listing.end_date <= datetime.utcnow()):
            raise ValidationException("Cannot activate expired listing")
        
        # Validate price if provided
        if update_data.price is not None and update_data.price <= 0:
            raise ValidationException("Price must be positive")
        
        # Validate quantity if provided
        if update_data.quantity_available is not None and update_data.quantity_available < 0:
            raise ValidationException("Quantity cannot be negative")
        
        # Prepare update data
        update_dict = {}
        if update_data.title is not None:
            update_dict['title'] = update_data.title
        if update_data.description is not None:
            update_dict['description'] = update_data.description
        if update_data.category is not None:
            update_dict['category'] = update_data.category
        if update_data.price is not None:
            update_dict['price'] = update_data.price
        if update_data.quantity_available is not None:
            update_dict['quantity_available'] = update_data.quantity_available
        if update_data.status is not None:
            update_dict['status'] = update_data.status.value
        if update_data.end_date is not None:
            update_dict['end_date'] = update_data.end_date
        if update_data.format_type is not None:
            update_dict['format_type'] = update_data.format_type
        if update_data.duration_days is not None:
            update_dict['duration_days'] = update_data.duration_days
        
        if update_dict:
            update_dict['last_updated'] = datetime.utcnow()
        
        return await self._listing_repo.update(listing_id, update_dict)
    
    async def delete_listing(self, listing_id: int) -> bool:
        """Delete listing (soft delete by setting status)"""
        listing = await self.get_listing(listing_id)
        
        # YAGNI: Simple status update instead of hard delete
        # Business rule: Don't delete if there are active related orders
        # Note: This would require order repository in full implementation
        
        await self._listing_repo.update(listing_id, {
            'status': ListingStatus.ENDED.value,
            'last_updated': datetime.utcnow()
        })
        
        return True
    
    async def search_listings(
        self, 
        filters: ListingFilter, 
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[Listing], int]:
        """Search listings with pagination"""
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50
        
        offset = (page - 1) * page_size
        return await self._listing_repo.search(filters, offset, page_size)
    
    async def bulk_update_listings(self, bulk_data: ListingBulkUpdate) -> Dict[str, Any]:
        """Bulk update listings - YAGNI: Simple operations only"""
        if not bulk_data.listing_ids:
            raise ValidationException("No listing IDs provided")
        
        if len(bulk_data.listing_ids) > 1000:
            raise ValidationException("Cannot update more than 1000 listings at once")
        
        result = {'updated': 0, 'errors': [], 'warnings': []}
        
        # Validate status if provided
        if bulk_data.status and bulk_data.status.value not in [s.value for s in ListingStatus]:
            raise ValidationException(f"Invalid status: {bulk_data.status}")
        
        # Validate price if provided
        if bulk_data.price is not None and bulk_data.price <= 0:
            raise ValidationException("Price must be positive")
        
        # Validate quantity if provided
        if bulk_data.quantity_available is not None and bulk_data.quantity_available < 0:
            raise ValidationException("Quantity cannot be negative")
        
        # Perform bulk update
        update_data = {}
        if bulk_data.status:
            update_data['status'] = bulk_data.status.value
        if bulk_data.price is not None:
            update_data['price'] = bulk_data.price
        if bulk_data.quantity_available is not None:
            update_data['quantity_available'] = bulk_data.quantity_available
        
        if update_data:
            update_data['last_updated'] = datetime.utcnow()
            try:
                updated_count = await self._listing_repo.bulk_update(bulk_data.listing_ids, update_data)
                result['updated'] = updated_count
                
                # Check if all listings were updated
                if updated_count < len(bulk_data.listing_ids):
                    result['warnings'].append(f"Only {updated_count} of {len(bulk_data.listing_ids)} listings were updated")
                    
            except EbayManagerException as e:
                result['errors'].append(str(e))
        
        return result
    
    async def get_account_listings(
        self, 
        account_id: int, 
        page: int = 1, 
        page_size: int = 50
    ) -> List[Listing]:
        """Get listings for specific account"""
        # Verify account exists
        account = await self._account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundError(f"Account {account_id} not found")
        
        # Validate pagination
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50
        
        offset = (page - 1) * page_size
        return await self._listing_repo.get_by_account(account_id, offset, page_size)
    
    async def get_expiring_listings(self, account_id: int, days: int = 3) -> List[Listing]:
        """Get listings expiring soon for specific account"""
        if days < 1 or days > 30:
            raise ValidationException("Days must be between 1 and 30")
        
        all_expiring = await self._listing_repo.get_expiring_soon(days)
        return [listing for listing in all_expiring if listing.account_id == account_id]
    
    async def get_performance_summary(self, account_id: int) -> Dict[str, Any]:
        """Get basic performance summary for account listings"""
        # Verify account exists
        account = await self._account_repo.get_by_id(account_id)
        if not account:
            raise NotFoundError(f"Account {account_id} not found")
        
        return await self._listing_repo.get_performance_summary(account_id)
    
    async def update_performance_metrics(self, ebay_item_id: str, view_count: int, watch_count: int) -> bool:
        """Update listing performance metrics from eBay data"""
        if view_count < 0 or watch_count < 0:
            raise ValidationException("Metrics cannot be negative")
        
        listing = await self._listing_repo.get_by_ebay_id(ebay_item_id)
        if not listing:
            return False
        
        await self._listing_repo.update(listing.id, {
            'view_count': view_count,
            'watch_count': watch_count,
            'last_updated': datetime.utcnow()
        })
        
        return True
    
    async def change_listing_status(self, listing_id: int, new_status: ListingStatus) -> Listing:
        """Change listing status with business rules"""
        listing = await self.get_listing(listing_id)
        
        # Business rules for status transitions
        if new_status == ListingStatus.ACTIVE:
            if listing.quantity_available <= 0:
                raise ValidationException("Cannot activate listing with 0 quantity")
            if listing.end_date and listing.end_date <= datetime.utcnow():
                raise ValidationException("Cannot activate expired listing")
        
        return await self._listing_repo.update(listing_id, {
            'status': new_status.value,
            'last_updated': datetime.utcnow()
        })