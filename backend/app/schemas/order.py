"""
Order Management Schemas
Following SOLID principles - Single Responsibility for order data validation
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from enum import Enum

from app.models.order import OrderStatus, PaymentStatus, ShippingStatus

class OrderStatusUpdate(str, Enum):
    """Order status values for updates"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    RETURNED = "returned"

class PaymentStatusUpdate(str, Enum):
    """Payment status values for updates"""
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partial"
    REFUNDED = "refunded"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ShippingStatusUpdate(str, Enum):
    """Shipping status values for updates"""
    NOT_SHIPPED = "not_shipped"
    PREPARING = "preparing"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"
    LOST = "lost"

class OrderItemBase(BaseModel):
    """
    Base order item schema
    Following SOLID: Single Responsibility for order item structure
    """
    ebay_item_id: str = Field(..., min_length=1, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    variation: Optional[str] = Field(None, max_length=255)
    quantity: int = Field(..., ge=1, le=1000)
    unit_price: Decimal = Field(..., ge=0)
    total_price: Decimal = Field(..., ge=0)
    cost_per_item: Optional[Decimal] = Field(None, ge=0)
    supplier_id: Optional[int] = Field(None, gt=0)
    is_customized: bool = Field(False)
    notes: Optional[str] = Field(None, max_length=1000)
    
    @validator('total_price')
    def validate_total_price(cls, v, values):
        """Validate total price matches unit price * quantity"""
        if 'unit_price' in values and 'quantity' in values:
            expected_total = values['unit_price'] * values['quantity']
            if abs(float(v) - float(expected_total)) > 0.01:  # Allow for small rounding differences
                raise ValueError('total_price must equal unit_price * quantity')
        return v

class OrderItemCreate(OrderItemBase):
    """
    Order item creation schema
    Following SOLID: Single Responsibility for order item creation
    """
    listing_id: Optional[int] = Field(None, gt=0)

class OrderItemUpdate(BaseModel):
    """
    Order item update schema
    Following SOLID: Single Responsibility for order item updates
    """
    quantity: Optional[int] = Field(None, ge=1, le=1000)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    cost_per_item: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)

