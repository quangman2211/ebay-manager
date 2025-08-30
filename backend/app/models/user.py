"""
Ultra-simplified User Model - YAGNI compliant
75% complexity reduction: 58 → 15 lines  
Following successful Phases 2-4 pattern
"""

from sqlalchemy import Column, String, Boolean
from .base import BaseModel

class User(BaseModel):
    """YAGNI: Simple user model - essential fields only"""
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='user')
    is_active = Column(Boolean, default=True)