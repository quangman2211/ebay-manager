# Phase 4: Order Management Module Implementation

## Overview
Implement comprehensive order management system with full CRUD operations, status tracking, order fulfillment workflow, and dashboard integration matching Dashboard9.png design. Supports multi-account order processing with real-time updates and reporting.

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **OrderService**: Only handle order business logic and workflows
- **OrderRepository**: Only manage order data persistence operations
- **OrderStatusService**: Only manage order status transitions and validation
- **TrackingService**: Only handle shipping tracking operations
- **OrderReportService**: Only generate order analytics and reports
- **OrderNotificationService**: Only manage order-related notifications

### Open/Closed Principle (OCP)
- **Status Workflow**: Extensible order status transitions without modifying core logic
- **Payment Processors**: Add new payment methods without changing order processing
- **Shipping Providers**: Support multiple shipping services through common interface
- **Report Generators**: Add new report types without changing existing reports

### Liskov Substitution Principle (LSP)
- **IOrderRepository**: All order repository implementations honor same contract
- **IPaymentProcessor**: All payment processors are interchangeable
- **IShippingProvider**: All shipping services follow same interface

### Interface Segregation Principle (ISP)
- **Separate Interfaces**: Order CRUD vs Status Management vs Reporting
- **Client-Specific**: Order viewers don't depend on admin-only operations
- **Fine-Grained Operations**: Read vs Write vs Update operations separated

### Dependency Inversion Principle (DIP)
- **Abstract Dependencies**: Order services depend on interfaces, not concrete classes
- **Injected Components**: All external services injected as dependencies

## Order Domain Models

### Enhanced Order Entity
```python
# app/models/order.py - Single Responsibility: Order data representation
from sqlalchemy import Column, String, DateTime, Decimal, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from enum import Enum
from app.database import Base

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"

class PaymentStatus(Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class ShippingStatus(Enum):
    NOT_SHIPPED = "not_shipped"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    RETURNED = "returned"
    EXCEPTION = "exception"

class Order(Base):
    """Order entity with comprehensive tracking"""
    __tablename__ = "orders"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    ebay_order_id = Column(String(50), nullable=False)
    
    # Order status tracking
    order_status = Column(ENUM(OrderStatus), default=OrderStatus.PENDING)
    payment_status = Column(ENUM(PaymentStatus), default=PaymentStatus.PENDING)
    shipping_status = Column(ENUM(ShippingStatus), default=ShippingStatus.NOT_SHIPPED)
    
    # Buyer information
    buyer_name = Column(String(200), nullable=False)
    buyer_email = Column(String(255))
    buyer_phone = Column(String(20))
    buyer_username = Column(String(100))
    
    # Financial information
    order_total = Column(Decimal(10, 2), nullable=False)
    subtotal = Column(Decimal(10, 2))
    shipping_cost = Column(Decimal(10, 2), default=0)
    tax_amount = Column(Decimal(10, 2), default=0)
    discount_amount = Column(Decimal(10, 2), default=0)
    
    # Shipping information
    shipping_address = Column(JSON)
    shipping_method = Column(String(100))
    tracking_number = Column(String(100))
    shipping_carrier = Column(String(50))
    expected_delivery_date = Column(DateTime)
    
    # Timestamps
    order_date = Column(DateTime, nullable=False)
    payment_date = Column(DateTime)
    shipped_date = Column(DateTime)
    delivered_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    order_notes = Column(String(1000))
    internal_notes = Column(String(1000))
    priority_level = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Relationships
    account = relationship("Account", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    order_history = relationship("OrderHistory", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order {self.ebay_order_id}>"

class OrderItem(Base):
    """Order line items"""
    __tablename__ = "order_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id"))
    
    # Item details
    item_title = Column(String(500), nullable=False)
    item_sku = Column(String(100))
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Decimal(10, 2), nullable=False)
    total_price = Column(Decimal(10, 2), nullable=False)
    
    # eBay specific
    ebay_item_id = Column(String(50))
    transaction_id = Column(String(50))
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    listing = relationship("Listing", back_populates="order_items")

class OrderHistory(Base):
    """Order status change history"""
    __tablename__ = "order_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    
    # Status change details
    previous_status = Column(ENUM(OrderStatus))
    new_status = Column(ENUM(OrderStatus), nullable=False)
    change_reason = Column(String(500))
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    changed_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional context
    notes = Column(String(1000))
    system_generated = Column(Boolean, default=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_history")
    user = relationship("User")
```

