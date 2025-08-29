"""
Dummy Models for Development
These are placeholder models to satisfy relationships until full implementation
Following SOLID principles - Single Responsibility for each entity
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, DECIMAL
from .base import BaseModel

# Placeholder models for relationships (will be properly implemented in later phases)

class Order(BaseModel):
    """Placeholder Order model"""
    __tablename__ = "orders"
    account_id = Column(Integer, ForeignKey("accounts.id"))
    ebay_order_id = Column(String(50))
    total_amount = Column(DECIMAL(10, 2))
    order_status = Column(String(20), default='pending')
    order_date = Column(DateTime(timezone=True))

class Listing(BaseModel):
    """Placeholder Listing model"""
    __tablename__ = "listings"
    account_id = Column(Integer, ForeignKey("accounts.id"))
    ebay_item_id = Column(String(50))
    title = Column(String(80))
    listing_status = Column(String(20), default='draft')

class Product(BaseModel):
    """Placeholder Product model"""
    __tablename__ = "products"
    account_id = Column(Integer, ForeignKey("accounts.id"))
    sku = Column(String(50))
    name = Column(String(200))
    cost_price = Column(DECIMAL(10, 2))

class Supplier(BaseModel):
    """Placeholder Supplier model"""
    __tablename__ = "suppliers"
    account_id = Column(Integer, ForeignKey("accounts.id"))
    name = Column(String(100))
    status = Column(String(20), default='active')

class Customer(BaseModel):
    """Placeholder Customer model"""
    __tablename__ = "customers"
    account_id = Column(Integer, ForeignKey("accounts.id"))
    ebay_username = Column(String(100))
    customer_segment = Column(String(20), default='NEW')

class Message(BaseModel):
    """Placeholder Message model"""
    __tablename__ = "messages"
    account_id = Column(Integer, ForeignKey("accounts.id"))
    subject = Column(String(200))
    content = Column(Text)
    message_type = Column(String(20), default='email')

class Template(BaseModel):
    """Placeholder Template model"""
    __tablename__ = "templates"
    account_id = Column(Integer, ForeignKey("accounts.id"))
    name = Column(String(100))
    content = Column(Text)

class Upload(BaseModel):
    """Placeholder Upload model"""
    __tablename__ = "uploads"
    account_id = Column(Integer, ForeignKey("accounts.id"))
    filename = Column(String(255))
    status = Column(String(20), default='uploaded')

class Setting(BaseModel):
    """Placeholder Setting model"""
    __tablename__ = "settings"
    account_id = Column(Integer, ForeignKey("accounts.id"))
    setting_key = Column(String(100))
    setting_value = Column(Text)