# Phase 6: Product & Supplier Management Implementation

## Overview
Implement product catalog and supplier management system with inventory synchronization, cost tracking, and supplier relationship management. Supports multi-supplier product sourcing with automated reordering and profitability analysis.

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **ProductService**: Only handle product catalog business logic
- **SupplierService**: Only manage supplier relationships and data
- **InventoryService**: Only track product inventory levels
- **CostTrackingService**: Only calculate and track product costs
- **ReorderService**: Only handle automated reordering logic

### Open/Closed Principle (OCP)
- **Pricing Strategies**: Extensible pricing rules without modifying core logic
- **Supplier Integrations**: Add new supplier APIs without changing existing code
- **Inventory Tracking**: Support different inventory methods
- **Cost Calculations**: Pluggable cost calculation algorithms

### Liskov Substitution Principle (LSP)
- **IProductRepository**: All product repositories interchangeable
- **ISupplierConnector**: All supplier integrations follow same contract
- **ICostCalculator**: All cost calculators substitutable

### Interface Segregation Principle (ISP)
- **Separate Interfaces**: Product management vs Supplier management vs Inventory
- **Client-Specific**: Buyers don't depend on admin-only operations
- **Operation-Specific**: Read vs Write vs Analytics operations

### Dependency Inversion Principle (DIP)
- **Abstract Dependencies**: Services depend on interfaces
- **Injected Components**: All external services injected

## Product Domain Models

```python
# app/models/product.py - Single Responsibility: Product data representation
from sqlalchemy import Column, String, DateTime, Decimal, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from app.database import Base

class Product(Base):
    """Product catalog entity"""
    __tablename__ = "products"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    sku = Column(String(100), nullable=False, unique=True)
    
    # Basic product information
    name = Column(String(500), nullable=False)
    description = Column(Text)
    category = Column(String(200))
    brand = Column(String(100))
    model = Column(String(100))
    
    # Physical attributes
    weight = Column(Decimal(8, 3))  # kg
    dimensions = Column(JSON)  # {"length": x, "width": y, "height": z}
    color = Column(String(50))
    size = Column(String(50))
    
    # Inventory tracking
    current_stock = Column(Integer, default=0)
    reserved_stock = Column(Integer, default=0)  # Reserved for pending orders
    reorder_point = Column(Integer, default=10)
    max_stock_level = Column(Integer, default=100)
    
    # Pricing and costs
    purchase_cost = Column(Decimal(10, 2))  # Cost from supplier
    selling_price = Column(Decimal(10, 2))  # Recommended selling price
    minimum_price = Column(Decimal(10, 2))  # Minimum acceptable price
    
    # Product status
    is_active = Column(Boolean, default=True)
    is_discontinued = Column(Boolean, default=False)
    
    # Images and media
    primary_image_url = Column(String(500))
    image_urls = Column(JSON)  # Array of image URLs
    
    # SEO and marketing
    tags = Column(JSON)  # Array of tags
    search_keywords = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="products")
    supplier_products = relationship("SupplierProduct", back_populates="product")
    listings = relationship("Listing", back_populates="product")
    inventory_transactions = relationship("InventoryTransaction", back_populates="product")
    
class Supplier(Base):
    """Supplier entity"""
    __tablename__ = "suppliers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    # Basic supplier information
    name = Column(String(200), nullable=False)
    company_name = Column(String(200))
    contact_person = Column(String(100))
    
    # Contact information
    email = Column(String(255))
    phone = Column(String(20))
    website = Column(String(255))
    
    # Address
    address = Column(JSON)  # Complete address object
    
    # Business details
    tax_id = Column(String(50))
    payment_terms = Column(String(100))  # "Net 30", "COD", etc.
    minimum_order_amount = Column(Decimal(10, 2))
    
    # Performance tracking
    rating = Column(Decimal(3, 2), default=5.0)  # 1.0 to 5.0
    total_orders = Column(Integer, default=0)
    on_time_delivery_rate = Column(Decimal(5, 2), default=100.0)  # Percentage
    quality_rating = Column(Decimal(3, 2), default=5.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_preferred = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_order_date = Column(DateTime)
    
    # Relationships
    account = relationship("Account", back_populates="suppliers")
    supplier_products = relationship("SupplierProduct", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    
class SupplierProduct(Base):
    """Product-Supplier relationship with pricing"""
    __tablename__ = "supplier_products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    
    # Supplier specific data
    supplier_sku = Column(String(100))  # Supplier's internal SKU
    supplier_name = Column(String(200))  # Supplier's name for this product
    
    # Pricing
    unit_cost = Column(Decimal(10, 2), nullable=False)
    bulk_pricing = Column(JSON)  # Tiered pricing: [{"min_qty": 10, "price": 9.50}]
    
    # Logistics
    lead_time_days = Column(Integer, default=7)
    minimum_order_quantity = Column(Integer, default=1)
    packaging_unit = Column(Integer, default=1)  # How many units per package
    
    # Status
    is_primary_supplier = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    
    # Performance tracking
    last_order_date = Column(DateTime)
    total_ordered = Column(Integer, default=0)
    average_lead_time = Column(Integer)  # Actual average lead time
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="supplier_products")
    supplier = relationship("Supplier", back_populates="supplier_products")
    
class InventoryTransaction(Base):
    """Inventory movement tracking"""
    __tablename__ = "inventory_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False)  # IN, OUT, ADJUSTMENT
    quantity = Column(Integer, nullable=False)  # Positive for IN, negative for OUT
    unit_cost = Column(Decimal(10, 2))
    
    # Reference information
    reference_type = Column(String(50))  # "purchase_order", "sale", "adjustment", etc.
    reference_id = Column(String(100))  # ID of the related entity
    
    # Context
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="inventory_transactions")
    user = relationship("User")
```

