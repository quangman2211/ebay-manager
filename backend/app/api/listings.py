"""
Ultra-simplified Listings API Endpoints
Following YAGNI principles - 90% complexity reduction
YAGNI: Essential CRUD operations only, no over-engineered features
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.base import get_db
from app.repositories.listing_repository import ListingRepository
from app.models.listing import ListingStatus
from app.schemas.listing import ListingCreate, ListingUpdate, ListingResponse
from app.core.exceptions import NotFoundError, ValidationException
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/listings", tags=["listings"])


def get_listing_repository(db: Session = Depends(get_db)) -> ListingRepository:
    """Dependency injection for listing repository"""
    return ListingRepository(db)


@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    *,
    listing_repo: ListingRepository = Depends(get_listing_repository),
    listing: ListingCreate,
    current_user: User = Depends(get_current_user)
) -> ListingResponse:
    """
    Create new listing
    YAGNI: Basic creation only, no complex validation or business rules
    """
    try:
        db_listing = await listing_repo.create(listing)
        return ListingResponse.from_orm(db_listing)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create listing: {str(e)}")


@router.get("/", response_model=List[ListingResponse])
async def get_listings(
    *,
    listing_repo: ListingRepository = Depends(get_listing_repository),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of listings to return"),
    offset: int = Query(0, ge=0, description="Number of listings to skip"),
    current_user: User = Depends(get_current_user)
) -> List[ListingResponse]:
    """
    Get listings with basic filtering
    YAGNI: Simple listing with essential filters only
    """
    try:
        listings = await listing_repo.get_listings(
            account_id=account_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return [ListingResponse.from_orm(listing) for listing in listings]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get listings: {str(e)}")


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    *,
    listing_repo: ListingRepository = Depends(get_listing_repository),
    listing_id: int,
    current_user: User = Depends(get_current_user)
) -> ListingResponse:
    """
    Get single listing by ID
    YAGNI: Basic retrieval only
    """
    try:
        listing = await listing_repo.get_by_id(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        return ListingResponse.from_orm(listing)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get listing: {str(e)}")


@router.put("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    *,
    listing_repo: ListingRepository = Depends(get_listing_repository),
    listing_id: int,
    listing_update: ListingUpdate,
    current_user: User = Depends(get_current_user)
) -> ListingResponse:
    """
    Update existing listing
    YAGNI: Basic updates only, no complex validation
    """
    try:
        existing_listing = await listing_repo.get_by_id(listing_id)
        if not existing_listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        update_data = listing_update.dict(exclude_unset=True)
        updated_listing = await listing_repo.update(listing_id, update_data)
        return ListingResponse.from_orm(updated_listing)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update listing: {str(e)}")


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    *,
    listing_repo: ListingRepository = Depends(get_listing_repository),
    listing_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Delete listing
    YAGNI: Simple deletion only
    """
    try:
        existing_listing = await listing_repo.get_by_id(listing_id)
        if not existing_listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        await listing_repo.delete(listing_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete listing: {str(e)}")


# Simple bulk operations - YAGNI: Basic bulk updates only
@router.post("/bulk-update-status", response_model=Dict[str, Any])
async def bulk_update_status(
    *,
    listing_repo: ListingRepository = Depends(get_listing_repository),
    listing_ids: List[int],
    new_status: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update status for multiple listings
    YAGNI: Simple bulk status update, no complex framework
    """
    try:
        # Validate status
        if new_status not in [s.value for s in ListingStatus]:
            raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
        
        if len(listing_ids) > 500:
            raise HTTPException(status_code=400, detail="Too many listings (max 500)")
        
        success_count = 0
        error_count = 0
        errors = []
        
        for listing_id in listing_ids:
            try:
                await listing_repo.update(listing_id, {'status': new_status})
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"Listing {listing_id}: {str(e)}")
        
        return {
            "message": f"Bulk status update completed",
            "total_items": len(listing_ids),
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[-10:]  # Last 10 errors only
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk update failed: {str(e)}")


@router.post("/bulk-update-price", response_model=Dict[str, Any])
async def bulk_update_price(
    *,
    listing_repo: ListingRepository = Depends(get_listing_repository),
    listing_ids: List[int],
    new_price: Decimal,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update price for multiple listings
    YAGNI: Simple bulk price update, no complex framework
    """
    try:
        if new_price <= 0:
            raise HTTPException(status_code=400, detail="Price must be positive")
        
        if len(listing_ids) > 500:
            raise HTTPException(status_code=400, detail="Too many listings (max 500)")
        
        success_count = 0
        error_count = 0
        errors = []
        
        for listing_id in listing_ids:
            try:
                await listing_repo.update(listing_id, {'price': new_price})
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"Listing {listing_id}: {str(e)}")
        
        return {
            "message": f"Bulk price update completed",
            "total_items": len(listing_ids),
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[-10:]  # Last 10 errors only
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk price update failed: {str(e)}")


@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_listing_stats(
    *,
    listing_repo: ListingRepository = Depends(get_listing_repository),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get basic listing statistics
    YAGNI: Simple counts only, no complex analytics
    """
    try:
        stats = await listing_repo.get_listing_counts(account_id)
        return {
            "total_listings": stats.get('total', 0),
            "active_listings": stats.get('active', 0),
            "inactive_listings": stats.get('inactive', 0),
            "ended_listings": stats.get('ended', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")