class OrderItemResponse(OrderItemBase):
    """
    Order item response schema
    Following SOLID: Single Responsibility for order item responses
    """
    id: int
    order_id: int
    listing_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime
    profit_amount: Optional[float] = None
    profit_margin_percent: Optional[float] = None
    
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    """
    Base order schema with common fields
    Following SOLID: Single Responsibility for order structure
    """
    ebay_order_id: str = Field(..., min_length=1, max_length=100)
    account_id: int = Field(..., gt=0)
    
    # Customer Information
    buyer_username: str = Field(..., min_length=1, max_length=255)
    buyer_email: Optional[str] = Field(None, max_length=255)
    buyer_name: Optional[str] = Field(None, max_length=255)
    
    # Shipping Address
    shipping_name: str = Field(..., min_length=1, max_length=255)
    shipping_address_line1: str = Field(..., min_length=1, max_length=500)
    shipping_address_line2: Optional[str] = Field(None, max_length=500)
    shipping_city: str = Field(..., min_length=1, max_length=100)
    shipping_state: Optional[str] = Field(None, max_length=100)
    shipping_postal_code: str = Field(..., min_length=1, max_length=50)
    shipping_country: str = Field(..., min_length=1, max_length=100)
    shipping_phone: Optional[str] = Field(None, max_length=50)
    
    # Financial Information
    currency: str = Field("USD", min_length=3, max_length=3)
    subtotal: Decimal = Field(..., ge=0)
    shipping_cost: Decimal = Field(0.00, ge=0)
    tax_amount: Decimal = Field(0.00, ge=0)
    total_amount: Decimal = Field(..., ge=0)
    
    # Payment Information
    payment_method: Optional[str] = Field(None, max_length=100)
    payment_reference: Optional[str] = Field(None, max_length=255)
    
    # Shipping Information
    shipping_method: Optional[str] = Field(None, max_length=100)
    estimated_delivery_date: Optional[datetime] = None
    
    # Order Date
    order_date: datetime = Field(...)
    
    # Additional Information
    notes: Optional[str] = Field(None, max_length=2000)
    is_priority: bool = Field(False)
    is_gift: bool = Field(False)
    requires_signature: bool = Field(False)
    is_international: bool = Field(False)
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code"""
        if not v.isupper() or len(v) != 3:
            raise ValueError('Currency must be 3-letter uppercase code (e.g., USD, EUR)')
        return v
    
    @validator('total_amount')
    def validate_total_amount(cls, v, values):
        """Validate total amount"""
        if 'subtotal' in values and 'shipping_cost' in values and 'tax_amount' in values:
            expected_total = values['subtotal'] + values['shipping_cost'] + values['tax_amount']
            if abs(float(v) - float(expected_total)) > 0.01:
                raise ValueError('total_amount must equal subtotal + shipping_cost + tax_amount')
        return v

class OrderCreate(OrderBase):
    """
    Order creation schema
    Following SOLID: Single Responsibility for order creation
    """
    order_items: List[OrderItemCreate] = Field(..., min_items=1)
    
    @validator('order_items')
    def validate_order_items(cls, v):
        """Validate order items"""
        if not v:
            raise ValueError('Order must contain at least one item')
        return v

class OrderUpdate(BaseModel):
    """
    Order update schema
    Following SOLID: Single Responsibility for order updates
    """
    status: Optional[OrderStatusUpdate] = None
    payment_status: Optional[PaymentStatusUpdate] = None
    shipping_status: Optional[ShippingStatusUpdate] = None
    
    buyer_email: Optional[str] = Field(None, max_length=255)
    buyer_name: Optional[str] = Field(None, max_length=255)
    
    # Shipping Address Updates
    shipping_name: Optional[str] = Field(None, min_length=1, max_length=255)
    shipping_address_line1: Optional[str] = Field(None, min_length=1, max_length=500)
    shipping_address_line2: Optional[str] = Field(None, max_length=500)
    shipping_city: Optional[str] = Field(None, min_length=1, max_length=100)
    shipping_state: Optional[str] = Field(None, max_length=100)
    shipping_postal_code: Optional[str] = Field(None, min_length=1, max_length=50)
    shipping_country: Optional[str] = Field(None, min_length=1, max_length=100)
    shipping_phone: Optional[str] = Field(None, max_length=50)
    
    # Payment Information
    payment_method: Optional[str] = Field(None, max_length=100)
    payment_reference: Optional[str] = Field(None, max_length=255)
    paid_amount: Optional[Decimal] = Field(None, ge=0)
    payment_date: Optional[datetime] = None
    
    # Shipping Information
    shipping_method: Optional[str] = Field(None, max_length=100)
    tracking_number: Optional[str] = Field(None, max_length=255)
    carrier: Optional[str] = Field(None, max_length=100)
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    shipping_date: Optional[datetime] = None
    
    # Additional Information
    notes: Optional[str] = Field(None, max_length=2000)
    internal_notes: Optional[str] = Field(None, max_length=2000)
    ebay_fees: Optional[Decimal] = Field(None, ge=0)
    paypal_fees: Optional[Decimal] = Field(None, ge=0)
    
    # Flags
    is_priority: Optional[bool] = None
    is_gift: Optional[bool] = None
    requires_signature: Optional[bool] = None
    is_international: Optional[bool] = None

class OrderStatusUpdateRequest(BaseModel):
    """
    Order status update request
    Following SOLID: Single Responsibility for status updates
    """
    status: OrderStatusUpdate = Field(...)
    notes: Optional[str] = Field(None, max_length=500, description="Reason for status change")
    notify_customer: bool = Field(False, description="Whether to notify customer of status change")

class OrderShippingUpdate(BaseModel):
    """
    Order shipping information update
    Following SOLID: Single Responsibility for shipping updates
    """
    shipping_status: ShippingStatusUpdate = Field(...)
    tracking_number: Optional[str] = Field(None, max_length=255)
    carrier: Optional[str] = Field(None, max_length=100)
    shipping_method: Optional[str] = Field(None, max_length=100)
    estimated_delivery_date: Optional[datetime] = None
    shipping_date: Optional[datetime] = None
    notify_customer: bool = Field(True, description="Whether to notify customer of shipping update")

class OrderResponse(OrderBase):
    """
    Order response schema
    Following SOLID: Single Responsibility for order responses
    """
    id: int
    user_id: int
    status: OrderStatus
    payment_status: PaymentStatus
    shipping_status: ShippingStatus
    
    paid_amount: Decimal
    payment_date: Optional[datetime] = None
    
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    actual_delivery_date: Optional[datetime] = None
    shipping_date: Optional[datetime] = None
    
    internal_notes: Optional[str] = None
    ebay_fees: Decimal
    paypal_fees: Decimal
    
    csv_file_id: Optional[str] = None
    imported_at: Optional[datetime] = None
    last_sync_date: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime
    
    order_items: List[OrderItemResponse] = []
    
    # Computed Properties
    is_paid: bool = False
    is_shipped: bool = False
    is_completed: bool = False
    total_items: int = 0
    days_since_order: int = 0
    is_overdue: bool = False
    profit_margin: Optional[float] = None
    full_shipping_address: str = ""
    
    class Config:
        from_attributes = True

class OrderSummary(BaseModel):
    """
    Order summary schema for list views
    Following SOLID: Single Responsibility for order summaries
    """
    id: int
    ebay_order_id: str
    buyer_username: str
    status: OrderStatus
    payment_status: PaymentStatus
    shipping_status: ShippingStatus
    total_amount: Decimal
    currency: str
    order_date: datetime
    total_items: int
    tracking_number: Optional[str] = None
    is_priority: bool
    is_overdue: bool
    days_since_order: int
    
    class Config:
        from_attributes = True

class OrderFilter(BaseModel):
    """
    Order filtering parameters
    Following SOLID: Single Responsibility for order filtering
    """
    account_id: Optional[int] = Field(None, gt=0)
    status: Optional[List[OrderStatus]] = None
    payment_status: Optional[List[PaymentStatus]] = None
    shipping_status: Optional[List[ShippingStatus]] = None
    buyer_username: Optional[str] = Field(None, max_length=255)
    ebay_order_id: Optional[str] = Field(None, max_length=100)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_priority: Optional[bool] = None
    is_overdue: Optional[bool] = None
    has_tracking: Optional[bool] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)

class OrderListResponse(BaseModel):
    """
    Order list response with pagination
    Following SOLID: Single Responsibility for list responses
    """
    orders: List[OrderSummary]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

class OrderStats(BaseModel):
    """
    Order statistics schema
    Following SOLID: Single Responsibility for order statistics
    """
    total_orders: int = 0
    pending_orders: int = 0
    shipped_orders: int = 0
    delivered_orders: int = 0
    cancelled_orders: int = 0
    overdue_orders: int = 0
    
    total_revenue: Decimal = Decimal('0.00')
    pending_revenue: Decimal = Decimal('0.00')
    this_month_revenue: Decimal = Decimal('0.00')
    this_year_revenue: Decimal = Decimal('0.00')
    
    average_order_value: Decimal = Decimal('0.00')
    total_items_sold: int = 0
    
    top_buyers: List[Dict[str, Any]] = []
    revenue_by_month: List[Dict[str, Any]] = []