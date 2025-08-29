# Phase 5: Listing Management Module Implementation

## Overview
Implement comprehensive listing management system with inventory tracking, performance analytics, and bulk operations. Integrates with Dashboard1.png metrics display and supports multi-account listing operations with real-time synchronization.

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **ListingService**: Only handle listing business logic and lifecycle
- **ListingRepository**: Only manage listing data persistence
- **InventoryService**: Only handle inventory tracking and updates
- **ListingAnalyticsService**: Only generate listing performance metrics
- **BulkOperationService**: Only handle batch listing operations

### Open/Closed Principle (OCP)
- **Listing Status Management**: Extensible status workflows
- **Performance Calculators**: Add new metrics without changing existing code
- **Export Formats**: Support multiple export formats through strategy pattern
- **Pricing Strategies**: Pluggable pricing rules and calculations

### Liskov Substitution Principle (LSP)
- **IListingRepository**: All listing repositories interchangeable
- **IInventoryTracker**: All inventory implementations follow same contract
- **IPerformanceCalculator**: All analytics calculators substitutable

### Interface Segregation Principle (ISP)
- **Separate Interfaces**: CRUD vs Analytics vs Bulk Operations
- **Client-Specific**: Viewers don't depend on admin operations
- **Granular Permissions**: Read vs Write vs Admin operations

### Dependency Inversion Principle (DIP)
- **Abstract Dependencies**: Services depend on interfaces
- **Injected Components**: All external services properly injected

## Listing Domain Models

```python
# app/models/listing.py - Single Responsibility: Listing data representation
from sqlalchemy import Column, String, DateTime, Decimal, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSON
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from enum import Enum
from app.database import Base

class ListingStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SOLD = "sold"
    ENDED = "ended"
    SUSPENDED = "suspended"
    OUT_OF_STOCK = "out_of_stock"

class ListingFormat(Enum):
    AUCTION = "auction"
    BUY_IT_NOW = "buy_it_now"
    CLASSIFIED = "classified"
    STORE_INVENTORY = "store_inventory"

class Listing(Base):
    """eBay listing entity with comprehensive tracking"""
    __tablename__ = "listings"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    ebay_item_id = Column(String(50), nullable=False)
    
    # Basic listing information
    title = Column(String(500), nullable=False)
    description = Column(Text)
    category_id = Column(String(20))
    category_name = Column(String(200))
    
    # Pricing and inventory
    current_price = Column(Decimal(10, 2), nullable=False)
    starting_price = Column(Decimal(10, 2))
    buy_it_now_price = Column(Decimal(10, 2))
    quantity_available = Column(Integer, default=1)
    quantity_sold = Column(Integer, default=0)
    
    # Status and timing
    listing_status = Column(ENUM(ListingStatus), default=ListingStatus.DRAFT)
    listing_format = Column(ENUM(ListingFormat), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    
    # Performance metrics
    view_count = Column(Integer, default=0)
    watch_count = Column(Integer, default=0)
    question_count = Column(Integer, default=0)
    bid_count = Column(Integer, default=0)
    
    # eBay specific data
    listing_url = Column(String(500))
    gallery_url = Column(String(500))
    condition_id = Column(String(10))
    condition_description = Column(String(200))
    
    # Internal tracking
    sku = Column(String(100))
    cost_price = Column(Decimal(10, 2))
    profit_margin = Column(Decimal(5, 2))  # Percentage
    tags = Column(JSON)  # Array of tags for internal organization
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync_at = Column(DateTime)  # Last eBay sync
    
    # Relationships
    account = relationship("Account", back_populates="listings")
    order_items = relationship("OrderItem", back_populates="listing")
    listing_history = relationship("ListingHistory", back_populates="listing")
    
class ListingHistory(Base):
    """Listing change history tracking"""
    __tablename__ = "listing_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)
    
    # Change tracking
    field_name = Column(String(100), nullable=False)
    old_value = Column(String(500))
    new_value = Column(String(500))
    change_reason = Column(String(200))
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    changed_at = Column(DateTime, default=datetime.utcnow)
    
    # Context
    system_generated = Column(Boolean, default=False)
    
    # Relationships
    listing = relationship("Listing", back_populates="listing_history")
    user = relationship("User")
```

