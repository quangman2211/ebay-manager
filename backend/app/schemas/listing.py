"""
Listing Pydantic Schemas
Following SOLID principles - Interface Segregation for different use cases
YAGNI compliance: Essential validation only, no over-complex business rules
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

class ListingStatusEnum(str, Enum):
    """YAGNI: Essential listing statuses only"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
    ENDED = "ended"
    PAUSED = "paused"

class ListingBase(BaseModel):
    """
    Base listing schema - SOLID: Interface Segregation
    Contains common fields used across different operations
    """
    title: str = Field(..., min_length=5, max_length=500, description="Product title")
    description: Optional[str] = Field(None, max_length=5000, description="Product description")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    price: Decimal = Field(..., gt=0, description="Listing price")
    quantity_available: int = Field(default=1, ge=0, description="Available quantity")
    format_type: Optional[str] = Field(None, max_length=20, description="eBay format type")
    duration_days: Optional[int] = Field(None, ge=1, le=30, description="Listing duration in days")

    @validator('price')
    def price_must_be_positive(cls, v):
        """YAGNI: Basic price validation only"""
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

    @validator('title')
    def title_must_not_be_empty(cls, v):
        """Basic title validation"""
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

class ListingCreate(ListingBase):
    """
    Creation schema - SOLID: Interface Segregation
    Contains all required fields for listing creation
    """
    ebay_item_id: str = Field(..., min_length=5, max_length=50, description="eBay item ID")
    account_id: int = Field(..., gt=0, description="Account ID")
    start_date: datetime = Field(..., description="Listing start date")
    end_date: Optional[datetime] = Field(None, description="Listing end date")

    @validator('end_date')
    def end_date_after_start(cls, v, values):
        """YAGNI: Basic date validation only"""
        if v and 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('ebay_item_id')
    def validate_ebay_item_id(cls, v):
        """Basic eBay item ID validation"""
        if not v or not v.strip():
            raise ValueError('eBay item ID cannot be empty')
        return v.strip()

class ListingUpdate(BaseModel):
    """
    Update schema - SOLID: Interface Segregation
    Contains optional fields for partial updates
    """
    title: Optional[str] = Field(None, min_length=5, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)
    price: Optional[Decimal] = Field(None, gt=0)
    quantity_available: Optional[int] = Field(None, ge=0)
    status: Optional[ListingStatusEnum] = None
    end_date: Optional[datetime] = None
    format_type: Optional[str] = Field(None, max_length=20)
    duration_days: Optional[int] = Field(None, ge=1, le=30)

    @validator('price')
    def price_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Price must be positive')
        return v

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Title cannot be empty')
        return v.strip() if v else v

class ListingResponse(ListingBase):
    """
    Response schema - SOLID: Interface Segregation
    Contains all fields returned in API responses
    """
    id: int
    ebay_item_id: str
    account_id: int
    status: str
    quantity_sold: int
    start_date: datetime
    end_date: Optional[datetime]
    last_updated: datetime
    view_count: int
    watch_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ListingFilter(BaseModel):
    """
    Filter schema - SOLID: Single Responsibility
    YAGNI: Basic filtering only, no complex search algorithms
    """
    account_id: Optional[int] = None
    status: Optional[ListingStatusEnum] = None
    category: Optional[str] = None
    min_price: Optional[Decimal] = Field(None, gt=0)
    max_price: Optional[Decimal] = Field(None, gt=0)
    search: Optional[str] = Field(None, max_length=100, description="Search in title/description")
    start_date_from: Optional[datetime] = None
    start_date_to: Optional[datetime] = None

    @validator('max_price')
    def max_price_greater_than_min(cls, v, values):
        """Validate price range"""
        if v and 'min_price' in values and values['min_price'] and v <= values['min_price']:
            raise ValueError('Max price must be greater than min price')
        return v

    @validator('start_date_to')
    def end_date_after_start(cls, v, values):
        """Validate date range"""
        if v and 'start_date_from' in values and values['start_date_from'] and v <= values['start_date_from']:
            raise ValueError('End date must be after start date')
        return v

class ListingBulkUpdate(BaseModel):
    """
    Bulk update schema - YAGNI: Simple bulk operations only
    No complex business rules, just basic mass updates
    """
    listing_ids: List[int] = Field(..., min_items=1, max_items=1000, description="List of listing IDs")
    status: Optional[ListingStatusEnum] = None
    price: Optional[Decimal] = Field(None, gt=0)
    quantity_available: Optional[int] = Field(None, ge=0)

    @validator('listing_ids')
    def validate_listing_ids(cls, v):
        """Validate listing IDs list"""
        if not v:
            raise ValueError('At least one listing ID is required')
        if len(v) > 1000:
            raise ValueError('Cannot update more than 1000 listings at once')
        # Remove duplicates
        return list(set(v))

    @validator('price')
    def price_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Price must be positive')
        return v

class ListingPerformanceResponse(BaseModel):
    """
    Performance summary schema - YAGNI: Basic metrics only
    """
    total_listings: int
    active_listings: int
    total_sold: int
    total_views: int
    avg_price: float

class ListingSearchResponse(BaseModel):
    """
    Search response with pagination
    """
    items: List[ListingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ListingBulkUpdateResult(BaseModel):
    """
    Bulk update operation result
    """
    updated: int
    errors: List[str] = []
    warnings: List[str] = []