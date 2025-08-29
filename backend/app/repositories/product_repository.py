"""
Product Repository Implementation
Following SOLID principles - Single Responsibility for product data access
YAGNI compliance: Essential queries only, no complex inventory analytics
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError

from app.models.product import Product, ProductStatus, Supplier
from app.schemas.product import ProductFilter
from app.repositories.base import BaseRepository
from app.core.exceptions import EbayManagerException

class ProductRepositoryInterface(ABC):
    """
    SOLID: Interface Segregation & Dependency Inversion
    Clean contract for product data access
    """
    
    @abstractmethod
    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU"""
        pass
    
    @abstractmethod
    async def get_by_supplier(self, supplier_id: int, offset: int = 0, limit: int = 100) -> List[Product]:
        """Get products for specific supplier with pagination"""
        pass
    
    @abstractmethod
    async def search(self, filters: ProductFilter, offset: int = 0, limit: int = 100) -> Tuple[List[Product], int]:
        """Search products with filters"""
        pass
    
    @abstractmethod
    async def get_low_stock_products(self, supplier_id: Optional[int] = None) -> List[Product]:
        """Get products at or below reorder point"""
        pass
    
    @abstractmethod
    async def update_inventory(self, product_id: int, quantity_change: int) -> bool:
        """Update product inventory"""
        pass