## Listing Service Implementation

```python
# app/services/listing_service.py - Single Responsibility: Listing business logic
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
import logging
from decimal import Decimal
from app.repositories.listing import ListingRepository
from app.services.inventory_service import InventoryService
from app.services.listing_analytics import ListingAnalyticsService
from app.models.listing import Listing, ListingStatus
from app.schemas.listing import ListingCreate, ListingUpdate, ListingFilter

class ListingService:
    """Comprehensive listing management service"""
    
    def __init__(
        self,
        listing_repo: ListingRepository,
        inventory_service: InventoryService,
        analytics_service: ListingAnalyticsService
    ):
        self._listing_repo = listing_repo
        self._inventory_service = inventory_service
        self._analytics_service = analytics_service
        self._logger = logging.getLogger(__name__)
    
    async def get_account_listings(
        self,
        account_id: UUID,
        filters: ListingFilter,
        skip: int = 0,
        limit: int = 100
    ) -> List[Listing]:
        """Get filtered listings for account"""
        return await self._listing_repo.get_filtered_listings(
            account_id, filters, skip, limit
        )
    
    async def get_listing_by_id(self, listing_id: UUID) -> Optional[Listing]:
        """Get single listing by ID"""
        return await self._listing_repo.get_by_id(listing_id)
    
    async def create_listing(self, listing_data: ListingCreate) -> Listing:
        """Create new listing with validation"""
        # Business rule: Check for duplicate eBay item ID
        if listing_data.ebay_item_id:
            existing = await self._listing_repo.get_by_ebay_item_id(
                listing_data.account_id,
                listing_data.ebay_item_id
            )
            if existing:
                raise ValueError(
                    f"Listing with eBay item ID {listing_data.ebay_item_id} already exists"
                )
        
        # Validate pricing
        await self._validate_pricing(listing_data)
        
        # Create listing
        listing = await self._listing_repo.create(listing_data)
        
        # Initialize inventory tracking
        await self._inventory_service.initialize_listing_inventory(
            listing.id,
            listing_data.quantity_available or 1
        )
        
        self._logger.info(f"Created listing {listing.title} for account {listing.account_id}")
        return listing
    
    async def update_listing(self, listing_id: UUID, listing_data: ListingUpdate) -> Listing:
        """Update existing listing with business logic"""
        existing_listing = await self._listing_repo.get_by_id(listing_id)
        if not existing_listing:
            raise ValueError(f"Listing {listing_id} not found")
        
        # Validate pricing if changed
        if any(field in listing_data.dict(exclude_unset=True) 
               for field in ['current_price', 'starting_price', 'buy_it_now_price']):
            await self._validate_pricing(listing_data, existing_listing)
        
        # Track inventory changes
        if listing_data.quantity_available is not None:
            await self._inventory_service.update_listing_inventory(
                listing_id,
                listing_data.quantity_available
            )
        
        # Update listing
        updated_listing = await self._listing_repo.update(listing_id, listing_data)
        
        # Auto-update status based on inventory
        await self._auto_update_status_by_inventory(listing_id)
        
        return updated_listing
    
    async def update_listing_status(
        self,
        listing_id: UUID,
        new_status: ListingStatus,
        reason: str,
        user_id: UUID
    ) -> Listing:
        """Update listing status with validation"""
        listing = await self._listing_repo.get_by_id(listing_id)
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")
        
        # Validate status transition
        if not self._is_valid_status_transition(listing.listing_status, new_status):
            raise ValueError(
                f"Invalid status transition from {listing.listing_status} to {new_status}"
            )
        
        # Update status
        old_status = listing.listing_status
        updated_listing = await self._listing_repo.update_status(
            listing_id, new_status
        )
        
        # Track history
        await self._track_status_change(
            listing_id, old_status, new_status, reason, user_id
        )
        
        return updated_listing
    
    async def get_listing_metrics(
        self,
        account_id: UUID,
        date_range: tuple
    ) -> Dict[str, Any]:
        """Get listing performance metrics for dashboard"""
        return await self._analytics_service.get_listing_metrics(
            account_id, date_range
        )
    
    async def bulk_update_status(
        self,
        listing_ids: List[UUID],
        new_status: ListingStatus,
        reason: str,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Bulk update listing status"""
        success_count = 0
        failed_count = 0
        errors = []
        
        for listing_id in listing_ids:
            try:
                await self.update_listing_status(
                    listing_id, new_status, reason, user_id
                )
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"Listing {listing_id}: {str(e)}")
                self._logger.error(f"Failed to update listing {listing_id}: {e}")
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors
        }
    
    async def _validate_pricing(self, listing_data, existing_listing=None) -> None:
        """Validate listing pricing rules"""
        current_price = getattr(listing_data, 'current_price', None)
        if existing_listing and current_price is None:
            current_price = existing_listing.current_price
        
        starting_price = getattr(listing_data, 'starting_price', None)
        if existing_listing and starting_price is None:
            starting_price = existing_listing.starting_price
        
        buy_it_now_price = getattr(listing_data, 'buy_it_now_price', None)
        if existing_listing and buy_it_now_price is None:
            buy_it_now_price = existing_listing.buy_it_now_price
        
        # Business rules
        if current_price and current_price <= 0:
            raise ValueError("Current price must be positive")
        
        if starting_price and starting_price <= 0:
            raise ValueError("Starting price must be positive")
        
        if (buy_it_now_price and starting_price and 
            buy_it_now_price < starting_price):
            raise ValueError("Buy It Now price cannot be less than starting price")
    
    def _is_valid_status_transition(
        self,
        current: ListingStatus,
        new: ListingStatus
    ) -> bool:
        """Validate listing status transitions"""
        valid_transitions = {
            ListingStatus.DRAFT: [
                ListingStatus.ACTIVE, ListingStatus.INACTIVE
            ],
            ListingStatus.ACTIVE: [
                ListingStatus.INACTIVE, ListingStatus.SOLD, 
                ListingStatus.ENDED, ListingStatus.OUT_OF_STOCK
            ],
            ListingStatus.INACTIVE: [
                ListingStatus.ACTIVE, ListingStatus.ENDED
            ],
            ListingStatus.OUT_OF_STOCK: [
                ListingStatus.ACTIVE, ListingStatus.INACTIVE
            ],
            ListingStatus.SOLD: [],  # Terminal state
            ListingStatus.ENDED: [],  # Terminal state
            ListingStatus.SUSPENDED: [ListingStatus.ACTIVE, ListingStatus.INACTIVE]
        }
        
        return new in valid_transitions.get(current, [])
    
    async def _auto_update_status_by_inventory(self, listing_id: UUID) -> None:
        """Auto-update listing status based on inventory"""
        listing = await self._listing_repo.get_by_id(listing_id)
        if not listing:
            return
        
        # Check if listing should be marked out of stock
        if (listing.quantity_available <= 0 and 
            listing.listing_status == ListingStatus.ACTIVE):
            await self._listing_repo.update_status(
                listing_id, ListingStatus.OUT_OF_STOCK
            )
        
        # Check if out of stock listing can be reactivated
        elif (listing.quantity_available > 0 and 
              listing.listing_status == ListingStatus.OUT_OF_STOCK):
            await self._listing_repo.update_status(
                listing_id, ListingStatus.ACTIVE
            )
    
    async def _track_status_change(
        self,
        listing_id: UUID,
        old_status: ListingStatus,
        new_status: ListingStatus,
        reason: str,
        user_id: UUID
    ) -> None:
        """Track listing status change in history"""
        # Implementation for tracking listing history
        pass
```

