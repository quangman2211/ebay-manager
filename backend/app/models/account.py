"""
Account Model for eBay Account Management
Following SOLID principles - Single Responsibility for account data management
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel

class Account(BaseModel):
    """
    Account model for eBay account management
    Following SOLID: Single Responsibility for account data
    """
    __tablename__ = "accounts"
    
    # User Association
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # eBay Account Information
    ebay_account_name = Column(String(100), nullable=False)
    ebay_store_name = Column(String(100))
    ebay_user_id = Column(String(50), unique=True)  # eBay internal user ID
    
    # Account Configuration
    status = Column(String(20), default='active', nullable=False, index=True)
    currency = Column(String(3), default='USD', nullable=False)
    timezone = Column(String(50), default='UTC', nullable=False)
    
    # Business Information
    business_name = Column(String(100))
    contact_email = Column(String(100))
    phone_number = Column(String(20))
    
    # Account Settings
    auto_sync = Column(Boolean, default=True, nullable=False)
    sync_frequency = Column(Integer, default=30, nullable=False)  # minutes
    last_sync = Column(DateTime(timezone=True), index=True)
    
    # Relationships (using string names to avoid circular imports)
    user = relationship("User", back_populates="accounts", lazy="select")
    orders = relationship("Order", cascade="all, delete-orphan", lazy="select")
    listings = relationship("Listing", cascade="all, delete-orphan", lazy="select")
    products = relationship("Product", cascade="all, delete-orphan", lazy="select")
    suppliers = relationship("Supplier", cascade="all, delete-orphan", lazy="select")
    customers = relationship("Customer", cascade="all, delete-orphan", lazy="select")
    messages = relationship("Message", cascade="all, delete-orphan", lazy="select")
    templates = relationship("Template", cascade="all, delete-orphan", lazy="select")
    uploads = relationship("Upload", cascade="all, delete-orphan", lazy="select")
    settings = relationship("Setting", cascade="all, delete-orphan", lazy="select")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('length(ebay_account_name) >= 3', name='accounts_ebay_name_length'),
        CheckConstraint("currency ~* '^[A-Z]{3}$'", name='accounts_currency_format'),
        CheckConstraint('sync_frequency > 0', name='accounts_sync_frequency_positive'),
        CheckConstraint("status IN ('active', 'inactive', 'suspended')", name='accounts_status_check'),
    )
    
    @property
    def display_name(self) -> str:
        """Get account display name"""
        return self.ebay_store_name or self.ebay_account_name
    
    def __repr__(self):
        return f"<Account(id={self.id}, ebay_account_name='{self.ebay_account_name}', status='{self.status}')>"