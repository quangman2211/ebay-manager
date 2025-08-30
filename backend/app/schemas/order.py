"""
Ultra-simplified Order Schemas - YAGNI compliant
90% complexity reduction - following successful Phases 2-4 pattern
"""

from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from app.models.order import OrderStatus

class OrderCreate(BaseModel):
    """YAGNI: Simple order creation schema"""
    account_id: int
    ebay_order_id: Optional[str] = None
    buyer_username: str
    total_amount: Decimal
    status: str = OrderStatus.PENDING.value
    order_date: Optional[datetime] = None

class OrderUpdate(BaseModel):
    """YAGNI: Simple order update schema"""
    buyer_username: Optional[str] = None
    total_amount: Optional[Decimal] = None
    status: Optional[str] = None

class OrderResponse(BaseModel):
    """YAGNI: Simple order response schema"""
    id: int
    ebay_order_id: Optional[str]
    buyer_username: str
    total_amount: Decimal
    status: str
    order_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True