## REST API Implementation

```python
# app/routers/listings.py - Single Responsibility: Listing HTTP endpoints
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.services.listing_service import ListingService
from app.dependencies.auth import get_current_user, require_permission
from app.schemas.listing import (
    ListingResponse, ListingCreate, ListingUpdate, 
    ListingFilter, ListingStatusUpdate, BulkStatusUpdate
)
from app.models.token import TokenPayload

router = APIRouter(prefix="/api/accounts/{account_id}/listings", tags=["listings"])

@router.get("/", response_model=List[ListingResponse])
async def get_listings(
    account_id: UUID,
    status: Optional[List[str]] = Query(None),
    category: Optional[str] = None,
    title_search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: TokenPayload = Depends(require_permission("read", account_id)),
    listing_service: ListingService = Depends(get_listing_service)
):
    """Get listings with filtering"""
    filters = ListingFilter(
        status=status,
        category=category,
        title_search=title_search
    )
    
    listings = await listing_service.get_account_listings(
        account_id, filters, skip, limit
    )
    return [ListingResponse.from_orm(listing) for listing in listings]

@router.post("/", response_model=ListingResponse)
async def create_listing(
    account_id: UUID,
    listing_data: ListingCreate,
    current_user: TokenPayload = Depends(require_permission("write", account_id)),
    listing_service: ListingService = Depends(get_listing_service)
):
    """Create new listing"""
    listing_data.account_id = account_id
    
    try:
        listing = await listing_service.create_listing(listing_data)
        return ListingResponse.from_orm(listing)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    account_id: UUID,
    listing_id: UUID,
    listing_data: ListingUpdate,
    current_user: TokenPayload = Depends(require_permission("write", account_id)),
    listing_service: ListingService = Depends(get_listing_service)
):
    """Update existing listing"""
    # Verify listing belongs to account
    existing_listing = await listing_service.get_listing_by_id(listing_id)
    if not existing_listing or existing_listing.account_id != account_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    try:
        listing = await listing_service.update_listing(listing_id, listing_data)
        return ListingResponse.from_orm(listing)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/bulk/status")
async def bulk_update_status(
    account_id: UUID,
    bulk_update: BulkStatusUpdate,
    current_user: TokenPayload = Depends(require_permission("write", account_id)),
    listing_service: ListingService = Depends(get_listing_service)
):
    """Bulk update listing status"""
    result = await listing_service.bulk_update_status(
        bulk_update.listing_ids,
        bulk_update.new_status,
        bulk_update.reason,
        current_user.user_id
    )
    
    return result
```