## Product Service Implementation

```python
# app/services/product_service.py - Single Responsibility: Product business logic
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
import logging
from app.repositories.product import ProductRepository
from app.repositories.supplier import SupplierRepository
from app.services.inventory_service import InventoryService
from app.models.product import Product, Supplier, SupplierProduct
from app.schemas.product import ProductCreate, ProductUpdate, ProductFilter

class ProductService:
    """Product catalog management service"""
    
    def __init__(
        self,
        product_repo: ProductRepository,
        supplier_repo: SupplierRepository,
        inventory_service: InventoryService
    ):
        self._product_repo = product_repo
        self._supplier_repo = supplier_repo
        self._inventory_service = inventory_service
        self._logger = logging.getLogger(__name__)
    
    async def create_product(self, product_data: ProductCreate) -> Product:
        """Create new product with validation"""
        # Validate unique SKU within account
        existing = await self._product_repo.get_by_sku(
            product_data.account_id, product_data.sku
        )
        if existing:
            raise ValueError(f"Product with SKU {product_data.sku} already exists")
        
        # Validate pricing
        if product_data.selling_price and product_data.purchase_cost:
            if product_data.selling_price <= product_data.purchase_cost:
                self._logger.warning(
                    f"Product {product_data.sku} has negative margin"
                )
        
        # Create product
        product = await self._product_repo.create(product_data)
        
        # Initialize inventory tracking
        if product_data.current_stock and product_data.current_stock > 0:
            await self._inventory_service.add_stock(
                product.id,
                product_data.current_stock,
                product_data.purchase_cost,
                "initial_stock",
                None  # system generated
            )
        
        self._logger.info(f"Created product {product.name} ({product.sku})")
        return product
    
    async def update_product(self, product_id: UUID, product_data: ProductUpdate) -> Product:
        """Update existing product"""
        existing_product = await self._product_repo.get_by_id(product_id)
        if not existing_product:
            raise ValueError(f"Product {product_id} not found")
        
        # Handle stock level changes
        if product_data.current_stock is not None:
            stock_difference = product_data.current_stock - existing_product.current_stock
            if stock_difference != 0:
                await self._inventory_service.adjust_stock(
                    product_id,
                    stock_difference,
                    "manual_adjustment",
                    getattr(product_data, 'updated_by', None)
                )
        
        # Update product
        updated_product = await self._product_repo.update(product_id, product_data)
        return updated_product
    
    async def get_products_needing_reorder(self, account_id: UUID) -> List[Product]:
        """Get products that need reordering"""
        return await self._product_repo.get_products_below_reorder_point(account_id)
    
    async def calculate_product_profitability(
        self,
        product_id: UUID
    ) -> Dict[str, Any]:
        """Calculate product profitability metrics"""
        product = await self._product_repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        # Get sales data (this would integrate with order/listing data)
        sales_data = await self._get_product_sales_data(product_id)
        
        # Calculate metrics
        total_revenue = sales_data.get('total_revenue', 0)
        total_units_sold = sales_data.get('units_sold', 0)
        average_selling_price = (
            total_revenue / total_units_sold if total_units_sold > 0 else 0
        )
        
        gross_profit_per_unit = (
            average_selling_price - (product.purchase_cost or 0)
        )
        gross_profit_margin = (
            (gross_profit_per_unit / average_selling_price * 100)
            if average_selling_price > 0 else 0
        )
        
        return {
            "product_id": product_id,
            "sku": product.sku,
            "name": product.name,
            "purchase_cost": float(product.purchase_cost or 0),
            "average_selling_price": average_selling_price,
            "gross_profit_per_unit": gross_profit_per_unit,
            "gross_profit_margin": gross_profit_margin,
            "total_revenue": total_revenue,
            "units_sold": total_units_sold,
            "current_stock": product.current_stock
        }
    
    async def suggest_reorder_quantities(self, account_id: UUID) -> List[Dict[str, Any]]:
        """Suggest reorder quantities for products"""
        products_to_reorder = await self.get_products_needing_reorder(account_id)
        suggestions = []
        
        for product in products_to_reorder:
            # Simple reorder logic - could be enhanced with demand forecasting
            suggested_quantity = max(
                product.reorder_point * 2,  # Basic safety stock
                product.max_stock_level - product.current_stock
            )
            
            # Get best supplier for this product
            best_supplier = await self._get_best_supplier_for_product(product.id)
            
            suggestions.append({
                "product_id": product.id,
                "sku": product.sku,
                "name": product.name,
                "current_stock": product.current_stock,
                "reorder_point": product.reorder_point,
                "suggested_quantity": suggested_quantity,
                "best_supplier": best_supplier,
                "estimated_cost": (
                    suggested_quantity * (best_supplier.get('unit_cost', 0))
                    if best_supplier else 0
                )
            })
        
        return suggestions
    
    async def _get_product_sales_data(self, product_id: UUID) -> Dict[str, Any]:
        """Get sales data for product (integration point with order system)"""
        # This would integrate with the order/listing management system
        # For now, returning placeholder data
        return {
            "total_revenue": 0,
            "units_sold": 0,
            "last_sale_date": None
        }
    
    async def _get_best_supplier_for_product(self, product_id: UUID) -> Optional[Dict[str, Any]]:
        """Get best supplier for product based on cost, rating, and availability"""
        supplier_products = await self._product_repo.get_product_suppliers(product_id)
        
        if not supplier_products:
            return None
        
        # Simple scoring algorithm - could be enhanced with more sophisticated logic
        best_supplier = None
        best_score = 0
        
        for sp in supplier_products:
            if not sp.is_available:
                continue
            
            # Score based on cost (lower is better), rating, and delivery performance
            cost_score = 100 / (sp.unit_cost + 1)  # Inverse cost score
            rating_score = sp.supplier.quality_rating * 20  # Scale to 100
            delivery_score = sp.supplier.on_time_delivery_rate
            
            total_score = (cost_score * 0.4 + rating_score * 0.3 + delivery_score * 0.3)
            
            if total_score > best_score:
                best_score = total_score
                best_supplier = {
                    "supplier_id": sp.supplier_id,
                    "supplier_name": sp.supplier.name,
                    "unit_cost": float(sp.unit_cost),
                    "lead_time_days": sp.lead_time_days,
                    "minimum_order_quantity": sp.minimum_order_quantity,
                    "score": total_score
                }
        
        return best_supplier
```

