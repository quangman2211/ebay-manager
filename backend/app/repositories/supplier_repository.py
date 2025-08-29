"""
Supplier Repository Implementation
Following SOLID principles - Single Responsibility for supplier data access
YAGNI compliance: Essential supplier operations only, no complex analytics
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError

from app.models.product import Supplier, Product, ProductStatus
from app.repositories.base import BaseRepository
from app.core.exceptions import EbayManagerException

class SupplierRepositoryInterface(ABC):
    """
    SOLID: Interface Segregation & Dependency Inversion
    Clean contract for supplier data access
    """
    
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Supplier]:
        """Get supplier by code"""
        pass
    
    @abstractmethod
    async def get_active_suppliers(self) -> List[Supplier]:
        """Get all active suppliers"""
        pass
    
    @abstractmethod
    async def search_by_name(self, name: str) -> List[Supplier]:
        """Search suppliers by name"""
        pass
    
    @abstractmethod
    async def get_supplier_performance(self, supplier_id: int) -> Dict[str, Any]:
        """Get basic supplier performance metrics"""
        pass

class SupplierRepository(BaseRepository[Supplier], SupplierRepositoryInterface):
    """
    SOLID: Single Responsibility - Supplier data access only
    YAGNI: Essential operations only, no complex supplier analytics
    """
    
    def __init__(self, db: Session):
        super().__init__(db, Supplier)
    
    async def get_by_code(self, code: str) -> Optional[Supplier]:
        """Get supplier by code"""
        try:
            return self.db.query(Supplier).filter(Supplier.code == code).first()
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get supplier by code: {str(e)}")
    
    async def get_active_suppliers(self) -> List[Supplier]:
        """Get all active suppliers ordered by name"""
        try:
            return self.db.query(Supplier).filter(
                Supplier.is_active == True
            ).order_by(Supplier.name).all()
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get active suppliers: {str(e)}")
    
    async def search_by_name(self, name: str) -> List[Supplier]:
        """Search suppliers by name (case-insensitive)"""
        try:
            return self.db.query(Supplier).filter(
                Supplier.name.ilike(f"%{name}%")
            ).order_by(Supplier.name).all()
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to search suppliers by name: {str(e)}")
    
    async def search(self, name: Optional[str] = None, is_active: Optional[bool] = None, 
                     offset: int = 0, limit: int = 100) -> List[Supplier]:
        """Search suppliers with basic filters"""
        try:
            query = self.db.query(Supplier)
            
            conditions = []
            
            if name:
                conditions.append(Supplier.name.ilike(f"%{name}%"))
            
            if is_active is not None:
                conditions.append(Supplier.is_active == is_active)
            
            if conditions:
                query = query.filter(and_(*conditions))
            
            return query.order_by(Supplier.name).offset(offset).limit(limit).all()
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to search suppliers: {str(e)}")
    
    async def get_supplier_performance(self, supplier_id: int) -> Dict[str, Any]:
        """Get basic supplier performance metrics - YAGNI: Simple metrics only"""
        try:
            supplier = await self.get_by_id(supplier_id)
            if not supplier:
                raise EbayManagerException(f"Supplier {supplier_id} not found")
            
            # Get product counts
            total_products = self.db.query(func.count(Product.id)).filter(
                Product.supplier_id == supplier_id
            ).scalar() or 0
            
            active_products = self.db.query(func.count(Product.id)).filter(
                and_(
                    Product.supplier_id == supplier_id,
                    Product.status == ProductStatus.ACTIVE.value
                )
            ).scalar() or 0
            
            # Get low stock product count
            low_stock_products = self.db.query(func.count(Product.id)).filter(
                and_(
                    Product.supplier_id == supplier_id,
                    Product.quantity_on_hand <= Product.reorder_point,
                    Product.status == ProductStatus.ACTIVE.value
                )
            ).scalar() or 0
            
            # Get total inventory value
            inventory_value = self.db.query(
                func.sum(Product.cost_price * Product.quantity_on_hand)
            ).filter(
                and_(
                    Product.supplier_id == supplier_id,
                    Product.status == ProductStatus.ACTIVE.value
                )
            ).scalar() or 0
            
            return {
                'total_products': total_products,
                'active_products': active_products,
                'low_stock_products': low_stock_products,
                'inventory_value': float(inventory_value),
                'total_orders': supplier.total_orders,
                'total_spent': float(supplier.total_spent),
                'avg_delivery_days': supplier.avg_delivery_days,
                'last_order_date': supplier.last_order_date,
                'is_active': supplier.is_active
            }
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get supplier performance: {str(e)}")
    
    async def update_supplier_stats(self, supplier_id: int, order_amount: float, delivery_days: int) -> bool:
        """Update supplier performance stats - YAGNI: Simple tracking only"""
        try:
            supplier = await self.get_by_id(supplier_id)
            if not supplier:
                return False
            
            # Update order statistics
            supplier.total_orders += 1
            supplier.total_spent += order_amount
            supplier.last_order_date = datetime.utcnow()
            
            # Update average delivery days (simple moving average)
            if supplier.avg_delivery_days:
                # Weighted average with existing data
                total_deliveries = supplier.total_orders
                supplier.avg_delivery_days = int((
                    (supplier.avg_delivery_days * (total_deliveries - 1)) + delivery_days
                ) / total_deliveries)
            else:
                supplier.avg_delivery_days = delivery_days
            
            supplier.updated_at = datetime.utcnow()
            self.db.commit()
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise EbayManagerException(f"Failed to update supplier stats: {str(e)}")
    
    async def get_suppliers_with_low_stock_products(self) -> List[Supplier]:
        """Get suppliers that have products with low stock"""
        try:
            # Subquery to find suppliers with low stock products
            subquery = self.db.query(Product.supplier_id).filter(
                and_(
                    Product.quantity_on_hand <= Product.reorder_point,
                    Product.status == ProductStatus.ACTIVE.value
                )
            ).distinct().subquery()
            
            return self.db.query(Supplier).filter(
                and_(
                    Supplier.id.in_(subquery),
                    Supplier.is_active == True
                )
            ).order_by(Supplier.name).all()
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get suppliers with low stock: {str(e)}")
    
    async def get_supplier_summary(self) -> Dict[str, Any]:
        """Get overall supplier summary - YAGNI: Basic metrics only"""
        try:
            total_suppliers = self.db.query(func.count(Supplier.id)).scalar() or 0
            
            active_suppliers = self.db.query(func.count(Supplier.id)).filter(
                Supplier.is_active == True
            ).scalar() or 0
            
            suppliers_with_products = self.db.query(
                func.count(func.distinct(Product.supplier_id))
            ).filter(
                Product.status == ProductStatus.ACTIVE.value
            ).scalar() or 0
            
            total_spent = self.db.query(
                func.sum(Supplier.total_spent)
            ).filter(
                Supplier.is_active == True
            ).scalar() or 0
            
            avg_delivery = self.db.query(
                func.avg(Supplier.avg_delivery_days)
            ).filter(
                and_(
                    Supplier.is_active == True,
                    Supplier.avg_delivery_days.isnot(None)
                )
            ).scalar() or 0
            
            return {
                'total_suppliers': total_suppliers,
                'active_suppliers': active_suppliers,
                'suppliers_with_products': suppliers_with_products,
                'total_spent': float(total_spent),
                'avg_delivery_days': float(avg_delivery) if avg_delivery else 0
            }
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get supplier summary: {str(e)}")
    
    async def deactivate_supplier(self, supplier_id: int) -> bool:
        """Deactivate supplier and handle related products"""
        try:
            supplier = await self.get_by_id(supplier_id)
            if not supplier:
                return False
            
            # Deactivate supplier
            supplier.is_active = False
            supplier.updated_at = datetime.utcnow()
            
            # YAGNI: Simple approach - just warn about active products
            # In a more complex system, might auto-deactivate products or reassign
            active_product_count = self.db.query(func.count(Product.id)).filter(
                and_(
                    Product.supplier_id == supplier_id,
                    Product.status == ProductStatus.ACTIVE.value
                )
            ).scalar() or 0
            
            self.db.commit()
            
            return {
                'success': True,
                'active_products_warning': active_product_count > 0,
                'active_product_count': active_product_count
            }
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise EbayManagerException(f"Failed to deactivate supplier: {str(e)}")
    
    async def get_top_suppliers(self, limit: int = 10, by: str = 'products') -> List[Dict[str, Any]]:
        """Get top suppliers - YAGNI: Simple ranking only"""
        try:
            if by == 'products':
                # Top suppliers by product count
                results = self.db.query(
                    Supplier.id,
                    Supplier.name,
                    Supplier.code,
                    func.count(Product.id).label('product_count')
                ).join(Product).filter(
                    and_(
                        Supplier.is_active == True,
                        Product.status == ProductStatus.ACTIVE.value
                    )
                ).group_by(Supplier.id, Supplier.name, Supplier.code).order_by(
                    desc('product_count')
                ).limit(limit).all()
                
                return [{
                    'supplier_id': r.id,
                    'name': r.name,
                    'code': r.code,
                    'product_count': r.product_count
                } for r in results]
                
            elif by == 'spending':
                # Top suppliers by total spent
                results = self.db.query(
                    Supplier.id,
                    Supplier.name,
                    Supplier.code,
                    Supplier.total_spent
                ).filter(
                    Supplier.is_active == True
                ).order_by(desc(Supplier.total_spent)).limit(limit).all()
                
                return [{
                    'supplier_id': r.id,
                    'name': r.name,
                    'code': r.code,
                    'total_spent': float(r.total_spent)
                } for r in results]
            
            else:
                raise ValueError(f"Invalid ranking criteria: {by}")
                
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get top suppliers: {str(e)}")