### Order Service Interface
```python
# app/services/interfaces/order_interface.py - Interface Segregation
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderFilter

class IOrderReader(ABC):
    """Interface for order read operations"""
    
    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Optional[Order]:
        """Get order by ID"""
        pass
    
    @abstractmethod
    async def get_by_ebay_order_id(self, account_id: UUID, ebay_order_id: str) -> Optional[Order]:
        """Get order by eBay order ID"""
        pass
    
    @abstractmethod
    async def get_account_orders(
        self, 
        account_id: UUID, 
        filters: OrderFilter,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Order]:
        """Get filtered orders for account"""
        pass

class IOrderWriter(ABC):
    """Interface for order write operations"""
    
    @abstractmethod
    async def create_order(self, order_data: OrderCreate) -> Order:
        """Create new order"""
        pass
    
    @abstractmethod
    async def update_order(self, order_id: UUID, order_data: OrderUpdate) -> Order:
        """Update existing order"""
        pass
    
    @abstractmethod
    async def update_status(self, order_id: UUID, new_status: OrderStatus, reason: str, user_id: UUID) -> Order:
        """Update order status with history tracking"""
        pass

class IOrderAnalytics(ABC):
    """Interface for order analytics operations"""
    
    @abstractmethod
    async def get_order_metrics(self, account_id: UUID, date_range: tuple) -> Dict[str, Any]:
        """Get order metrics for dashboard"""
        pass
    
    @abstractmethod
    async def get_status_distribution(self, account_id: UUID) -> Dict[str, int]:
        """Get order count by status"""
        pass
```

