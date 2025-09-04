from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, JSON, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="staff")  # 'admin' or 'staff'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    accounts = relationship("Account", back_populates="user")
    account_permissions = relationship("UserAccountPermission", foreign_keys="UserAccountPermission.user_id", back_populates="user")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform_username = Column(String, nullable=False, index=True)  # Primary platform username (eBay, Etsy, etc.)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Sprint 7 enhancements - REDESIGNED STATUS FIELDS
    account_type = Column(String, default="ebay")  # ebay, etsy (multi-platform support)
    connection_status = Column(String, default="authenticated")  # authenticated, expired, failed, pending
    last_sync_at = Column(DateTime(timezone=True))
    data_processing_enabled = Column(Boolean, default=True)  # CSV processing control
    settings = Column(Text, default='{}')  # JSON as TEXT for SQLite
    performance_metrics = Column(Text, default='{}')  # JSON as TEXT for SQLite

    user = relationship("User", back_populates="accounts")
    csv_data = relationship("CSVData", back_populates="account")
    user_permissions = relationship("UserAccountPermission", back_populates="account")
    metrics = relationship("AccountMetrics", back_populates="account")
    settings_records = relationship("AccountSettings", back_populates="account")


class CSVData(Base):
    __tablename__ = "csv_data"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    data_type = Column(String, nullable=False, index=True)  # 'order' or 'listing'
    csv_row = Column(JSON, nullable=False)
    item_id = Column(String, index=True)  # order_number or item_number
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Sprint 7 enhancements
    account_context = Column(Text, default='{}')  # JSON as TEXT for SQLite
    processed_at = Column(DateTime(timezone=True))
    processing_status = Column(String, default="pending")  # pending, processing, completed, error

    account = relationship("Account", back_populates="csv_data")
    order_status = relationship("OrderStatus", back_populates="csv_data", uselist=False)


class OrderStatus(Base):
    __tablename__ = "order_status"

    id = Column(Integer, primary_key=True, index=True)
    csv_data_id = Column(Integer, ForeignKey("csv_data.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, processing, shipped, completed
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    csv_data = relationship("CSVData", back_populates="order_status")
    updated_by_user = relationship("User")


# =============================================================================
# Sprint 7: Enhanced Account Management Models
# =============================================================================

class UserAccountPermission(Base):
    """User permissions for specific eBay accounts"""
    __tablename__ = "user_account_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    permission_level = Column(String, default="view", nullable=False)  # view, edit, admin
    granted_by = Column(Integer, ForeignKey("users.id"))
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="account_permissions")
    account = relationship("Account", back_populates="user_permissions")
    granted_by_user = relationship("User", foreign_keys=[granted_by])


class AccountMetrics(Base):
    """Daily performance metrics for eBay accounts"""
    __tablename__ = "account_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    metric_date = Column(Date, nullable=False)
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Numeric(12,2), default=0)
    active_listings = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    watchers = Column(Integer, default=0)
    conversion_rate = Column(Numeric(5,4), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="metrics")


class AccountSettings(Base):
    """Account-specific settings and configuration"""
    __tablename__ = "account_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    setting_key = Column(String, nullable=False)
    setting_value = Column(Text)
    setting_type = Column(String, default="string")  # string, number, boolean, json
    updated_by = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="settings_records")
    updated_by_user = relationship("User")