"""
Listing Repository Implementation
Following SOLID principles - Single Responsibility for listing data access
YAGNI compliance: Essential queries only, no complex analytics
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError

from app.models.listing import Listing, ListingStatus
from app.schemas.listing import ListingFilter
from app.repositories.base import BaseRepository
from app.core.exceptions import EbayManagerException

class ListingRepositoryInterface(ABC):
    """
    SOLID: Interface Segregation & Dependency Inversion
    Clean contract for listing data access
    """
    
    @abstractmethod
    async def get_by_ebay_id(self, ebay_item_id: str) -> Optional[Listing]:
        """Get listing by eBay item ID"""
        pass
    
    @abstractmethod
    async def get_by_account(self, account_id: int, offset: int = 0, limit: int = 100) -> List[Listing]:
        """Get listings for specific account with pagination"""
        pass
    
    @abstractmethod
    async def search(self, filters: ListingFilter, offset: int = 0, limit: int = 100) -> Tuple[List[Listing], int]:
        """Search listings with filters"""
        pass
    
    @abstractmethod
    async def bulk_update_status(self, listing_ids: List[int], status: str) -> int:
        """Bulk update listing status"""
        pass
    
    @abstractmethod
    async def get_expiring_soon(self, days: int = 3) -> List[Listing]:
        """Get listings expiring within specified days"""
        pass

class ListingRepository(BaseRepository[Listing], ListingRepositoryInterface):
    """
    SOLID: Single Responsibility - Data access only
    YAGNI: Essential queries only, no complex analytics
    """
    
    def __init__(self, db: Session):
        super().__init__(db, Listing)
    
    async def get_by_ebay_id(self, ebay_item_id: str) -> Optional[Listing]:
        """Get listing by eBay item ID"""
        try:
            return self.db.query(Listing).filter(
                Listing.ebay_item_id == ebay_item_id
            ).first()
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get listing by eBay ID: {str(e)}")
    
    async def get_by_account(self, account_id: int, offset: int = 0, limit: int = 100) -> List[Listing]:
        """Get listings for specific account with pagination"""
        try:
            return self.db.query(Listing).filter(
                Listing.account_id == account_id
            ).order_by(desc(Listing.last_updated)).offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get account listings: {str(e)}")
    
    async def search(self, filters: ListingFilter, offset: int = 0, limit: int = 100) -> Tuple[List[Listing], int]:
        """
        Search listings with filters - YAGNI: Basic filtering only
        Returns (results, total_count)
        """
        try:
            query = self.db.query(Listing)
            
            # Apply filters
            conditions = []
            
            if filters.account_id:
                conditions.append(Listing.account_id == filters.account_id)
            
            if filters.status:
                conditions.append(Listing.status == filters.status.value)
            
            if filters.category:
                conditions.append(Listing.category.ilike(f"%{filters.category}%"))
            
            if filters.min_price:
                conditions.append(Listing.price >= filters.min_price)
            
            if filters.max_price:
                conditions.append(Listing.price <= filters.max_price)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                conditions.append(
                    or_(
                        Listing.title.ilike(search_term),
                        Listing.description.ilike(search_term),
                        Listing.ebay_item_id.ilike(search_term)
                    )
                )
            
            if filters.start_date_from:
                conditions.append(Listing.start_date >= filters.start_date_from)
            
            if filters.start_date_to:
                conditions.append(Listing.start_date <= filters.start_date_to)
            
            # Apply all conditions
            if conditions:
                query = query.filter(and_(*conditions))
            
            # Get total count
            total = query.count()
            
            # Get paginated results
            results = query.order_by(desc(Listing.last_updated)).offset(offset).limit(limit).all()
            
            return results, total
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to search listings: {str(e)}")
    
    async def bulk_update_status(self, listing_ids: List[int], status: str) -> int:
        """Bulk update listing status - YAGNI: Simple bulk operation"""
        try:
            if not listing_ids:
                return 0
            
            updated_count = self.db.query(Listing).filter(
                Listing.id.in_(listing_ids)
            ).update(
                {"status": status, "last_updated": datetime.utcnow()},
                synchronize_session=False
            )
            
            self.db.commit()
            return updated_count
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise EbayManagerException(f"Failed to bulk update listing status: {str(e)}")
    
    async def get_expiring_soon(self, days: int = 3) -> List[Listing]:
        """Get listings expiring within specified days"""
        try:
            expiry_date = datetime.utcnow() + timedelta(days=days)
            
            return self.db.query(Listing).filter(
                and_(
                    Listing.end_date.isnot(None),
                    Listing.end_date <= expiry_date,
                    Listing.status.in_([ListingStatus.ACTIVE.value])
                )
            ).order_by(asc(Listing.end_date)).all()
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get expiring listings: {str(e)}")
    
    async def get_performance_summary(self, account_id: int) -> Dict[str, Any]:
        """Get basic performance summary - YAGNI: Simple metrics only"""
        try:
            result = self.db.query(
                func.count(Listing.id).label('total_listings'),
                func.sum(func.case(
                    [(Listing.status == ListingStatus.ACTIVE.value, 1)], 
                    else_=0
                )).label('active_listings'),
                func.sum(Listing.quantity_sold).label('total_sold'),
                func.sum(Listing.view_count).label('total_views'),
                func.avg(Listing.price).label('avg_price')
            ).filter(Listing.account_id == account_id).first()
            
            return {
                'total_listings': result.total_listings or 0,
                'active_listings': result.active_listings or 0,
                'total_sold': result.total_sold or 0,
                'total_views': result.total_views or 0,
                'avg_price': float(result.avg_price) if result.avg_price else 0.0
            }
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get performance summary: {str(e)}")
    
    async def get_by_status(self, account_id: int, status: str, limit: int = 100) -> List[Listing]:
        """Get listings by status for specific account"""
        try:
            return self.db.query(Listing).filter(
                and_(
                    Listing.account_id == account_id,
                    Listing.status == status
                )
            ).order_by(desc(Listing.last_updated)).limit(limit).all()
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get listings by status: {str(e)}")
    
    async def count_by_account(self, account_id: int) -> int:
        """Get total listing count for account"""
        try:
            return self.db.query(Listing).filter(
                Listing.account_id == account_id
            ).count()
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to count listings: {str(e)}")
    
    async def update_performance_metrics(self, ebay_item_id: str, view_count: int, watch_count: int) -> bool:
        """Update listing performance metrics from eBay data"""
        try:
            listing = await self.get_by_ebay_id(ebay_item_id)
            if not listing:
                return False
            
            await self.update(listing.id, {
                'view_count': view_count,
                'watch_count': watch_count,
                'last_updated': datetime.utcnow()
            })
            
            return True
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to update performance metrics: {str(e)}")
        except Exception as e:
            raise EbayManagerException(f"Error updating metrics: {str(e)}")