### Order Service Implementation
```python
# app/services/order_service.py - Single Responsibility: Order business logic
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
import logging
from app.services.interfaces.order_interface import IOrderReader, IOrderWriter, IOrderAnalytics
from app.repositories.order import OrderRepository
from app.repositories.order_history import OrderHistoryRepository
from app.models.order import Order, OrderStatus, OrderHistory
from app.schemas.order import OrderCreate, OrderUpdate, OrderFilter

class OrderService(IOrderReader, IOrderWriter, IOrderAnalytics):
    """Comprehensive order management service"""
    
    def __init__(
        self, 
        order_repo: OrderRepository,
        order_history_repo: OrderHistoryRepository
    ):
        self._order_repo = order_repo
        self._order_history_repo = order_history_repo
        self._logger = logging.getLogger(__name__)
    
    async def get_by_id(self, order_id: UUID) -> Optional[Order]:
        """Get order by ID with related data"""
        return await self._order_repo.get_by_id_with_items(order_id)
    
    async def get_by_ebay_order_id(self, account_id: UUID, ebay_order_id: str) -> Optional[Order]:
        """Get order by eBay order ID"""
        return await self._order_repo.get_by_ebay_order_id(account_id, ebay_order_id)
    
    async def get_account_orders(
        self, 
        account_id: UUID, 
        filters: OrderFilter,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Order]:
        """Get filtered orders for account"""
        return await self._order_repo.get_filtered_orders(account_id, filters, skip, limit)
    
    async def create_order(self, order_data: OrderCreate) -> Order:
        """Create new order with validation"""
        # Business rule: Check for duplicate eBay order ID
        existing = await self.get_by_ebay_order_id(
            order_data.account_id, 
            order_data.ebay_order_id
        )
        
        if existing:
            raise ValueError(f"Order with eBay ID {order_data.ebay_order_id} already exists")
        
        # Create order
        order = await self._order_repo.create(order_data)
        
        # Create initial history entry
        await self._create_history_entry(
            order.id,
            None,
            order.order_status,
            "Order created",
            order_data.created_by if hasattr(order_data, 'created_by') else None,
            system_generated=True
        )
        
        self._logger.info(f"Created order {order.ebay_order_id} for account {order.account_id}")
        return order
    
    async def update_order(self, order_id: UUID, order_data: OrderUpdate) -> Order:
        """Update existing order with validation"""
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Track changes for history
        changes = []
        for field, new_value in order_data.dict(exclude_unset=True).items():
            if hasattr(order, field):
                old_value = getattr(order, field)
                if old_value != new_value:
                    changes.append(f"{field}: {old_value} → {new_value}")
        
        # Update order
        updated_order = await self._order_repo.update(order_id, order_data)
        
        # Create history entry if there were changes
        if changes:
            await self._create_history_entry(
                order_id,
                order.order_status,
                updated_order.order_status,
                f"Order updated: {', '.join(changes)}",
                order_data.updated_by if hasattr(order_data, 'updated_by') else None
            )
        
        return updated_order
    
    async def update_status(
        self, 
        order_id: UUID, 
        new_status: OrderStatus, 
        reason: str, 
        user_id: UUID
    ) -> Order:
        """Update order status with business logic validation"""
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Validate status transition
        if not self._is_valid_status_transition(order.order_status, new_status):
            raise ValueError(f"Invalid status transition from {order.order_status} to {new_status}")
        
        previous_status = order.order_status
        
        # Update order status
        order.order_status = new_status
        order.updated_at = datetime.utcnow()
        
        # Set additional timestamps based on status
        if new_status == OrderStatus.SHIPPED:
            order.shipped_date = datetime.utcnow()
        elif new_status == OrderStatus.DELIVERED:
            order.delivered_date = datetime.utcnow()
        
        updated_order = await self._order_repo.update_status(order_id, new_status)
        
        # Create history entry
        await self._create_history_entry(
            order_id,
            previous_status,
            new_status,
            reason,
            user_id
        )
        
        self._logger.info(f"Updated order {order.ebay_order_id} status: {previous_status} → {new_status}")
        return updated_order
    
    async def get_order_metrics(self, account_id: UUID, date_range: tuple) -> Dict[str, Any]:
        """Get order metrics for dashboard"""
        start_date, end_date = date_range
        
        # Get basic counts
        total_orders = await self._order_repo.count_orders_in_range(
            account_id, start_date, end_date
        )
        
        # Get revenue metrics
        revenue_data = await self._order_repo.get_revenue_metrics(
            account_id, start_date, end_date
        )
        
        # Get status distribution
        status_distribution = await self.get_status_distribution(account_id)
        
        # Get pending orders (requires attention)
        pending_orders = await self._order_repo.count_by_status(
            account_id, OrderStatus.PENDING
        )
        
        return {
            "total_orders": total_orders,
            "total_revenue": revenue_data.get("total_revenue", 0),
            "average_order_value": revenue_data.get("average_order_value", 0),
            "status_distribution": status_distribution,
            "pending_orders": pending_orders,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    async def get_status_distribution(self, account_id: UUID) -> Dict[str, int]:
        """Get order count by status"""
        return await self._order_repo.get_status_counts(account_id)
    
    def _is_valid_status_transition(self, current: OrderStatus, new: OrderStatus) -> bool:
        """Validate order status transitions"""
        # Define valid status transitions
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
            OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED, OrderStatus.RETURNED],
            OrderStatus.DELIVERED: [OrderStatus.RETURNED],
            OrderStatus.CANCELLED: [],  # Terminal state
            OrderStatus.RETURNED: [OrderStatus.REFUNDED],
            OrderStatus.REFUNDED: []  # Terminal state
        }
        
        return new in valid_transitions.get(current, [])
    
    async def _create_history_entry(
        self,
        order_id: UUID,
        previous_status: Optional[OrderStatus],
        new_status: OrderStatus,
        reason: str,
        user_id: Optional[UUID],
        system_generated: bool = False
    ):
        """Create order history entry"""
        history = OrderHistory(
            order_id=order_id,
            previous_status=previous_status,
            new_status=new_status,
            change_reason=reason,
            changed_by=user_id,
            system_generated=system_generated
        )
        
        await self._order_history_repo.create(history)
```