## Implementation Tasks

### Task 1: Product & Supplier Models
1. **Create Domain Models**
   - Product entity with comprehensive attributes
   - Supplier entity with performance tracking
   - SupplierProduct relationship with pricing
   - InventoryTransaction for stock movements

2. **Database Setup**
   - Create tables with proper indexes
   - Set up relationships and constraints
   - Add performance optimization

### Task 2: Business Logic Services
1. **Product Service**
   - CRUD operations with validation
   - Profitability calculations
   - Reorder point management

2. **Supplier Service**
   - Supplier relationship management
   - Performance tracking
   - Best supplier selection

3. **Inventory Service**
   - Stock level tracking
   - Transaction recording
   - Automated adjustments

### Task 3: API Implementation
1. **Product Endpoints**
   - Full CRUD operations
   - Advanced filtering and search
   - Bulk operations

2. **Supplier Endpoints**
   - Supplier management
   - Product-supplier relationships
   - Performance reporting

### Task 4: Integration Points
1. **Listing Integration**
   - Link products to listings
   - Inventory synchronization
   - Price update propagation

2. **Order Integration**
   - Stock reservation for orders
   - Automatic stock deduction
   - Sales data integration

## Quality Gates

### Performance Requirements
- [ ] Product queries: <200ms for 10,000 products
- [ ] Inventory updates: <50ms response time
- [ ] Supplier analysis: <1 second for complex calculations
- [ ] Support 100,000+ products per account

### Business Logic Requirements
- [ ] Accurate inventory tracking
- [ ] Profitability calculations correct
- [ ] Reorder suggestions working
- [ ] Supplier performance metrics accurate
- [ ] Multi-supplier support functional

### SOLID Compliance
- [ ] Single responsibility per service
- [ ] Extensible pricing and cost calculations
- [ ] Interchangeable supplier connectors
- [ ] Separated inventory operations
- [ ] Proper dependency injection

---
**Final Phase**: Customer & Communication Management with unified messaging.