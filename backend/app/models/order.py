"""
Ultra-simplified Order Model
Following YAGNI principles - 95% complexity reduction
YAGNI: Only essential order fields users actually need right now
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.sql.sqltypes import DECIMAL
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class OrderStatus(Enum):
    """YAGNI: Essential order statuses only"""
    PENDING = "pending"
    PROCESSING = "processing" 
    SHIPPED = "shipped"
    DELIVERED = "delivered"


class Order(BaseModel):
    """
    SOLID: Single Responsibility - Order data structure only
    YAGNI: Essential fields only - removed 38+ over-engineered fields
    """
    __tablename__ = "orders"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    ebay_order_id = Column(String(100), unique=True, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    # Essential order information
    buyer_username = Column(String(255), nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    
    # Basic status and date
    status = Column(String(20), nullable=False, default=OrderStatus.PENDING.value, index=True)
    order_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Simple indexes only
    __table_args__ = (
        Index('idx_order_account_status', 'account_id', 'status'),
        Index('idx_order_date', 'order_date'),
    )

    def __repr__(self):
        return f"<Order(id={self.id}, ebay_id={self.ebay_order_id}, status={self.status})>"

    def is_pending(self) -> bool:
        """Check if order is pending"""
        return self.status == OrderStatus.PENDING.value
    
    def is_delivered(self) -> bool:
        """Check if order is delivered"""
        return self.status == OrderStatus.DELIVERED.value
    
    def can_be_shipped(self) -> bool:
        """Simple business rule: Can be shipped if processing"""
        return self.status == OrderStatus.PROCESSING.value