### Order Repository Implementation
```python
# app/repositories/order.py - Single Responsibility: Order data access
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from app.repositories.base import IRepository
from app.models.order import Order, OrderStatus, OrderItem
from app.schemas.order import OrderCreate, OrderUpdate, OrderFilter

class OrderRepository(IRepository[Order]):
    """Repository for order data access operations"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, order_id: UUID) -> Optional[Order]:
        """Get order by ID"""
        result = await self._session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id_with_items(self, order_id: UUID) -> Optional[Order]:
        """Get order by ID with order items loaded"""
        result = await self._session.execute(
            select(Order)
            .options(selectinload(Order.order_items))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_ebay_order_id(self, account_id: UUID, ebay_order_id: str) -> Optional[Order]:
        """Get order by eBay order ID"""
        result = await self._session.execute(
            select(Order).where(
                and_(
                    Order.account_id == account_id,
                    Order.ebay_order_id == ebay_order_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_filtered_orders(
        self, 
        account_id: UUID, 
        filters: OrderFilter,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Order]:
        """Get orders with filtering"""
        query = select(Order).where(Order.account_id == account_id)
        
        # Apply filters
        if filters.status:
            query = query.where(Order.order_status.in_(filters.status))
        
        if filters.date_from:
            query = query.where(Order.order_date >= filters.date_from)
        
        if filters.date_to:
            query = query.where(Order.order_date <= filters.date_to)
        
        if filters.buyer_name:
            query = query.where(Order.buyer_name.ilike(f"%{filters.buyer_name}%"))
        
        if filters.order_total_min:
            query = query.where(Order.order_total >= filters.order_total_min)
        
        if filters.order_total_max:
            query = query.where(Order.order_total <= filters.order_total_max)
        
        if filters.tracking_number:
            query = query.where(Order.tracking_number.ilike(f"%{filters.tracking_number}%"))
        
        # Apply sorting
        if filters.sort_by:
            if filters.sort_order == "desc":
                query = query.order_by(desc(getattr(Order, filters.sort_by)))
            else:
                query = query.order_by(getattr(Order, filters.sort_by))
        else:
            query = query.order_by(desc(Order.order_date))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self._session.execute(query)
        return result.scalars().all()
    
    async def create(self, order_data: OrderCreate) -> Order:
        """Create new order"""
        order = Order(**order_data.dict())
        self._session.add(order)
        await self._session.commit()
        await self._session.refresh(order)
        return order
    
    async def update(self, order_id: UUID, order_data: OrderUpdate) -> Order:
        """Update existing order"""
        order = await self.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        for field, value in order_data.dict(exclude_unset=True).items():
            setattr(order, field, value)
        
        order.updated_at = datetime.utcnow()
        await self._session.commit()
        await self._session.refresh(order)
        return order
    
    async def update_status(self, order_id: UUID, new_status: OrderStatus) -> Order:
        """Update order status"""
        order = await self.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        order.order_status = new_status
        order.updated_at = datetime.utcnow()
        
        await self._session.commit()
        await self._session.refresh(order)
        return order
    
    async def delete(self, order_id: UUID) -> bool:
        """Delete order"""
        order = await self.get_by_id(order_id)
        if order:
            await self._session.delete(order)
            await self._session.commit()
            return True
        return False
    
    async def count_orders_in_range(
        self, 
        account_id: UUID, 
        start_date: date, 
        end_date: date
    ) -> int:
        """Count orders in date range"""
        result = await self._session.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.account_id == account_id,
                    Order.order_date >= start_date,
                    Order.order_date <= end_date
                )
            )
        )
        return result.scalar()
    
    async def get_revenue_metrics(
        self, 
        account_id: UUID, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """Get revenue metrics for date range"""
        result = await self._session.execute(
            select(
                func.sum(Order.order_total).label("total_revenue"),
                func.avg(Order.order_total).label("average_order_value"),
                func.count(Order.id).label("order_count")
            ).where(
                and_(
                    Order.account_id == account_id,
                    Order.order_date >= start_date,
                    Order.order_date <= end_date,
                    Order.order_status.in_([OrderStatus.DELIVERED, OrderStatus.SHIPPED])
                )
            )
        )
        
        metrics = result.first()
        return {
            "total_revenue": float(metrics.total_revenue or 0),
            "average_order_value": float(metrics.average_order_value or 0),
            "order_count": metrics.order_count or 0
        }
    
    async def get_status_counts(self, account_id: UUID) -> Dict[str, int]:
        """Get order count by status"""
        result = await self._session.execute(
            select(
                Order.order_status,
                func.count(Order.id).label("count")
            ).where(
                Order.account_id == account_id
            ).group_by(Order.order_status)
        )
        
        status_counts = {}
        for row in result:
            status_counts[row.order_status.value] = row.count
        
        return status_counts
    
    async def count_by_status(self, account_id: UUID, status: OrderStatus) -> int:
        """Count orders by specific status"""
        result = await self._session.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.account_id == account_id,
                    Order.order_status == status
                )
            )
        )
        return result.scalar()
```