## Implementation Tasks

### Task 1: Listing Models & Database
1. **Create Listing Models**
   - Listing entity with comprehensive fields
   - ListingHistory for change tracking
   - Database indexes for performance

2. **Repository Implementation**
   - CRUD operations with filtering
   - Bulk operations support
   - Performance optimization

### Task 2: Business Logic Services
1. **Listing Service**
   - Status workflow management
   - Pricing validation rules
   - Inventory integration

2. **Analytics Service**
   - Performance metrics calculation
   - Dashboard data aggregation
   - Reporting functionality

### Task 3: API Implementation
1. **REST Endpoints**
   - Full CRUD operations
   - Bulk update capabilities
   - Advanced filtering

2. **Security & Validation**
   - Permission-based access
   - Input validation
   - Account isolation

## Quality Gates

### Performance Requirements
- [ ] Listing queries: <300ms for 1000 listings
- [ ] Bulk operations: Handle 100+ listings efficiently
- [ ] Dashboard metrics: <500ms load time
- [ ] Support 50,000+ listings per account

### SOLID Compliance
- [ ] Single responsibility per service
- [ ] Extensible status workflows
- [ ] Interchangeable repository implementations
- [ ] Separated read/write operations
- [ ] Dependency injection throughout

---
**Next Phase**: Product & Supplier Management with inventory synchronization.