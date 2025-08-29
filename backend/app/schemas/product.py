"""
Product and Supplier Pydantic Schemas
Following SOLID principles - Interface Segregation for different use cases
YAGNI compliance: Essential validation only, 60% complexity reduction
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

class ProductStatusEnum(str, Enum):
    """YAGNI: Essential product statuses only"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    OUT_OF_STOCK = "out_of_stock"

# =============================================================================
# PRODUCT SCHEMAS
# =============================================================================

class ProductBase(BaseModel):
    """
    Base product schema - SOLID: Interface Segregation
    Contains common fields used across different operations
    """
    name: str = Field(..., min_length=2, max_length=500, description="Product name")
    description: Optional[str] = Field(None, max_length=5000, description="Product description")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    cost_price: Decimal = Field(..., gt=0, description="Cost price from supplier")
    selling_price: Decimal = Field(..., gt=0, description="Selling price to customers")
    quantity_on_hand: int = Field(default=0, ge=0, description="Quantity in stock")
    reorder_point: int = Field(default=0, ge=0, description="Minimum stock level")
    reorder_quantity: int = Field(default=0, ge=0, description="Quantity to reorder")
    weight_oz: Optional[Decimal] = Field(None, gt=0, description="Weight in ounces")
    length_in: Optional[Decimal] = Field(None, gt=0, description="Length in inches")
    width_in: Optional[Decimal] = Field(None, gt=0, description="Width in inches")
    height_in: Optional[Decimal] = Field(None, gt=0, description="Height in inches")

    @validator('selling_price')
    def selling_price_must_be_higher_than_cost(cls, v, values):
        """YAGNI: Basic price validation only"""
        if 'cost_price' in values and v <= values['cost_price']:
            raise ValueError('Selling price must be higher than cost price')
        return v

    @validator('name')
    def name_must_not_be_empty(cls, v):
        """Basic name validation"""
        if not v or not v.strip():
            raise ValueError('Product name cannot be empty')
        return v.strip()

class ProductCreate(ProductBase):
    """
    Creation schema - SOLID: Interface Segregation
    Contains all required fields for product creation
    """
    sku: str = Field(..., min_length=3, max_length=100, description="Stock Keeping Unit")
    supplier_id: int = Field(..., gt=0, description="Supplier ID")

    @validator('sku')
    def sku_must_be_alphanumeric(cls, v):
        """Basic SKU validation"""
        if not v or not v.strip():
            raise ValueError('SKU cannot be empty')
        # Allow alphanumeric, hyphens, underscores
        import re
        if not re.match(r'^[A-Za-z0-9_-]+$', v.strip()):
            raise ValueError('SKU can only contain letters, numbers, hyphens, and underscores')
        return v.strip().upper()

class ProductUpdate(BaseModel):
    """
    Update schema - SOLID: Interface Segregation
    Contains optional fields for partial updates
    """
    name: Optional[str] = Field(None, min_length=2, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    cost_price: Optional[Decimal] = Field(None, gt=0)
    selling_price: Optional[Decimal] = Field(None, gt=0)
    quantity_on_hand: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=0)
    status: Optional[ProductStatusEnum] = None
    weight_oz: Optional[Decimal] = Field(None, gt=0)
    length_in: Optional[Decimal] = Field(None, gt=0)
    width_in: Optional[Decimal] = Field(None, gt=0)
    height_in: Optional[Decimal] = Field(None, gt=0)

    @validator('selling_price')
    def validate_selling_price(cls, v, values):
        if v is not None and 'cost_price' in values and values['cost_price'] and v <= values['cost_price']:
            raise ValueError('Selling price must be higher than cost price')
        return v

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Product name cannot be empty')
        return v.strip() if v else v

class ProductResponse(ProductBase):
    """
    Response schema - SOLID: Interface Segregation
    Contains all fields returned in API responses
    """
    id: int
    sku: str
    supplier_id: int
    status: str
    margin_percent: Optional[Decimal]
    quantity_reserved: int
    last_ordered_date: Optional[datetime]
    last_received_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Include supplier info if loaded
    supplier: Optional[dict] = None

    class Config:
        orm_mode = True

