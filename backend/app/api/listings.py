"""
Listing API Endpoints
Following SOLID principles - Single Responsibility for HTTP concerns only
YAGNI compliance: Essential endpoints only, no over-complex operations
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.services.listing_service import ListingService
from app.repositories.listing_repository import ListingRepository
from app.repositories.account_repository import AccountRepository
from app.schemas.listing import (
    ListingResponse, 
    ListingCreate, 
    ListingUpdate, 
    ListingFilter, 
    ListingBulkUpdate,
    ListingPerformanceResponse,
    ListingSearchResponse,
    ListingBulkUpdateResult,
    ListingStatusEnum
)
from app.core.exceptions import NotFoundError, ValidationException, EbayManagerException
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/listings", tags=["listings"])

def get_listing_service(db: Session = Depends(get_db)) -> ListingService:
    """
    SOLID: Dependency Inversion - Factory function for service injection
    """
    listing_repo = ListingRepository(db)
    account_repo = AccountRepository(db)
    return ListingService(listing_repo, account_repo)

@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    *,
    listing_service: ListingService = Depends(get_listing_service),
    listing_in: ListingCreate,
    current_user: User = Depends(get_current_user)
) -> ListingResponse:
    """
    Create new listing
    SOLID: Single Responsibility - Endpoint handles HTTP concerns only
    """
    try:
        listing = await listing_service.create_listing(listing_in)
        return ListingResponse.from_orm(listing)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    *,
    listing_service: ListingService = Depends(get_listing_service),
    listing_id: int,
    current_user: User = Depends(get_current_user)
) -> ListingResponse:
    """Get listing by ID"""
    try:
        listing = await listing_service.get_listing(listing_id)
        return ListingResponse.from_orm(listing)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ebay/{ebay_item_id}", response_model=Optional[ListingResponse])
async def get_listing_by_ebay_id(
    *,
    listing_service: ListingService = Depends(get_listing_service),
    ebay_item_id: str,
    current_user: User = Depends(get_current_user)
) -> Optional[ListingResponse]:
    """Get listing by eBay item ID"""
    try:
        listing = await listing_service.get_listing_by_ebay_id(ebay_item_id)
        return ListingResponse.from_orm(listing) if listing else None
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    *,
    listing_service: ListingService = Depends(get_listing_service),
    listing_id: int,
    listing_update: ListingUpdate,
    current_user: User = Depends(get_current_user)
) -> ListingResponse:
    """Update listing"""
    try:
        listing = await listing_service.update_listing(listing_id, listing_update)
        return ListingResponse.from_orm(listing)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{listing_id}")
async def delete_listing(
    *,
    listing_service: ListingService = Depends(get_listing_service),
    listing_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete listing (end listing)"""
    try:
        await listing_service.delete_listing(listing_id)
        return {"message": "Listing ended successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=ListingSearchResponse)
async def search_listings(
    *,
    listing_service: ListingService = Depends(get_listing_service),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    status: Optional[ListingStatusEnum] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, gt=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, gt=0, description="Maximum price filter"),
    search: Optional[str] = Query(None, max_length=100, description="Search in title/description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user)
) -> ListingSearchResponse:
    """
    Search listings with filters and pagination
    YAGNI: Basic filtering only, no complex search algorithms
    """
    try:
        filters = ListingFilter(
            account_id=account_id,
            status=status,
            category=category,
            min_price=min_price,
            max_price=max_price,
            search=search
        )
        
        results, total = await listing_service.search_listings(filters, page, page_size)
        
        return ListingSearchResponse(
            items=[ListingResponse.from_orm(listing) for listing in results],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account/{account_id}", response_model=List[ListingResponse])
async def get_account_listings(
    *,
    listing_service: ListingService = Depends(get_listing_service),
    account_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user)
) -> List[ListingResponse]:
    """Get all listings for specific account"""
    try:
        listings = await listing_service.get_account_listings(account_id, page, page_size)
        return [ListingResponse.from_orm(listing) for listing in listings]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-update", response_model=ListingBulkUpdateResult)
async def bulk_update_listings(
    *,
    listing_service: ListingService = Depends(get_listing_service),
    bulk_data: ListingBulkUpdate,
    current_user: User = Depends(get_current_user)
) -> ListingBulkUpdateResult:
    """Bulk update multiple listings - YAGNI: Simple operations only"""
    try:
        result = await listing_service.bulk_update_listings(bulk_data)
        return ListingBulkUpdateResult(**result)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account/{account_id}/expiring", response_model=List[ListingResponse])
async def get_expiring_listings(
    *,
    listing_service: ListingService = Depends(get_listing_service),
    account_id: int,
    days: int = Query(3, ge=1, le=30, description="Days until expiration"),
    current_user: User = Depends(get_current_user)
) -> List[ListingResponse]:
    """Get listings expiring within specified days"""
    try:
        listings = await listing_service.get_expiring_listings(account_id, days)
        return [ListingResponse.from_orm(listing) for listing in listings]
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/account/{account_id}/performance", response_model=ListingPerformanceResponse)
async def get_performance_summary(
    *,
    listing_service: ListingService = Depends(get_listing_service),
    account_id: int,
    current_user: User = Depends(get_current_user)
) -> ListingPerformanceResponse:
    """Get performance summary for account listings"""
    try:
        summary = await listing_service.get_performance_summary(account_id)
        return ListingPerformanceResponse(**summary)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/ebay/{ebay_item_id}/metrics")
async def update_performance_metrics(
    *,
    listing_service: ListingService = Depends(get_listing_service),
    ebay_item_id: str,
    view_count: int = Query(..., ge=0, description="Current view count"),
    watch_count: int = Query(..., ge=0, description="Current watch count"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Update listing performance metrics from eBay data"""
    try:
        success = await listing_service.update_performance_metrics(
            ebay_item_id, view_count, watch_count
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        return {"message": "Metrics updated successfully"}
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{listing_id}/status")
async def change_listing_status(
    *,
    listing_service: ListingService = Depends(get_listing_service),
    listing_id: int,
    status: ListingStatusEnum,
    current_user: User = Depends(get_current_user)
) -> ListingResponse:
    """Change listing status with business rule validation"""
    try:
        from app.models.listing import ListingStatus
        # Convert enum to model enum
        model_status = ListingStatus(status.value)
        listing = await listing_service.change_listing_status(listing_id, model_status)
        return ListingResponse.from_orm(listing)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))