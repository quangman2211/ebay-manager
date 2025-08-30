"""
Database Models Package
Following SOLID principles for model organization
"""

from .base import Base, BaseModel, engine, SessionLocal
from .user import User
from .account import Account
from .order import Order, OrderItem, OrderStatus, PaymentStatus, ShippingStatus
from .csv import CSVUpload
from .listing import Listing, ListingStatus
from .product import Product, ProductStatus, Supplier, product_listings
from .communication import Email, EmailThread, EbayMessage, MessageThread, MessageDirection, MessageType, MessagePriority, ResponseTemplate
from .dummy_models import (
    Customer, Message, Template, Upload, Setting
)

# Import all models to ensure they are registered with SQLAlchemy
__all__ = [
    "Base", "BaseModel", "engine", "SessionLocal",
    "User", "Account", "Order", "OrderItem", "OrderStatus", "PaymentStatus", "ShippingStatus",
    "CSVUpload", "Listing", "ListingStatus", "Product", "ProductStatus", "Supplier", "product_listings",
    "Email", "EmailThread", "EbayMessage", "MessageThread", "MessageDirection", "MessageType", "MessagePriority", "ResponseTemplate",
    "Customer", "Message", "Template", "Upload", "Setting"
]