class ProductFilter(BaseModel):
    """
    Filter schema - SOLID: Single Responsibility
    YAGNI: Basic filtering only, no complex search algorithms
    """
    supplier_id: Optional[int] = None
    status: Optional[ProductStatusEnum] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    search: Optional[str] = Field(None, max_length=100, description="Search in name/SKU/description")
    low_stock: Optional[bool] = None  # quantity_on_hand <= reorder_point
    min_price: Optional[Decimal] = Field(None, gt=0)
    max_price: Optional[Decimal] = Field(None, gt=0)

    @validator('max_price')
    def max_price_greater_than_min(cls, v, values):
        """Validate price range"""
        if v and 'min_price' in values and values['min_price'] and v <= values['min_price']:
            raise ValueError('Max price must be greater than min price')
        return v

# =============================================================================
# SUPPLIER SCHEMAS
# =============================================================================

class SupplierBase(BaseModel):
    """
    Base supplier schema - SOLID: Interface Segregation
    Contains common supplier fields
    """
    name: str = Field(..., min_length=2, max_length=200, description="Supplier name")
    contact_person: Optional[str] = Field(None, max_length=100, description="Primary contact person")
    email: Optional[str] = Field(None, max_length=255, description="Contact email")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    website: Optional[str] = Field(None, max_length=255, description="Website URL")
    address_line1: Optional[str] = Field(None, max_length=255, description="Address line 1")
    address_line2: Optional[str] = Field(None, max_length=255, description="Address line 2")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=50, description="State/Province")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    tax_id: Optional[str] = Field(None, max_length=50, description="Tax identification number")
    payment_terms: Optional[str] = Field(None, max_length=100, description="Payment terms (Net 30, etc.)")
    currency: str = Field(default="USD", min_length=3, max_length=10, description="Currency code")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")

    @validator('name')
    def name_must_not_be_empty(cls, v):
        """Basic name validation"""
        if not v or not v.strip():
            raise ValueError('Supplier name cannot be empty')
        return v.strip()

    @validator('email')
    def validate_email_format(cls, v):
        """Basic email validation"""
        if v and v.strip():
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v.strip()):
                raise ValueError('Invalid email format')
        return v.strip() if v else v

class SupplierCreate(SupplierBase):
    """
    Creation schema - SOLID: Interface Segregation
    Contains all required fields for supplier creation
    """
    code: str = Field(..., min_length=2, max_length=50, description="Unique supplier code")

    @validator('code')
    def code_must_be_alphanumeric(cls, v):
        """Basic code validation"""
        if not v or not v.strip():
            raise ValueError('Supplier code cannot be empty')
        # Allow alphanumeric, hyphens, underscores
        import re
        if not re.match(r'^[A-Za-z0-9_-]+$', v.strip()):
            raise ValueError('Supplier code can only contain letters, numbers, hyphens, and underscores')
        return v.strip().upper()

class SupplierUpdate(BaseModel):
    """
    Update schema - SOLID: Interface Segregation
    Contains optional fields for partial updates
    """
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    payment_terms: Optional[str] = Field(None, max_length=100)
    currency: Optional[str] = Field(None, min_length=3, max_length=10)
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=2000)

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Supplier name cannot be empty')
        return v.strip() if v else v

    @validator('email')
    def validate_email_format(cls, v):
        if v and v.strip():
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v.strip()):
                raise ValueError('Invalid email format')
        return v.strip() if v else v

class SupplierResponse(SupplierBase):
    """
    Response schema - SOLID: Interface Segregation
    Contains all fields returned in API responses
    """
    id: int
    code: str
    total_orders: int
    total_spent: Decimal
    avg_delivery_days: Optional[int]
    last_order_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# =============================================================================
# UTILITY SCHEMAS
# =============================================================================

class InventoryUpdate(BaseModel):
    """
    Inventory update schema - YAGNI: Simple inventory operations
    """
    product_id: int = Field(..., gt=0, description="Product ID")
    quantity_change: int = Field(..., description="Positive for additions, negative for reductions")
    reason: str = Field(..., min_length=3, max_length=100, description="Reason for inventory change")

    @validator('reason')
    def reason_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Reason cannot be empty')
        return v.strip()

class ProductSearchResponse(BaseModel):
    """Product search response with pagination"""
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class SupplierSearchResponse(BaseModel):
    """Supplier search response with pagination"""
    items: List[SupplierResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class InventorySummaryResponse(BaseModel):
    """Inventory summary response - YAGNI: Basic metrics only"""
    total_products: int
    total_quantity: int
    total_value: float
    low_stock_count: int

class SupplierPerformanceResponse(BaseModel):
    """Supplier performance response - YAGNI: Basic metrics only"""
    total_products: int
    active_products: int
    total_orders: int
    total_spent: float
    avg_delivery_days: Optional[int]
    last_order_date: Optional[datetime]