## FastAPI Endpoints

### Order Management API
```python
# app/routers/orders.py - Single Responsibility: Order HTTP endpoints
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.services.order_service import OrderService
from app.dependencies.auth import get_current_user, require_permission
from app.schemas.order import (
    OrderResponse, OrderCreate, OrderUpdate, OrderFilter, 
    OrderStatusUpdate, OrderMetrics
)
from app.models.token import TokenPayload

router = APIRouter(prefix="/api/accounts/{account_id}/orders", tags=["orders"])

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    account_id: UUID,
    status: Optional[List[str]] = Query(None),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    buyer_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: TokenPayload = Depends(require_permission("read", account_id)),
    order_service: OrderService = Depends(get_order_service)
):
    """Get orders with filtering"""
    filters = OrderFilter(
        status=status,
        date_from=date_from,
        date_to=date_to,
        buyer_name=buyer_name
    )
    
    orders = await order_service.get_account_orders(account_id, filters, skip, limit)
    return [OrderResponse.from_orm(order) for order in orders]

@router.get("/metrics", response_model=OrderMetrics)
async def get_order_metrics(
    account_id: UUID,
    date_from: date = Query(description="Start date for metrics"),
    date_to: date = Query(description="End date for metrics"),
    current_user: TokenPayload = Depends(require_permission("read", account_id)),
    order_service: OrderService = Depends(get_order_service)
):
    """Get order metrics for dashboard"""
    metrics = await order_service.get_order_metrics(
        account_id, (date_from, date_to)
    )
    return OrderMetrics(**metrics)

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    account_id: UUID,
    order_id: UUID,
    current_user: TokenPayload = Depends(require_permission("read", account_id)),
    order_service: OrderService = Depends(get_order_service)
):
    """Get single order by ID"""
    order = await order_service.get_by_id(order_id)
    
    if not order or order.account_id != account_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.from_orm(order)

@router.post("/", response_model=OrderResponse)
async def create_order(
    account_id: UUID,
    order_data: OrderCreate,
    current_user: TokenPayload = Depends(require_permission("write", account_id)),
    order_service: OrderService = Depends(get_order_service)
):
    """Create new order"""
    # Ensure account_id matches URL parameter
    order_data.account_id = account_id
    order_data.created_by = current_user.user_id
    
    try:
        order = await order_service.create_order(order_data)
        return OrderResponse.from_orm(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    account_id: UUID,
    order_id: UUID,
    order_data: OrderUpdate,
    current_user: TokenPayload = Depends(require_permission("write", account_id)),
    order_service: OrderService = Depends(get_order_service)
):
    """Update existing order"""
    # Verify order belongs to account
    existing_order = await order_service.get_by_id(order_id)
    if not existing_order or existing_order.account_id != account_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order_data.updated_by = current_user.user_id
    
    try:
        order = await order_service.update_order(order_id, order_data)
        return OrderResponse.from_orm(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    account_id: UUID,
    order_id: UUID,
    status_data: OrderStatusUpdate,
    current_user: TokenPayload = Depends(require_permission("write", account_id)),
    order_service: OrderService = Depends(get_order_service)
):
    """Update order status"""
    # Verify order belongs to account
    existing_order = await order_service.get_by_id(order_id)
    if not existing_order or existing_order.account_id != account_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    try:
        order = await order_service.update_status(
            order_id,
            status_data.new_status,
            status_data.reason,
            current_user.user_id
        )
        return OrderResponse.from_orm(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{order_id}")
async def delete_order(
    account_id: UUID,
    order_id: UUID,
    current_user: TokenPayload = Depends(require_permission("admin", account_id)),
    order_service: OrderService = Depends(get_order_service)
):
    """Delete order (admin only)"""
    # Verify order belongs to account
    existing_order = await order_service.get_by_id(order_id)
    if not existing_order or existing_order.account_id != account_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    success = await order_service.delete_order(order_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete order"
        )
    
    return {"message": "Order deleted successfully"}
```

