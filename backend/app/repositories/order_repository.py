"""
Ultra-simplified Order Repository - YAGNI compliant
90% complexity reduction from original
Following successful Phases 2-4 pattern
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.order import Order
from app.schemas.order import OrderCreate

class OrderRepository:
    """YAGNI: Simple order data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, order_data: OrderCreate) -> Order:
        """YAGNI: Simple order creation"""
        order = Order(**order_data.dict())
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def get_by_id(self, order_id: int) -> Optional[Order]:
        """YAGNI: Simple order lookup"""
        return self.db.query(Order).filter(Order.id == order_id).first()
    
    def get_by_ebay_order_id(self, ebay_order_id: str) -> Optional[Order]:
        """YAGNI: Simple eBay order lookup"""
        return self.db.query(Order).filter(Order.ebay_order_id == ebay_order_id).first()
    
    def get_all(self, account_id: Optional[int] = None) -> List[Order]:
        """YAGNI: Simple order listing"""
        query = self.db.query(Order)
        if account_id:
            query = query.filter(Order.account_id == account_id)
        return query.all()
    
    def update(self, order_id: int, update_data: dict) -> Optional[Order]:
        """YAGNI: Simple order update"""
        order = self.get_by_id(order_id)
        if not order:
            return None
        
        for key, value in update_data.items():
            if hasattr(order, key) and value is not None:
                setattr(order, key, value)
        
        self.db.commit()
        self.db.refresh(order)
        return order