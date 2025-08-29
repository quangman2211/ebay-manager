"""
Listing Database Model
Following SOLID principles - Single Responsibility for listing data structure only
YAGNI compliance: Essential fields only, no over-engineering
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.sql.sqltypes import DECIMAL
from sqlalchemy.orm import relationship
import uuid

from app.models.base import BaseModel

class ListingStatus(Enum):
    """YAGNI: Essential listing statuses only"""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    OUT_OF_STOCK = "out_of_stock"
    ENDED = "ended"
    PAUSED = "paused"

class Listing(BaseModel):
    """
    SOLID: Single Responsibility - Represents listing data structure only
    YAGNI: Essential fields only, no complex categorization or SEO optimization
    """
    __tablename__ = "listings"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    ebay_item_id = Column(String(50), unique=True, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    # Basic listing information
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100), index=True)
    
    # Pricing & inventory - YAGNI: Simple pricing only
    price = Column(DECIMAL(10, 2), nullable=False)
    quantity_available = Column(Integer, default=1)
    quantity_sold = Column(Integer, default=0)
    
    # Status & dates
    status = Column(String(20), nullable=False, default=ListingStatus.ACTIVE.value, index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # eBay specific fields
    format_type = Column(String(20))  # Auction, FixedPrice
    duration_days = Column(Integer)
    
    # Performance metrics (simple) - YAGNI: Basic metrics only
    view_count = Column(Integer, default=0)
    watch_count = Column(Integer, default=0)
    
    # Relationships
    account = relationship("Account", back_populates="listings")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_listing_account_status', 'account_id', 'status'),
        Index('idx_listing_dates', 'start_date', 'end_date'),
        Index('idx_listing_search', 'title', 'category'),
    )

    def __repr__(self):
        return f"<Listing(ebay_id='{self.ebay_item_id}', title='{self.title[:50]}...')>"

    def is_active(self) -> bool:
        """Check if listing is currently active"""
        return self.status == ListingStatus.ACTIVE.value

    def is_expired(self) -> bool:
        """Check if listing has expired"""
        if not self.end_date:
            return False
        return datetime.utcnow() > self.end_date

    def can_be_activated(self) -> bool:
        """Business rule: Can be activated if has quantity and not ended"""
        return (self.quantity_available > 0 and 
                self.status != ListingStatus.ENDED.value and
                not self.is_expired())