class ProductRepository(BaseRepository[Product], ProductRepositoryInterface):
    """
    SOLID: Single Responsibility - Product data access only
    YAGNI: Essential queries only, no complex inventory analytics
    """
    
    def __init__(self, db: Session):
        super().__init__(db, Product)
    
    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU with supplier info"""
        try:
            return self.db.query(Product).options(
                joinedload(Product.supplier)
            ).filter(Product.sku == sku).first()
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get product by SKU: {str(e)}")
    
    async def get_by_supplier(self, supplier_id: int, offset: int = 0, limit: int = 100) -> List[Product]:
        """Get products for specific supplier with pagination"""
        try:
            return self.db.query(Product).options(
                joinedload(Product.supplier)
            ).filter(
                Product.supplier_id == supplier_id
            ).order_by(desc(Product.updated_at)).offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get supplier products: {str(e)}")
    
    async def search(self, filters: ProductFilter, offset: int = 0, limit: int = 100) -> Tuple[List[Product], int]:
        """
        Search products with filters - YAGNI: Basic filtering only
        Returns (results, total_count)
        """
        try:
            # Base query with supplier join for search
            query = self.db.query(Product).options(joinedload(Product.supplier))
            
            # Apply filters
            conditions = []
            
            if filters.supplier_id:
                conditions.append(Product.supplier_id == filters.supplier_id)
            
            if filters.status:
                conditions.append(Product.status == filters.status.value)
            
            if filters.category:
                conditions.append(Product.category.ilike(f"%{filters.category}%"))
            
            if filters.brand:
                conditions.append(Product.brand.ilike(f"%{filters.brand}%"))
            
            if filters.search:
                search_term = f"%{filters.search}%"
                conditions.append(
                    or_(
                        Product.name.ilike(search_term),
                        Product.sku.ilike(search_term),
                        Product.description.ilike(search_term)
                    )
                )
            
            if filters.low_stock is True:
                conditions.append(Product.quantity_on_hand <= Product.reorder_point)
            
            if filters.min_price:
                conditions.append(Product.selling_price >= filters.min_price)
            
            if filters.max_price:
                conditions.append(Product.selling_price <= filters.max_price)
            
            # Apply all conditions
            if conditions:
                query = query.filter(and_(*conditions))
            
            # Get total count
            total = query.count()
            
            # Get paginated results with supplier info
            results = query.order_by(desc(Product.updated_at)).offset(offset).limit(limit).all()
            
            return results, total
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to search products: {str(e)}")
    
    async def get_low_stock_products(self, supplier_id: Optional[int] = None) -> List[Product]:
        """Get products that are at or below reorder point"""
        try:
            query = self.db.query(Product).options(
                joinedload(Product.supplier)
            ).filter(
                and_(
                    Product.quantity_on_hand <= Product.reorder_point,
                    Product.status == ProductStatus.ACTIVE.value
                )
            )
            
            if supplier_id:
                query = query.filter(Product.supplier_id == supplier_id)
            
            return query.order_by(asc(Product.quantity_on_hand)).all()
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get low stock products: {str(e)}")
    
    async def update_inventory(self, product_id: int, quantity_change: int) -> bool:
        """Update product inventory - YAGNI: Simple quantity tracking"""
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return False
            
            new_quantity = max(0, product.quantity_on_hand + quantity_change)
            old_quantity = product.quantity_on_hand
            
            # Update quantity
            product.quantity_on_hand = new_quantity
            product.updated_at = datetime.utcnow()
            
            # Auto-update status based on inventory - YAGNI: Simple rules only
            if new_quantity == 0 and product.status == ProductStatus.ACTIVE.value:
                product.status = ProductStatus.OUT_OF_STOCK.value
            elif old_quantity == 0 and new_quantity > 0 and product.status == ProductStatus.OUT_OF_STOCK.value:
                product.status = ProductStatus.ACTIVE.value
            
            self.db.commit()
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise EbayManagerException(f"Failed to update inventory: {str(e)}")
    
    async def get_inventory_summary(self, supplier_id: Optional[int] = None) -> Dict[str, Any]:
        """Get basic inventory summary - YAGNI: Simple metrics only"""
        try:
            query = self.db.query(
                func.count(Product.id).label('total_products'),
                func.sum(Product.quantity_on_hand).label('total_quantity'),
                func.sum(Product.cost_price * Product.quantity_on_hand).label('total_value'),
                func.count(func.case(
                    [(Product.quantity_on_hand <= Product.reorder_point, 1)], 
                    else_=None
                )).label('low_stock_count')
            ).filter(Product.status == ProductStatus.ACTIVE.value)
            
            if supplier_id:
                query = query.filter(Product.supplier_id == supplier_id)
            
            result = query.first()
            
            return {
                'total_products': result.total_products or 0,
                'total_quantity': result.total_quantity or 0,
                'total_value': float(result.total_value) if result.total_value else 0.0,
                'low_stock_count': result.low_stock_count or 0
            }
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get inventory summary: {str(e)}")
    
    async def get_by_status(self, status: str, supplier_id: Optional[int] = None, limit: int = 100) -> List[Product]:
        """Get products by status for specific supplier"""
        try:
            query = self.db.query(Product).options(
                joinedload(Product.supplier)
            ).filter(Product.status == status)
            
            if supplier_id:
                query = query.filter(Product.supplier_id == supplier_id)
            
            return query.order_by(desc(Product.updated_at)).limit(limit).all()
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get products by status: {str(e)}")
    
    async def count_by_supplier(self, supplier_id: int) -> int:
        """Get total product count for supplier"""
        try:
            return self.db.query(Product).filter(
                Product.supplier_id == supplier_id
            ).count()
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to count products: {str(e)}")
    
    async def bulk_update_prices(self, product_ids: List[int], price_changes: Dict[str, Any]) -> int:
        """YAGNI: Simple bulk price update"""
        try:
            if not product_ids:
                return 0
            
            # Basic bulk update for prices
            update_data = {}
            if 'cost_price' in price_changes:
                update_data['cost_price'] = price_changes['cost_price']
            if 'selling_price' in price_changes:
                update_data['selling_price'] = price_changes['selling_price']
                
                # Recalculate margin if both prices are provided
                if 'cost_price' in price_changes:
                    cost = price_changes['cost_price']
                    selling = price_changes['selling_price']
                    if cost > 0:
                        update_data['margin_percent'] = ((selling - cost) / cost) * 100
            
            if update_data:
                update_data['updated_at'] = datetime.utcnow()
                
                updated_count = self.db.query(Product).filter(
                    Product.id.in_(product_ids)
                ).update(
                    update_data,
                    synchronize_session=False
                )
                
                self.db.commit()
                return updated_count
            
            return 0
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise EbayManagerException(f"Failed to bulk update prices: {str(e)}")
    
    async def get_margin_analysis(self, supplier_id: Optional[int] = None) -> Dict[str, Any]:
        """Get basic margin analysis - YAGNI: Simple calculations only"""
        try:
            query = self.db.query(
                func.avg(Product.margin_percent).label('avg_margin'),
                func.min(Product.margin_percent).label('min_margin'),
                func.max(Product.margin_percent).label('max_margin'),
                func.count(Product.id).label('product_count')
            ).filter(
                and_(
                    Product.status == ProductStatus.ACTIVE.value,
                    Product.margin_percent.isnot(None)
                )
            )
            
            if supplier_id:
                query = query.filter(Product.supplier_id == supplier_id)
            
            result = query.first()
            
            return {
                'avg_margin': float(result.avg_margin) if result.avg_margin else 0.0,
                'min_margin': float(result.min_margin) if result.min_margin else 0.0,
                'max_margin': float(result.max_margin) if result.max_margin else 0.0,
                'product_count': result.product_count or 0
            }
            
        except SQLAlchemyError as e:
            raise EbayManagerException(f"Failed to get margin analysis: {str(e)}")