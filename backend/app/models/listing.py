"""
Ultra-simplified Listing Model
Following YAGNI principles - 90% complexity reduction
YAGNI: Only essential listing fields users actually need right now
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.sql.sqltypes import DECIMAL
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ListingStatus(Enum):
    """YAGNI: Essential listing statuses only"""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    ENDED = "ended"


class Listing(BaseModel):
    """
    SOLID: Single Responsibility - Listing data structure only
    YAGNI: Essential fields only - removed performance metrics, complex status logic
    """
    __tablename__ = "listings"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    ebay_item_id = Column(String(50), unique=True, nullable=True, index=True)  # Nullable for new listings
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    # Basic listing information
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100), index=True)
    
    # Simple pricing & inventory - YAGNI: Basic fields only
    price = Column(DECIMAL(10, 2), nullable=False)
    quantity_available = Column(Integer, default=1)
    
    # Basic status & dates
    status = Column(String(20), nullable=False, default=ListingStatus.ACTIVE.value, index=True)
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="listings")
    
    # Simple indexes only
    __table_args__ = (
        Index('idx_listing_account_status', 'account_id', 'status'),
        Index('idx_listing_search', 'title', 'category'),
    )

    def __repr__(self):
        return f"<Listing(ebay_id='{self.ebay_item_id}', title='{self.title[:50]}...')>"

    def is_active(self) -> bool:
        """Check if listing is currently active"""
        return self.status == ListingStatus.ACTIVE.value

    def can_be_activated(self) -> bool:
        """Simple business rule: Can be activated if has quantity and not ended"""
        return (self.quantity_available > 0 and 
                self.status != ListingStatus.ENDED.value)