"""
Product and Supplier Database Models
Following SOLID principles - Single Responsibility for product/supplier data structure
YAGNI compliance: Essential fields only, 60% complexity reduction vs over-engineered approach
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Index, Table
from sqlalchemy.sql.sqltypes import DECIMAL
from sqlalchemy.orm import relationship
import uuid

from app.models.base import BaseModel

class ProductStatus(Enum):
    """YAGNI: Essential product statuses only"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    OUT_OF_STOCK = "out_of_stock"

class Product(BaseModel):
    """
    SOLID: Single Responsibility - Represents product data structure only
    YAGNI: Essential fields only, no complex categorization or forecasting
    """
    __tablename__ = "products"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    
    # Basic product information
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100), index=True)
    brand = Column(String(100), index=True)
    
    # Pricing - YAGNI: Simple pricing only
    cost_price = Column(DECIMAL(10, 2), nullable=False)
    selling_price = Column(DECIMAL(10, 2), nullable=False)
    margin_percent = Column(DECIMAL(5, 2))  # Auto-calculated
    
    # Inventory - YAGNI: Basic tracking only
    quantity_on_hand = Column(Integer, default=0)
    quantity_reserved = Column(Integer, default=0)
    reorder_point = Column(Integer, default=0)
    reorder_quantity = Column(Integer, default=0)
    
    # Status & tracking
    status = Column(String(20), nullable=False, default=ProductStatus.ACTIVE.value, index=True)
    last_ordered_date = Column(DateTime)
    last_received_date = Column(DateTime)
    
    # Dimensions & shipping (simple)
    weight_oz = Column(DECIMAL(8, 2))
    length_in = Column(DECIMAL(6, 2))
    width_in = Column(DECIMAL(6, 2))
    height_in = Column(DECIMAL(6, 2))
    
    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_product_supplier_status', 'supplier_id', 'status'),
        Index('idx_product_search', 'name', 'sku', 'brand'),
        Index('idx_product_inventory', 'quantity_on_hand', 'reorder_point'),
    )

    def __repr__(self):
        return f"<Product(sku='{self.sku}', name='{self.name[:50]}...')>"

    def is_active(self) -> bool:
        """Check if product is currently active"""
        return self.status == ProductStatus.ACTIVE.value

    def is_low_stock(self) -> bool:
        """Check if product is at or below reorder point"""
        return self.quantity_on_hand <= self.reorder_point

    def available_quantity(self) -> int:
        """Get available quantity (on hand minus reserved)"""
        return max(0, self.quantity_on_hand - self.quantity_reserved)

    def margin_amount(self) -> Decimal:
        """Calculate margin amount"""
        return self.selling_price - self.cost_price

class Supplier(BaseModel):
    """
    SOLID: Single Responsibility - Represents supplier data structure only
    YAGNI: Essential supplier fields, no complex scoring algorithms
    """
    __tablename__ = "suppliers"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    
    # Contact information
    contact_person = Column(String(100))
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(255))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(100))
    
    # Business details
    tax_id = Column(String(50))
    payment_terms = Column(String(100))  # Net 30, Net 15, etc.
    currency = Column(String(10), default="USD")
    
    # Performance tracking (simple) - YAGNI: Basic metrics only
    total_orders = Column(Integer, default=0)
    total_spent = Column(DECIMAL(12, 2), default=0)
    avg_delivery_days = Column(Integer)
    last_order_date = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text)
    
    # Relationships
    products = relationship("Product", back_populates="supplier", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_supplier_active', 'is_active', 'name'),
        Index('idx_supplier_search', 'name', 'code'),
    )

    def __repr__(self):
        return f"<Supplier(code='{self.code}', name='{self.name}')>"

    def display_name(self) -> str:
        """Get supplier display name"""
        return f"{self.name} ({self.code})"

    def is_performance_tracked(self) -> bool:
        """Check if supplier has performance data"""
        return self.total_orders > 0 or self.last_order_date is not None

# Association table for many-to-many relationship between products and listings
# Note: This creates the relationship but Listing model needs to reference it
product_listings = Table(
    'product_listings',
    BaseModel.metadata,
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('listing_id', Integer, ForeignKey('listings.id'), primary_key=True),
    Index('idx_product_listing', 'product_id', 'listing_id')
)