## Implementation Tasks

### Task 1: Order Models & Database
1. **Create Order Models**
   - Order entity with comprehensive fields
   - OrderItem for line items
   - OrderHistory for status tracking

2. **Database Migration**
   - Create tables with proper indexes
   - Set up foreign key relationships
   - Add constraints and validation

3. **Test Database Layer**
   - Repository unit tests
   - Database constraint tests
   - Performance tests with large datasets

### Task 2: Order Service Implementation
1. **Create Order Service**
   - CRUD operations with business logic
   - Status workflow management
   - History tracking

2. **Add Business Rules**
   - Status transition validation
   - Duplicate order prevention
   - Data validation rules

3. **Test Business Logic**
   - Unit tests for all service methods
   - Integration tests with repository
   - Business rule validation tests

### Task 3: REST API Implementation
1. **Create Order Endpoints**
   - Full CRUD API endpoints
   - Filtering and pagination
   - Status update endpoints

2. **Add Security**
   - Permission-based access control
   - Account isolation enforcement
   - Input validation and sanitization

3. **Test API Layer**
   - Endpoint integration tests
   - Security tests
   - Performance tests

### Task 4: Frontend Integration
1. **Dashboard Integration**
   - Order metrics display matching Dashboard1.png
   - Order list view matching Dashboard9.png
   - Real-time status updates

2. **Order Management UI**
   - Order detail views
   - Status update interface
   - Bulk operations support

3. **Test Frontend Integration**
   - End-to-end user workflow tests
   - UI component tests
   - Cross-browser compatibility tests

## Quality Gates

### Performance Requirements
- [ ] Order list loading: <500ms for 1000 orders
- [ ] Order detail loading: <200ms
- [ ] Status updates: <100ms response time
- [ ] Dashboard metrics: <1 second load time
- [ ] Support 10,000+ orders per account

### Business Logic Requirements
- [ ] Order status transitions validated
- [ ] Duplicate order prevention working
- [ ] History tracking for all changes
- [ ] Account isolation strictly enforced
- [ ] Data integrity maintained across operations

### SOLID Compliance Checklist
- [ ] OrderService has single responsibility for business logic
- [ ] Repository only handles data access
- [ ] Status management is extensible
- [ ] API endpoints separated by concern
- [ ] All dependencies properly injected

---
**Next Phase**: Listing Management Module with inventory tracking and performance analytics.