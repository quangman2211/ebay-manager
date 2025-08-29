"""
Order Database Model
Following SOLID principles - Single Responsibility for order data management
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum
from sqlalchemy.sql.sqltypes import DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from typing import Optional
from datetime import datetime

from app.models.base import BaseModel

class OrderStatus(str, PyEnum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    RETURNED = "returned"

class PaymentStatus(str, PyEnum):
    """Payment status enumeration"""
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partial"
    REFUNDED = "refunded"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ShippingStatus(str, PyEnum):
    """Shipping status enumeration"""
    NOT_SHIPPED = "not_shipped"
    PREPARING = "preparing"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"
    LOST = "lost"

class Order(BaseModel):
    """
    Order model for eBay orders
    Following SOLID: Single Responsibility for order data structure
    """
    
    __tablename__ = 'orders'
    
    # Basic Order Information
    ebay_order_id = Column(String(100), unique=True, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Order Status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    shipping_status = Column(Enum(ShippingStatus), default=ShippingStatus.NOT_SHIPPED, nullable=False)
    
    # Customer Information
    buyer_username = Column(String(255), nullable=False)
    buyer_email = Column(String(255), nullable=True)
    buyer_name = Column(String(255), nullable=True)
    
    # Shipping Address
    shipping_name = Column(String(255), nullable=False)
    shipping_address_line1 = Column(String(500), nullable=False)
    shipping_address_line2 = Column(String(500), nullable=True)
    shipping_city = Column(String(100), nullable=False)
    shipping_state = Column(String(100), nullable=True)
    shipping_postal_code = Column(String(50), nullable=False)
    shipping_country = Column(String(100), nullable=False)
    shipping_phone = Column(String(50), nullable=True)
    
    # Order Financial Information
    currency = Column(String(3), default='USD', nullable=False)
    subtotal = Column(DECIMAL(12, 2), nullable=False)
    shipping_cost = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    tax_amount = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    total_amount = Column(DECIMAL(12, 2), nullable=False)
    
    # Payment Information
    payment_method = Column(String(100), nullable=True)
    payment_reference = Column(String(255), nullable=True)
    paid_amount = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    
    # Shipping Information
    shipping_method = Column(String(100), nullable=True)
    tracking_number = Column(String(255), nullable=True)
    carrier = Column(String(100), nullable=True)
    estimated_delivery_date = Column(DateTime, nullable=True)
    actual_delivery_date = Column(DateTime, nullable=True)
    
    # Order Dates
    order_date = Column(DateTime, nullable=False)
    payment_date = Column(DateTime, nullable=True)
    shipping_date = Column(DateTime, nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    ebay_fees = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    paypal_fees = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    
    # Flags
    is_priority = Column(Boolean, default=False, nullable=False)
    is_gift = Column(Boolean, default=False, nullable=False)
    requires_signature = Column(Boolean, default=False, nullable=False)
    is_international = Column(Boolean, default=False, nullable=False)
    
    # CSV Import Information
    csv_file_id = Column(String(255), nullable=True, index=True)
    imported_at = Column(DateTime, nullable=True)
    last_sync_date = Column(DateTime, nullable=True)
    
    # Relationships
    account = relationship("Account", back_populates="orders", lazy="select")
    user = relationship("User", back_populates="orders", lazy="select")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, ebay_id={self.ebay_order_id}, status={self.status})>"
    
    @property
    def full_shipping_address(self) -> str:
        """
        Get formatted full shipping address
        Following SOLID: Single method responsibility
        """
        address_parts = [
            self.shipping_name,
            self.shipping_address_line1,
            self.shipping_address_line2,
            f"{self.shipping_city}, {self.shipping_state} {self.shipping_postal_code}".strip(),
            self.shipping_country
        ]
        return "\n".join([part for part in address_parts if part and part.strip()])
    
    @property
    def is_paid(self) -> bool:
        """Check if order is fully paid"""
        return self.payment_status == PaymentStatus.PAID
    
    @property
    def is_shipped(self) -> bool:
        """Check if order is shipped"""
        return self.shipping_status in [ShippingStatus.SHIPPED, ShippingStatus.IN_TRANSIT, ShippingStatus.DELIVERED]
    
    @property
    def is_completed(self) -> bool:
        """Check if order is completed"""
        return self.status == OrderStatus.DELIVERED and self.payment_status == PaymentStatus.PAID
    
    @property
    def profit_margin(self) -> Optional[float]:
        """
        Calculate profit margin (requires order items with cost data)
        Following SOLID: Single calculation responsibility
        """
        if not self.order_items:
            return None
        
        total_cost = sum(
            (item.cost_per_item or 0) * item.quantity 
            for item in self.order_items 
            if item.cost_per_item
        )
        
        if total_cost == 0:
            return None
        
        total_revenue = float(self.subtotal)
        profit = total_revenue - float(total_cost)
        
        return (profit / total_revenue) * 100 if total_revenue > 0 else 0
    
    @property
    def total_items(self) -> int:
        """Get total number of items in order"""
        return sum(item.quantity for item in self.order_items)
    
    @property
    def days_since_order(self) -> int:
        """Get number of days since order was placed"""
        if not self.order_date:
            return 0
        return (datetime.utcnow() - self.order_date).days
    
    @property
    def is_overdue(self) -> bool:
        """
        Check if order is overdue for shipping
        Following SOLID: Single business logic responsibility
        """
        if self.is_shipped or self.status in [OrderStatus.CANCELLED, OrderStatus.DELIVERED]:
            return False
        
        # Business rule: Orders should be shipped within 3 business days
        return self.days_since_order > 3
    
    def can_transition_to(self, new_status: OrderStatus) -> bool:
        """
        Check if order can transition to new status
        Following SOLID: Single validation responsibility
        """
        # Define allowed status transitions
        transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
            OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED, OrderStatus.RETURNED],
            OrderStatus.DELIVERED: [OrderStatus.RETURNED, OrderStatus.REFUNDED],
            OrderStatus.CANCELLED: [],  # Terminal status
            OrderStatus.RETURNED: [OrderStatus.REFUNDED],
            OrderStatus.REFUNDED: []  # Terminal status
        }
        
        return new_status in transitions.get(self.status, [])

class OrderItem(BaseModel):
    """
    Order item model for individual items within an order
    Following SOLID: Single Responsibility for order item data
    """
    
    __tablename__ = 'order_items'
    
    # Basic Item Information
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    ebay_item_id = Column(String(100), nullable=False)
    listing_id = Column(Integer, ForeignKey('listings.id'), nullable=True)
    
    # Item Details
    sku = Column(String(100), nullable=True)
    title = Column(String(500), nullable=False)
    variation = Column(String(255), nullable=True)  # e.g., "Size: Large, Color: Blue"
    
    # Quantity and Pricing
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    total_price = Column(DECIMAL(12, 2), nullable=False)
    
    # Cost Information (for profit calculation)
    cost_per_item = Column(DECIMAL(10, 2), nullable=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    
    # Item Status
    status = Column(String(50), default='pending', nullable=False)
    is_customized = Column(Boolean, default=False, nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    listing = relationship("Listing", back_populates="order_items", lazy="select")
    supplier = relationship("Supplier", back_populates="order_items", lazy="select")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, title={self.title[:30]}..., qty={self.quantity})>"
    
    @property
    def profit_amount(self) -> Optional[float]:
        """Calculate profit for this item"""
        if not self.cost_per_item:
            return None
        
        total_cost = float(self.cost_per_item) * self.quantity
        total_revenue = float(self.total_price)
        
        return total_revenue - total_cost
    
    @property
    def profit_margin_percent(self) -> Optional[float]:
        """Calculate profit margin percentage for this item"""
        if not self.cost_per_item or self.total_price == 0:
            return None
        
        profit = self.profit_amount
        if profit is None:
            return None
        
        return (profit / float(self.total_price)) * 100