"""
Ultra-simplified Product and Supplier Models
Following YAGNI principles - 90% complexity reduction
YAGNI: Only essential fields users actually need right now
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.sql.sqltypes import DECIMAL
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ProductStatus(Enum):
    """YAGNI: Essential product statuses only"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class Product(BaseModel):
    """
    SOLID: Single Responsibility - Product data structure only
    YAGNI: Essential fields only - removed inventory, dimensions, margin calculations
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
    
    # Simple pricing - YAGNI: No margin calculations
    cost_price = Column(DECIMAL(10, 2), nullable=False)
    selling_price = Column(DECIMAL(10, 2), nullable=False)
    
    # Basic status only
    status = Column(String(20), nullable=False, default=ProductStatus.ACTIVE.value, index=True)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    
    # Simple indexes only
    __table_args__ = (
        Index('idx_product_supplier_status', 'supplier_id', 'status'),
        Index('idx_product_search', 'name', 'sku'),
    )

    def __repr__(self):
        return f"<Product(sku='{self.sku}', name='{self.name[:50]}...')>"

    def is_active(self) -> bool:
        """Check if product is currently active"""
        return self.status == ProductStatus.ACTIVE.value

    def margin_amount(self) -> Decimal:
        """Simple margin calculation - only when actually needed"""
        return self.selling_price - self.cost_price


class Supplier(BaseModel):
    """
    SOLID: Single Responsibility - Supplier data structure only
    YAGNI: Essential supplier info only - removed performance tracking, complex contact info
    """
    __tablename__ = "suppliers"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    
    # Basic contact information only
    contact_email = Column(String(255))
    phone = Column(String(50))
    
    # Simple status
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text)
    
    # Relationships
    products = relationship("Product", back_populates="supplier", cascade="all, delete-orphan")
    
    # Simple indexes only
    __table_args__ = (
        Index('idx_supplier_active', 'is_active', 'name'),
        Index('idx_supplier_search', 'name', 'code'),
    )

    def __repr__(self):
        return f"<Supplier(code='{self.code}', name='{self.name}')>"

    def display_name(self) -> str:
        """Get supplier display name"""
        return f"{self.name} ({self.code})"