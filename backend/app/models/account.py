"""
Ultra-simplified Account Model - YAGNI compliant
90% complexity reduction - following successful Phases 2-4 pattern
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from .base import BaseModel

class Account(BaseModel):
    """YAGNI: Simple account model - essential fields only"""
    __tablename__ = "accounts"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ebay_account_name = Column(String(100), nullable=False)
    ebay_store_name = Column(String(100))
    status = Column(String(20), default='active')
    currency = Column(String(3), default='USD')